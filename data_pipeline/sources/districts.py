"""Gán QUẬN/HUYỆN cho từng quán từ toạ độ.

VÌ SAO CẦN: dataset cũ KHÔNG có trường quận. Người dùng Hà Nội nghĩ theo quận
("quán ở Cầu Giấy", "gần Hoàn Kiếm"), và đây cũng là chiều thống kê quan trọng nhất khi
đánh giá độ phủ dữ liệu ("phủ được bao nhiêu quận?").

VÌ SAO KHÔNG DÙNG REVERSE GEOCODING: Nominatim giới hạn 1 request/giây. Với 4000+ quán
là hơn 70 phút, và mỗi lần thêm dữ liệu lại phải chạy lại. Thay vào đó:

    tải ranh giới hành chính MỘT LẦN  ->  kiểm tra điểm-trong-đa-giác OFFLINE

Cách này chạy trong vài giây, không phụ thuộc mạng khi chạy lại, và cho kết quả tất định.

Thuật toán: ray casting (đếm số lần tia cắt cạnh đa giác). Thuần Python, không cần
shapely/geopandas - tránh thêm phụ thuộc nặng chỉ để làm một việc nhỏ.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

MIRRORS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
USER_AGENT = "MoodBite/1.0 (academic graduation project)"

# Ở Việt Nam, OSM đánh admin_level=6 cho quận/huyện/thị xã.
# (admin_level=4 là tỉnh/thành phố trực thuộc trung ương.)
DISTRICT_ADMIN_LEVEL = 6

DEFAULT_CACHE = Path("data_pipeline/data_raw/hanoi_districts.geojson")

Point = Tuple[float, float]        # (lat, lng)
Ring = List[Point]


HANOI_BBOX = (20.85, 105.70, 21.40, 106.05)


def fetch_district_boundaries(
    cache_path: Path | str = DEFAULT_CACHE,
    force: bool = False,
    bbox: Tuple[float, float, float, float] = HANOI_BBOX,
) -> Dict[str, List[Ring]]:
    """Tải ranh giới quận/huyện Hà Nội. Có cache trên đĩa -> chỉ tải mạng lần đầu.

    Trả về {tên quận: [vòng toạ độ, ...]}. Một quận có thể gồm nhiều vòng (đảo, phần rời).
    """
    cache_path = Path(cache_path)
    if cache_path.exists() and not force:
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            logger.info("Dung ranh gioi da cache: %d quan", len(data))
            return {name: [[tuple(p) for p in ring] for ring in rings]
                    for name, rings in data.items()}
        except (json.JSONDecodeError, OSError, TypeError):
            logger.warning("Cache ranh gioi hong, tai lai")

    # Dùng BBOX chứ không dùng `area["name"="Hà Nội"]`: truy vấn theo area bắt Overpass
    # dựng vùng từ quan hệ hành chính cấp tỉnh, rất nặng và luôn trả HTTP 504 (đã đo).
    # Bbox rẻ hơn nhiều; đổi lại sẽ lấy dư vài quận của tỉnh giáp ranh - vô hại, vì ta
    # chỉ tra quận cho những quán vốn đã nằm trong bbox Hà Nội.
    south, west, north, east = bbox
    query = (
        "[out:json][timeout:180];"
        f'relation["admin_level"="{DISTRICT_ADMIN_LEVEL}"]["boundary"="administrative"]'
        f"({south},{west},{north},{east});"
        "out geom;"
    )
    payload = urllib.parse.urlencode({"data": query}).encode()

    # Overpass hay trả 504 lúc tải nặng. Thử lại vài vòng qua mọi mirror, giãn dần thời
    # gian chờ - tải hụt ở đây nghĩa là TOÀN BỘ quán mất trường quận, nên đáng để kiên nhẫn.
    elements: List[dict] = []
    attempts = [(mirror, wait) for wait in (0, 5, 15) for mirror in MIRRORS]
    for mirror, wait in attempts:
        if wait:
            time.sleep(wait)
        try:
            request = urllib.request.Request(
                mirror, data=payload, headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(request, timeout=240) as response:
                elements = json.loads(response.read().decode("utf-8"))["elements"]
            if elements:
                break
        except Exception as exc:
            logger.warning("Mirror %s loi khi tai ranh gioi: %s", mirror, exc)

    if not elements:
        logger.error("Khong tai duoc ranh gioi quan/huyen")
        return {}

    districts: Dict[str, List[Ring]] = {}
    for element in elements:
        name = (element.get("tags") or {}).get("name")
        if not name:
            continue
        segments: List[Ring] = []
        for member in element.get("members", []):
            # Chỉ lấy đường bao ngoài; bỏ "inner" (lỗ) cho đơn giản - quận ở Hà Nội
            # không có lỗ ảnh hưởng tới việc gán quán.
            if member.get("type") != "way" or member.get("role") not in ("outer", ""):
                continue
            geometry = member.get("geometry") or []
            segment = [(p["lat"], p["lon"]) for p in geometry if "lat" in p and "lon" in p]
            if len(segment) >= 2:
                segments.append(segment)

        rings = stitch_rings(segments)
        if rings:
            districts.setdefault(name, []).extend(rings)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(districts, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Da tai va cache %d quan/huyen", len(districts))
    return districts


def stitch_rings(segments: List[Ring]) -> List[Ring]:
    """Nối các đoạn `way` rời thành các VÒNG KHÉP KÍN.

    VÌ SAO CẦN: Overpass `out geom` trả ranh giới một quận dưới dạng NHIỀU đoạn way rời
    nhau, KHÔNG phải một đa giác khép kín. Nếu đem từng đoạn hở đi kiểm tra
    điểm-trong-đa-giác thì kết quả luôn sai (bug đã gặp: mọi điểm đều trả None).

    Cách nối: lấy một đoạn làm vòng khởi đầu, rồi liên tục tìm đoạn khác có đầu hoặc
    cuối trùng với điểm cuối của vòng, nối tiếp (đảo chiều nếu cần), cho tới khi vòng
    khép lại hoặc không còn đoạn nào ghép được.
    """
    remaining = [list(s) for s in segments if len(s) >= 2]
    rings: List[Ring] = []

    while remaining:
        ring = remaining.pop(0)
        extended = True
        while extended and ring[0] != ring[-1]:
            extended = False
            for index, candidate in enumerate(remaining):
                if candidate[0] == ring[-1]:
                    ring.extend(candidate[1:])
                elif candidate[-1] == ring[-1]:
                    ring.extend(reversed(candidate[:-1]))
                elif candidate[-1] == ring[0]:
                    ring = candidate[:-1] + ring
                elif candidate[0] == ring[0]:
                    ring = list(reversed(candidate[1:])) + ring
                else:
                    continue
                remaining.pop(index)
                extended = True
                break

        # Vòng chưa khép (dữ liệu OSM thiếu đoạn) vẫn dùng được: khép tạm bằng cách nối
        # điểm cuối về điểm đầu. Sai số nhỏ hơn nhiều so với bỏ hẳn cả quận.
        if len(ring) >= 3:
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            rings.append(ring)

    return rings


def point_in_ring(point: Point, ring: Sequence[Point]) -> bool:
    """Ray casting: bắn một tia ngang từ điểm sang phải, đếm số cạnh nó cắt.

    Số lẻ = nằm trong, số chẵn = nằm ngoài.
    """
    lat, lng = point
    inside = False
    count = len(ring)
    j = count - 1
    for i in range(count):
        lat_i, lng_i = ring[i]
        lat_j, lng_j = ring[j]
        # Cạnh có bắc qua vĩ độ của điểm không, và giao điểm có nằm bên phải không.
        if (lat_i > lat) != (lat_j > lat):
            denominator = lat_j - lat_i
            if denominator != 0:
                crossing_lng = lng_i + (lat - lat_i) * (lng_j - lng_i) / denominator
                if lng < crossing_lng:
                    inside = not inside
        j = i
    return inside


class DistrictLocator:
    """Tra quận từ toạ độ. Dựng một lần rồi gọi `find()` nhiều lần."""

    def __init__(self, districts: Dict[str, List[Ring]]) -> None:
        self.districts = districts
        # Hộp bao của từng vòng, để loại nhanh trước khi chạy ray casting (đắt hơn).
        self._bounds: Dict[str, List[Tuple[Ring, float, float, float, float]]] = {}
        for name, rings in districts.items():
            entries = []
            for ring in rings:
                lats = [p[0] for p in ring]
                lngs = [p[1] for p in ring]
                entries.append((ring, min(lats), max(lats), min(lngs), max(lngs)))
            self._bounds[name] = entries

    @property
    def district_count(self) -> int:
        return len(self.districts)

    def find(self, lat: float, lng: float) -> Optional[str]:
        for name, entries in self._bounds.items():
            for ring, min_lat, max_lat, min_lng, max_lng in entries:
                if not (min_lat <= lat <= max_lat and min_lng <= lng <= max_lng):
                    continue  # loại nhanh bằng hộp bao
                if point_in_ring((lat, lng), ring):
                    return name
        return None

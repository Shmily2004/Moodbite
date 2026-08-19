"""NGUỒN: OpenStreetMap qua Overpass API.

VÌ SAO CHỌN NGUỒN NÀY LÀM CHÍNH:
  - Miễn phí, KHÔNG cần API key, KHÔNG cần đăng ký.
  - Giấy phép ODbL cho phép dùng lại (chỉ cần ghi công "© OpenStreetMap contributors").
  - Phủ tốt về TÊN + TOẠ ĐỘ + LOẠI HÌNH (100% bản ghi có).

GIỚI HẠN THẲNG THẮN:
  - KHÔNG có rating, KHÔNG có review, KHÔNG có ảnh. Đây là dữ liệu bản đồ, không phải
    nền tảng đánh giá. Muốn có rating/review phải dùng Google Places (tốn tiền, cần key).
  - Giá (`price`) hầu như không có.

BÀI HỌC ĐÃ SỬA Ở BẢN NÀY:
  1. Query cả bbox Hà Nội một lần -> Overpass trả HTTP 504. Phải CHIA Ô (tiling).
  2. Mirror overpass-api.de thường xuyên 504 vào giờ cao điểm -> phải có DANH SÁCH MIRROR
     và tự đổi khi lỗi.
  3. Bản cào cũ chỉ lấy name/toạ độ/cuisine, BỎ PHÍ hàng chục tag hữu ích
     (outdoor_seating, air_conditioning, diet:*, delivery, takeaway, phone, opening_hours...).
     Bản này lấy hết những tag đó -> lấp đúng các trường mà MoodBite cần để lọc/xếp hạng.
"""
from __future__ import annotations

import json
import logging
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from data_pipeline.sources.base import (
    CONFIDENCE_COMMUNITY,
    RawPlace,
    dedupe_places,
    utc_now_iso,
)

logger = logging.getLogger(__name__)

# Bbox Hà Nội (nam, tây, bắc, đông).
HANOI_BBOX = (20.85, 105.70, 21.40, 106.05)

# PHẠM VI THU THẬP: **CHỈ HÀ NỘI** — chủ dự án chốt ngày 2026-08-19.
#
# Bảng này từng có 8 thành phố (TP.HCM, Đà Nẵng, Hải Phòng, Cần Thơ, Huế, Nha Trang,
# Đà Lạt). Đã GỠ BỎ theo yêu cầu: sản phẩm chỉ phục vụ Hà Nội, thêm quán tỉnh khác chỉ
# làm loãng dữ liệu và làm bộ lọc bán kính vô nghĩa.
#
# ĐỪNG THÊM THÀNH PHỐ VÀO ĐÂY nếu chưa hỏi chủ dự án. Bảng có nhiều mục là lời mời chạy
# nhầm, và một lượt harvest nhầm sẽ trộn hàng chục nghìn quán tỉnh khác vào dataset -
# gỡ ra rất tốn công vì lúc đó đã qua bước khử trùng lặp và gán quận.
CITY_BBOXES: dict[str, tuple[float, float, float, float]] = {
    "ha_noi": HANOI_BBOX,
}

# Mirror xếp theo độ tin cậy đo được (2026-08): kumi.systems ổn định nhất,
# overpass-api.de hay 504 vào giờ cao điểm.
MIRRORS = [
    # Thu tu theo so slot con trong do duoc tu /api/status (do 2026-08-16):
    # overpass-api.de cap 2 slot/IP va thuong con trong; kumi.systems khong gioi han
    # slot nhung hay qua tai vi phuc vu nhieu nguoi.
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

USER_AGENT = "MoodBite/1.0 (academic graduation project; OSM data via Overpass)"

# Loại hình lấy về. Bám theo tài liệu OSM Map Features (amenity + shop liên quan ăn uống).
AMENITY_VALUES = "restaurant|cafe|fast_food|bar|pub|food_court|ice_cream|biergarten"
SHOP_VALUES = "bakery|confectionery|deli|pastry|tea|coffee|greengrocer"

# amenity/shop -> nhãn tiếng Việt, khớp cách đặt tên của dữ liệu Google đang có
# (để `dish_knowledge_base.json` và bộ lọc mood khớp được cùng một bộ từ vựng).
CATEGORY_LABELS = {
    "restaurant": "Nhà hàng",
    "cafe": "Quán cà phê",
    "fast_food": "Nhà hàng ăn nhanh",
    "bar": "Quán bar",
    "pub": "Quán bia",
    "food_court": "Khu ăn uống",
    "ice_cream": "Quán kem",
    "biergarten": "Quán bia",
    "bakery": "Tiệm bánh",
    "confectionery": "Tiệm bánh kẹo",
    "deli": "Cửa hàng đồ nguội",
    "pastry": "Tiệm bánh ngọt",
    "tea": "Quán trà",
    "coffee": "Quán cà phê",
    "greengrocer": "Cửa hàng rau quả",
}

# Tag tiện nghi: tên tag OSM -> nhãn nội bộ. Chỉ nhận khi giá trị là "yes".
AMENITY_TAGS = {
    "outdoor_seating": "outdoor_seating",
    "air_conditioning": "air_conditioning",
    "wheelchair": "wheelchair_accessible",
    "internet_access": "wifi",
    "smoking": "smoking_area",
    "highchair": "highchair",
    "toilets": "toilets",
    "drive_through": "drive_through",
    "reservation": "reservation",
    "live_music": "live_music",
}

# Tag chế độ ăn. Đây chính là trường mà dataset cũ KHÔNG HỀ CÓ, khiến bộ lọc
# `dietary_restrictions` của API phải trả cảnh báo "không hỗ trợ".
DIET_TAGS = {
    "diet:vegetarian": "vegetarian",
    "diet:vegan": "vegan",
    "diet:halal": "halal",
    "diet:kosher": "kosher",
    "diet:gluten_free": "gluten_free",
}


def _truthy(value: Optional[str]) -> bool:
    return str(value).strip().lower() in {"yes", "only", "designated", "limited", "wlan"}


class OsmOverpassSource:
    """Adapter OSM. Thoả `SourceAdapter` ở `sources/base.py`."""

    def __init__(
        self,
        bbox: tuple[float, float, float, float] = HANOI_BBOX,
        tile_size_deg: float = 0.08,
        cache_dir: Path | str = "data_pipeline/data_raw/.osm_cache",
        sleep_between_tiles: float = 1.5,
        timeout_seconds: int = 60,
        retry_backoff: tuple[int, ...] = (3, 10, 20, 40, 60),
    ) -> None:
        self.bbox = bbox
        self.tile_size_deg = tile_size_deg
        self.cache_dir = Path(cache_dir)
        self.sleep_between_tiles = sleep_between_tiles
        self.timeout_seconds = timeout_seconds
        # Số vòng thử lại và thời gian chờ giữa các vòng (giây).
        self.retry_backoff = retry_backoff
        self._mirror_index = 0

    @property
    def name(self) -> str:
        return "openstreetmap"

    def is_available(self) -> tuple[bool, str]:
        """OSM luôn dùng được, chỉ cần có mạng."""
        try:
            request = urllib.request.Request(
                "https://overpass-api.de/api/status", headers={"User-Agent": USER_AGENT}
            )
            urllib.request.urlopen(request, timeout=10).read()
            return True, "san sang"
        except Exception as exc:
            return False, f"khong ket noi duoc Overpass: {exc}"

    # --- chia ô ---------------------------------------------------------

    def _tiles(self) -> Iterator[tuple[float, float, float, float]]:
        """Chia bbox thành lưới ô nhỏ.

        Cần thiết vì Overpass giới hạn thời gian xử lý MỖI request: hỏi cả Hà Nội một
        lần luôn trả 504. Ô nhỏ -> mỗi request nhẹ, và lỗi 1 ô không mất cả mẻ.

        Đếm số ô bằng SỐ NGUYÊN thay vì cộng dồn số thực: cộng dồn 0.1 nhiều lần sinh
        sai số (105.0+0.1+0.1 = 105.19999999999999 < 105.2) và tạo ra ô rộng bằng 0 ở
        rìa - vẫn tốn 1 request và 1.5s chờ nhưng không bao giờ trả về gì.
        """
        south, west, north, east = self.bbox
        # `round(..., 9)` trước `ceil` vì phép chia số thực cho sai số: 0.2/0.1 cho
        # 2.0000000000000004, khiến ceil ra 3 và sinh thêm một cột ô rộng bằng 0.
        rows = max(1, math.ceil(round((north - south) / self.tile_size_deg, 9)))
        cols = max(1, math.ceil(round((east - west) / self.tile_size_deg, 9)))

        for row in range(rows):
            tile_south = south + row * self.tile_size_deg
            tile_north = min(tile_south + self.tile_size_deg, north)
            for col in range(cols):
                tile_west = west + col * self.tile_size_deg
                tile_east = min(tile_west + self.tile_size_deg, east)
                # Chốt chặn cuối: không bao giờ trả ô suy biến (tốn request, không có dữ liệu).
                if tile_north - tile_south <= 0 or tile_east - tile_west <= 0:
                    continue
                yield (
                    round(tile_south, 4), round(tile_west, 4),
                    round(tile_north, 4), round(tile_east, 4),
                )

    def _query(self, tile: tuple[float, float, float, float]) -> str:
        bbox = ",".join(str(v) for v in tile)
        return (
            f"[out:json][timeout:{self.timeout_seconds}];"
            f"(nwr[amenity~'^({AMENITY_VALUES})$']({bbox});"
            f"nwr[shop~'^({SHOP_VALUES})$']({bbox}););"
            # `meta` thêm timestamp/version/user của lần sửa cuối. Không có nó thì không
            # biết bản ghi cũ hay mới - và đo 2026-08-19 cho thấy chuyện đó rất đáng biết:
            # chỉ 34,9% quán OSM Hà Nội được sửa trong năm 2026, cũ nhất là năm 2010.
            # Chi phí: gói tin nặng thêm chút ít, không thêm lần gọi mạng nào.
            "out center tags meta;"
        )

    def _fetch_tile(self, tile: tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        """Lấy 1 ô, tự đổi mirror khi lỗi. Có cache trên đĩa để chạy lại không tốn công."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / f"tile_{'_'.join(str(v) for v in tile)}.json"
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                cache_file.unlink(missing_ok=True)  # cache hỏng thì lấy lại

        payload = urllib.parse.urlencode({"data": self._query(tile)}).encode()
        last_error = "khong ro"

        # Overpass trả 504 khá thường xuyên khi máy chủ đang tải nặng, NHƯNG cùng một
        # query lúc rảnh chỉ mất ~8 giây. Nói cách khác lỗi là TẠM THỜI, không phải do
        # query sai -> phải thử lại nhiều vòng với thời gian chờ tăng dần thay vì bỏ ô.
        # Bỏ ô = mất vĩnh viễn toàn bộ quán trong khu vực đó.
        for round_index, backoff in enumerate(self.retry_backoff):
            for mirror_offset in range(len(MIRRORS)):
                mirror = MIRRORS[(self._mirror_index + mirror_offset) % len(MIRRORS)]
                try:
                    request = urllib.request.Request(
                        mirror, data=payload, headers={"User-Agent": USER_AGENT}
                    )
                    with urllib.request.urlopen(
                        request, timeout=self.timeout_seconds + 30
                    ) as response:
                        elements = json.loads(response.read().decode("utf-8"))["elements"]
                    # Mirror này chạy được -> lần sau ưu tiên dùng luôn.
                    self._mirror_index = (self._mirror_index + mirror_offset) % len(MIRRORS)
                    cache_file.write_text(
                        json.dumps(elements, ensure_ascii=False), encoding="utf-8"
                    )
                    return elements
                except (urllib.error.URLError, urllib.error.HTTPError, OSError, KeyError) as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    logger.debug("Mirror %s loi o o %s: %s", mirror, tile, last_error)

            if round_index < len(self.retry_backoff) - 1:
                logger.info(
                    "O %s chua lay duoc (%s) - cho %ds roi thu lai",
                    tile, last_error, backoff,
                )
                time.sleep(backoff)

        logger.warning("Bo qua o %s sau %d vong thu (%s)",
                       tile, len(self.retry_backoff), last_error)
        return []

    # --- chuyển đổi -----------------------------------------------------

    @staticmethod
    def _address(tags: Dict[str, str]) -> Optional[str]:
        parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:quarter") or tags.get("addr:suburb"),
            tags.get("addr:district") or tags.get("addr:city_district"),
            tags.get("addr:city") or "Hà Nội",
        ]
        joined = ", ".join(p for p in parts if p)
        return joined or None

    @staticmethod
    def _category(tags: Dict[str, str]) -> Optional[str]:
        key = tags.get("amenity") or tags.get("shop")
        return CATEGORY_LABELS.get(key, key.replace("_", " ").title() if key else None)

    def _to_place(self, element: Dict[str, Any]) -> Optional[RawPlace]:
        tags = element.get("tags") or {}
        name = tags.get("name") or tags.get("name:vi") or tags.get("name:en")
        if not name:
            # Quán không có tên thì không hiển thị được cho người dùng -> bỏ.
            return None

        lat = element.get("lat") or (element.get("center") or {}).get("lat")
        lng = element.get("lon") or (element.get("center") or {}).get("lon")
        if lat is None or lng is None:
            return None

        osm_type, osm_id = element.get("type", "node"), element.get("id")

        aliases = [
            tags[k]
            for k in ("name:en", "name:vi", "alt_name", "old_name", "short_name", "brand")
            if tags.get(k) and tags[k] != name
        ]

        amenities = [
            label for tag, label in AMENITY_TAGS.items() if _truthy(tags.get(tag))
        ]
        dietary = [label for tag, label in DIET_TAGS.items() if _truthy(tags.get(tag))]

        # OSM ghi cuisine dạng nhiều giá trị: "vietnamese;noodle;pho"
        cuisine_raw = tags.get("cuisine")
        cuisine = cuisine_raw.split(";")[0].strip() if cuisine_raw else None
        # Giá trị cuisine cũng là gợi ý MÓN khá tốt ("pho", "banh_mi", "chicken").
        dishes = (
            [c.strip().replace("_", " ") for c in cuisine_raw.split(";") if c.strip()]
            if cuisine_raw
            else []
        )

        return RawPlace(
            placeId=f"osm-{osm_type}-{osm_id}",
            title=name,
            source=self.name,
            source_url=f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
            last_updated=utc_now_iso(),
            # NGÀY SỬA THẬT trên OSM, khác hẳn `last_updated` (ngày ta cào).
            source_updated_at=element.get("timestamp"),
            source_datasets=["openstreetmap"],
            # `check_date` = ngày một người thật đi tới tận nơi xác minh. Bằng chứng mạnh
            # nhất có thể có, nhưng chỉ 4,3% quán có (đo 2026-08-19).
            # `survey:date` là tag cũ cùng nghĩa, vẫn còn dùng ở một số nơi.
            surveyed_at=tags.get("check_date") or tags.get("survey:date"),
            data_confidence=CONFIDENCE_COMMUNITY,
            categoryName=self._category(tags),
            cuisine=cuisine,
            aliases=aliases,
            location={"lat": str(lat), "lng": str(lng)},
            address=self._address(tags),
            district=tags.get("addr:district") or tags.get("addr:city_district"),
            street=tags.get("addr:street"),
            city=tags.get("addr:city") or "Hà Nội",
            phone=tags.get("phone") or tags.get("contact:phone"),
            website=tags.get("website") or tags.get("contact:website"),
            openingHours=tags.get("opening_hours"),
            amenities=amenities,
            dietary=dietary,
            delivery=_truthy(tags.get("delivery")) if tags.get("delivery") else None,
            takeaway=_truthy(tags.get("takeaway")) if tags.get("takeaway") else None,
            dishes=dishes,
            menu=tags.get("menu") or tags.get("website:menu"),
        )

    # --- API chính ------------------------------------------------------

    def fetch(self) -> List[RawPlace]:
        tiles = list(self._tiles())
        logger.info("OSM: bat dau lay %d o (moi o %.2f do)", len(tiles), self.tile_size_deg)

        places: List[RawPlace] = []
        failed_tiles = 0
        for index, tile in enumerate(tiles, start=1):
            elements = self._fetch_tile(tile)
            if not elements:
                failed_tiles += 1
            for element in elements:
                place = self._to_place(element)
                if place:
                    places.append(place)

            if index % 10 == 0 or index == len(tiles):
                logger.info(
                    "OSM: %d/%d o, da thu %d quan", index, len(tiles), len(places)
                )
            time.sleep(self.sleep_between_tiles)

        unique, duplicates = dedupe_places(places)
        logger.info(
            "OSM: xong. %d quan duy nhat (bo %d trung lap, %d o loi)",
            len(unique), duplicates, failed_tiles,
        )
        return unique

"""
MoodBite - Gộp nhiều file JSON cào được (Apify hoặc nguồn khác) thành 1 file CSV
sẵn sàng cho data_cleaning.py.

Vì sao cần script này:
- Các file *_raw_places.json cào được có field `location` dạng object lồng nhau
  ({"lat": "...", "lng": "..."}), trong khi data_cleaning.py/feature_engineering.py
  đang đọc CSV với cột phẳng `location/lat`, `location/lng`.
- Nhiều lần cào (nhiều file) thường trùng lặp địa điểm -> cần khử trùng lặp.
- Cần lọc bỏ các địa điểm không phải quán ăn/nhà hàng (dùng lại filter_restaurants.py
  đã có sẵn và đã test).

Cách dùng:
    python data_pipeline/merge_and_prepare_raw.py

Input: mọi file *.json trong data_pipeline/data_raw/ (định dạng list các dict,
       field như title, address, categoryName, location.lat/lng, ...)
Output: data_pipeline/data_raw/merged_places.csv
        (rồi chạy tiếp: python data_pipeline/data_cleaning.py)
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from data_pipeline.filter_restaurants import is_restaurant_item

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _dedupe_key(record: Dict[str, Any]) -> tuple:
    """Khóa khử trùng lặp: ưu tiên placeId (định danh duy nhất từ Google Maps)
    nếu có, nếu không thì fallback về (title, address) đã chuẩn hóa."""
    place_id = record.get("placeId")
    if place_id:
        return ("placeId", str(place_id).strip().lower())
    return (
        "title_address",
        str(record.get("title", "")).strip().lower(),
        str(record.get("address", "")).strip().lower(),
    )


def merge_raw_json_files(raw_dir: Path) -> List[Dict[str, Any]]:
    json_files = sorted(raw_dir.glob("*.json"))
    if not json_files:
        logger.warning(f"Không tìm thấy file JSON nào trong {raw_dir}")
        return []

    all_records: List[Dict[str, Any]] = []
    for f in json_files:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as e:
            logger.error(f"Không đọc được {f}: {e}")
            continue

        if not isinstance(data, list):
            logger.warning(f"Bỏ qua {f}: không phải định dạng list record")
            continue

        logger.info(f"Đọc {f.name}: {len(data)} record")
        all_records.extend(data)

    logger.info(f"Tổng cộng (trước khử trùng lặp): {len(all_records)} record từ {len(json_files)} file")

    unique_records = _dedupe_keep_richest(all_records)
    logger.info(f"Sau khi khử trùng lặp: {len(unique_records)} record")
    return unique_records


# Trường quyết định "bản ghi nào giàu thông tin hơn". Không đếm mọi field vì Apify trả về
# 80+ field, phần lớn là rác kỹ thuật (searchString, isAdvertisement...) và có mặt ở mọi
# bản ghi nên không phân biệt được gì.
RICHNESS_FIELDS = (
    "totalScore", "reviewsCount", "reviews", "price", "imageUrls", "imagesCount",
    "openingHours", "phone", "website", "categoryName", "address", "cuisine",
    "district", "amenities", "dietary", "menu",
)


def _richness(record: Dict[str, Any]) -> int:
    """Đếm số trường CÓ dữ liệu thật. Dùng để chọn bản ghi tốt hơn khi trùng lặp."""
    return sum(
        1 for field in RICHNESS_FIELDS
        if record.get(field) not in (None, "", [], {}, "[]")
    )


def _dedupe_keep_richest(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Khử trùng lặp, GIỮ BẢN GHI GIÀU THÔNG TIN NHẤT cho mỗi địa điểm.

    VÌ SAO KHÔNG GIỮ BẢN ĐẦU TIÊN: cách cũ phụ thuộc THỨ TỰ TÊN FILE - thêm một file cào
    mới mà đặt tên sai thứ tự là dữ liệu mới bị bản cũ (rỗng hơn) đè mất. Đã suýt xảy ra:
    15 quán lẽ ra nhận được rating từ đợt cào mới nhưng bị bản cũ không có rating giữ chỗ.

    Chọn theo độ giàu thông tin thì thứ tự file không còn quan trọng nữa.
    """
    best: Dict[tuple, Dict[str, Any]] = {}
    order: List[tuple] = []

    for record in records:
        key = _dedupe_key(record)
        if key not in best:
            best[key] = record
            order.append(key)
        elif _richness(record) > _richness(best[key]):
            best[key] = record

    return [best[key] for key in order]


# Tiền tố placeId -> nguồn. Dùng để bù thông tin nguồn cho dữ liệu cào từ trước khi
# pipeline có khái niệm provenance (các file 01-03 do Apify cào từ Google Maps).
PLACE_ID_SOURCE_PREFIX = {
    "ChIJ": ("google_maps_apify", "verified"),
    "osm-": ("openstreetmap", "community"),
}


def backfill_provenance(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Bảo đảm MỌI bản ghi đều trả lời được "ở đâu ra, đáng tin tới đâu".

    Các file cào cũ (01-03) không có field `source` vì lúc đó pipeline chưa có khái niệm
    này. Suy ngược từ tiền tố `placeId` là cách duy nhất đúng - KHÔNG bịa thêm dữ liệu,
    chỉ ghi lại sự thật vốn đã nằm trong định danh.
    """
    filled = 0
    for record in records:
        # Chuẩn hoá biến thể tên nguồn TRƯỚC, không phụ thuộc việc có đủ field hay chưa.
        # Bản cào cũ ghi "OSM", bản mới ghi "openstreetmap" - để lẫn hai cách viết thì
        # thống kê theo nguồn sẽ tách nhầm thành hai nguồn khác nhau.
        if str(record.get("source") or "").strip().upper() == "OSM":
            record["source"] = "openstreetmap"

        if record.get("source") and record.get("data_confidence"):
            continue

        place_id = str(record.get("placeId") or "")
        for prefix, (source, confidence) in PLACE_ID_SOURCE_PREFIX.items():
            if place_id.startswith(prefix):
                record.setdefault("source", source)
                record["source"] = record.get("source") or source
                record.setdefault("data_confidence", confidence)
                filled += 1
                break

    if filled:
        logger.info(f"Đã bù thông tin nguồn cho {filled} record cào từ trước")
    return records


# Hai bản ghi được coi là CÙNG MỘT QUÁN khi ở rất gần nhau VÀ tên khớp.
# 50m: đủ rộng để bù sai số toạ độ giữa hai nguồn (OSM đặt điểm ở cửa, Google đặt ở giữa
# toà nhà), nhưng đủ hẹp để không gộp nhầm hai quán khác nhau trên cùng một phố.
CROSS_SOURCE_MAX_METRES = 50.0
# Tên ngắn hơn ngưỡng này thì không dùng luật "tên này nằm trong tên kia".
# Ngưỡng 4 chọn theo dữ liệu thật:
#   - "chops" (5) vs "chops tay ho"  -> PHẢI gộp, là cùng một quán
#   - "bun" (3) vs "bun cha huong lien" -> KHÔNG gộp, "bún" quá chung chung
#   - "pho" (3) vs "pho thin bo ho"     -> KHÔNG gộp, cùng lý do
MIN_NAME_LENGTH_FOR_SUBSTRING = 4


def _haversine_metres(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(d_lng / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _coords(record: Dict[str, Any]) -> Optional[tuple[float, float]]:
    location = record.get("location") or {}
    try:
        return float(location.get("lat")), float(location.get("lng"))
    except (TypeError, ValueError):
        return None


def _same_place(name_a: str, name_b: str) -> bool:
    """Hai tên có chỉ cùng một quán không (đã bỏ dấu, hạ chữ thường).

    Khớp theo TỪ NGUYÊN VẸN chứ không phải chuỗi con: "an" là chuỗi con của "banh mi"
    nhưng không phải cùng quán. Dùng lại `contains_phrase` của domain để chỉ có MỘT
    cách so khớp tên trong toàn dự án.
    """
    from src.domain.value_objects.text import contains_phrase

    if not name_a or not name_b:
        return False
    if name_a == name_b:
        return True
    shorter, longer = sorted((name_a, name_b), key=len)
    if len(shorter) < MIN_NAME_LENGTH_FOR_SUBSTRING:
        return False
    return contains_phrase(longer, shorter)


def dedupe_across_sources(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Gộp bản ghi CÙNG MỘT QUÁN nhưng đến từ hai nguồn khác nhau.

    VÌ SAO CẦN: OSM đánh id `osm-node-123`, Google đánh `ChIJ...`. Cùng một quán ở hai
    nguồn sẽ có id khác nhau nên bước khử trùng lặp theo `placeId` KHÔNG bắt được.
    Đo thực tế: 22/435 quán trong một đợt cào Apify đã có sẵn trong dataset từ OSM
    (VD "Chops Tay Ho" vs "Chops", "Ding tea Xuân La" vs "Ding tea").

    Cách nhận biết: gần nhau <= 50m VÀ tên khớp. Giữ bản ghi giàu thông tin hơn.

    Dùng lưới ô vuông để chỉ so sánh các bản ghi lân cận - so tất cả với tất cả trên
    4700 bản ghi là 22 triệu phép tính, quá chậm.
    """
    from src.domain.value_objects.text import normalize

    # Ô lưới ~0.001 độ (~111m). Chỉ cần dò 9 ô quanh mỗi điểm là phủ hết bán kính 50m.
    grid: Dict[tuple[int, int], List[int]] = {}
    kept: List[Dict[str, Any]] = []
    merged = 0

    for record in records:
        point = _coords(record)
        if point is None:
            kept.append(record)
            continue

        lat, lng = point
        name = normalize(record.get("title"))
        cell = (int(lat * 1000), int(lng * 1000))

        duplicate_index = None
        for d_lat in (-1, 0, 1):
            for d_lng in (-1, 0, 1):
                for index in grid.get((cell[0] + d_lat, cell[1] + d_lng), []):
                    other = kept[index]
                    other_point = _coords(other)
                    if other_point is None:
                        continue
                    if not _same_place(name, normalize(other.get("title"))):
                        continue
                    if _haversine_metres(lat, lng, *other_point) <= CROSS_SOURCE_MAX_METRES:
                        duplicate_index = index
                        break
                if duplicate_index is not None:
                    break
            if duplicate_index is not None:
                break

        if duplicate_index is not None:
            merged += 1
            # Giữ bản giàu thông tin hơn, nhưng KHÔNG vứt bỏ dữ liệu của bản kia:
            # bổ sung những trường mà bản thắng còn trống.
            winner, loser = kept[duplicate_index], record
            if _richness(loser) > _richness(winner):
                winner, loser = loser, winner
            for key, value in loser.items():
                if value not in (None, "", [], {}, "[]") and winner.get(key) in (None, "", [], {}, "[]"):
                    winner[key] = value
            kept[duplicate_index] = winner
            continue

        grid.setdefault(cell, []).append(len(kept))
        kept.append(record)

    if merged:
        logger.info(f"Đã gộp {merged} quán trùng giữa các nguồn (gần nhau + trùng tên)")
    return kept


# Số đơn vị hành chính cấp 6 của Hà Nội, đo bằng chính ranh giới OSM ngày 2026-08-24
# (relation 1903516 -> 126 đơn vị). Dùng làm CHỐT AN TOÀN: tải hụt ranh giới mà vẫn đem
# đi lọc thì sẽ xoá nhầm hàng chục nghìn quán, nên dưới ngưỡng này là KHÔNG lọc.
SO_DON_VI_HA_NOI_TOI_THIEU = 100


def assign_districts_and_filter_hanoi(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Gán LẠI khu vực cho MỌI bản ghi từ toạ độ, rồi bỏ quán nằm ngoài Hà Nội.

    HAI THAY ĐỔI so với bản cũ (`assign_missing_districts`), đều có số đo ngày 2026-08-24:

    1. GÁN LẠI CHO MỌI BẢN GHI, không chỉ bản ghi còn trống.
       Bản cũ giữ nguyên giá trị do nguồn cung cấp, và giá trị đó BẨN: dataset có 185 giá
       trị `district` khác nhau trong khi Hà Nội chỉ có 126 đơn vị. Thực tế gặp phải:
       "Hoan Kiem" / "Dong Da" (không dấu) · "Hà đông" / "Hà Đông" (khác hoa thường) ·
       "quận Long Biên" (lẫn tiền tố) · "Phố Phan Huy Chú" (là TÊN PHỐ) · "Hà Nội" (là
       thành phố). Đo được 904 bản ghi sai kiểu này. Toạ độ + ranh giới hành chính là
       nguồn sự thật đáng tin hơn hẳn chuỗi tự do của nguồn.

    2. BỎ QUÁN NGOÀI HÀ NỘI. `CLAUDE.md` mục 4b chốt phạm vi CHỈ HÀ NỘI, nhưng đo được
       3.184 quán (6,0%) nằm ở tỉnh khác: Từ Sơn/Tiên Du/Yên Phong (Bắc Ninh),
       Ecopark - Xã Phụng Công/Văn Giang/Như Quỳnh (Hưng Yên), Phúc Yên/Xuân Hoà
       (Vĩnh Phúc), Việt Yên/Hiệp Hoà (Bắc Giang). Chúng lọt vào vì bbox cũ lấn sang
       phía đông - xem ghi chú ở `sources/districts.py`.

    THIẾU RANH GIỚI THÌ KHÔNG LỌC. Xoá dữ liệu vì một lỗi mạng thoáng qua là hỏng nặng
    hơn nhiều so với để lẫn vài trăm quán tỉnh bên cạnh thêm một hôm.
    """
    try:
        from data_pipeline.sources.districts import (
            DistrictLocator,
            fetch_district_boundaries,
        )

        boundaries = fetch_district_boundaries()
    except Exception as exc:
        logger.warning(f"Bỏ qua bước gán khu vực: {exc}")
        return records

    if len(boundaries) < SO_DON_VI_HA_NOI_TOI_THIEU:
        logger.warning(
            "Chỉ có %d đơn vị ranh giới (cần >=%d) - GÁN nhưng KHÔNG lọc, "
            "để một lần tải hụt không xoá mất dữ liệu",
            len(boundaries), SO_DON_VI_HA_NOI_TOI_THIEU,
        )

    locator = DistrictLocator(boundaries)
    du_de_loc = len(boundaries) >= SO_DON_VI_HA_NOI_TOI_THIEU

    giu: List[Dict[str, Any]] = []
    gan_moi = sua_lai = ngoai_ha_noi = khong_toa_do = 0

    for record in records:
        location = record.get("location") or {}
        try:
            lat = float(location.get("lat"))
            lng = float(location.get("lng"))
        except (TypeError, ValueError):
            khong_toa_do += 1
            giu.append(record)   # không có toạ độ thì không kết luận được - giữ lại
            continue

        district = locator.find(lat, lng)
        if district is None:
            ngoai_ha_noi += 1
            if du_de_loc:
                continue
            giu.append(record)
            continue

        cu = record.get("district")
        if not cu:
            gan_moi += 1
        elif cu != district:
            sua_lai += 1
        record["district"] = district
        # Khu vực là giá trị SUY RA từ toạ độ, không do nguồn cung cấp.
        record["district_confidence"] = "derived"
        giu.append(record)

    logger.info(
        "Khu vực: gán mới %d · sửa lại %d sai/bẩn · %d không toạ độ · "
        "%d ngoài Hà Nội (%s)",
        gan_moi, sua_lai, khong_toa_do, ngoai_ha_noi,
        "đã bỏ" if du_de_loc else "GIỮ vì thiếu ranh giới",
    )
    return giu


def filter_to_food_only(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    filtered = [r for r in records if is_restaurant_item(r)]
    logger.info(f"Sau khi lọc chỉ giữ đồ ăn cho người: {len(filtered)}/{len(records)} record")
    return filtered


def merge_and_prepare(raw_dir: str | Path | None = None, output_filename: str = "merged_places.csv") -> Path | None:
    base_dir = Path.cwd()
    raw_dir = Path(raw_dir) if raw_dir else base_dir / "data_pipeline" / "data_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    unique_records = merge_raw_json_files(raw_dir)
    if not unique_records:
        return None

    unique_records = backfill_provenance(unique_records)
    unique_records = dedupe_across_sources(unique_records)
    unique_records = assign_districts_and_filter_hanoi(unique_records)
    filtered_records = filter_to_food_only(unique_records)
    if not filtered_records:
        logger.warning("Không còn record nào sau khi lọc.")
        return None

    # json_normalize làm phẳng field lồng nhau (location.lat -> location/lat)
    # để khớp với cột mà data_cleaning.py/feature_engineering.py đang mong đợi.
    df = pd.json_normalize(filtered_records, sep="/")

    output_path = raw_dir / output_filename
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info(f"Đã lưu {len(df)} record vào {output_path}")
    logger.info("Bước tiếp theo: chạy `python data_pipeline/data_cleaning.py`")

    return output_path


if __name__ == "__main__":
    merge_and_prepare()

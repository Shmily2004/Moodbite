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
from pathlib import Path
from typing import Any, Dict, List

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

    seen = set()
    unique_records = []
    for record in all_records:
        key = _dedupe_key(record)
        if key not in seen:
            seen.add(key)
            unique_records.append(record)

    logger.info(f"Sau khi khử trùng lặp: {len(unique_records)} record")
    return unique_records


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

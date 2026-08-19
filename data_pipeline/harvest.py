"""CLI thu thập dữ liệu quán ăn từ các nguồn đã đăng ký.

    python -m data_pipeline.harvest                     # chạy mọi nguồn dùng được
    python -m data_pipeline.harvest --source openstreetmap
    python -m data_pipeline.harvest --list              # xem nguồn nào sẵn sàng
    python -m data_pipeline.harvest --no-districts      # bỏ bước gán quận

Ghi ra `data_pipeline/data_raw/NN_<source>.json` — đúng nơi `merge_and_prepare_raw.py`
đang quét, nên không phải sửa pipeline.

Sau khi chạy xong:
    python -m data_pipeline.merge_and_prepare_raw
    python -m data_pipeline.data_cleaning
    python -m data_pipeline.feature_engineering
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

from data_pipeline.sources import AVAILABLE_SOURCES
from data_pipeline.sources.osm_overpass import CITY_BBOXES
from data_pipeline.sources.base import CONFIDENCE_DERIVED, RawPlace
from data_pipeline.sources.districts import DistrictLocator, fetch_district_boundaries

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("harvest")

RAW_DIR = Path("data_pipeline/data_raw")

# Số thứ tự file để thứ tự gộp ổn định. Nguồn mới thêm số mới.
SOURCE_FILE_PREFIX = {
    "openstreetmap": "05",
    "overture": "11",
}


def assign_districts(places: List[RawPlace]) -> tuple[int, int]:
    """Gán quận cho các quán chưa có. Trả (số quán được gán, số quận khác nhau)."""
    boundaries = fetch_district_boundaries()
    if not boundaries:
        logger.warning("Bo qua buoc gan quan - khong co ranh gioi")
        return 0, 0

    locator = DistrictLocator(boundaries)
    assigned = 0
    seen: set[str] = set()

    for place in places:
        if place.district:
            place.district_confidence = place.data_confidence  # do nguồn cung cấp
            seen.add(place.district)
            continue
        try:
            lat = float(place.location.get("lat"))
            lng = float(place.location.get("lng"))
        except (TypeError, ValueError):
            continue
        district = locator.find(lat, lng)
        if district:
            place.district = district
            # Quận là giá trị SUY RA từ toạ độ, không phải do nguồn cung cấp -
            # đánh dấu để sau này còn phân biệt được.
            place.district_confidence = CONFIDENCE_DERIVED
            assigned += 1
            seen.add(district)

    logger.info("Da gan quan cho %d quan (%d quan/huyen khac nhau)", assigned, len(seen))
    return assigned, len(seen)


def write_source_file(source_name: str, places: List[RawPlace]) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    prefix = SOURCE_FILE_PREFIX.get(source_name, "09")
    output = RAW_DIR / f"{prefix}_raw_places_{source_name}.json"
    records = [p.to_record() for p in places]
    output.write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    logger.info("Da ghi %d quan vao %s", len(records), output)
    return output


def list_sources() -> int:
    print(f"{'NGUON':20s} {'TRANG THAI':12s} LY DO")
    print("-" * 70)
    for name, factory in AVAILABLE_SOURCES.items():
        available, reason = factory().is_available()
        print(f"{name:20s} {'san sang' if available else 'chua dung duoc':12s} {reason}")
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Thu thap du lieu quan an cho MoodBite")
    parser.add_argument("--source", action="append", help="Chi chay nguon nay (lap lai duoc)")
    parser.add_argument("--list", action="store_true", help="Liet ke nguon va trang thai")
    parser.add_argument("--no-districts", action="store_true", help="Bo qua buoc gan quan")
    parser.add_argument("--city", default="ha_noi",
                        help="Thanh pho can lay (chi ap dung cho openstreetmap). "
                             "Xem CITY_BBOXES trong sources/osm_overpass.py")
    parser.add_argument("--tile-size", type=float, default=0.08,
                        help="Kich thuoc o luoi (do). Nho hon = nhieu request hon nhung it 504 hon")
    args = parser.parse_args(argv)

    if args.list:
        return list_sources()

    wanted = args.source or list(AVAILABLE_SOURCES)
    unknown = [s for s in wanted if s not in AVAILABLE_SOURCES]
    if unknown:
        logger.error("Nguon khong ton tai: %s. Co: %s", unknown, list(AVAILABLE_SOURCES))
        return 1

    total = 0
    for name in wanted:
        factory = AVAILABLE_SOURCES[name]
        if name == "overture":
            if args.city not in CITY_BBOXES:
                logger.error("Khong co thanh pho '%s'. Co: %s",
                             args.city, sorted(CITY_BBOXES))
                return 2
            source = factory(bbox=CITY_BBOXES[args.city], city=args.city)
        elif name == "openstreetmap":
            # Thanh pho khong co trong bang -> DUNG LAI va noi ro, khong am tham lay Ha Noi:
            # chay 20 phut roi phat hien lay nham thanh pho la mat cong vo ich.
            if args.city not in CITY_BBOXES:
                logger.error("Khong co thanh pho '%s'. Co: %s",
                             args.city, sorted(CITY_BBOXES))
                return 2
            source = factory(bbox=CITY_BBOXES[args.city], tile_size_deg=args.tile_size)
        else:
            source = factory()

        available, reason = source.is_available()
        if not available:
            # Nguồn chưa cấu hình KHÔNG được làm hỏng cả lượt chạy.
            logger.warning("Bo qua nguon '%s': %s", name, reason)
            continue

        logger.info("=== Bat dau nguon: %s ===", name)
        places = source.fetch()
        if not places:
            logger.warning("Nguon '%s' khong tra ve du lieu nao", name)
            continue

        if not args.no_districts:
            assign_districts(places)

        write_source_file(name, places)
        total += len(places)

    logger.info("TONG CONG: %d quan tu %d nguon", total, len(wanted))
    if total:
        logger.info("Buoc tiep theo: python -m data_pipeline.merge_and_prepare_raw")
    return 0


if __name__ == "__main__":
    sys.exit(main())

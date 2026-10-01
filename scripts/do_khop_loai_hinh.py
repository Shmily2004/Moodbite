"""Đo: trang món nào để quán CHỈ khớp LOẠI HÌNH (`categoryName`) chen lên trên quán khớp
TÊN quán mà vẫn còn quán khớp tên (trong bán kính) bị ẩn khỏi top-20.

CLAUDE.md §4.6: ưu tiên TÊN QUÁN hơn `categoryName`. Số đo 2026-09-29 trên 298 trang món
(tâm Hà Nội, bán kính mặc định): trước khi tách bậc 10 trang / 84 quán, sau 0 / 0.

Chạy:
    python scripts/do_khop_loai_hinh.py
    python scripts/do_khop_loai_hinh.py --ghi top20.json   # ghi top-20 để so hai lần chạy
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.application.use_cases.find_restaurants_for_dish import (  # noqa: E402
    RestaurantsForDishQuery,
)
from src.domain.services.dish_matching import (  # noqa: E402
    FIELD_CATEGORY,
    FIELD_NAME,
    MATCHED_BY_REVIEW,
)
from src.domain.services.search_ranking import DEFAULT_MAX_DISTANCE_KM  # noqa: E402
from src.domain.value_objects.location import (  # noqa: E402
    HANOI_CENTER_LAT,
    HANOI_CENTER_LNG,
    Location,
)
from src.domain.value_objects.price import has_known_price  # noqa: E402
from src.presentation.api.dependencies import build_container  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ghi", help="ghi top-20 của mọi trang ra file JSON")
    args = parser.parse_args()

    logging.disable(logging.CRITICAL)
    uc = build_container().find_restaurants_for_dish
    index = uc._index
    origin = Location(lat=HANOI_CENTER_LAT, lng=HANOI_CENTER_LNG)

    tops = {}
    for only_price in (False, True):
        trang = trang_vp = quan_vp = 0
        for dish_id, matches in index.items():
            if not matches:
                continue
            trang += 1
            shown = uc.execute(RestaurantsForDishQuery(
                session_id="do", dish_id=dish_id, only_with_price=only_price,
            )).results
            tops[f"{dish_id}|{int(only_price)}"] = [r.restaurant_id for r in shown]
            shown_ids = {r.restaurant_id for r in shown}
            ten_bi_an = [
                m for m in matches
                if m.matched_by != MATCHED_BY_REVIEW and m.match_source == FIELD_NAME
                and m.restaurant.location.distance_km(origin) <= DEFAULT_MAX_DISTANCE_KM
                and (not only_price or has_known_price(m.restaurant.price))
                and m.restaurant.place_id not in shown_ids
            ]
            loai_hinh = [r for r in shown if r.match_source == FIELD_CATEGORY]
            if loai_hinh and ten_bi_an:
                trang_vp += 1
                quan_vp += len(loai_hinh)
        nhan = "bật lọc giá" if only_price else "không lọc giá"
        print(f"{nhan}: {trang} trang món · {trang_vp} trang có quán loại hình chen trên "
              f"quán khớp tên đang bị ẩn ({quan_vp} quán)")

    if args.ghi:
        Path(args.ghi).write_text(json.dumps(tops), encoding="utf-8")


if __name__ == "__main__":
    main()

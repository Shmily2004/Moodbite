"""
MoodBite - Cào dữ liệu quán ăn Hà Nội qua Apify (actor Google Maps Scraper).

VÌ SAO DÙNG APIFY THAY VÌ TỰ CÀO GOOGLE MAPS:
- Tự cào Google Maps trực tiếp vi phạm ToS của Google và đã được audit là dễ vỡ.
- Apify là dịch vụ có vận hành thương mại, chịu trách nhiệm phần thu thập; đây cũng chính
  là nguồn đã sinh ra 02_raw_places.json / 03_raw_places.json đang dùng trong dự án.
- Chỉ Apify mới có sẵn cùng lúc: price, reviews (có text + sao), imageUrls,
  additionalInfo (Bầu không khí / Tiện nghi) - thứ mà OpenStreetMap KHÔNG hề có
  (đã đo: 0% giá, 0% review, 0% rating trên 3708 quán OSM).

MỤC TIÊU: bù dữ liệu cho 3623/4170 quán hiện chỉ có từ OSM (không giá, không review).

OUTPUT: data_pipeline/data_raw/05_raw_places_apify.json, schema TRÙNG với các file
  *_raw_places.json sẵn có -> chạy thẳng `python -m data_pipeline.merge_and_prepare_raw`.

CÁCH DÙNG:
    # 1. Xem trước cấu hình + ước lượng chi phí, KHÔNG tốn tiền, không cần token:
    python -m data_pipeline.scrape_apify_hanoi --dry-run

    # 2. Chạy thật (cần token Apify):
    $env:APIFY_TOKEN = "apify_api_xxx"      # PowerShell
    python -m data_pipeline.scrape_apify_hanoi --max-places 2000

    # 3. Gộp vào dataset rồi tính lại đặc trưng:
    python -m data_pipeline.merge_and_prepare_raw
    python -m data_pipeline.data_cleaning
    python -m data_pipeline.feature_engineering

LƯU Ý CHI PHÍ: Apify tính tiền theo số place cào được, và cào review/ảnh đắt hơn cào
  thông tin cơ bản. Luôn chạy --dry-run trước, và đặt --max-places để chặn trần.
  Hãy tự kiểm tra đơn giá hiện hành trên trang actor - đừng tin con số hard-code ở đây.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Bbox chuẩn của dự án - PHỦ TOÀN HÀ NỘI, không chỉ khu trung tâm.
# Đây là giá trị đã được sửa đúng sau khi phát hiện bbox cũ quá hẹp; đừng thu hẹp lại.
HANOI_BBOX = {"south": 20.85, "west": 105.70, "north": 21.40, "east": 106.05}

ACTOR_ID = "compass~crawler-google-places"
APIFY_API = "https://api.apify.com/v2"

OUTPUT_PATH = Path("data_pipeline/data_raw/05_raw_places_apify.json")

# Từ khóa tiếng Việt: Google Maps ở Hà Nội gắn nhãn chủ yếu bằng tiếng Việt, tìm bằng
# tiếng Anh ("restaurant") sẽ bỏ sót rất nhiều quán bình dân.
SEARCH_TERMS = [
    "nhà hàng", "quán ăn", "quán cà phê", "quán phở", "bún chả", "cơm bình dân",
    "lẩu", "nướng", "quán nhậu", "bún đậu mắm tôm", "xôi", "bánh mì", "trà sữa",
    "quán ốc", "hải sản", "cháo", "miến", "bánh cuốn", "chè", "kem",
]

# 2 field này BẮT BUỘC phải có trong output, nếu không toàn bộ pipeline phía sau hỏng:
# categoryName dùng để chấm mood-score, placeId dùng làm khóa gộp + tra chi tiết.
# Lỗi thiếu 2 field này đã lặp lại nhiều lần ở các script cào trước đây -> kiểm tra tự động.
REQUIRED_FIELDS = ("categoryName", "placeId")


def build_actor_input(max_places: int, max_reviews: int, max_images: int) -> Dict[str, Any]:
    """Cấu hình actor. customGeolocation dùng polygon từ bbox để giới hạn đúng Hà Nội."""
    b = HANOI_BBOX
    polygon = [[
        [b["west"], b["south"]],
        [b["east"], b["south"]],
        [b["east"], b["north"]],
        [b["west"], b["north"]],
        [b["west"], b["south"]],
    ]]

    return {
        "searchStringsArray": SEARCH_TERMS,
        "customGeolocation": {"type": "Polygon", "coordinates": polygon},
        "maxCrawledPlacesPerSearch": max(1, max_places // len(SEARCH_TERMS)),
        "language": "vi",
        "countryCode": "vn",
        # Bật lấy chi tiết: nếu tắt sẽ KHÔNG có price/additionalInfo/reviews.
        "scrapePlaceDetailPage": True,
        "maxReviews": max_reviews,
        "maxImages": max_images,
        "reviewsSort": "newest",
        "scrapeReviewerName": True,
        "skipClosedPlaces": True,
    }


def start_run(token: str, actor_input: Dict[str, Any]) -> str:
    r = requests.post(
        f"{APIFY_API}/acts/{ACTOR_ID}/runs",
        params={"token": token},
        json=actor_input,
        timeout=60,
    )
    r.raise_for_status()
    run = r.json()["data"]
    logger.info("Đã khởi chạy run %s (xem tiến độ tại https://console.apify.com)", run["id"])
    return run["id"]


def wait_for_run(token: str, run_id: str, poll_seconds: int = 20) -> Dict[str, Any]:
    """Chờ run xong. Cào vài nghìn quán kèm review có thể mất hàng chục phút - đây là
    việc bình thường, không phải treo."""
    while True:
        r = requests.get(f"{APIFY_API}/actor-runs/{run_id}",
                         params={"token": token}, timeout=60)
        r.raise_for_status()
        data = r.json()["data"]
        status = data["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            logger.info("Run kết thúc với trạng thái: %s", status)
            if status != "SUCCEEDED":
                raise RuntimeError(f"Apify run {run_id} kết thúc bất thường: {status}")
            return data
        logger.info("  ... đang chạy (%s), chờ %ss", status, poll_seconds)
        time.sleep(poll_seconds)


def fetch_items(token: str, dataset_id: str) -> List[Dict[str, Any]]:
    """Tải toàn bộ item, phân trang để không bị cắt khi dataset lớn."""
    items: List[Dict[str, Any]] = []
    offset, limit = 0, 1000
    while True:
        r = requests.get(
            f"{APIFY_API}/datasets/{dataset_id}/items",
            params={"token": token, "format": "json", "offset": offset, "limit": limit},
            timeout=120,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        items.extend(batch)
        logger.info("  đã tải %d item", len(items))
        offset += limit
    return items


def validate(items: List[Dict[str, Any]]) -> bool:
    """Chặn sẵn lỗi đã lặp lại nhiều lần: script cào mới quên xuất categoryName/placeId."""
    if not items:
        logger.error("Không có item nào được cào về.")
        return False

    ok = True
    for field in REQUIRED_FIELDS:
        n = sum(1 for it in items if it.get(field))
        pct = 100 * n / len(items)
        level = logger.info if pct >= 95 else logger.error
        level("  %-14s có ở %d/%d item (%.1f%%)", field, n, len(items), pct)
        if pct < 95:
            ok = False

    for field in ("price", "reviews", "imageUrls", "additionalInfo", "totalScore"):
        n = sum(1 for it in items if it.get(field))
        logger.info("  %-14s có ở %d/%d item (%.1f%%)", field, n, len(items),
                    100 * n / len(items))
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Cào quán ăn Hà Nội qua Apify")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chỉ in cấu hình, không gọi API, không tốn tiền")
    parser.add_argument("--max-places", type=int, default=2000,
                        help="Trần số quán cào (mặc định 2000)")
    parser.add_argument("--max-reviews", type=int, default=10,
                        help="Số review mỗi quán (mặc định 10 - khớp giới hạn của feature_engineering)")
    parser.add_argument("--max-images", type=int, default=12)
    args = parser.parse_args()

    actor_input = build_actor_input(args.max_places, args.max_reviews, args.max_images)

    if args.dry_run:
        print("=== DRY RUN - không gọi Apify, không mất phí ===")
        print(f"Actor      : {ACTOR_ID}")
        print(f"Bbox       : {HANOI_BBOX}")
        print(f"Từ khóa    : {len(SEARCH_TERMS)} từ ({', '.join(SEARCH_TERMS[:5])}, ...)")
        print(f"Trần quán  : {args.max_places} "
              f"(= {actor_input['maxCrawledPlacesPerSearch']} quán/từ khóa)")
        print(f"Review/quán: {args.max_reviews}   Ảnh/quán: {args.max_images}")
        print(f"Output     : {OUTPUT_PATH}")
        print()
        print("--- actor input JSON ---")
        print(json.dumps(actor_input, ensure_ascii=False, indent=2))
        print()
        print("Chi phí phụ thuộc đơn giá hiện hành của actor - hãy tự kiểm tra trên")
        print("https://apify.com/compass/crawler-google-places trước khi chạy thật.")
        return 0

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        logger.error("Thiếu APIFY_TOKEN. PowerShell: $env:APIFY_TOKEN = \"apify_api_xxx\"")
        return 1

    run_id = start_run(token, actor_input)
    run = wait_for_run(token, run_id)
    items = fetch_items(token, run["defaultDatasetId"])

    logger.info("Kiểm tra dữ liệu cào về:")
    ok = validate(items)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False)
    logger.info("Đã lưu %d quán vào %s", len(items), OUTPUT_PATH)

    if not ok:
        logger.error("THIẾU field bắt buộc - ĐỪNG gộp vào dataset cho tới khi sửa xong.")
        return 1

    logger.info("Bước tiếp theo: python -m data_pipeline.merge_and_prepare_raw "
                "&& python -m data_pipeline.data_cleaning "
                "&& python -m data_pipeline.feature_engineering")
    return 0


if __name__ == "__main__":
    sys.exit(main())

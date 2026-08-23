"""Báo cáo ĐỘ PHỦ và CHẤT LƯỢNG của dataset quán ăn.

    python scripts/data_report.py
    python scripts/data_report.py --json        # dạng máy đọc, để so sánh trước/sau

VÌ SAO CẦN: câu "dataset đã đủ chưa?" chỉ trả lời được bằng SỐ ĐO, không phải cảm tính.
Script này in ra đúng những con số dùng để đánh giá:
    - tổng số quán, số quán duy nhất, tỷ lệ trùng lặp
    - độ phủ từng trường quan trọng
    - số đơn vị hành chính phủ được
    - số loại hình / ẩm thực
    - phân bố theo nguồn dữ liệu

Chạy TRƯỚC và SAU mỗi lần bổ sung dữ liệu để chứng minh cải thiện là có thật.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

# Console Windows mặc định là cp1252 và sẽ NỔ khi in chữ tiếng Việt — script
# đang chạy dở bị dừng giữa chừng. Lỗi này đã xảy ra thật với
# "additionalInfo/Bầu không khí" trong `data_report.py`.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DATASET = Path("data_pipeline/data_cleaned/dataset_moodbite_features.csv")
DETAILS = Path("data_pipeline/data_cleaned/restaurant_details.json")

# Trường -> vì sao nó quan trọng với MoodBite. Nhóm theo mức thiết yếu.
CRITICAL_FIELDS = {
    "title": "tên quán - không có thì không hiển thị được",
    "location/lat": "toạ độ - cần cho bản đồ và tính khoảng cách",
    "location/lng": "toạ độ",
    "categoryName": "loại hình - dùng để suy luận món ăn",
    "address": "địa chỉ - người dùng cần để tìm đến",
}

IMPORTANT_FIELDS = {
    "district": "đơn vị hành chính - lọc theo khu vực",
    "cuisine": "ẩm thực - tăng chất lượng gợi ý",
    "openingHours": "giờ mở cửa - lọc 'đang mở'",
    "phone": "liên hệ",
    "website": "liên hệ / xem menu",
    "totalScore": "đánh giá - tiêu chí xếp hạng",
    "reviewsCount": "độ phổ biến",
    "price": "khoảng giá",
}

ENRICHMENT_FIELDS = {
    "amenities": "tiện nghi - lọc theo ngữ cảnh",
    "dietary": "chế độ ăn - lọc chay/thuần chay",
    "dishes": "món ăn",
    "aliases": "tên gọi khác - tăng khả năng khớp tìm kiếm",
    "additionalInfo/Bầu không khí": "không gian",
    "source": "nguồn gốc dữ liệu",
    "data_confidence": "độ tin cậy",
}


# Giá trị "có ô nhưng không có dữ liệu". Danh sách rỗng `[]` là trường hợp hay gặp nhất:
# adapter luôn ghi ra list, kể cả khi không tìm được tag nào.
EMPTY_MARKERS = {"", "[]", "{}", "nan", "none", "null", "n/a"}


def _non_empty(series: pd.Series) -> int:
    """Đếm ô thực sự CÓ dữ liệu. Chuỗi rỗng và list rỗng ('[]') KHÔNG tính là có.

    KHÔNG kiểm tra `dtype == object`: pandas 3.x đặt dtype `str` cho cột chuỗi, nên phép
    so sánh đó luôn sai và toàn bộ bộ lọc bị bỏ qua - báo cáo từng thổi phồng `dietary`
    từ 117 lên 3620 vì đếm cả 3503 ô `[]`.
    """
    if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
        return int(series.notna().sum())

    stripped = series.astype(str).str.strip().str.lower()
    mask = series.notna() & ~stripped.isin(EMPTY_MARKERS)
    return int(mask.sum())


def build_report(dataset_path: Path = DATASET, details_path: Path = DETAILS) -> Dict[str, Any]:
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Khong tim thay {dataset_path}. Chay: python -m data_pipeline.feature_engineering"
        )

    df = pd.read_csv(dataset_path, low_memory=False)
    total = len(df)

    unique_ids = df["placeId"].nunique() if "placeId" in df.columns else 0
    duplicate_rate = (total - unique_ids) / total * 100 if total else 0.0

    def coverage(fields: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        out = {}
        for name, why in fields.items():
            if name not in df.columns:
                out[name] = {"count": 0, "percent": 0.0, "why": why, "missing_column": True}
                continue
            count = _non_empty(df[name])
            out[name] = {
                "count": count,
                "percent": round(count / total * 100, 1) if total else 0.0,
                "why": why,
            }
        return out

    districts = (
        sorted(df["district"].dropna().astype(str).unique().tolist())
        if "district" in df.columns
        else []
    )
    cuisines = (
        sorted(df["cuisine"].dropna().astype(str).unique().tolist())
        if "cuisine" in df.columns
        else []
    )
    categories = (
        sorted(df["categoryName"].dropna().astype(str).unique().tolist())
        if "categoryName" in df.columns
        else []
    )

    by_source: Dict[str, int] = {}
    if "source" in df.columns:
        by_source = {str(k): int(v) for k, v in df["source"].fillna("(khong ro)").value_counts().items()}
    elif "placeId" in df.columns:
        # Dataset cũ chưa có cột `source` -> suy từ tiền tố placeId.
        guess = df["placeId"].astype(str).apply(
            lambda x: "google" if x.startswith("ChIJ") else ("openstreetmap" if x.startswith("osm-") else "khac")
        )
        by_source = {str(k): int(v) for k, v in guess.value_counts().items()}

    details_count = 0
    reviews_count = 0
    if details_path.exists():
        try:
            details = json.loads(details_path.read_text(encoding="utf-8"))
            details_count = len(details)
            reviews_count = sum(
                1 for v in details.values() if (v.get("reviews") or [])
            )
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "total_restaurants": total,
        "unique_restaurants": unique_ids,
        "duplicate_rate_percent": round(duplicate_rate, 2),
        "districts_covered": len(districts),
        "district_names": districts,
        "cuisine_types": len(cuisines),
        "category_types": len(categories),
        "by_source": by_source,
        "restaurants_with_details": details_count,
        "restaurants_with_reviews": reviews_count,
        "critical": coverage(CRITICAL_FIELDS),
        "important": coverage(IMPORTANT_FIELDS),
        "enrichment": coverage(ENRICHMENT_FIELDS),
    }


def _print_group(title: str, group: Dict[str, Dict[str, Any]], total: int) -> None:
    print(f"\n{title}")
    print("-" * 78)
    for name, info in group.items():
        bar_len = int(info["percent"] / 5)
        bar = "#" * bar_len + "." * (20 - bar_len)
        flag = " (THIEU COT)" if info.get("missing_column") else ""
        print(f"  {name:34s} {bar} {info['count']:5d}/{total} = {info['percent']:5.1f}%{flag}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Bao cao do phu dataset MoodBite")
    parser.add_argument("--json", action="store_true", help="In ra JSON thay vi bang")
    parser.add_argument("--dataset", default=str(DATASET))
    args = parser.parse_args(argv)

    try:
        report = build_report(Path(args.dataset))
    except FileNotFoundError as exc:
        print(exc)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    total = report["total_restaurants"]
    print("=" * 78)
    print("BAO CAO DO PHU DATASET MOODBITE")
    print("=" * 78)
    print(f"  Tong so quan            : {total}")
    print(f"  So quan duy nhat        : {report['unique_restaurants']}")
    print(f"  Ty le trung lap         : {report['duplicate_rate_percent']}%")
    print(f"  Don vi hanh chinh phu   : {report['districts_covered']}")
    print(f"  So loai hinh (category) : {report['category_types']}")
    print(f"  So loai am thuc (cuisine): {report['cuisine_types']}")
    print(f"  Quan co chi tiet        : {report['restaurants_with_details']}")
    print(f"  Quan co review          : {report['restaurants_with_reviews']}")
    print(f"\n  Theo nguon: {report['by_source']}")

    _print_group("TRUONG THIET YEU (khong co thi quan vo dung)", report["critical"], total)
    _print_group("TRUONG QUAN TRONG (quyet dinh chat luong goi y)", report["important"], total)
    _print_group("TRUONG LAM GIAU (tang trai nghiem)", report["enrichment"], total)

    print("\n" + "=" * 78)
    weak = [n for n, i in report["critical"].items() if i["percent"] < 99]
    if weak:
        print(f"CANH BAO: truong thiet yeu chua phu du: {weak}")
    else:
        print("Moi truong thiet yeu deu phu >= 99%.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())

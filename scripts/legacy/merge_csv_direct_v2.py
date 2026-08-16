"""
MoodBite - Gộp trực tiếp ở cấp CSV (bản tổng quát): lấy dataset_moodbite_features.csv
đã có (từ git pull), giữ lại các dòng cũ hợp lệ, rồi cộng thêm TẤT CẢ record mới từ
MỌI file JSON có trong data_pipeline/data_raw/ (không hardcode tên file cụ thể).

Dùng khi máy hiện tại KHÔNG có đủ toàn bộ file JSON gốc (thiếu Apify) để chạy lại
merge_and_prepare_raw.py từ đầu - script này merge thẳng ở cấp CSV.

CÁCH DÙNG:
    python merge_csv_direct.py
"""
import sys
import pandas as pd
import json
from pathlib import Path

sys.path.insert(0, ".")
from data_pipeline.filter_restaurants import is_restaurant_item

EXISTING_CSV = Path("data_pipeline/data_cleaned/dataset_moodbite_features.csv")
DATA_RAW_DIR = Path("data_pipeline/data_raw")

MOOD_COLS = ["comfort_cozy_score", "spicy_hot_score", "fresh_healthy_score",
             "cheap_budget_score", "quick_fast_score"]


def main():
    if not EXISTING_CSV.exists():
        print(f"LỖI: không tìm thấy {EXISTING_CSV}. Hãy git pull trước.")
        return

    df_existing = pd.read_csv(EXISTING_CSV)
    print(f"Dataset hiện có (từ git): {len(df_existing)} dòng")

    broken_mask = df_existing["placeId"].isna()
    n_broken = broken_mask.sum()
    df_existing_clean = df_existing[~broken_mask].copy()
    if n_broken > 0:
        print(f"Loại bỏ {n_broken} dòng lỗi cũ (thiếu placeId)")
    print(f"Dữ liệu gốc giữ lại: {len(df_existing_clean)} dòng")

    # Đọc TẤT CẢ file JSON trong data_raw/, không hardcode tên file cụ thể.
    json_files = sorted(DATA_RAW_DIR.glob("*.json"))
    if not json_files:
        print(f"CẢNH BÁO: không có file JSON nào trong {DATA_RAW_DIR}")
        return

    all_new_records = []
    for jf in json_files:
        with open(jf, encoding="utf-8") as f:
            records = json.load(f)
        print(f"  Đọc {jf.name}: {len(records)} record")
        all_new_records.extend(records)

    print(f"Tổng record thô từ JSON: {len(all_new_records)}")

    filtered = [r for r in all_new_records if is_restaurant_item(r)]
    print(f"Sau khi lọc chỉ giữ đồ ăn cho người: {len(filtered)}")

    if not filtered:
        print("Không có record nào qua được filter - dừng lại, không ghi đè gì.")
        return

    df_new = pd.json_normalize(filtered, sep="/")

    missing_new = df_new["placeId"].isna().sum() if "placeId" in df_new.columns else len(df_new)
    if missing_new > 0:
        print(f"CẢNH BÁO: {missing_new} record mới thiếu placeId - sẽ bị loại (không merge được an toàn)")
        df_new = df_new[df_new["placeId"].notna()]

    for col in MOOD_COLS:
        if col not in df_new.columns:
            df_new[col] = 0.0

    df_new_aligned = df_new.reindex(columns=df_existing_clean.columns)

    combined = pd.concat([df_existing_clean, df_new_aligned], ignore_index=True)
    before_dedup = len(combined)
    # Ưu tiên giữ bản ghi CŨ khi trùng placeId (đã qua feature_engineering, có mood-score
    # thật thay vì mặc định 0.0 của bản ghi mới chưa xử lý).
    combined = combined.drop_duplicates(subset=["placeId"], keep="first")
    print(f"Sau khi gộp: {before_dedup} -> {len(combined)} dòng (loại {before_dedup - len(combined)} trùng lặp)")

    combined.to_csv(EXISTING_CSV, index=False, encoding="utf-8-sig")
    print(f"\nĐã lưu: {EXISTING_CSV}")
    print(f"Tổng cuối cùng: {len(combined)} dòng")
    print(f"Số dòng thiếu placeId: {combined['placeId'].isna().sum()} (phải là 0)")
    print(f"Số placeId trùng lặp: {combined['placeId'].duplicated().sum()} (phải là 0)")


if __name__ == "__main__":
    main()

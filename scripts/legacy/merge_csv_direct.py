"""
MoodBite - Gộp trực tiếp ở cấp CSV: lấy dataset_moodbite_features.csv đã có (từ git
pull, có thể chứa dữ liệu cũ lỗi thiếu placeId từ lần chạy enhanced_osm_query.py
trước khi fix), loại bỏ các dòng lỗi đó, rồi cộng thêm dữ liệu enhanced mới (đã đúng,
có placeId) vào.

Dùng khi KHÔNG có đủ toàn bộ file JSON gốc (01/02/03_raw_places.json,
04_raw_places_osm.json) trên máy hiện tại để chạy lại toàn bộ merge_and_prepare_raw.py
từ đầu - script này merge thẳng ở cấp CSV thay vì JSON thô.

CÁCH DÙNG:
    python merge_csv_direct.py
"""
import pandas as pd
import json
from pathlib import Path

EXISTING_CSV = Path("data_pipeline/data_cleaned/dataset_moodbite_features.csv")
NEW_ENHANCED_JSON = Path("data_pipeline/data_raw/04_raw_places_osm_enhanced.json")


def main():
    if not EXISTING_CSV.exists():
        print(f"LỖI: không tìm thấy {EXISTING_CSV}. Hãy git pull trước.")
        return

    df_existing = pd.read_csv(EXISTING_CSV)
    print(f"Dataset hiện có (từ git): {len(df_existing)} dòng")

    # Loại bỏ dòng lỗi từ lần chạy enhanced_osm_query.py TRƯỚC KHI fix (thiếu placeId).
    broken_mask = df_existing["placeId"].isna()
    n_broken = broken_mask.sum()
    df_existing_clean = df_existing[~broken_mask].copy()
    print(f"Loại bỏ {n_broken} dòng lỗi cũ (thiếu placeId)")
    print(f"Còn lại (dữ liệu gốc tốt): {len(df_existing_clean)} dòng")

    if not NEW_ENHANCED_JSON.exists():
        print(f"LỖI: không tìm thấy {NEW_ENHANCED_JSON}. Chạy enhanced_osm_query.py trước.")
        return

    with open(NEW_ENHANCED_JSON, encoding="utf-8") as f:
        new_records = json.load(f)

    df_new = pd.json_normalize(new_records, sep="/")
    print(f"Dữ liệu mới (đã fix, có placeId): {len(df_new)} dòng")

    missing_new = df_new["placeId"].isna().sum()
    if missing_new > 0:
        print(f"CẢNH BÁO: {missing_new} dòng trong file mới cũng thiếu placeId - kiểm tra lại enhanced_osm_query.py")

    # Điền các cột mood-score bằng 0 cho dữ liệu mới (chưa qua feature_engineering.py)
    mood_cols = ["comfort_cozy_score", "spicy_hot_score", "fresh_healthy_score",
                 "cheap_budget_score", "quick_fast_score"]
    for col in mood_cols:
        if col not in df_new.columns:
            df_new[col] = 0.0

    # Chỉ giữ các cột khớp với dataset gốc.
    common_cols = [c for c in df_existing_clean.columns if c in df_new.columns or c in mood_cols]
    df_new_aligned = df_new.reindex(columns=df_existing_clean.columns)

    # Gộp + khử trùng lặp theo placeId (ưu tiên giữ bản ghi cũ nếu trùng).
    combined = pd.concat([df_existing_clean, df_new_aligned], ignore_index=True)
    before_dedup = len(combined)
    combined = combined.drop_duplicates(subset=["placeId"], keep="first")
    print(f"Sau khi gộp: {before_dedup} -> {len(combined)} dòng (loại {before_dedup - len(combined)} trùng lặp)")

    combined.to_csv(EXISTING_CSV, index=False, encoding="utf-8-sig")
    print(f"\nĐã lưu: {EXISTING_CSV}")
    print(f"Tổng cuối cùng: {len(combined)} dòng")
    print(f"Số dòng thiếu placeId: {combined['placeId'].isna().sum()} (phải là 0)")


if __name__ == "__main__":
    main()

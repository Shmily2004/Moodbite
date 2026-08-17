"""Đo dữ liệu REVIEW để quyết định Lớp 4 (tóm tắt review) có đáng làm hay không.

    python scripts/review_report.py

VÌ SAO CÓ FILE NÀY: `PROJECT_CHECKLIST.md` ghi Lớp 4 "chưa làm — review TB 106 ký tự,
quá ngắn". Con số 106 đó đo trên dataset CŨ (440 quán có chi tiết). Nay đã có 1310 quán
có chi tiết, nên phải ĐO LẠI trước khi kết luận, đúng tinh thần CLAUDE.md mục 4b:
"Không có số đo thì không được nói dữ liệu đã cải thiện".

Script chỉ ĐỌC và IN SỐ, không sửa gì.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.infrastructure.config.settings import Settings  # noqa: E402

# Ngưỡng tham khảo: dưới mức này thì "tóm tắt" không còn ý nghĩa - bản tóm tắt sẽ dài
# gần bằng bản gốc. Chọn 300 ký tự vì đó là cỡ 2-3 câu tiếng Việt hoàn chỉnh.
MIN_USEFUL_CHARS = 300

# Số review tối thiểu để tóm tắt nói được điều gì đó chung, thay vì chép lại 1 ý kiến.
MIN_REVIEWS_FOR_SUMMARY = 5


def percentile(sorted_values: list[int], q: float) -> int:
    if not sorted_values:
        return 0
    idx = min(len(sorted_values) - 1, int(q * len(sorted_values)))
    return sorted_values[idx]


def main() -> int:
    settings = Settings.from_env()
    path = settings.restaurant_details_json
    if not path.exists():
        print(f"[LOI] Khong tim thay {path}")
        print("      Chay: python -m data_pipeline.merge_and_prepare_raw")
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    # File là dict {place_id: {...}} hoặc list - chấp nhận cả hai để không phụ thuộc
    # chi tiết định dạng của pipeline.
    records = list(data.values()) if isinstance(data, dict) else list(data)

    per_review_lengths: list[int] = []
    per_place_total: list[int] = []
    per_place_count: list[int] = []
    places_with_reviews = 0

    for rec in records:
        if not isinstance(rec, dict):
            continue
        reviews = rec.get("reviews") or []
        texts = [
            str(r.get("text") or "").strip() if isinstance(r, dict) else str(r).strip()
            for r in reviews
        ]
        texts = [t for t in texts if t]
        if not texts:
            continue
        places_with_reviews += 1
        per_review_lengths.extend(len(t) for t in texts)
        per_place_total.append(sum(len(t) for t in texts))
        per_place_count.append(len(texts))

    print("=" * 68)
    print("DO DU LIEU REVIEW - quyet dinh Lop 4 (tom tat review)")
    print("=" * 68)
    print(f"Nguon: {path}")
    print(f"  Ban ghi co chi tiet          : {len(records)}")
    print(f"  Quan CO it nhat 1 review     : {places_with_reviews}")
    print(f"  Tong so review               : {len(per_review_lengths)}")

    if not per_review_lengths:
        print("\n[KET LUAN] Khong co review nao -> Lop 4 KHONG kha thi.")
        return 0

    lengths = sorted(per_review_lengths)
    totals = sorted(per_place_total)
    counts = sorted(per_place_count)

    print("\n-- Do dai MOT review (ky tu) --")
    print(f"  trung binh : {sum(lengths) / len(lengths):.1f}")
    print(f"  trung vi   : {percentile(lengths, 0.50)}")
    print(f"  p75 / p90  : {percentile(lengths, 0.75)} / {percentile(lengths, 0.90)}")
    print(f"  dai nhat   : {lengths[-1]}")

    print("\n-- GOP tat ca review cua MOT quan (ky tu) --")
    print(f"  trung binh : {sum(totals) / len(totals):.1f}")
    print(f"  trung vi   : {percentile(totals, 0.50)}")
    print(f"  p75 / p90  : {percentile(totals, 0.75)} / {percentile(totals, 0.90)}")

    print("\n-- So review MOI quan --")
    print(f"  trung binh : {sum(counts) / len(counts):.1f}")
    print(f"  trung vi   : {percentile(counts, 0.50)}")

    # Điều kiện đáng tóm tắt: gộp đủ dài VÀ đủ nhiều ý kiến.
    du_dieu_kien = sum(
        1
        for total, count in zip(per_place_total, per_place_count)
        if total >= MIN_USEFUL_CHARS and count >= MIN_REVIEWS_FOR_SUMMARY
    )
    ty_le = du_dieu_kien / len(records) * 100 if records else 0.0

    print("\n" + "=" * 68)
    print(f"Quan DANG tom tat (gop >= {MIN_USEFUL_CHARS} ky tu VA >= "
          f"{MIN_REVIEWS_FOR_SUMMARY} review):")
    print(f"  {du_dieu_kien} quan = {ty_le:.1f}% so quan co chi tiet")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""LỚP 4 của đề án — TÓM TẮT REVIEW thành nhận xét ngắn cho từng quán.

    python -m data_pipeline.review_summary
    python -m data_pipeline.review_summary --min-reviews 5   # khắt khe hơn

CHẠY OFFLINE, KHÔNG chạy lúc người dùng tìm kiếm. Đề án mục 7 nói rõ: "chạy trước mô hình
tổng hợp nhận xét (Lớp 4) để lưu sẵn kết quả - tránh phải xử lý ngôn ngữ tự nhiên nặng tại
thời điểm người dùng tìm kiếm". Kết quả ghi ra `review_summaries.json`, backend chỉ đọc.

TÓM TẮT TRÍCH RÚT, KHÔNG PHẢI SINH VĂN BẢN
------------------------------------------
Mọi câu trong bản tóm tắt đều là câu NGUYÊN VĂN của người đánh giá, chỉ được CHỌN LỌC chứ
không viết lại. Lý do:

  1. Sinh văn bản cần mô hình ngôn ngữ lớn -> cần thẻ thanh toán hoặc GPU. Ràng buộc chi
     phí ở CLAUDE.md mục 1b loại phương án đó.
  2. Sinh văn bản có thể BỊA - đúng thứ CLAUDE.md mục 4b cấm. Trích nguyên văn thì câu nào
     hiện ra cũng truy được về một review có thật.

Đề án mục 3 (Lớp 4) cho phép cả hai: "tóm tắt trích rút hoặc tóm tắt sinh, tuỳ năng lực
triển khai". Đây là bản trích rút.

CÁCH CHỌN CÂU
-------------
Xếp hạng câu bằng TF-IDF + độ gần TÂM (centroid) của chính quán đó: câu nào gần tâm nhất
là câu nói lên điều NHIỀU NGƯỜI cùng nhắc, thay vì một ý kiến cá biệt. Đây là kỹ thuật
tóm tắt trích rút kinh điển, dùng lại đúng thư viện đã có (`scikit-learn`) - không thêm
phụ thuộc nào.

Tách riêng ĐIỂM MẠNH và ĐIỂM YẾU theo số sao của review chứa câu đó: 4-5 sao là điểm mạnh,
1-2 sao là điểm yếu. KHÔNG đoán cảm xúc bằng mô hình - số sao là nhãn do chính người viết
đặt, đáng tin hơn nhiều.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("review_summary")

DETAILS_PATH = ROOT / "data_pipeline" / "data_cleaned" / "restaurant_details.json"
OUTPUT_PATH = ROOT / "data_pipeline" / "data_cleaned" / "review_summaries.json"

# Số review TỐI THIỂU để tóm tắt. Dưới ngưỡng này thì "tóm tắt" chỉ là chép lại một ý kiến
# cá nhân - vô nghĩa và dễ gây hiểu lầm là "đánh giá chung của quán".
MIN_REVIEWS = 3

# Câu quá ngắn ("Ngon", "Ok ạ") không mang thông tin; câu quá dài thường là cả đoạn dính
# liền do người viết không chấm câu, đọc trên thẻ sẽ tràn.
MIN_SENTENCE_CHARS = 25
MAX_SENTENCE_CHARS = 220

# Số câu lấy cho mỗi phần.
TOP_SENTENCES = 3
TOP_POSITIVE = 2
TOP_NEGATIVE = 2

# Ngưỡng sao. Review 3 sao là trung tính -> KHÔNG tính vào cả điểm mạnh lẫn điểm yếu,
# vì gán nó vào bên nào cũng làm sai lệch bức tranh.
POSITIVE_STARS = 4
NEGATIVE_STARS = 2

_SENTENCE_SPLIT = re.compile(r"[.!?\n]+")


def split_sentences(text: str) -> List[str]:
    """Tách câu tiếng Việt bằng dấu kết câu.

    Đủ dùng cho review: người viết review hiếm khi dùng câu phức có dấu chấm trong ngoặc.
    Không dùng thư viện tách câu chuyên dụng vì sẽ thêm một phụ thuộc chỉ để phục vụ đúng
    chỗ này.
    """
    out: List[str] = []
    for raw in _SENTENCE_SPLIT.split(text or ""):
        sentence = " ".join(raw.split())
        if MIN_SENTENCE_CHARS <= len(sentence) <= MAX_SENTENCE_CHARS:
            out.append(sentence)
    return out


def _rank_by_centrality(sentences: Sequence[str], top_k: int) -> List[str]:
    """Chọn `top_k` câu GẦN TÂM nhất - tức câu nói lên điều nhiều người cùng nhắc.

    Thiếu sklearn hoặc quá ít câu -> lui về lấy câu dài nhất. Suy biến an toàn là bắt buộc
    (CLAUDE.md mục 4c): mọi thành phần ML phải chạy được kể cả khi thiếu thư viện.
    """
    unique = list(dict.fromkeys(sentences))
    if len(unique) <= top_k:
        return unique

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return sorted(unique, key=len, reverse=True)[:top_k]

    try:
        matrix = TfidfVectorizer(max_features=2000).fit_transform(unique)
        centroid = matrix.mean(axis=0)
        # `mean` trả về numpy.matrix -> ép về mảng 2 chiều cho cosine_similarity.
        scores = cosine_similarity(matrix, centroid.A if hasattr(centroid, "A") else centroid)
        ranked = sorted(range(len(unique)), key=lambda i: -float(scores[i][0]))
    except Exception:
        return sorted(unique, key=len, reverse=True)[:top_k]

    chosen = sorted(ranked[:top_k])          # giữ thứ tự xuất hiện cho dễ đọc
    return [unique[i] for i in chosen]


def summarize_one(
    reviews: Sequence[dict], min_reviews: int = MIN_REVIEWS
) -> Optional[Dict[str, Any]]:
    """Tóm tắt review của MỘT quán. Không đủ dữ liệu -> None (KHÔNG bịa).

    Nhận `min_reviews` qua tham số thay vì đọc biến toàn cục: hàm thuần thì test gọi
    thẳng được với ngưỡng bất kỳ, không phải chọc vào trạng thái module.
    """
    usable = [r for r in reviews if (r or {}).get("text")]
    if len(usable) < min_reviews:
        return None

    all_sentences: List[str] = []
    positive: List[str] = []
    negative: List[str] = []

    for review in usable:
        sentences = split_sentences(review.get("text") or "")
        if not sentences:
            continue
        all_sentences.extend(sentences)
        stars = review.get("stars")
        if isinstance(stars, (int, float)):
            if stars >= POSITIVE_STARS:
                positive.extend(sentences)
            elif stars <= NEGATIVE_STARS:
                negative.extend(sentences)

    if not all_sentences:
        return None

    stars_values = [
        r["stars"] for r in usable if isinstance(r.get("stars"), (int, float))
    ]

    summary = _rank_by_centrality(all_sentences, TOP_SENTENCES)
    # Điểm mạnh/yếu KHÔNG lặp lại câu đã nằm trong phần tóm tắt: đọc cùng một câu hai lần
    # trên cùng một màn hình làm người dùng tưởng hệ thống lỗi.
    used = set(summary)

    return {
        "summary": summary,
        "positive": _rank_by_centrality(
            [x for x in positive if x not in used], TOP_POSITIVE
        ),
        "negative": _rank_by_centrality(
            [x for x in negative if x not in used], TOP_NEGATIVE
        ),
        "review_count": len(usable),
        "average_stars": (
            round(sum(stars_values) / len(stars_values), 2) if stars_values else None
        ),
        # NÓI RÕ đây là câu trích nguyên văn, không phải máy viết. Giao diện phải hiển thị
        # điều này, nếu không người đọc tưởng hệ thống tự nhận xét về quán.
        "method": "extractive_tfidf",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Tom tat review (Lop 4)")
    parser.add_argument("--min-reviews", type=int, default=MIN_REVIEWS)
    parser.add_argument("--details", type=Path, default=DETAILS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    if not args.details.exists():
        logger.error("Khong tim thay %s - chay data_pipeline truoc.", args.details)
        return 1

    details = json.loads(args.details.read_text(encoding="utf-8"))
    summaries: Dict[str, Any] = {}
    skipped_few = 0

    for place_id, entry in details.items():
        result = summarize_one((entry or {}).get("reviews") or [], args.min_reviews)
        if result is None:
            skipped_few += 1
            continue
        summaries[place_id] = result

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "_readme": (
                    "SINH TU DONG boi data_pipeline/review_summary.py (Lop 4 de an). "
                    "Moi cau la trich NGUYEN VAN tu review that, KHONG phai may viet."
                ),
                "min_reviews": args.min_reviews,
                "count": len(summaries),
                "summaries": summaries,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with_negative = sum(1 for s in summaries.values() if s["negative"])
    logger.info("=" * 60)
    logger.info("TOM TAT REVIEW (Lop 4)")
    logger.info("=" * 60)
    logger.info("Quan trong file chi tiet : %d", len(details))
    logger.info("Da tom tat               : %d", len(summaries))
    logger.info("Bo qua (duoi %d review)   : %d", args.min_reviews, skipped_few)
    logger.info("Co ca diem yeu           : %d", with_negative)
    logger.info("Da ghi: %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""ADAPTER: tìm kiếm ngữ nghĩa bằng TF-IDF + cosine similarity (Lớp 2 của đề án).

VÌ SAO TF-IDF CHỨ KHÔNG PHẢI SENTENCE-TRANSFORMERS:
  - Chạy được ngay trên CPU, không cần tải model vài trăm MB, không cần GPU.
  - Dựng chỉ mục cho ~5000 quán mất dưới 1 giây; truy vấn mất vài mili-giây.
  - Với tiếng Việt và tập dữ liệu nhỏ, TF-IDF n-gram cho kết quả đủ tốt.

  Khi nào nên đổi: khi độ phủ review vượt ~50% và cần khớp được các cặp từ đồng nghĩa
  KHÔNG dùng chung ký tự nào (VD "yên tĩnh" ~ "không ồn"). Lúc đó viết adapter mới thoả
  cùng `SemanticSearchPort`, KHÔNG sửa use case.

GIỚI HẠN THẲNG THẮN: TF-IDF khớp theo TỪ, không thật sự "hiểu" nghĩa. Nó bắt được
"yên tĩnh" ~ "tĩnh lặng" (chung ký tự qua n-gram) nhưng không bắt được "yên tĩnh" ~
"không ồn ào". Vẫn tốt hơn hẳn khớp từ khoá thuần vì có TRỌNG SỐ theo độ hiếm của từ:
từ hiếm như "sashimi" mang nhiều thông tin hơn từ phổ biến như "ngon".
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence

from src.domain.entities.restaurant import Restaurant
from src.domain.value_objects.text import normalize

logger = logging.getLogger("moodbite.semantic")

# Chỉ giữ quán có điểm tương đồng đáng kể - dưới ngưỡng này gần như là nhiễu.
MIN_SIMILARITY = 0.05
# Số quán trả về nhiều nhất cho một truy vấn.
MAX_RESULTS = 200


class TfidfSemanticSearch:
    """Triển khai `SemanticSearchPort` bằng TF-IDF trên toàn bộ văn bản mô tả quán."""

    def __init__(self, restaurants: Sequence[Restaurant]) -> None:
        self._place_ids: List[str] = []
        self._matrix = None
        self._vectorizer = None
        self._error: Optional[str] = None
        self._build(restaurants)

    @property
    def is_ready(self) -> bool:
        return self._matrix is not None

    def _document(self, restaurant: Restaurant) -> str:
        """Gộp mọi văn bản mô tả một quán thành 1 tài liệu.

        Tên và loại hình lặp lại 2 lần để tăng trọng số - đó là tín hiệu chắc chắn nhất,
        trong khi review dài dễ làm loãng (một review nhắc 10 món khác nhau).
        """
        parts = [
            normalize(restaurant.name), normalize(restaurant.name),
            normalize(restaurant.category), normalize(restaurant.category),
            normalize(restaurant.cuisine),
            normalize(restaurant.atmosphere_text),
            normalize(" ".join(restaurant.amenities)),
            normalize(restaurant.experience_cluster_label),
            normalize(restaurant.review_text),
        ]
        return " ".join(p for p in parts if p)

    def _build(self, restaurants: Sequence[Restaurant]) -> None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ImportError as exc:
            # Thiếu sklearn KHÔNG được làm sập app - chỉ mất tín hiệu ngữ nghĩa.
            self._error = f"thieu scikit-learn: {exc}"
            logger.warning("Tim kiem ngu nghia tat: %s", self._error)
            return

        documents: List[str] = []
        for restaurant in restaurants:
            if not restaurant.place_id:
                continue
            document = self._document(restaurant)
            if not document.strip():
                continue
            self._place_ids.append(restaurant.place_id)
            documents.append(document)

        if len(documents) < 10:
            self._error = f"qua it tai lieu ({len(documents)})"
            logger.warning("Tim kiem ngu nghia tat: %s", self._error)
            return

        try:
            # analyzer="char_wb" + ngram 2-4: tiếng Việt không tách từ bằng khoảng trắng
            # một cách đáng tin ("bánh mì" là 1 từ nhưng có dấu cách), nên n-gram ký tự
            # bền hơn tách từ. `char_wb` chỉ lấy n-gram trong phạm vi một từ.
            self._vectorizer = TfidfVectorizer(
                analyzer="char_wb", ngram_range=(2, 4),
                min_df=2, max_features=60000, sublinear_tf=True,
            )
            self._matrix = self._vectorizer.fit_transform(documents)
            logger.info(
                "Tim kiem ngu nghia san sang: %d quan, %d dac trung",
                self._matrix.shape[0], self._matrix.shape[1],
            )
        except Exception as exc:
            self._error = str(exc)
            self._matrix = None
            logger.warning("Khong dung duoc chi muc ngu nghia: %s", exc)

    def similarity(self, query_text: str) -> Dict[str, float]:
        if not self.is_ready or not query_text or not query_text.strip():
            return {}
        try:
            from sklearn.metrics.pairwise import linear_kernel

            vector = self._vectorizer.transform([normalize(query_text)])
            # Ma trận TF-IDF đã chuẩn hoá L2 nên tích vô hướng CHÍNH LÀ cosine similarity.
            scores = linear_kernel(vector, self._matrix).ravel()
        except Exception as exc:
            logger.debug("Truy van ngu nghia loi, bo qua: %s", exc)
            return {}

        ranked = scores.argsort()[::-1][:MAX_RESULTS]
        return {
            self._place_ids[i]: float(scores[i])
            for i in ranked
            if scores[i] >= MIN_SIMILARITY
        }

    def status(self) -> dict:
        return {
            "ready": self.is_ready,
            "indexed": len(self._place_ids) if self.is_ready else 0,
            "method": "tfidf-char-ngram(2,4)",
            "error": self._error,
        }

"""Mô hình XẾP HẠNG THEO NGỮ CẢNH - Lớp 3 của đề án.

Tổng hợp mọi tín hiệu thành 1 điểm `predicted_score` duy nhất:

    câu tự do  ─┐
    mood        ├─→  predicted_score  →  thứ hạng
    khoảng cách │
    rating      │
    ngữ cảnh   ─┘

Giai đoạn 1 dùng CÔNG THỨC TRỌNG SỐ TƯỜNG MINH, không phải mô hình học.
Đề án nói rõ sẽ nâng cấp lên mô hình học có giám sát (Gradient Boosting/Logistic
Regression) khi thu đủ dữ liệu tương tác - đó là lý do có `POST /interactions` để tích
nhãn từ bây giờ.

Vì sao chưa dùng mô hình học ngay: chưa có MỘT bản ghi tương tác nào. Huấn luyện mô hình
xếp hạng mà không có nhãn thật thì chỉ tạo ra ảo giác chính xác - đúng loại lỗi đã từng
xảy ra với model gợi ý món cũ (rò rỉ nhãn, 98.56% vô nghĩa).

Thuần Python - KHÔNG import pandas/fastapi.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from src.domain.entities.restaurant import Restaurant
from src.domain.services import text_relevance
from src.domain.value_objects.context_signal import NEUTRAL_CONTEXT, ContextSignal
from src.domain.value_objects.location import Location

# Bán kính mặc định. Dataset trải tới ~37km (tận Xuân Mai): trước đây quán cách 36.6km
# vẫn lọt top-5 của người dùng ở Hoàn Kiếm, vì khoảng cách chỉ là tiêu chí phụ nên gần
# như không bao giờ tới lượt.
DEFAULT_MAX_DISTANCE_KM = 10.0

# Trọng số tổng hợp. Tổng = 1.0 để predicted_score nằm gọn trong [0, 1] và giải thích được.
#
# Câu tự do được ưu tiên cao nhất vì đó là thứ người dùng CHỦ ĐỘNG nói ra.
# Ngữ cảnh (thời tiết/giờ) trọng số thấp nhất - nó chỉ nên đẩy nhẹ, không lấn át ý người dùng.
W_TEXT = 0.22        # khớp TỪ KHOÁ (tên, loại hình, review)
W_SEMANTIC = 0.16    # khớp NGỮ NGHĨA (TF-IDF cosine) - Lớp 2 đề án
W_MOOD = 0.26
W_DISTANCE = 0.17
W_RATING = 0.09
# Cụm trải nghiệm (Lớp 1 đề án) - tín hiệu PHỤ, trọng số nhỏ nhất có chủ đích.
# Đề án nói rõ phân cụm "dùng làm một tín hiệu đầu vào cho bước xếp hạng, KHÔNG phải
# bước ra quyết định cuối cùng".
W_CLUSTER = 0.10

# Rating trung bình toàn hệ thống, dùng làm giá trị TRUNG LẬP cho quán chưa có rating.
# Tuyệt đối không dùng 0: quán chưa có đánh giá không phải quán dở (quy tắc Cold Start,
# rules/rules.md mục 3.3).
NEUTRAL_RATING = 4.0
MAX_RATING = 5.0


@dataclass(frozen=True)
class RankedRestaurant:
    """1 quán kèm điểm và LÝ DO - đủ để giao diện giải thích vì sao quán này đứng đây."""

    restaurant: Restaurant
    predicted_score: float
    distance_km: float
    rank_position: int
    text_score: float = 0.0
    semantic_score: float = 0.0
    mood_score: float = 0.0
    cluster_score: float = 0.0
    match_sources: List[str] = field(default_factory=list)

    @property
    def match_source(self) -> str:
        """Nguồn khớp chính, để client hiển thị trung thực vì sao quán này được gợi ý."""
        return "+".join(self.match_sources) if self.match_sources else "mood"


def _distance_score(distance_km: float, max_distance_km: Optional[float]) -> float:
    """Càng gần càng cao, giảm tuyến tính về 0 tại rìa bán kính.

    Dùng giảm dần thay vì chỉ lọc nhị phân: quán cách 1km nên hơn quán cách 9km, chứ
    không phải "cả hai đều trong bán kính nên bằng nhau".
    """
    horizon = max_distance_km or DEFAULT_MAX_DISTANCE_KM
    if horizon <= 0:
        return 0.0
    return max(0.0, 1.0 - (distance_km / horizon))


def _rating_score(rating: Optional[float]) -> float:
    """Chuẩn hoá rating về [0, 1]. Chưa có rating -> dùng mức trung lập, không phải 0."""
    value = NEUTRAL_RATING if rating is None else rating
    return max(0.0, min(value / MAX_RATING, 1.0))


# Giá trị TRUNG LẬP cho quán chưa được phân cụm (Cold Start).
# rules/rules.md mục 3.3 cấm tuyệt đối việc gán 0 hoặc NULL cho `cluster_score`:
# quán chưa phân cụm KHÔNG phải quán dở, nó chỉ là chưa đủ dữ liệu để xếp nhóm.
NEUTRAL_CLUSTER_SCORE = 0.5


def _cluster_score(
    restaurant: Restaurant, cluster_quality: Optional[Dict[int, float]]
) -> float:
    """Điểm chất lượng cụm mà quán thuộc về, chuẩn hoá [0, 1].

    Chưa phân cụm -> trả giá trị TRUNG LẬP toàn hệ thống, đúng quy tắc Cold Start.
    """
    if not cluster_quality or restaurant.experience_cluster_id is None:
        return NEUTRAL_CLUSTER_SCORE
    return cluster_quality.get(restaurant.experience_cluster_id, NEUTRAL_CLUSTER_SCORE)


def compute_cluster_quality(restaurants: Sequence[Restaurant]) -> Dict[int, float]:
    """Chất lượng trung bình của từng cụm, suy từ rating thật của các quán trong cụm.

    Tính từ DỮ LIỆU chứ không gán tay: cụm nào quy tụ nhiều quán đánh giá cao thì điểm
    cụm cao. Nhờ vậy một quán chưa có rating vẫn được hưởng tín hiệu chất lượng từ
    "hàng xóm cùng cụm" - đây chính là giá trị của việc phân cụm.
    """
    totals: Dict[int, List[float]] = {}
    for restaurant in restaurants:
        cluster_id = restaurant.experience_cluster_id
        if cluster_id is None or restaurant.rating is None:
            continue
        totals.setdefault(cluster_id, []).append(restaurant.rating)

    return {
        cluster_id: max(0.0, min(sum(values) / len(values) / MAX_RATING, 1.0))
        for cluster_id, values in totals.items()
        if values
    }


def _normalize_mood(raw_score: float) -> float:
    """Điểm mood thô có thể âm (trọng số âm) hoặc > 1. Ép về [0, 1] để cộng được với
    các tín hiệu khác mà không có tín hiệu nào lấn át chỉ vì thang đo khác nhau."""
    return max(0.0, min(raw_score, 1.0))


def _merge_weights(
    base: Optional[Dict[str, float]], bias: Dict[str, float]
) -> Dict[str, float]:
    merged: Dict[str, float] = dict(base or {})
    for column, value in bias.items():
        merged[column] = merged.get(column, 0.0) + value
    return merged


def rank_restaurants(
    restaurants: Sequence[Restaurant],
    origin: Location,
    query_text: Optional[str] = None,
    mood_weights: Optional[Dict[str, float]] = None,
    context: ContextSignal = NEUTRAL_CONTEXT,
    max_distance_km: Optional[float] = DEFAULT_MAX_DISTANCE_KM,
    limit: int = 10,
    semantic_scores: Optional[Dict[str, float]] = None,
) -> List[RankedRestaurant]:
    """Xếp hạng nhà hàng theo toàn bộ tín hiệu hiện có.

    `mood_weights` None và `query_text` None -> chỉ còn khoảng cách + rating quyết định.
    Đó là hành vi ĐÚNG cho một lượt tìm kiếm không nêu nhu cầu gì.
    """
    # Quán bị ẩn (soft-delete) không bao giờ được lộ ra ngoài - rules/rules.md mục 3.2.
    active = [r for r in restaurants if r.is_active]
    if not active:
        return []

    effective_weights = _merge_weights(mood_weights, context.mood_bias())
    # Chất lượng cụm tính MỘT LẦN cho cả lượt tìm kiếm, không tính lại cho từng quán.
    cluster_quality = compute_cluster_quality(active)

    scored: List[tuple[Restaurant, float, float, float, List[str], float, float]] = []
    for restaurant in active:
        distance_km = origin.distance_km(restaurant.location)

        relevance = text_relevance.relevance(restaurant, query_text)
        mood_raw = (
            restaurant.weighted_mood_score(effective_weights)
            if effective_weights
            else 0.0
        )
        mood_norm = _normalize_mood(mood_raw)
        cluster = _cluster_score(restaurant, cluster_quality)
        semantic = (
            semantic_scores.get(restaurant.place_id, 0.0)
            if semantic_scores and restaurant.place_id else 0.0
        )

        predicted = (
            W_TEXT * relevance.score
            + W_SEMANTIC * min(semantic, 1.0)
            + W_MOOD * mood_norm
            + W_DISTANCE * _distance_score(distance_km, max_distance_km)
            + W_RATING * _rating_score(restaurant.rating)
            + W_CLUSTER * cluster
        )
        sources = list(relevance.sources)
        if semantic >= 0.15 and "semantic" not in sources:
            sources.append("semantic")
        scored.append(
            (restaurant, predicted, distance_km, relevance.score, sources, cluster, semantic)
        )

    # Lọc bán kính TRƯỚC khi cắt top. Nếu bán kính làm rỗng kết quả thì bỏ lọc -
    # thà gợi ý quán xa còn hơn trả về danh sách trống.
    if max_distance_km is not None:
        within = [s for s in scored if s[2] <= max_distance_km]
        if within:
            scored = within

    # Hoà điểm thì quán gần hơn thắng.
    scored.sort(key=lambda s: (-s[1], s[2]))

    ranked: List[RankedRestaurant] = []
    for position, (restaurant, predicted, distance_km, text_score, sources, cluster,
                   semantic) in enumerate(scored[:limit], start=1):
        mood_value = (
            restaurant.weighted_mood_score(effective_weights) if effective_weights else 0.0
        )
        ranked.append(
            RankedRestaurant(
                restaurant=restaurant,
                predicted_score=round(predicted, 4),
                distance_km=round(distance_km, 2),
                rank_position=position,
                text_score=round(text_score, 4),
                semantic_score=round(semantic, 4),
                mood_score=round(mood_value, 4),
                cluster_score=round(cluster, 4),
                match_sources=sources,
            )
        )
    return ranked


__all__ = ["RankedRestaurant", "rank_restaurants", "compute_cluster_quality",
           "DEFAULT_MAX_DISTANCE_KM", "NEUTRAL_CLUSTER_SCORE"]

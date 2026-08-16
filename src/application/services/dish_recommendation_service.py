"""
Luồng "món ăn trước, quán sau" (dish-first) - thay thế cho cách cũ (quán trước, không
biết món gì) bằng cách: (1) chọn ra vài món ăn phù hợp mood, dùng
data_pipeline/dish_knowledge_base.json để suy luận món thật từ categoryName, (2) với mỗi
món, tìm các quán có categoryName khớp rule sinh ra món đó, xếp hạng như /api/recommend
hiện tại (mood-score giảm dần, hòa thì ưu tiên quán gần).

Dùng lại RecommendationService (dataset đã load sẵn) thay vì đọc lại CSV, để không phải
maintain 2 chỗ load dữ liệu.
"""
import math
from typing import Dict, List

from src.application.services.recommendation_service import (
    RecommendationService,
    MOOD_TO_SCORE_COLUMN,
    _haversine_km,
    recommendation_service,
)
from data_pipeline.dish_knowledge import load_knowledge_base, match_rule_for_category
from src.config.di import predict_rule_id

# Cùng 1 mood (happy/sad/excited/relaxed) cần ánh xạ sang 2 nơi khác nhau:
#   - MOOD_TO_SCORE_COLUMN (đã có sẵn): cột mood-score cấp QUÁN để xếp hạng/lọc.
#   - MOOD_TO_DISH_KEYWORDS (mới): tag mood_keywords cấp MÓN trong dish_knowledge_base.json,
#     dùng để chọn món nào đáng được đề xuất trước cho mood này.
# Giữ nhất quán về Ý NGHĨA với MOOD_TO_SCORE_COLUMN, dù tên field khác nhau.
MOOD_TO_DISH_KEYWORDS: Dict[str, List[str]] = {
    "happy": ["fresh", "sweet"],
    "sad": ["comfort", "cozy"],
    "excited": ["spicy"],
    "relaxed": ["comfort", "cozy"],
}

MAX_DISHES = 5


class DishRecommendationService:
    def __init__(self, base_service: RecommendationService = recommendation_service):
        self._base = base_service
        self._kb = load_knowledge_base()

    def suggest(
        self,
        mood: str,
        user_lat: float = 21.0285,
        user_lng: float = 105.8542,
        top_k_restaurants_per_dish: int = 5,
    ) -> List[Dict]:
        if not self._base.is_ready or self._base.restaurants is None:
            raise FileNotFoundError(
                f"Dataset chưa sẵn sàng ({self._base.dataset_path} không tồn tại). "
                "Endpoint này không dùng được ở chế độ degraded."
            )

        mood_key = mood.lower()
        score_column = MOOD_TO_SCORE_COLUMN.get(mood_key)
        dish_keywords = MOOD_TO_DISH_KEYWORDS.get(mood_key)
        if score_column is None or dish_keywords is None:
            raise ValueError(
                f"Mood '{mood}' không được hỗ trợ. Các mood hợp lệ: {list(MOOD_TO_SCORE_COLUMN.keys())}"
            )

        # 1. Chọn ứng viên món ăn: quét toàn bộ rule trong knowledge base, giữ lại món
        #    nào có mood_keywords khớp mood đang xét. Giữ nguyên thứ tự rule trong JSON
        #    (rule cụ thể đứng trước rule chung chung, xem dish_knowledge.py).
        candidate_dishes = []  # list of (rule, dish)
        for rule in self._kb["rules"]:
            for dish in rule["dishes"]:
                if any(k in dish.get("mood_keywords", []) for k in dish_keywords):
                    candidate_dishes.append((rule, dish))

        if not candidate_dishes:
            return []

        # 2. Gán mỗi quán vào đúng 1 rule (dựa trên categoryName), tính khoảng cách 1 lần
        #    cho toàn bộ dataset thay vì lặp lại cho từng món (tốn CPU với 4180 quán).
        df = self._base.restaurants.copy()
        df["distance_km"] = df.apply(
            lambda row: _haversine_km(user_lat, user_lng, row["location/lat"], row["location/lng"]),
            axis=1,
        )
        # Prefer ML prediction for rule id when available, otherwise fallback to KB matching
        def _assign_rule(row):
            predicted = predict_rule_id(row.get("categoryName"), row.get("cuisine"))
            if predicted:
                return predicted
            return (match_rule_for_category(row.get("categoryName"), self._kb) or {}).get("id")

        df["_rule_id"] = df.apply(_assign_rule, axis=1)
        # mark whether the rule assignment came from ML (for downstream confidence reporting)
        df["_predicted_by_ml"] = df.apply(
            lambda row: predict_rule_id(row.get("categoryName"), row.get("cuisine")) is not None,
            axis=1,
        )

        # 3. Với mỗi món ứng viên, lấy quán thuộc đúng rule đó, xếp hạng theo mood-score
        #    giảm dần rồi khoảng cách tăng dần (giống hệt tiêu chí của /api/recommend).
        results = []
        seen_rule_ids = set()
        for rule, dish in candidate_dishes:
            if rule["id"] in seen_rule_ids:
                continue  # mỗi rule chỉ hiện 1 lần dù có nhiều món khớp mood
            seen_rule_ids.add(rule["id"])

            matching = df[df["_rule_id"] == rule["id"]]
            if matching.empty:
                continue

            top_restaurants = matching.sort_values(
                by=[score_column, "distance_km"], ascending=[False, True]
            ).head(top_k_restaurants_per_dish)

            restaurant_list = [
                {
                    "name": r["title"],
                    "category": r["categoryName"],
                    "address": r.get("address", "N/A"),
                    "lat": r["location/lat"],
                    "lng": r["location/lng"],
                    "distance_km": round(float(r["distance_km"]), 2),
                    "mood_match_score": float(r[score_column]),
                }
                for _, r in top_restaurants.iterrows()
            ]

            # if any matching restaurant was assigned via ML, mark dish_confidence as 'ml'
            ml_assigned = matching["_predicted_by_ml"].any() if not matching.empty else False
            results.append({
                "dish_name": dish["name"],
                "cuisine": dish.get("cuisine"),
                "spice_level": dish.get("spice_level"),
                "temperature": dish.get("temperature"),
                "dish_confidence": "ml" if ml_assigned else rule["confidence"],
                "restaurants": restaurant_list,
            })

            if len(results) >= MAX_DISHES:
                break

        return results


# Note: do NOT create module-level singleton here. Service should be instantiated
# by application startup and provided via DI (app.state or Depends).

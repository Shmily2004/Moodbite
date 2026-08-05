import pandas as pd
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
import math


@dataclass
class Restaurant:
    id: str
    name: str
    category: str
    lat: float
    lng: float
    mood_score: float
    distance: float


# Ánh xạ mood theo cảm xúc (API nhận: happy/sad/excited/relaxed) sang cột mood-score
# theo THUỘC TÍNH MÓN ĂN đã được data_pipeline/feature_engineering.py tính sẵn
# (comfort_cozy, spicy_hot, fresh_healthy, cheap_budget, quick_fast).
#
# Đây là 2 bộ từ vựng khác nhau (cảm xúc người dùng vs. đặc điểm món ăn), nên việc ánh xạ
# là quyết định sản phẩm, không có đáp án "đúng tuyệt đối" - dưới đây là lựa chọn hợp lý,
# có thể điều chỉnh lại tùy trải nghiệm mong muốn:
#   - happy    -> fresh_healthy (vui vẻ, năng lượng tích cực, đồ ăn tươi/nhẹ nhàng)
#   - sad      -> comfort_cozy  (buồn thường tìm món ăn "comfort food", ấm cúng)
#   - excited  -> spicy_hot     (hào hứng, muốn thử món mạnh/cay/nóng)
#   - relaxed  -> comfort_cozy  (thư giãn, không gian ấm cúng, nhẹ nhàng)
MOOD_TO_SCORE_COLUMN = {
    "happy": "fresh_healthy_score",
    "sad": "comfort_cozy_score",
    "excited": "spicy_hot_score",
    "relaxed": "comfort_cozy_score",
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
    d_lat = lat2_r - lat1_r
    d_lon = lon2_r - lon1_r
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(d_lon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class RecommendationService:
    def __init__(self, dataset_path: str = "data_pipeline/data_cleaned/dataset_moodbite_features.csv"):
        """Load restaurant dataset"""
        self.dataset_path = Path(dataset_path)
        self.restaurants = self._load_dataset()

    def _load_dataset(self) -> pd.DataFrame:
        """Load CSV dataset"""
        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {self.dataset_path}. "
                "Chạy trước: python -m data_pipeline.merge_and_prepare_raw && "
                "python -m data_pipeline.data_cleaning && python -m data_pipeline.feature_engineering"
            )

        df = pd.read_csv(self.dataset_path)
        print(f"✅ Loaded {len(df)} restaurants")
        return df

    def recommend(self, mood: str, user_lat: float = 21.0285, user_lng: float = 105.8542, top_k: int = 5) -> List[Dict]:
        """
        Recommend restaurants based on mood.

        Dùng lại mood-score đã được data_pipeline/feature_engineering.py tính sẵn từ
        categoryName tiếng Việt (comfort_cozy_score, spicy_hot_score, ...), thay vì so khớp
        từ khóa tiếng Anh trực tiếp với categoryName tiếng Việt (cách cũ luôn ra 0 vì
        2 ngôn ngữ khác nhau, khiến kết quả gần như ngẫu nhiên bất kể mood chọn gì).

        Args:
            mood: happy, sad, excited, relaxed
            user_lat, user_lng: vị trí người dùng (mặc định: trung tâm Hà Nội)
            top_k: số lượng gợi ý

        Returns:
            List of recommended restaurants, đã sắp xếp theo mood-score giảm dần
            (khi bằng điểm, quán gần hơn được ưu tiên).
        """
        score_column = MOOD_TO_SCORE_COLUMN.get(mood.lower())
        if score_column is None:
            raise ValueError(
                f"Mood '{mood}' không được hỗ trợ. Các mood hợp lệ: {list(MOOD_TO_SCORE_COLUMN.keys())}"
            )

        df = self.restaurants.copy()

        df["distance_km"] = df.apply(
            lambda row: _haversine_km(user_lat, user_lng, row["location/lat"], row["location/lng"]),
            axis=1,
        )

        # Sắp xếp theo mood-score giảm dần, hòa điểm thì ưu tiên quán gần hơn.
        top_restaurants = df.sort_values(
            by=[score_column, "distance_km"], ascending=[False, True]
        ).head(top_k)

        recommendations = []
        for _, row in top_restaurants.iterrows():
            recommendations.append({
                "name": row["title"],
                "category": row["categoryName"],
                "address": row.get("address", "N/A"),
                "lat": row["location/lat"],
                "lng": row["location/lng"],
                "distance_km": round(float(row["distance_km"]), 2),
                "mood_match_score": float(row[score_column]),
                "mood": mood,
            })

        return recommendations


# Initialize service (global)
recommendation_service = RecommendationService()
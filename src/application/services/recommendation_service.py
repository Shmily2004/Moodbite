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
#
# MOOD_PROFILES: mỗi mood là TỔ HỢP CÓ TRỌNG SỐ của nhiều cột, không chỉ 1 cột.
# Lý do (2 bug thật, đã đo trên dataset 4169 quán):
#   1. Trước đây "sad" và "relaxed" cùng trỏ vào comfort_cozy_score nên trả về DANH SÁCH
#      QUÁN GIỐNG HỆT NHAU - người dùng đổi mood mà kết quả không đổi.
#   2. cheap_budget_score và quick_fast_score được data_pipeline tính ra nhưng KHÔNG mood
#      nào dùng tới - 2/5 feature chết, phí công tính.
# Trọng số âm nghĩa là "trừ điểm".
#
# sad và relaxed cùng lấy comfort_cozy làm cột chính (cả hai đều là "ấm cúng"), nên phải
# có cột phụ đủ mạnh để tách ra, nếu không kết quả lại giống hệt nhau. Chọn cheap_budget
# làm cột tách, dựa trên số liệu thật của dataset:
#   - Trong nhóm comfort_cozy cao, quick_fast gần như bằng 0 (chỉ 164/1774 quán khác 0)
#     -> KHÔNG tách được gì, dù đặt trọng số bao nhiêu.
#   - cheap_budget thì trải rộng (0.0 - 0.73 ngay trong top comfort) và là cột dày nhất
#     (3977/4169 quán khác 0) -> tách được thật.
# Ý nghĩa sản phẩm: buồn thì tìm đồ ăn ấm bụng, no, rẻ; thư giãn thì tìm chỗ ngồi lâu,
# yên tĩnh, chịu chi hơn (quán cà phê/sân vườn) và nhất định không phải đồ ăn nhanh.
MOOD_PROFILES: Dict[str, Dict[str, float]] = {
    "happy":   {"fresh_healthy_score": 1.0, "quick_fast_score": 0.3},
    "sad":     {"comfort_cozy_score": 1.0, "cheap_budget_score": 0.5},
    "excited": {"spicy_hot_score": 1.0, "fresh_healthy_score": 0.2},
    "relaxed": {"comfort_cozy_score": 1.0, "cheap_budget_score": -0.5,
                "quick_fast_score": -0.5},
}

# Cột CHÍNH của mỗi mood (trọng số lớn nhất). Giữ lại vì dish_recommendation_service.py
# cần đúng 1 tên cột để xếp hạng quán trong từng nhóm món - không đổi hành vi bên đó.
MOOD_TO_SCORE_COLUMN = {
    mood: max(weights, key=weights.get) for mood, weights in MOOD_PROFILES.items()
}

# Bán kính mặc định. Dataset trải tới ~37km (tận Xuân Mai): trước đây quán cách 36.6km
# vẫn lọt top-5 của người dùng ở Hoàn Kiếm, vì khoảng cách chỉ là tiêu chí phụ THỨ BA nên
# gần như không bao giờ tới lượt (rating là số thực, rất hiếm khi hòa đúng bằng nhau).
DEFAULT_MAX_DISTANCE_KM = 10.0


def _none_if_nan(value):
    """NaN của pandas không phải JSON hợp lệ (thành NaN literal, JSON.parse phía JS sẽ lỗi).
    Trả None để FastAPI serialize thành null - đúng quy ước "không có dữ liệu" của dự án."""
    return None if value is None or pd.isna(value) else value


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
    d_lat = lat2_r - lat1_r
    d_lon = lon2_r - lon1_r
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(d_lon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class RecommendationService:
    def __init__(self, dataset_path: str = "data_pipeline/data_cleaned/dataset_moodbite_features.csv"):
        """Load restaurant dataset - KHÔNG crash nếu thiếu file, chỉ đánh dấu is_ready=False.
        Toàn bộ app (bao gồm endpoint /predict-floorplan không liên quan) sẽ vẫn chạy được
        thay vì sập hoàn toàn chỉ vì thiếu 1 dataset - đúng nguyên tắc graceful degradation
        đã áp dụng xuyên suốt dự án (VD: CsvRestaurantRepository.ts phía TypeScript)."""
        self.dataset_path = Path(dataset_path)
        self.restaurants: pd.DataFrame | None = None
        self.is_ready = False
        try:
            self.restaurants = self._load_dataset()
            self.is_ready = True
        except FileNotFoundError as e:
            print(f"⚠️  {e}")
            print("⚠️  RecommendationService khởi động ở chế độ degraded - /api/recommend sẽ trả lỗi rõ ràng thay vì crash app.")

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

    def recommend(
        self,
        mood: str,
        user_lat: float = 21.0285,
        user_lng: float = 105.8542,
        top_k: int = 5,
        max_distance_km: float | None = DEFAULT_MAX_DISTANCE_KM,
    ) -> List[Dict]:
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
        if not self.is_ready or self.restaurants is None:
            raise FileNotFoundError(
                f"Dataset chưa sẵn sàng ({self.dataset_path} không tồn tại). "
                "Server đang chạy ở chế độ degraded - endpoint này không dùng được."
            )

        weights = MOOD_PROFILES.get(mood.lower())
        if weights is None:
            raise ValueError(
                f"Mood '{mood}' không được hỗ trợ. Các mood hợp lệ: {list(MOOD_PROFILES.keys())}"
            )

        df = self.restaurants.copy()

        df["distance_km"] = df.apply(
            lambda row: _haversine_km(user_lat, user_lng, row["location/lat"], row["location/lng"]),
            axis=1,
        )

        # Điểm mood = tổng có trọng số của nhiều cột (xem MOOD_PROFILES).
        df["_mood_score"] = sum(
            df[col].fillna(0) * w for col, w in weights.items()
        )

        # Lọc theo bán kính TRƯỚC khi xếp hạng: gợi ý quán cách 36km cho người ở Hoàn Kiếm
        # là vô dụng dù mood-score có cao tới đâu. Nếu bán kính quá hẹp đến mức không còn
        # quán nào thì bỏ lọc (thà gợi ý quán xa còn hơn trả về rỗng).
        if max_distance_km is not None:
            within = df[df["distance_km"] <= max_distance_km]
            if not within.empty:
                df = within

        # Sắp xếp theo: (1) mood-score giảm dần, (2) rating thật giảm dần (quán không
        # có rating coi như 0 CHỈ để xếp hạng, KHÔNG ghi đè giá trị thật - dùng cột
        # tạm _rating_for_sort), (3) khoảng cách gần hơn. Thêm bước (2) vì ~48% dataset
        # có mood-score bằng nhau (thường = 0, do categoryName quá chung chung như
        # "Nhà hàng") - nếu không có rating làm tiêu chí phụ, thứ tự sẽ gần như ngẫu
        # nhiên trong nhóm đó, để lọt quán rating thấp lên trước quán rating cao.
        df["_rating_for_sort"] = df["totalScore"].fillna(0)
        top_restaurants = df.sort_values(
            by=["_mood_score", "_rating_for_sort", "distance_km"],
            ascending=[False, False, True],
        ).head(top_k)

        recommendations = []
        for _, row in top_restaurants.iterrows():
            recommendations.append({
                # placeId để client gọi tiếp GET /api/restaurant/{place_id} lấy review/ảnh.
                "placeId": row.get("placeId"),
                "name": row["title"],
                "category": row["categoryName"],
                "address": row.get("address", "N/A"),
                # Hiện luôn giá + rating ngay ở danh sách; None nghĩa là CHƯA CÓ dữ liệu
                # (quán từ OSM), không phải "miễn phí" hay "0 sao".
                "price": _none_if_nan(row.get("price")),
                "rating": _none_if_nan(row.get("totalScore")),
                "reviews_count": _none_if_nan(row.get("reviewsCount")),
                "lat": row["location/lat"],
                "lng": row["location/lng"],
                "distance_km": round(float(row["distance_km"]), 2),
                "mood_match_score": round(float(row["_mood_score"]), 4),
                "mood": mood,
            })

        return recommendations


# Initialize service (global)
recommendation_service = RecommendationService()
"""Tra cứu thông tin CHI TIẾT của 1 quán: giá, review thật, ảnh, không gian, giờ mở cửa.

Tách khỏi RecommendationService vì 2 việc có đặc tính hoàn toàn khác nhau:
  - Xếp hạng: cần TOÀN BỘ 4170 quán nhưng chỉ vài cột nhẹ, chạy ở mọi request.
  - Xem chi tiết: chỉ cần ĐÚNG 1 quán nhưng kèm dữ liệu nặng (review, ảnh).
Nhét chung vào dataset_moodbite_features.csv làm file phồng từ 0.7MB lên 12MB, mà
recommend() lại gọi df.copy() mỗi request -> copy 12MB mỗi lần gọi API.

Dữ liệu do data_pipeline/feature_engineering.py sinh ra (bước _write_details).
"""
import json
from pathlib import Path
from typing import Dict, Optional


class RestaurantDetailsService:
    def __init__(
        self,
        details_path: str = "data_pipeline/data_cleaned/restaurant_details.json",
    ):
        self.details_path = Path(details_path)
        self._details: Dict[str, dict] = {}
        self.is_ready = False
        try:
            self._details = self._load()
            self.is_ready = True
        except FileNotFoundError as e:
            # Graceful degradation giống RecommendationService: thiếu file thì endpoint
            # chi tiết báo lỗi rõ ràng, KHÔNG làm sập cả app.
            print(f"⚠️  {e}")
            print("⚠️  RestaurantDetailsService chạy ở chế độ degraded - "
                  "GET /api/restaurant/{place_id} sẽ báo lỗi thay vì crash app.")

    def _load(self) -> Dict[str, dict]:
        if not self.details_path.exists():
            raise FileNotFoundError(
                f"Details not found: {self.details_path}. "
                "Chạy trước: python -m data_pipeline.feature_engineering"
            )
        with open(self.details_path, encoding="utf-8") as fh:
            data = json.load(fh)
        print(f"✅ Loaded details for {len(data)} restaurants")
        return data

    def get(self, place_id: str) -> Optional[dict]:
        """Trả None nếu không có dữ liệu chi tiết. Đây là trường hợp BÌNH THƯỜNG chứ không
        phải lỗi: 3623/4170 quán đến từ OpenStreetMap, vốn không hề có giá/review/ảnh."""
        if not self.is_ready:
            raise FileNotFoundError(
                f"Dữ liệu chi tiết chưa sẵn sàng ({self.details_path} không tồn tại)."
            )
        return self._details.get(str(place_id))

    @property
    def count(self) -> int:
        return len(self._details)


restaurant_details_service = RestaurantDetailsService()

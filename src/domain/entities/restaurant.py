"""Entity Restaurant. Thuần Python - KHÔNG import pandas/FastAPI.

Quy ước QUAN TRỌNG về giá trị thiếu: `price`, `rating`, `reviews_count` để None nghĩa là
CHƯA CÓ DỮ LIỆU, không phải "miễn phí" hay "0 sao". 3623/4170 quán đến từ OpenStreetMap
vốn không hề có các trường này. Tuyệt đối không thay None bằng 0 khi trả cho client.

`price` là CHUỖI hiển thị theo khoảng giá của Google Maps ("1-100.000 ₫", "70 US$"),
KHÔNG phải số. Dataset có nhiều đơn vị tiền tệ và dạng khoảng, nên ép về float vừa sai
vừa làm hỏng response. Muốn lọc theo giá thì phải parse thành value object riêng trước.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.domain.value_objects.location import Location
from src.domain.value_objects.mood import MOOD_SCORE_COLUMNS


@dataclass(frozen=True)
class Restaurant:
    place_id: Optional[str]
    name: str
    category: Optional[str]
    location: Location
    address: Optional[str] = None
    cuisine: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    # {tên cột mood-score -> giá trị}. Thiếu cột nào coi như 0.0.
    mood_scores: Dict[str, float] = field(default_factory=dict)

    # --- Dữ liệu phục vụ tìm kiếm bằng câu tự do -------------------------------
    # Tất cả đều THƯA (xem PROJECT_CHECKLIST.md). Thiếu = None, và việc thiếu KHÔNG
    # được coi là điểm xấu khi xếp hạng.
    atmosphere_tags: List[str] = field(default_factory=list)   # 8.7% quán có
    review_text: Optional[str] = None                          # 8.4% quán có
    opening_hours: Optional[str] = None                        # 25.6% quán có
    is_active: bool = True  # soft-delete: quán tắt không bao giờ được trả cho người dùng

    # --- trường bổ sung từ bản thu thập OSM mới --------------------------------
    # Đơn vị hành chính (OSM admin_level=6). Từ 2025 Việt Nam bỏ cấp quận/huyện nên
    # giá trị thực tế là "Phường ..." chứ không phải "Quận ...".
    district: Optional[str] = None
    dietary: List[str] = field(default_factory=list)    # vegetarian / vegan / halal
    amenities: List[str] = field(default_factory=list)  # outdoor_seating, wifi...
    phone: Optional[str] = None
    website: Optional[str] = None
    # Nguồn gốc dữ liệu - để giải thích được "quán này ở đâu ra, đáng tin tới đâu".
    source: Optional[str] = None
    data_confidence: Optional[str] = None

    @property
    def atmosphere_text(self) -> Optional[str]:
        """Các tag không gian gộp thành 1 chuỗi để so khớp văn bản."""
        return " ".join(self.atmosphere_tags) if self.atmosphere_tags else None

    def mood_score(self, column: str) -> float:
        """Điểm mood theo 1 cột. Thiếu dữ liệu -> 0.0 (trung lập, không phải điểm trừ)."""
        value = self.mood_scores.get(column)
        return 0.0 if value is None else float(value)

    def weighted_mood_score(self, weights: Dict[str, float]) -> float:
        """Tổng có trọng số của nhiều cột mood-score. Xem domain/value_objects/mood.py."""
        return sum(self.mood_score(col) * w for col, w in weights.items())

    def rating_for_ranking(self) -> float:
        """Rating dùng ĐỂ XẾP HẠNG: quán chưa có rating coi như 0.

        Chỉ dùng nội bộ khi sort. KHÔNG được dùng giá trị này khi trả về cho client -
        client phải thấy None để hiển thị "chưa có đánh giá".
        """
        return 0.0 if self.rating is None else float(self.rating)


__all__ = ["Restaurant", "MOOD_SCORE_COLUMNS"]

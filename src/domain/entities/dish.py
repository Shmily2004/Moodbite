"""Entity Dish và DishRule (1 rule trong dish_knowledge_base.json).

Thuần Python - KHÔNG import pandas/FastAPI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.domain.value_objects.text import contains_phrase

# Mức độ tin cậy của việc suy luận "quán này bán món gì".
# Đây là suy luận HEURISTIC từ categoryName, KHÔNG phải menu thật của quán.
CONFIDENCE_SPECIFIC = "specific"          # khớp rule cụ thể: "phở", "lẩu"...
CONFIDENCE_GENERIC = "generic_fallback"   # suy luận rộng từ nhóm chung: "nhà hàng"
CONFIDENCE_UNKNOWN = "unknown"            # không khớp rule nào
CONFIDENCE_ML = "ml"                      # rule do model ML gán


@dataclass(frozen=True)
class Dish:
    name: str
    cuisine: Optional[str] = None
    spice_level: Optional[int] = None
    temperature: Optional[str] = None
    portion_size: Optional[str] = None
    mood_keywords: List[str] = field(default_factory=list)

    def matches_any_mood_keyword(self, keywords: List[str]) -> bool:
        return any(k in self.mood_keywords for k in keywords)


@dataclass(frozen=True)
class DishRule:
    """1 rule ánh xạ categoryName -> danh sách món."""

    id: str
    confidence: str
    dishes: List[Dish] = field(default_factory=list)
    match_category: List[str] = field(default_factory=list)
    match_cuisine: List[str] = field(default_factory=list)

    def matches_text(self, text: Optional[str]) -> bool:
        """Rule này có khớp một đoạn chữ không (tên quán hoặc loại hình).

        Khớp theo CỤM TỪ NGUYÊN VẸN sau khi bỏ dấu, vì hai lý do đo được trên dữ liệu thật:
          - Nhiều quán tự đặt tên không dấu ("Pho Bo", "O Bun Cha") -> phải bỏ dấu mới khớp.
          - Bỏ dấu xong "ốc" thành "oc"; nếu khớp chuỗi con thì "oc" khớp luôn "Ngọc",
            "Học", "Cốc" -> gợi ý món ốc cho quán chè. Khớp theo từ nguyên vẹn loại bỏ
            hoàn toàn lỗi này.
        """
        return any(contains_phrase(text, keyword) for keyword in self.match_category)

    # Tên cũ, giữ lại để không phải sửa mọi nơi gọi cùng lúc.
    def matches_category(self, category_name: Optional[str]) -> bool:
        return self.matches_text(category_name)

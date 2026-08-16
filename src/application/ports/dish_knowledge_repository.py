"""PORT: hợp đồng đọc tri thức món ăn (dish_knowledge_base.json)."""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from src.domain.entities.dish import DishRule


@runtime_checkable
class DishKnowledgeRepository(Protocol):
    def list_rules(self) -> List[DishRule]:
        """Toàn bộ rule, GIỮ NGUYÊN thứ tự trong file JSON.

        Thứ tự quyết định độ ưu tiên: rule cụ thể ("phở") phải đứng trước rule chung
        ("nhà hàng"), nếu không rule chung sẽ nuốt mất rule cụ thể.
        """
        ...

    def match_rule_for_category(self, category_name: Optional[str]) -> Optional[DishRule]:
        """Rule đầu tiên khớp categoryName, None nếu không khớp gì."""
        ...

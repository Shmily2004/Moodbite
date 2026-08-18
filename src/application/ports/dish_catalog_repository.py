"""PORT: hợp đồng đọc DANH MỤC MÓN ĂN.

Khác `DishKnowledgeRepository` (đọc rule để đoán "quán này bán món gì") - port này phục vụ
chiều ngược lại: người dùng chọn MÓN trước, nên món phải là thực thể tra cứu được theo id.

Hai adapter cùng triển khai port này:
  - `JsonDishCatalogRepository`   : đọc dish_catalog.json (chỉ đọc, mặc định)
  - `SqliteDishCatalogRepository` : đọc/ghi, cho trang quản trị thêm món thủ công
"""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from src.domain.entities.dish import Dish


@runtime_checkable
class DishCatalogRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        """Đã nạp được danh mục chưa. False -> endpoint liên quan trả 503 kèm cách khắc phục."""
        ...

    def list_dishes(self) -> List[Dish]:
        """Toàn bộ món đang bật (`is_active`). Món bị ẩn KHÔNG được lộ ra ngoài."""
        ...

    def get_dish(self, dish_id: str) -> Optional[Dish]:
        """Một món theo id, None nếu không có."""
        ...

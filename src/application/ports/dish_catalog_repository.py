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

    def list_all_dishes(self) -> List[Dish]:
        """TOÀN BỘ món, KỂ CẢ món đang tắt. Chỉ dùng cho trang quản trị.

        ⚠️ ĐỪNG dùng cho endpoint công khai — `list_dishes()` mới là thứ người dùng được
        thấy. Món tắt là món chưa có quán nào ở Hà Nội bán, hiện ra cho người dùng thì
        bấm vào chỉ gặp danh sách quán rỗng.

        Vì sao quản trị cần: đo được 855 món trong file nhưng chỉ 298 món đang bật
        (2026-08-26). Trang quản trị phải nói được cả ba con số — tổng, có quán, chưa có
        quán — nếu không thì người quản trị nhìn thấy 298 và tưởng mất 557 món.
        """
        ...

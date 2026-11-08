"""PORT: bản SỬA TAY của mô tả món (do quản trị viên nhập).

Chỉ lưu phần người dùng đã sửa, KHÔNG sao chép cả món. Khi đọc, bản sửa được đọc chồng lên
danh mục gốc (xem `OverlayDishCatalogRepository`), nhờ vậy chạy lại `build_dish_catalog.py`
không làm mất chữ người quản trị đã sửa.
"""
from __future__ import annotations

from typing import Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class DishOverrideRepository(Protocol):
    def all_descriptions(self) -> Dict[str, str]:
        """dish_id -> mô tả đã sửa tay. Món không sửa thì không có khoá."""
        ...

    def get_description(self, dish_id: str) -> Optional[str]:
        ...

    def set_description(self, dish_id: str, text: str, actor: str) -> None:
        ...

    def clear_description(self, dish_id: str) -> None:
        """Gỡ bản sửa; món quay về mô tả gốc. Gỡ món chưa sửa là no-op, không lỗi."""
        ...

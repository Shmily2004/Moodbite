"""ADAPTER: danh mục món = danh mục GỐC + bản SỬA TAY đọc chồng lên.

VÌ SAO LÀ MỘT LỚP BAO (decorator) chứ không sửa `JsonDishCatalogRepository`: danh mục gốc
là file sinh tự động và phải giữ nguyên. Bản sửa nằm ở CSDL riêng; lớp này ghép hai nguồn khi
đọc, để MỌI nơi dùng danh mục (người dùng lẫn quản trị) đều thấy cùng một mô tả.

Đọc bản sửa MỖI LẦN gọi, không đệm: bảng nhỏ, và đệm là đúng loại bug "sửa xong mà vẫn thấy
bản cũ" đã gặp ở kho quán (xem `_write` trong `sqlite_restaurant_repository.py`).
"""
from __future__ import annotations

from dataclasses import replace
from typing import List, Optional

from src.application.ports.dish_override_repository import DishOverrideRepository
from src.domain.entities.dish import Dish


class OverlayDishCatalogRepository:
    def __init__(self, base, overrides: DishOverrideRepository) -> None:
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name: str):
        # Phần còn lại (`status`, `load_error`, `json_path`...) đi thẳng xuống danh mục gốc.
        return getattr(self._base, name)

    @property
    def is_ready(self) -> bool:
        return self._base.is_ready

    def _ap_ban_sua(self, dishes: List[Dish], sua: dict) -> List[Dish]:
        if not sua:
            return dishes
        return [
            replace(d, description=sua[d.identifier]) if d.identifier in sua else d
            for d in dishes
        ]

    def list_dishes(self) -> List[Dish]:
        return self._ap_ban_sua(self._base.list_dishes(), self._overrides.all_descriptions())

    def list_all_dishes(self) -> List[Dish]:
        return self._ap_ban_sua(
            self._base.list_all_dishes(), self._overrides.all_descriptions()
        )

    def get_dish(self, dish_id: str) -> Optional[Dish]:
        mon = self._base.get_dish(dish_id)
        if mon is None:
            return None
        sua = self._overrides.get_description(dish_id)
        return replace(mon, description=sua) if sua is not None else mon

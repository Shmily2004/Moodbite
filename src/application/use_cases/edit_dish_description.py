"""Use case: quản trị viên sửa (hoặc gỡ sửa) mô tả một món.

Chỉ ĐIỀU PHỐI: kiểm món có tồn tại, đưa chữ qua quy tắc domain, rồi ghi hoặc gỡ bản sửa.
Quy tắc độ dài và "chuỗi rỗng = gỡ" nằm ở `domain/value_objects/dish_description.py`.
"""
from __future__ import annotations

from typing import Optional

from src.application.ports.dish_override_repository import DishOverrideRepository
from src.application.use_cases.find_restaurants_for_dish import DishNotFoundError
from src.domain.entities.dish import Dish
from src.domain.value_objects.dish_description import chuan_hoa_mo_ta


class EditDishDescriptionUseCase:
    def __init__(self, catalog, overrides: DishOverrideRepository) -> None:
        self._catalog = catalog
        self._overrides = overrides

    def execute(self, dish_id: str, text: Optional[str], actor: str) -> Dish:
        ma = (dish_id or "").strip()
        if not any(d.identifier == ma for d in self._catalog.list_all_dishes()):
            raise DishNotFoundError(dish_id)

        # Kiểm độ dài TRƯỚC khi chạm CSDL: một lỗi nhập không được để lại dữ liệu dở dang.
        cleaned = chuan_hoa_mo_ta(text)
        if cleaned is None:
            self._overrides.clear_description(ma)
        else:
            self._overrides.set_description(ma, cleaned, actor)

        mon = self._catalog.get_dish(ma)
        if mon is None:  # không xảy ra trừ khi danh mục vừa bị dựng lại giữa chừng
            raise DishNotFoundError(dish_id)
        return mon

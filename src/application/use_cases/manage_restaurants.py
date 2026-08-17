"""USE CASE quản trị: xem, sửa, ẩn/bỏ ẩn quán.

Chỉ ĐIỀU PHỐI. Quy tắc "trường nào được sửa" nằm ở
`domain/value_objects/restaurant_edit.py`, không nằm ở đây và càng không ở router.

Ba use case tách riêng vì là ba luồng khác nhau, dù cùng thao tác trên một repository.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Mapping, Optional

from src.application.errors import DataNotReadyError
from src.application.ports.admin_restaurant_repository import AdminRestaurantRepository

# Dùng lại đúng lớp lỗi mà `/interactions` đang dùng, để `error_handlers.py` ánh xạ
# sang 404 RESTAURANT_NOT_FOUND ở MỘT chỗ duy nhất.
from src.application.use_cases.log_interaction import RestaurantNotFoundError
from src.domain.entities.restaurant import Restaurant
from src.domain.value_objects.restaurant_edit import RestaurantEdit

logger = logging.getLogger("moodbite.admin")

MAX_ADMIN_PAGE_SIZE = 200


def _require_ready(repository: object) -> None:
    """Chưa nạp được dữ liệu -> 503 kèm cách khắc phục, không phải 500."""
    if not getattr(repository, "is_ready", False):
        raise DataNotReadyError(
            "Kho dữ liệu quản trị chưa sẵn sàng. Chạy: python scripts/build_sqlite.py "
            "rồi khởi động lại với MOODBITE_STORAGE=sqlite"
        )


@dataclass
class ListRestaurantsForAdminUseCase:
    restaurants: AdminRestaurantRepository

    def execute(
        self,
        query: Optional[str] = None,
        limit: int = 50,
        include_hidden: bool = True,
    ) -> List[Restaurant]:
        _require_ready(self.restaurants)
        # Chặn trên số lượng: admin gõ limit=999999 sẽ kéo cả 4938 quán qua JSON.
        safe_limit = max(1, min(int(limit), MAX_ADMIN_PAGE_SIZE))
        return self.restaurants.list_for_admin(
            query=query, limit=safe_limit, include_hidden=include_hidden
        )


@dataclass
class UpdateRestaurantUseCase:
    restaurants: AdminRestaurantRepository

    def execute(self, place_id: str, raw_changes: Mapping[str, object]) -> Restaurant:
        _require_ready(self.restaurants)
        # Kiểm tra hợp lệ TRƯỚC khi hỏi CSDL: yêu cầu sai thì phải là 400, không phải 404.
        edit = RestaurantEdit.from_dict(raw_changes)

        if self.restaurants.get_for_admin(place_id) is None:
            raise RestaurantNotFoundError(f"Không tìm thấy quán: {place_id}")

        self.restaurants.update_fields(place_id, edit.changes)
        logger.info("Admin sửa quán %s: %s", place_id, sorted(edit.changes))

        updated = self.restaurants.get_for_admin(place_id)
        if updated is None:  # pragma: no cover - chỉ xảy ra nếu bị xoá xen giữa
            raise RestaurantNotFoundError(f"Không tìm thấy quán: {place_id}")
        return updated


@dataclass
class SetRestaurantVisibilityUseCase:
    """Ẩn (soft-delete) hoặc bỏ ẩn.

    Ẩn KHÔNG xoá dữ liệu: quán biến mất khỏi tìm kiếm và `/restaurants/{id}` trả 404,
    nhưng admin vẫn thấy và bỏ ẩn lại được.
    """

    restaurants: AdminRestaurantRepository

    def execute(self, place_id: str, is_active: bool) -> Restaurant:
        _require_ready(self.restaurants)
        if self.restaurants.get_for_admin(place_id) is None:
            raise RestaurantNotFoundError(f"Không tìm thấy quán: {place_id}")

        self.restaurants.set_active(place_id, is_active)
        logger.info("Admin %s quán %s", "bỏ ẩn" if is_active else "ẩn", place_id)

        updated = self.restaurants.get_for_admin(place_id)
        if updated is None:  # pragma: no cover
            raise RestaurantNotFoundError(f"Không tìm thấy quán: {place_id}")
        return updated


__all__ = [
    "ListRestaurantsForAdminUseCase",
    "UpdateRestaurantUseCase",
    "SetRestaurantVisibilityUseCase",
    "MAX_ADMIN_PAGE_SIZE",
]

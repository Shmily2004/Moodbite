"""PORT: hợp đồng đọc dữ liệu quán.

Application chỉ biết interface này, KHÔNG biết dữ liệu đến từ CSV, PostgreSQL hay API.
Muốn đổi nguồn dữ liệu -> viết adapter mới ở infrastructure/repositories, không sửa use case.
"""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from src.domain.entities.restaurant import Restaurant


@runtime_checkable
class RestaurantRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        """False khi nguồn dữ liệu chưa sẵn sàng (VD chưa chạy data_pipeline)."""
        ...

    def list_all(self) -> List[Restaurant]:
        """Toàn bộ quán. Raise DataNotReadyError nếu nguồn dữ liệu chưa sẵn sàng."""
        ...

    def get_by_place_id(self, place_id: str) -> Optional[Restaurant]:
        """1 quán theo placeId, None nếu không có."""
        ...

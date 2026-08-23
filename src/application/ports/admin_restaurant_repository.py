"""PORT: hợp đồng GHI dữ liệu quán, dành riêng cho luồng quản trị.

Tách khỏi `RestaurantRepository` (chỉ đọc) CÓ CHỦ ĐÍCH: luồng của người dùng cuối
tuyệt đối không cần khả năng ghi, nên không được nhìn thấy nó. Repository CSV cố tình
KHÔNG triển khai port này — CSV không ghi an toàn được (ghi đè cả file, không có
transaction). Chỉ `SqliteRestaurantRepository` triển khai.
"""
from __future__ import annotations

from typing import List, Mapping, Optional, Protocol, runtime_checkable

from src.domain.entities.restaurant import Restaurant


class RestaurantAlreadyExists(Exception):
    """`place_id` đã tồn tại -> HTTP 409."""


@runtime_checkable
class AdminRestaurantRepository(Protocol):
    def list_for_admin(
        self, query: Optional[str] = None, limit: int = 50, include_hidden: bool = True
    ) -> List[Restaurant]:
        """Danh sách cho trang quản trị.

        KHÁC `list_all()` ở chỗ MẶC ĐỊNH có cả quán đã ẩn — admin phải nhìn thấy quán
        mình vừa ẩn, nếu không sẽ không có cách nào bỏ ẩn lại.
        """
        ...

    def get_for_admin(self, place_id: str) -> Optional[Restaurant]:
        """1 quán, KỂ CẢ khi đã ẩn. `get_by_place_id()` thường bỏ qua quán ẩn."""
        ...

    def create(self, restaurant: Restaurant) -> Restaurant:
        """Thêm quán MỚI. Ném `RestaurantAlreadyExists` nếu `place_id` đã có.

        Kiểm trùng phải do TẦNG LƯU TRỮ làm (ràng buộc UNIQUE), không phải SELECT trước
        rồi INSERT — hai request cùng lúc sẽ cùng vượt qua phép kiểm đó.
        """
        ...

    def update_fields(self, place_id: str, changes: Mapping[str, object]) -> bool:
        """Ghi các trường đã được kiểm tra. Trả False nếu không có quán nào khớp."""
        ...

    def set_active(self, place_id: str, is_active: bool) -> bool:
        """Ẩn (soft-delete) hoặc bỏ ẩn. Trả False nếu không có quán nào khớp."""
        ...

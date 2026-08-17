"""PORT: hợp đồng lưu trữ tài khoản người dùng.

Application chỉ biết interface này, KHÔNG biết tài khoản nằm ở SQLite hay đâu khác.

⚠️ LƯU Ý VỀ NƠI LƯU: tài khoản là DỮ LIỆU GỐC (mất là mất hẳn), còn CSDL quán là DỮ LIỆU
DẪN XUẤT (dựng lại từ CSV bất cứ lúc nào bằng `scripts/build_sqlite.py`). Vì vậy hai thứ
phải nằm ở HAI FILE KHÁC NHAU - xem `sqlite_user_repository.py`.
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from src.domain.entities.user import User


@runtime_checkable
class UserRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        """False khi chưa mở được kho tài khoản."""
        ...

    def get_by_username(self, username: str) -> Optional[User]:
        """Tìm theo tên đăng nhập (đã chuẩn hoá về chữ thường). None nếu không có."""
        ...

    def get_by_id(self, user_id: str) -> Optional[User]:
        ...

    def create(self, user: User) -> User:
        """Tạo tài khoản mới.

        Raise `UsernameAlreadyExists` nếu tên đã có. Kiểm trùng phải do TẦNG LƯU TRỮ làm
        (ràng buộc UNIQUE), không phải kiểm trước rồi mới ghi - hai người đăng ký cùng
        lúc sẽ lọt qua phép kiểm đó.
        """
        ...

    def count(self) -> int:
        """Số tài khoản. Dùng cho /health và trang quản trị."""
        ...


class UsernameAlreadyExists(Exception):
    """Tên đăng nhập đã có người dùng -> HTTP 409."""

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

    def get_by_email(self, email: str) -> Optional[User]:
        """Tìm theo email (đã chuẩn hoá về chữ thường). None nếu không có.

        Dùng cho luồng QUÊN MẬT KHẨU: người dùng thường nhớ email hơn là nhớ tên đăng nhập.

        ⚠️ Email KHÔNG UNIQUE ở tầng CSDL, cố ý: đây là đồ án, một người có thể tạo vài
        tài khoản thử bằng cùng một hộp thư. Trùng thì trả tài khoản TẠO TRƯỚC — ổn định
        và đoán trước được, thay vì phụ thuộc thứ tự SQLite trả về.
        """
        ...

    def update_password(self, user_id: str, password_hash: str) -> bool:
        """Đổi chuỗi băm mật khẩu. Trả False nếu không có tài khoản đó.

        Nhận CHUỖI BĂM chứ không nhận mật khẩu thô: tầng lưu trữ không bao giờ được nhìn
        thấy mật khẩu gốc, và cũng không phải nơi quyết định băm bằng thuật toán nào.
        """
        ...

    def mark_email_verified(self, user_id: str, email: str) -> bool:
        """Đánh dấu hộp thư của tài khoản này đã được xác minh. False nếu không có tài khoản.

        NHẬN CẢ `email` chứ không chỉ `user_id`, cố ý: người dùng có thể đã đổi email sau
        khi thư xác minh được gửi đi. Tầng lưu trữ chỉ đánh dấu khi email hiện tại ĐÚNG
        BẰNG địa chỉ ghi trong thư — nếu không, ta sẽ đóng dấu "đã xác minh" lên một địa
        chỉ chưa ai chứng minh là có thật.
        """
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

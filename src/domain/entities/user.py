"""Entity User. Thuần Python — KHÔNG import framework, KHÔNG biết CSDL.

PHÂN QUYỀN: dự án chỉ có HAI vai nên dùng một trường `role`, KHÔNG dựng hệ RBAC đầy đủ
(bảng permission, nhóm quyền...). Hai vai mà làm RBAC thì tốn công viết và không bao giờ
dùng tới. Cần thêm vai thứ ba thì mở rộng enum này.

⚠️ Entity này TUYỆT ĐỐI không giữ mật khẩu thô. Chỉ giữ chuỗi băm, và chuỗi băm cũng
không bao giờ được trả ra ngoài qua API - xem `to_public()`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    """Vai của tài khoản. Kế thừa `str` để so sánh và lưu xuống CSDL trực tiếp được."""

    USER = "user"
    ADMIN = "admin"


# Quy tắc đặt tên đăng nhập. Đặt ở domain vì đây là QUY TẮC NGHIỆP VỤ, không phải
# validation của HTTP: mai kia có CLI tạo tài khoản thì vẫn phải theo đúng luật này.
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 32
MIN_PASSWORD_LENGTH = 8


class InvalidCredentialsFormat(ValueError):
    """Tên đăng nhập/mật khẩu sai định dạng -> HTTP 400, KHÔNG phải 401.

    Phân biệt rõ với "sai mật khẩu": đây là lỗi ĐỊNH DẠNG lúc đăng ký, nói cụ thể được
    mà không lộ thông tin gì. Còn lúc đăng nhập thì luôn trả câu chung chung.
    """


def validate_username(username: str) -> str:
    """Chuẩn hoá và kiểm tên đăng nhập. Trả về bản đã chuẩn hoá (viết thường)."""
    name = (username or "").strip().lower()
    if not (MIN_USERNAME_LENGTH <= len(name) <= MAX_USERNAME_LENGTH):
        raise InvalidCredentialsFormat(
            f"Tên đăng nhập phải từ {MIN_USERNAME_LENGTH} đến {MAX_USERNAME_LENGTH} ký tự."
        )
    # CHỈ ASCII: a-z, 0-9, gạch dưới, gạch ngang.
    #
    # ⚠️ Cố tình KHÔNG dùng `str.isalnum()` — hàm đó chấp nhận MỌI chữ Unicode, nên
    # "аdmin" viết bằng chữ Cyrillic `а` (U+0430) sẽ lọt qua và nhìn y hệt "admin" viết
    # bằng chữ Latin. Đó là tấn công homograph: kẻ xấu tạo tài khoản trông giống hệt
    # tài khoản người khác. Tên tiếng Việt có dấu cũng bị chặn vì cùng lý do.
    #
    # Người dùng vẫn đặt tên tiếng Việt có dấu được — ở trường `display_name`, thứ chỉ
    # dùng để HIỂN THỊ chứ không dùng để định danh khi đăng nhập.
    if not all(("a" <= c <= "z") or ("0" <= c <= "9") or c in "_-" for c in name):
        raise InvalidCredentialsFormat(
            "Tên đăng nhập chỉ được chứa chữ cái không dấu (a-z), số, "
            "dấu gạch dưới và gạch ngang."
        )
    return name


def validate_password(password: str) -> str:
    """Kiểm độ dài mật khẩu.

    CỐ Ý không bắt phải có hoa/thường/số/ký tự đặc biệt: các quy tắc đó khiến người dùng
    chọn kiểu "Matkhau1!" - dễ đoán hơn một câu dài. NIST SP 800-63B khuyến nghị ưu tiên
    ĐỘ DÀI thay vì độ phức tạp bắt buộc.
    """
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise InvalidCredentialsFormat(
            f"Mật khẩu phải có ít nhất {MIN_PASSWORD_LENGTH} ký tự."
        )
    return password


@dataclass(frozen=True)
class User:
    user_id: str
    username: str
    password_hash: str
    role: UserRole = UserRole.USER
    display_name: Optional[str] = None
    created_at: Optional[datetime] = None

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def to_public(self) -> dict:
        """Bản AN TOÀN để trả ra API.

        KHÔNG BAO GIỜ chứa `password_hash`. Có hàm này để không ai lỡ tay
        `asdict(user)` rồi trả nguyên cả chuỗi băm cho client - có test khoá việc đó.
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role.value,
            "display_name": self.display_name,
        }


__all__ = [
    "User",
    "UserRole",
    "InvalidCredentialsFormat",
    "validate_username",
    "validate_password",
    "MIN_USERNAME_LENGTH",
    "MAX_USERNAME_LENGTH",
    "MIN_PASSWORD_LENGTH",
]

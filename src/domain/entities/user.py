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

# Chặn trên cho mật khẩu. KHÔNG phải để "bảo mật hơn" — dài hơn luôn mạnh hơn. Đây là
# chặn TÀI NGUYÊN: băm PBKDF2 600k vòng một chuỗi vài megabyte tốn CPU thật, và endpoint
# đăng ký/đăng nhập là công khai nên ai cũng gửi được. 128 ký tự thừa sức cho một câu dài.
MAX_PASSWORD_LENGTH = 128


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
    if len(password) > MAX_PASSWORD_LENGTH:
        raise InvalidCredentialsFormat(
            f"Mật khẩu không được dài quá {MAX_PASSWORD_LENGTH} ký tự."
        )
    return password


# Chặn trên độ dài email. 254 là giới hạn của một địa chỉ thư theo RFC 5321 (kích thước
# tối đa của đường "forward-path"). Đặt bằng đúng chuẩn để không tự nghĩ ra luật riêng.
MAX_EMAIL_LENGTH = 254


class InvalidEmailFormat(ValueError):
    """Email sai định dạng -> HTTP 400."""


def validate_email(email: str) -> str:
    """Chuẩn hoá và kiểm email. Trả về bản đã chuẩn hoá (bỏ khoảng trắng, viết thường).

    CỐ Ý KIỂM RẤT LỎNG — chỉ đòi có đúng một dấu `@`, hai bên đều khác rỗng, và phần miền
    có ít nhất một dấu chấm. Vì sao không dùng biểu thức chính quy "chuẩn RFC 5322":

      1. Không có regex nào đúng hoàn toàn với RFC — bản hay được chép trên mạng dài hơn
         6000 ký tự và vẫn từ chối nhầm địa chỉ hợp lệ.
      2. Cách DUY NHẤT biết chắc một email có thật là GỬI THƯ tới đó. Ta có làm việc đó:
         đường dẫn đặt lại mật khẩu chỉ tới được hộp thư thật.

    Nên phép kiểm này chỉ để bắt lỗi gõ nhầm rõ ràng ("quen@" hay "chua-co-a-cong").
    """
    value = (email or "").strip().lower()
    if not value:
        raise InvalidEmailFormat("Chưa nhập email.")
    if len(value) > MAX_EMAIL_LENGTH:
        raise InvalidEmailFormat(f"Email không được dài quá {MAX_EMAIL_LENGTH} ký tự.")
    if value.count("@") != 1:
        raise InvalidEmailFormat("Email phải có đúng một dấu @.")
    ten, mien = value.split("@")
    if not ten or not mien or "." not in mien or mien.startswith(".") or mien.endswith("."):
        raise InvalidEmailFormat("Email chưa đúng dạng, ví dụ đúng: ten@vidu.com")
    if any(c.isspace() for c in value):
        raise InvalidEmailFormat("Email không được chứa khoảng trắng.")
    return value


@dataclass(frozen=True)
class User:
    user_id: str
    username: str
    password_hash: str
    role: UserRole = UserRole.USER
    display_name: Optional[str] = None
    created_at: Optional[datetime] = None
    # TUỲ CHỌN. Chỉ dùng để gửi thư đặt lại mật khẩu — không dùng để đăng nhập, không hiện
    # ra API công khai (xem `to_public`). Tài khoản không có email thì vẫn dùng bình thường,
    # chỉ là không tự lấy lại mật khẩu được.
    email: Optional[str] = None

    # Hộp thư này đã được CHỨNG MINH là có thật chưa (chủ tài khoản đã bấm vào đường dẫn
    # trong thư). Mặc định False.
    #
    # VÌ SAO KHÔNG CHẶN ĐĂNG NHẬP KHI CHƯA XÁC MINH: email vốn là trường TUỲ CHỌN ở dự án
    # này (xem `RegisterUserUseCase`), nên chặn đăng nhập sẽ khoá luôn cả người không khai
    # email. Xác minh ở đây là để TRẢ LỜI ĐƯỢC câu "địa chỉ này có thật không", phục vụ
    # đúng một việc: gửi thư đặt lại mật khẩu tới đúng người.
    email_verified: bool = False

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

    def to_self(self) -> dict:
        """Bản dành cho CHÍNH CHỦ xem hồ sơ của mình (`GET /auth/me`).

        Khác `to_public()` ở chỗ có thêm EMAIL và NGÀY THAM GIA.

        ⚠️ TUYỆT ĐỐI KHÔNG dùng hàm này cho danh sách người dùng hay bất cứ chỗ nào người
        này xem người khác — email là dữ liệu cá nhân. `to_public()` vẫn là bản mặc định;
        chỗ nào cần lộ thêm thì phải cố ý gọi `to_self()` và tự chịu trách nhiệm.

        Vẫn KHÔNG BAO GIỜ chứa `password_hash` — có test khoá.
        """
        return {
            **self.to_public(),
            "email": self.email,
            # Chính chủ cần biết hộp thư của mình đã xác minh chưa để còn bấm gửi lại thư.
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def has_email(self) -> bool:
        return bool(self.email)

    @property
    def can_receive_mail(self) -> bool:
        """Gửi thư tới tài khoản này thì có tới nơi không.

        Có email nhưng CHƯA xác minh vẫn trả True, cố ý: chưa xác minh nghĩa là ta CHƯA
        BIẾT địa chỉ có thật hay không, chứ không phải đã biết là sai. Coi "chưa biết"
        thành "không gửi" sẽ khoá luôn đường lấy lại mật khẩu của mọi tài khoản cũ —
        tất cả đều `email_verified = False` cho tới khi họ bấm xác minh.
        """
        return bool(self.email)


__all__ = [
    "User",
    "UserRole",
    "InvalidCredentialsFormat",
    "InvalidEmailFormat",
    "validate_email",
    "MAX_EMAIL_LENGTH",
    "validate_username",
    "validate_password",
    "MIN_USERNAME_LENGTH",
    "MAX_USERNAME_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "MAX_PASSWORD_LENGTH",
]

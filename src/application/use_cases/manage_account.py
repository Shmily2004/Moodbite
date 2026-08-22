"""USE CASE: đăng ký, đăng nhập và đặt lại mật khẩu tài khoản người dùng.

Chỉ ĐIỀU PHỐI. Quy tắc đặt tên/mật khẩu nằm ở `domain/entities/user.py`; băm mật khẩu và
ký token nằm ở `infrastructure/auth/crypto.py`. File này không tự làm hai việc đó.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Protocol

from src.application.errors import InvalidCredentialsError
from src.application.ports.email_sender import EmailSender
from src.application.ports.user_repository import UserRepository, UsernameAlreadyExists
from src.domain.entities.user import (
    User,
    UserRole,
    validate_email,
    validate_password,
    validate_username,
)

logger = logging.getLogger("moodbite.account")


class PasswordHasher(Protocol):
    """Hợp đồng băm mật khẩu — để use case không phụ thuộc thẳng vào `crypto.py`."""

    def __call__(self, password: str) -> str: ...


class TokenIssuer(Protocol):
    def __call__(self, user: User) -> str: ...


@dataclass
class RegisterUserUseCase:
    users: UserRepository
    hash_password: PasswordHasher
    issue_token: TokenIssuer

    def execute(
        self,
        username: str,
        password: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> tuple[User, str]:
        """Tạo tài khoản mới, trả về (user, token) để đăng ký xong là dùng được luôn.

        `email` TUỲ CHỌN: không có email thì tài khoản vẫn dùng bình thường, chỉ là sau
        này không tự lấy lại mật khẩu được. Không bắt buộc vì bản thiết kế của chủ dự án
        không có ô email, và ép nhập chỉ để phòng xa sẽ làm rơi người đăng ký.
        """
        # Kiểm định dạng TRƯỚC khi băm: băm mất ~0.4s, không nên tốn cho input rác.
        name = validate_username(username)
        validate_password(password)
        dia_chi = validate_email(email) if (email or "").strip() else None

        # ⚠️ Vai LUÔN là `user`. Tuyệt đối không lấy vai từ input - nếu không thì bất kỳ
        # ai cũng tự đăng ký thành admin. Nâng vai là việc riêng, phải qua admin.
        user = User(
            user_id="",
            username=name,
            password_hash=self.hash_password(password),
            role=UserRole.USER,
            display_name=(display_name or "").strip() or None,
            email=dia_chi,
        )

        created = self.users.create(user)   # ném UsernameAlreadyExists nếu trùng
        logger.info("Tài khoản mới: %s", created.username)
        return created, self.issue_token(created)


@dataclass
class LoginUseCase:
    users: UserRepository
    verify_password: object       # (password, hash) -> bool
    issue_token: TokenIssuer

    def execute(self, username: str, password: str) -> tuple[User, str]:
        name = (username or "").strip().lower()
        user = self.users.get_by_username(name)

        # ⚠️ CHỐNG DÒ TÀI KHOẢN: dù không tìm thấy người dùng, VẪN phải băm mật khẩu rồi
        # mới trả lỗi. Nếu thoát sớm thì tài khoản không tồn tại trả lời trong ~1ms còn
        # tài khoản có thật mất ~400ms - kẻ tấn công đo thời gian là biết tên nào có thật.
        stored = user.password_hash if user else _HASH_GIA
        ok = self.verify_password(password or "", stored)

        if user is None or not ok:
            logger.warning("Đăng nhập thất bại: %r", name)
            # Câu chung chung, không nói sai tên hay sai mật khẩu.
            raise InvalidCredentialsError("Sai tài khoản hoặc mật khẩu.")

        return user, self.issue_token(user)


@dataclass
class RequestPasswordResetUseCase:
    """Nhận yêu cầu quên mật khẩu -> gửi thư kèm đường dẫn đặt lại.

    ⚠️ LUÔN BÁO THÀNH CÔNG với người gọi, kể cả khi không có tài khoản nào khớp.
    Nếu trả lời khác nhau giữa "có" và "không có", trang này thành công cụ dò xem email
    nào đã đăng ký MoodBite — đúng thứ mà trang đăng nhập đã cẩn thận tránh (xem
    `LoginUseCase`). Việc phải giấu là CÓ TỒN TẠI HAY KHÔNG, chứ không phải giấu lỗi hệ
    thống: máy chủ thư hỏng thì vẫn ném lỗi ra ngoài để người dùng biết mà thử lại.
    """

    users: UserRepository
    emails: EmailSender
    issue_reset_token: TokenIssuer
    app_base_url: str
    token_ttl_seconds: int

    def execute(self, dinh_danh: str) -> bool:
        """`dinh_danh` là email HOẶC tên đăng nhập. Trả True nếu đã thực sự gửi thư.

        Giá trị trả về CHỈ để ghi log và cho test — router không được đem nó ra ngoài,
        nếu không thì lộ đúng thứ vừa nói ở trên.
        """
        khoa = (dinh_danh or "").strip().lower()
        if not khoa:
            return False

        # Thử cả hai đường: người dùng nhớ email hay nhớ tên đăng nhập đều dùng được.
        user = self.users.get_by_email(khoa) or self.users.get_by_username(khoa)
        if user is None or not user.has_email:
            # Không có tài khoản, hoặc có nhưng chưa khai email -> không gửi được gì.
            # Ghi log ở mức info để chủ dự án còn chẩn đoán được khi thử.
            logger.info("Yêu cầu đặt lại mật khẩu không gửi được cho %r", khoa)
            return False

        token = self.issue_reset_token(user)
        # ⚠️ Phải KHỚP `ROUTES.resetPassword` ở frontend
        # (`frontend/apps/client/src/shared/config/routes.ts`). Lệch một chữ là link trong
        # thư ra 404. Frontend có giữ chuyển hướng từ đường dẫn cũ để thư cũ không chết.
        lien_ket = f"{self.app_base_url.rstrip('/')}/reset-password?token={token}"
        phut = max(1, self.token_ttl_seconds // 60)

        # Soạn thư bằng cách NỐI DANH SÁCH DÒNG thay vì một chuỗi dài có "\n":
        # thư này toàn tiếng Việt và sẽ còn phải sửa câu chữ nhiều lần, để dạng danh sách
        # thì mỗi dòng nhìn thấy rõ, không ai đếm nhầm ký tự xuống dòng.
        dong = [
            f"Chào {user.display_name or user.username},",
            "",
            "Có người vừa yêu cầu đặt lại mật khẩu cho tài khoản MoodBite của bạn",
            f"({user.username}).",
            "",
            "Mở đường dẫn dưới đây để đặt mật khẩu mới:",
            lien_ket,
            "",
            f"Đường dẫn có hiệu lực trong {phut} phút và chỉ dùng được MỘT lần.",
            "",
            "Nếu không phải bạn yêu cầu thì cứ bỏ qua thư này — mật khẩu hiện tại vẫn",
            "giữ nguyên.",
            "",
            "— MoodBite",
        ]

        self.emails.send(
            to=user.email,
            subject="Đặt lại mật khẩu MoodBite",
            body=chr(10).join(dong),
        )
        logger.info("Đã gửi thư đặt lại mật khẩu cho %s", user.username)
        return True


class ResetTokenReader(Protocol):
    """Hợp đồng đọc token đặt lại mật khẩu. Hai bước, xem `infrastructure/auth/password_reset.py`."""

    def subject_of(self, token: str) -> str:
        """Kiểm chữ ký + hạn dùng, trả `user_id`."""
        ...

    def ensure_unused(self, token: str, current_password_hash: str) -> None:
        """Chốt chặn chỉ-dùng-một-lần. Ném lỗi nếu token đã dùng rồi."""
        ...


@dataclass
class ResetPasswordUseCase:
    """Đổi mật khẩu bằng token trong thư."""

    users: UserRepository
    hash_password: PasswordHasher
    reset_tokens: ResetTokenReader

    def execute(self, token: str, mat_khau_moi: str) -> User:
        # Bước 1: chữ ký + hạn dùng. Qua được thì `user_id` là đáng tin.
        user_id = self.reset_tokens.subject_of(token)
        user = self.users.get_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError("Đường dẫn đặt lại mật khẩu không hợp lệ.")

        # Bước 2: vân tay mật khẩu hiện tại -> token đã dùng rồi thì chết ở đây.
        self.reset_tokens.ensure_unused(token, user.password_hash)

        # Kiểm mật khẩu mới SAU khi token hợp lệ: người cầm token sai không cần biết luật
        # đặt mật khẩu của hệ thống.
        validate_password(mat_khau_moi)

        if not self.users.update_password(user.user_id, self.hash_password(mat_khau_moi)):
            raise InvalidCredentialsError("Không tìm thấy tài khoản để đổi mật khẩu.")

        logger.info("Đã đổi mật khẩu cho %s", user.username)
        # KHÔNG phát token đăng nhập ở đây: đổi xong thì bắt đăng nhập lại bằng mật khẩu
        # mới. Vừa để người dùng gõ thử một lần cho nhớ, vừa tránh biến đường dẫn trong
        # thư thành một cách đăng nhập không cần mật khẩu.
        return user


# Chuỗi băm giả, dùng để so khớp khi tài khoản không tồn tại (xem giải thích ở trên).
# Đúng định dạng thật để `verify_password` chạy trọn vẹn số vòng lặp.
_HASH_GIA = (
    "pbkdf2_sha256$600000$"
    "00000000000000000000000000000000$"
    "0000000000000000000000000000000000000000000000000000000000000000"
)


__all__ = ["RegisterUserUseCase", "LoginUseCase", "UsernameAlreadyExists"]

"""USE CASE: đăng ký và đăng nhập tài khoản người dùng.

Chỉ ĐIỀU PHỐI. Quy tắc đặt tên/mật khẩu nằm ở `domain/entities/user.py`; băm mật khẩu và
ký token nằm ở `infrastructure/auth/crypto.py`. File này không tự làm hai việc đó.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Protocol

from src.application.errors import InvalidCredentialsError
from src.application.ports.user_repository import UserRepository, UsernameAlreadyExists
from src.domain.entities.user import (
    User,
    UserRole,
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
        self, username: str, password: str, display_name: Optional[str] = None
    ) -> tuple[User, str]:
        """Tạo tài khoản mới, trả về (user, token) để đăng ký xong là dùng được luôn."""
        # Kiểm định dạng TRƯỚC khi băm: băm mất ~0.4s, không nên tốn cho input rác.
        name = validate_username(username)
        validate_password(password)

        # ⚠️ Vai LUÔN là `user`. Tuyệt đối không lấy vai từ input - nếu không thì bất kỳ
        # ai cũng tự đăng ký thành admin. Nâng vai là việc riêng, phải qua admin.
        user = User(
            user_id="",
            username=name,
            password_hash=self.hash_password(password),
            role=UserRole.USER,
            display_name=(display_name or "").strip() or None,
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


# Chuỗi băm giả, dùng để so khớp khi tài khoản không tồn tại (xem giải thích ở trên).
# Đúng định dạng thật để `verify_password` chạy trọn vẹn số vòng lặp.
_HASH_GIA = (
    "pbkdf2_sha256$600000$"
    "00000000000000000000000000000000$"
    "0000000000000000000000000000000000000000000000000000000000000000"
)


__all__ = ["RegisterUserUseCase", "LoginUseCase", "UsernameAlreadyExists"]

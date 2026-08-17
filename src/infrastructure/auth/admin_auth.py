"""Xác thực cho trang quản trị: MỘT tài khoản admin + token ngắn hạn.

VÌ SAO TỰ VIẾT CHỨ KHÔNG DÙNG THƯ VIỆN JWT:
dự án vừa gỡ 8 thư viện chỉ phục vụ một tính năng đã dừng. Thêm `PyJWT` + `passlib` +
`bcrypt` cho ĐÚNG MỘT tài khoản là đi ngược lại việc đó. `hmac`, `hashlib`, `secrets`
đều nằm trong thư viện chuẩn và đủ dùng cho bài toán này.

Token có định dạng giống JWT (`<payload>.<chữ ký>`) nhưng KHÔNG phải JWT thật — không
có header `alg`, nên không dính lỗ hổng "alg: none" kinh điển. Thuật toán được cố định
cứng trong code, client không chọn được.

FAIL-CLOSED: chưa cấu hình mật khẩu/secret thì `is_configured` = False và MỌI endpoint
admin trả 503. Tuyệt đối không được mặc định thành "cho qua" — bug kiểu đó biến trang
quản trị thành công khai.
"""
from __future__ import annotations

import hmac
import logging
from typing import Optional

from src.application.errors import AdminNotConfiguredError, InvalidCredentialsError
from src.infrastructure.auth.crypto import (
    TokenInvalid,
    hash_password,
    sign_token,
    verify_password,
    verify_token,
)

logger = logging.getLogger("moodbite.auth")

# Băm mật khẩu và ký token nay nằm ở `crypto.py` — NƠI DUY NHẤT làm hai việc đó.
# Trước đây code nằm ngay file này; khi người dùng cũng cần đăng nhập, để nguyên sẽ thành
# hai bản băm mật khẩu song song. Re-export để `scripts/make_admin_password.py` và các
# import cũ không vỡ.
DEFAULT_TOKEN_TTL_SECONDS = 3600  # 1 giờ - "ngắn hạn" theo PROJECT_CHECKLIST


class AdminAuthService:
    """Đăng nhập và kiểm token cho admin."""

    def __init__(
        self,
        username: str,
        password_hash: str,
        token_secret: str,
        token_ttl_seconds: int = DEFAULT_TOKEN_TTL_SECONDS,
    ) -> None:
        self.username = username
        self._password_hash = password_hash
        self._secret = token_secret.encode("utf-8") if token_secret else b""
        self.token_ttl_seconds = token_ttl_seconds

    @property
    def is_configured(self) -> bool:
        """Thiếu BẤT KỲ thứ nào trong ba thứ này thì coi như chưa bật admin."""
        return bool(self.username and self._password_hash and self._secret)

    def ensure_configured(self) -> None:
        if not self.is_configured:
            raise AdminNotConfiguredError(
                "Chưa bật trang quản trị. Đặt 3 biến môi trường rồi khởi động lại: "
                "MOODBITE_ADMIN_USER, MOODBITE_ADMIN_PASSWORD_HASH, MOODBITE_ADMIN_SECRET. "
                "Sinh hash mật khẩu bằng: python scripts/make_admin_password.py"
            )

    def login(self, username: str, password: str) -> str:
        self.ensure_configured()
        # So khớp cả tên đăng nhập bằng compare_digest để không lộ "tên này có tồn tại".
        ok_user = hmac.compare_digest(username or "", self.username)
        ok_pass = verify_password(password or "", self._password_hash)
        if not (ok_user and ok_pass):
            logger.warning("Đăng nhập admin thất bại cho tài khoản %r", username)
            raise InvalidCredentialsError("Sai tài khoản hoặc mật khẩu.")
        return self._issue_token(self.username)

    def _issue_token(self, subject: str) -> str:
        return sign_token({"sub": subject, "role": "admin"}, self._secret,
                          self.token_ttl_seconds)

    def verify(self, token: str) -> str:
        """Trả về tên tài khoản nếu token hợp lệ, ngược lại ném InvalidCredentialsError."""
        self.ensure_configured()
        try:
            payload = verify_token(token, self._secret)
        except TokenInvalid as exc:
            raise InvalidCredentialsError(str(exc))
        return str(payload.get("sub", ""))

    def status(self) -> dict:
        """Cho /health. TUYỆT ĐỐI không trả hash hay secret ra ngoài."""
        return {
            "ready": self.is_configured,
            "source": "admin auth (1 tài khoản, token HMAC ngắn hạn)",
            "error": None if self.is_configured else "chưa cấu hình biến môi trường admin",
        }


__all__ = [
    "AdminAuthService",
    "InvalidCredentialsError",
    "AdminNotConfiguredError",
    "hash_password",
    "verify_password",
]

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

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from typing import Optional

from src.application.errors import AdminNotConfiguredError, InvalidCredentialsError

logger = logging.getLogger("moodbite.auth")

# 600k vòng PBKDF2-SHA256: mức OWASP khuyến nghị cho SHA-256 (2023). Đủ chậm để dò mật
# khẩu tốn kém, vẫn dưới ~0.5s trên máy thường nên đăng nhập không bị ì.
PBKDF2_ITERATIONS = 600_000
_HASH_PREFIX = "pbkdf2_sha256"

DEFAULT_TOKEN_TTL_SECONDS = 3600  # 1 giờ - "ngắn hạn" theo PROJECT_CHECKLIST


def hash_password(password: str, *, salt: Optional[bytes] = None) -> str:
    """Sinh chuỗi hash để đặt vào biến môi trường MOODBITE_ADMIN_PASSWORD_HASH."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"{_HASH_PREFIX}${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """So khớp mật khẩu. Chuỗi hash sai định dạng -> False, KHÔNG ném lỗi."""
    try:
        prefix, iterations, salt_hex, digest_hex = stored.split("$")
        if prefix != _HASH_PREFIX:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    # compare_digest: so sánh trong thời gian hằng định, không rò rỉ thông tin qua
    # thời gian phản hồi.
    return hmac.compare_digest(digest.hex(), digest_hex)


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


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
        payload = {"sub": subject, "exp": int(time.time()) + self.token_ttl_seconds}
        body = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        return f"{body}.{self._sign(body)}"

    def _sign(self, body: str) -> str:
        return _b64encode(hmac.new(self._secret, body.encode("ascii"), hashlib.sha256).digest())

    def verify(self, token: str) -> str:
        """Trả về tên tài khoản nếu token hợp lệ, ngược lại ném InvalidCredentialsError."""
        self.ensure_configured()
        try:
            body, signature = (token or "").split(".")
        except ValueError:
            raise InvalidCredentialsError("Token không hợp lệ.")

        # Kiểm CHỮ KÝ TRƯỚC khi đọc nội dung: chưa xác thực thì payload là dữ liệu do
        # kẻ tấn công kiểm soát, không được tin.
        if not hmac.compare_digest(signature, self._sign(body)):
            raise InvalidCredentialsError("Token không hợp lệ.")

        try:
            payload = json.loads(_b64decode(body))
        except (ValueError, TypeError):
            raise InvalidCredentialsError("Token không hợp lệ.")

        if int(payload.get("exp", 0)) < time.time():
            raise InvalidCredentialsError("Token đã hết hạn, hãy đăng nhập lại.")
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

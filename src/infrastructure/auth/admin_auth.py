"""Xác thực cho trang quản trị: tài khoản `role='admin'` trong bảng `users` + token ngắn hạn.

ĐỔI 2026-09-29 (chủ dự án duyệt): admin KHÔNG còn là MỘT tài khoản nằm trong biến môi
trường (`MOODBITE_ADMIN_USER` / `MOODBITE_ADMIN_PASSWORD_HASH`). Admin là một dòng trong
bảng `users` có `role = 'admin'`. Được gì:
  - nhiều admin, mỗi người một mật khẩu, nhật ký quản trị ghi đúng tên người làm;
  - hạ quyền / đổi mật khẩu / đăng xuất có hiệu lực NGAY (đọc lại tài khoản mỗi request,
    so `token_version` - cùng cơ chế với token người dùng);
  - không phải khởi động lại server để đổi mật khẩu admin.
Tạo admin: `python scripts/make_admin_user.py` (có `--tu-env` để chuyển tài khoản cũ).

VẪN GIỮ SECRET RIÊNG `MOODBITE_ADMIN_SECRET`, KHÁC secret người dùng: chữ ký token người
dùng không bao giờ hợp lệ ở phía quản trị, kể cả khi code đọc `role` có sai.

VÌ SAO TỰ VIẾT CHỨ KHÔNG DÙNG THƯ VIỆN JWT: dự án vừa gỡ 8 thư viện chỉ phục vụ một tính
năng đã dừng. `hmac`, `hashlib`, `secrets` trong thư viện chuẩn là đủ. Token có dạng giống
JWT nhưng KHÔNG có header `alg`, nên không dính lỗ hổng "alg: none".

FAIL-CLOSED: chưa đặt secret hoặc kho tài khoản không mở được thì `is_configured` = False
và MỌI endpoint admin trả 503. Tuyệt đối không mặc định thành "cho qua".
"""
from __future__ import annotations

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

DEFAULT_TOKEN_TTL_SECONDS = 3600  # 1 giờ - "ngắn hạn" theo PROJECT_CHECKLIST

# Câu lỗi DUY NHẤT cho mọi kiểu đăng nhập hỏng (sai mật khẩu, không có tên, không phải
# admin). Khác câu là lộ cho kẻ dò biết tài khoản nào tồn tại / tài khoản nào là admin.
_SAI_DANG_NHAP = "Sai tài khoản hoặc mật khẩu."

# Chuỗi băm giả, cùng định dạng thật: tên không tồn tại vẫn chạy trọn 600k vòng PBKDF2,
# nên thời gian trả lời không lộ "tên này có hay không". Cùng kỹ thuật với `LoginUseCase`.
_HASH_GIA = (
    "pbkdf2_sha256$600000$"
    "00000000000000000000000000000000$"
    "0000000000000000000000000000000000000000000000000000000000000000"
)


class AdminAuthService:
    """Đăng nhập và kiểm token cho admin."""

    def __init__(
        self,
        users,
        token_secret: str,
        token_ttl_seconds: int = DEFAULT_TOKEN_TTL_SECONDS,
    ) -> None:
        # `users` là `UserRepository` (port ở tầng application) - dùng duck typing để file
        # hạ tầng này không phải biết adapter cụ thể nào.
        self._users = users
        self._secret = token_secret.encode("utf-8") if token_secret else b""
        self.token_ttl_seconds = token_ttl_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self._secret) and bool(self._users is not None and self._users.is_ready)

    def ensure_configured(self) -> None:
        if not self._secret:
            raise AdminNotConfiguredError(
                "Chưa bật trang quản trị. Đặt biến môi trường MOODBITE_ADMIN_SECRET "
                "(chuỗi ngẫu nhiên, KHÁC MOODBITE_AUTH_SECRET) rồi khởi động lại, và tạo "
                "tài khoản quản trị bằng: python scripts/make_admin_user.py"
            )
        if not self.is_configured:
            raise AdminNotConfiguredError(
                "Không mở được kho tài khoản nên trang quản trị đang tắt. "
                "Kiểm tra quyền ghi ở đường dẫn MOODBITE_USERS_DB."
            )

    def login(self, username: str, password: str) -> str:
        self.ensure_configured()
        user = self._users.get_by_username(username or "")
        # Luôn chạy verify_password, kể cả khi không có tài khoản - xem `_HASH_GIA`.
        ok = verify_password(password or "", user.password_hash if user else _HASH_GIA)
        if user is None or not ok or not user.is_admin:
            logger.warning("Đăng nhập admin thất bại cho tài khoản %r", username)
            raise InvalidCredentialsError(_SAI_DANG_NHAP)
        return sign_token(
            {"sub": user.user_id, "role": "admin", "tv": user.token_version},
            self._secret,
            self.token_ttl_seconds,
        )

    def verify(self, token: str) -> str:
        """Trả TÊN ĐĂNG NHẬP của admin nếu token còn hiệu lực, ngược lại ném
        InvalidCredentialsError -> 401.

        Đọc LẠI tài khoản ở mỗi request: hạ quyền, xoá tài khoản, đăng xuất, đổi mật khẩu
        đều có hiệu lực ngay - không đợi token hết hạn.
        """
        self.ensure_configured()
        try:
            payload = verify_token(token, self._secret)
        except TokenInvalid as exc:
            raise InvalidCredentialsError(str(exc))

        user = self._users.get_by_id(str(payload.get("sub", "")))
        if user is None or not user.is_admin:
            raise InvalidCredentialsError(
                "Tài khoản này không còn quyền quản trị. Hãy đăng nhập lại."
            )
        if _token_version(payload) != user.token_version:
            raise InvalidCredentialsError(
                "Phiên quản trị đã kết thúc (đã đăng xuất hoặc đổi mật khẩu). "
                "Hãy đăng nhập lại."
            )
        return user.username

    def status(self) -> dict:
        """Cho /health. TUYỆT ĐỐI không trả hash hay secret ra ngoài."""
        error: Optional[str] = None
        if not self._secret:
            error = "chưa đặt MOODBITE_ADMIN_SECRET"
        elif not self.is_configured:
            error = "kho tài khoản không mở được"
        return {
            "ready": self.is_configured,
            "source": "admin auth (tài khoản role=admin trong bảng users, token HMAC ngắn hạn)",
            "error": error,
        }


def _token_version(payload: dict) -> int:
    try:
        return int(payload.get("tv", -1))
    except (TypeError, ValueError):
        return -1


__all__ = [
    "AdminAuthService",
    "InvalidCredentialsError",
    "AdminNotConfiguredError",
    "hash_password",
    "verify_password",
]

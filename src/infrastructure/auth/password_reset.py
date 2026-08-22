"""Token ĐẶT LẠI MẬT KHẨU — ký và kiểm.

Tách khỏi `user_auth.py` vì đây là loại token KHÁC HẲN token đăng nhập:

| | Token đăng nhập | Token đặt lại mật khẩu |
|---|---|---|
| Sống bao lâu | 24 giờ | 30 phút |
| Gửi đi đâu | Giữ trong trình duyệt | Gửi qua thư, đi qua mạng Internet |
| Dùng mấy lần | Nhiều lần | **Đúng một lần** |

⚠️ DÙNG SECRET RIÊNG (`MOODBITE_RESET_SECRET`), không dùng chung với token đăng nhập.
Lý do giống hệt chỗ tách secret admin/người dùng: token đặt lại nằm trong hộp thư — nơi
dễ lộ hơn hẳn — nên chữ ký của nó tuyệt đối không được mở được cửa đăng nhập. Chưa khai
secret riêng thì lui về `MOODBITE_AUTH_SECRET` (xem `dependencies.py`), vì thà chạy được
với một secret còn hơn tắt hẳn tính năng của một đồ án.

MỘT LẦN DÙNG MÀ KHÔNG CẦN BẢNG NÀO: token nhét kèm "vân tay" của chuỗi băm mật khẩu HIỆN
TẠI. Đổi mật khẩu xong thì chuỗi băm đổi -> vân tay không khớp -> chính cái link vừa dùng
lập tức hết hiệu lực. Không phải thêm bảng `password_reset_tokens`, không phải dọn rác
token hết hạn, và cũng không thể quên xoá.

Đây là lý do KHÔNG lưu token vào CSDL: xem `docs/API_DECISIONS_PENDING.md` — đổi lược đồ
dữ liệu là việc phải chốt trước, mà cách này đạt cùng mục tiêu với 0 thay đổi.
"""
from __future__ import annotations

import hashlib
import logging

from src.application.errors import AuthNotConfiguredError, InvalidCredentialsError
from src.domain.entities.user import User
from src.infrastructure.auth.crypto import TokenInvalid, sign_token, verify_token

logger = logging.getLogger("moodbite.auth")

# 30 phút. Đủ để mở hộp thư và gõ mật khẩu mới, nhưng đủ ngắn để một lá thư bị đọc lén
# vài tiếng sau không còn dùng được. Gmail/Outlook đều dùng khoảng 15-60 phút.
DEFAULT_RESET_TTL_SECONDS = 1_800


def _van_tay(password_hash: str) -> str:
    """16 ký tự hex băm từ chuỗi băm mật khẩu.

    KHÔNG nhét thẳng `password_hash` vào token: token đi qua thư và có thể nằm lại trong
    log máy chủ thư, nên không được mang theo bất cứ mẩu nào của chuỗi băm thật. Băm thêm
    một lần nữa cho ra thứ chỉ dùng để SO SÁNH, không suy ngược lại được.
    """
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:16]


class PasswordResetTokenService:
    """Ký và mở token trong đường dẫn đặt lại mật khẩu."""

    def __init__(
        self,
        token_secret: str,
        token_ttl_seconds: int = DEFAULT_RESET_TTL_SECONDS,
    ) -> None:
        self._secret = token_secret.encode("utf-8") if token_secret else b""
        self.token_ttl_seconds = token_ttl_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self._secret)

    def ensure_configured(self) -> None:
        """FAIL-CLOSED. Không có secret thì KHÔNG phát token nào cả."""
        if not self.is_configured:
            raise AuthNotConfiguredError(
                "Chưa bật tính năng đặt lại mật khẩu. Đặt biến môi trường "
                "MOODBITE_RESET_SECRET (hoặc MOODBITE_AUTH_SECRET) rồi khởi động lại. "
                'Sinh chuỗi bằng: python -c "import secrets; print(secrets.token_hex(32))"'
            )

    def issue(self, user: User) -> str:
        """Phát token cho MỘT lần đặt lại mật khẩu của đúng tài khoản này."""
        self.ensure_configured()
        return sign_token(
            {"sub": user.user_id, "pw": _van_tay(user.password_hash)},
            self._secret,
            self.token_ttl_seconds,
        )

    def subject_of(self, token: str) -> str:
        """BƯỚC 1 — kiểm chữ ký và hạn dùng, trả `user_id`.

        CHƯA kiểm vân tay: muốn kiểm thì phải có chuỗi băm hiện tại của tài khoản, mà
        muốn có chuỗi băm thì trước hết phải biết là tài khoản NÀO. Đó là lý do việc này
        tách làm hai bước, và vì sao người gọi BẮT BUỘC gọi tiếp `ensure_unused`.
        """
        self.ensure_configured()
        try:
            payload = verify_token(token, self._secret)
        except TokenInvalid as exc:
            # Giữ nguyên câu của tầng dưới: nó phân biệt được "hỏng" với "hết hạn", và
            # người dùng cần biết mình phải bấm gửi lại thư hay chỉ gõ nhầm đường dẫn.
            raise InvalidCredentialsError(str(exc))

        user_id = str(payload.get("sub", ""))
        if not user_id:
            raise InvalidCredentialsError("Đường dẫn đặt lại mật khẩu không hợp lệ.")
        return user_id

    def ensure_unused(self, token: str, current_password_hash: str) -> None:
        """BƯỚC 2 — chốt chặn CHỈ DÙNG MỘT LẦN.

        So vân tay trong token với chuỗi băm mật khẩu HIỆN TẠI. Mật khẩu đã đổi (dù bằng
        chính đường dẫn này lúc nãy) thì vân tay lệch -> token chết ngay.
        """
        self.ensure_configured()
        try:
            payload = verify_token(token, self._secret)
        except TokenInvalid as exc:
            raise InvalidCredentialsError(str(exc))

        if payload.get("pw") != _van_tay(current_password_hash):
            raise InvalidCredentialsError(
                "Đường dẫn này đã được dùng rồi. Hãy yêu cầu gửi lại thư mới."
            )


__all__ = ["PasswordResetTokenService", "DEFAULT_RESET_TTL_SECONDS"]

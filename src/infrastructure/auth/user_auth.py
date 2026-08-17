"""Phát và kiểm token đăng nhập của NGƯỜI DÙNG CUỐI.

Khác `admin_auth.py` ở một điểm căn bản: admin là MỘT tài khoản nằm trong biến môi
trường, còn người dùng nằm trong CSDL và số lượng không giới hạn. Vì vậy file này chỉ lo
phần token, còn việc tra tài khoản là của `UserRepository`.

⚠️ HAI SECRET RIÊNG BIỆT, KHÔNG DÙNG CHUNG với admin.
Dùng chung thì một token người dùng bị lộ + một lỗi lập trình nhỏ ở chỗ đọc `role` là đủ
để giả mạo admin. Tách secret khiến chữ ký của bên này không bao giờ hợp lệ ở bên kia,
kể cả khi code có sai.

⚠️ TOKEN CHỈ CHỨA `sub` (user_id) — CỐ TÌNH KHÔNG CHỨA `role`.
Nếu nhét vai vào token thì vai trở thành ảnh chụp lúc đăng nhập: hạ quyền một admin sẽ
KHÔNG có hiệu lực cho tới khi token hết hạn. Vai phải đọc từ CSDL ở mỗi request. Một câu
SELECT theo khoá chính là quá rẻ so với rủi ro đó.
"""
from __future__ import annotations

import logging

from src.application.errors import AuthNotConfiguredError, InvalidCredentialsError
from src.domain.entities.user import User
from src.infrastructure.auth.crypto import TokenInvalid, sign_token, verify_token

logger = logging.getLogger("moodbite.auth")

# 24 giờ. Ngắn hơn mức thường thấy của một ứng dụng tiêu dùng (7-30 ngày) vì hiện CHƯA CÓ
# cơ chế thu hồi token: đăng xuất chỉ xoá token ở phía client, bản thân token vẫn hợp lệ
# tới lúc hết hạn. Chừng nào chưa có thu hồi thì thời hạn chính là trần thiệt hại khi
# token bị lộ. Nâng lên được sau khi làm thu hồi — xem docs/API_DECISIONS_PENDING.md.
DEFAULT_USER_TOKEN_TTL_SECONDS = 86_400


class UserTokenService:
    """Ký và mở token phiên đăng nhập của người dùng."""

    def __init__(
        self,
        token_secret: str,
        token_ttl_seconds: int = DEFAULT_USER_TOKEN_TTL_SECONDS,
    ) -> None:
        self._secret = token_secret.encode("utf-8") if token_secret else b""
        self.token_ttl_seconds = token_ttl_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self._secret)

    def ensure_configured(self) -> None:
        """FAIL-CLOSED: chưa có secret thì TẮT hẳn tính năng tài khoản.

        CỐ TÌNH không tự sinh secret ngẫu nhiên lúc khởi động. Làm vậy trông thì "chạy
        được ngay", nhưng mỗi lần khởi động lại là toàn bộ người dùng bị đăng xuất, và
        chạy nhiều tiến trình thì token của tiến trình này không hợp lệ ở tiến trình kia
        - lỗi chập chờn cực khó chẩn đoán. Thà báo 503 kèm hướng dẫn.
        """
        if not self.is_configured:
            raise AuthNotConfiguredError(
                "Chưa bật tính năng tài khoản. Đặt biến môi trường MOODBITE_AUTH_SECRET "
                "(chuỗi ngẫu nhiên dài, KHÁC MOODBITE_ADMIN_SECRET) rồi khởi động lại. "
                "Sinh chuỗi bằng: python -c \"import secrets; print(secrets.token_hex(32))\""
            )

    def issue(self, user: User) -> str:
        """Phát token cho một tài khoản đã xác thực xong."""
        self.ensure_configured()
        return sign_token({"sub": user.user_id}, self._secret, self.token_ttl_seconds)

    def subject_of(self, token: str) -> str:
        """Trả `user_id` trong token hợp lệ, ngược lại ném InvalidCredentialsError -> 401.

        KHÔNG trả vai. Người gọi phải tự đọc tài khoản từ kho để lấy vai hiện tại.
        """
        self.ensure_configured()
        try:
            payload = verify_token(token, self._secret)
        except TokenInvalid as exc:
            raise InvalidCredentialsError(str(exc))
        user_id = str(payload.get("sub", ""))
        if not user_id:
            # Chữ ký đúng nhưng ruột thiếu `sub` = token do chính ta ký sai. Là bug, nhưng
            # vẫn phải từ chối chứ không được coi là hợp lệ.
            logger.error("Token hợp lệ nhưng thiếu 'sub' - kiểm tra lại chỗ phát token.")
            raise InvalidCredentialsError("Token không hợp lệ.")
        return user_id

    def status(self) -> dict:
        """Cho /health. TUYỆT ĐỐI không trả secret ra ngoài."""
        return {
            "ready": self.is_configured,
            "source": "user auth (token HMAC, hạn %ss)" % self.token_ttl_seconds,
            "error": None
            if self.is_configured
            else "chưa đặt MOODBITE_AUTH_SECRET - tính năng tài khoản đang tắt",
        }


__all__ = ["UserTokenService", "DEFAULT_USER_TOKEN_TTL_SECONDS"]

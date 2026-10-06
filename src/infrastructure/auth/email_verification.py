"""Token XÁC MINH EMAIL — ký và kiểm.

Cùng khuôn với `password_reset.py`, khác ở ba chỗ và đều có lý do:

| | Đặt lại mật khẩu | Xác minh email |
|---|---|---|
| Sống bao lâu | 30 phút | **24 giờ** |
| Vân tay một-lần-dùng | chuỗi băm mật khẩu | **email + trạng thái đã xác minh** |
| Hỏng thì mất gì | không đăng nhập lại được | chỉ là chưa đóng được dấu |

**VÌ SAO 24 GIỜ chứ không 30 phút.** Thư đặt lại mật khẩu là thứ người ta đang cần gấp
nên mở ngay; thư xác minh thì hay bị để đó tới tối mới đọc, có khi rơi vào hộp spam.
Cắt 30 phút ở đây chỉ tạo ra vòng lặp "bấm vào thì báo hết hạn -> gửi lại". Rủi ro cũng
thấp hơn hẳn: token này KHÔNG mở được cửa đăng nhập và KHÔNG đổi được mật khẩu, nó chỉ
đóng đúng một dấu `email_verified = 1`.

**VÌ SAO VÂN TAY LÀ `email + đã xác minh`.** Cùng mẹo với `password_reset.py`: nhét vào
token vân tay của TRẠNG THÁI HIỆN TẠI, nên trạng thái đổi là token chết, không cần bảng
lưu token, không cần dọn token hết hạn, và không thể quên xoá.

    - Xác minh xong  -> `email_verified` 0 -> 1 -> vân tay đổi -> bấm lại link cũ vô hiệu.
    - Đổi email      -> địa chỉ đổi        -> vân tay đổi -> thư gửi cho địa chỉ CŨ chết.

Vế thứ hai mới là vế quan trọng về bảo mật. Không có nó thì kịch bản này lọt: người dùng
khai `a@x.com`, nhận thư, chưa bấm; đổi email sang `b@y.com`; rồi bấm vào link cũ — và hệ
thống đóng dấu "đã xác minh" cho `b@y.com` dù chưa ai chứng minh hộp thư đó có thật.
`SqliteUserRepository.mark_email_verified` còn chặn thêm một lần nữa ở câu UPDATE — hai
lớp cho cùng một lỗi, vì đây là chỗ sai thì im lặng, không ai thấy.

Token mang `typ`='verify' (2026-10-06) nên không bao giờ được nhận làm token đăng nhập,
kể cả khi secret lui về trùng secret đăng nhập.

⚠️ DÙNG SECRET RIÊNG. Thứ tự lui: `MOODBITE_EMAIL_VERIFY_SECRET` ->
`MOODBITE_RESET_SECRET` -> `MOODBITE_AUTH_SECRET` (lắp ở `dependencies.py`). Lý do giống
`password_reset.py`: token này nằm trong hộp thư, nơi dễ lộ hơn hẳn, nên chữ ký của nó
tuyệt đối không được mở được cửa đăng nhập.
"""
from __future__ import annotations

import hashlib
import logging

from src.application.errors import AuthNotConfiguredError, InvalidCredentialsError
from src.domain.entities.user import User
from src.infrastructure.auth.crypto import (
    PURPOSE_VERIFY,
    TokenInvalid,
    sign_token,
    verify_token,
)

logger = logging.getLogger("moodbite.auth")

# 24 giờ — xem giải thích ở đầu file.
DEFAULT_VERIFY_TTL_SECONDS = 86_400


def _van_tay(email: str, da_xac_minh: bool) -> str:
    """16 ký tự hex đại diện cho TRẠNG THÁI EMAIL hiện tại của tài khoản.

    Băm chứ không nhét thẳng địa chỉ: token đi qua thư và có thể nằm lại trong log của
    máy chủ thư, nên không mang theo địa chỉ ở dạng đọc được. Bản băm chỉ dùng để SO
    SÁNH, không suy ngược ra địa chỉ.

    `|` ngăn giữa hai phần để không có cặp giá trị nào khác nhau mà nối lại ra cùng một
    chuỗi.
    """
    nguyen_lieu = f"{(email or '').strip().lower()}|{int(bool(da_xac_minh))}"
    return hashlib.sha256(nguyen_lieu.encode("utf-8")).hexdigest()[:16]


class EmailVerificationTokenService:
    """Ký và mở token trong đường dẫn xác minh email."""

    def __init__(
        self,
        token_secret: str,
        token_ttl_seconds: int = DEFAULT_VERIFY_TTL_SECONDS,
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
                "Chưa bật tính năng xác minh email. Đặt biến môi trường "
                "MOODBITE_EMAIL_VERIFY_SECRET (hoặc MOODBITE_AUTH_SECRET) rồi khởi động "
                'lại. Sinh chuỗi bằng: python -c "import secrets; print(secrets.token_hex(32))"'
            )

    def issue(self, user: User) -> str:
        """Phát token xác minh cho ĐÚNG địa chỉ email hiện tại của tài khoản này."""
        self.ensure_configured()
        if not user.has_email:
            # Không có địa chỉ thì không có gì để xác minh. Ném lỗi thay vì phát một token
            # rỗng nghĩa — token đó sẽ luôn hỏng ở bước kiểm và rất khó lần ra vì sao.
            raise InvalidCredentialsError("Tài khoản này chưa khai email.")
        # KHÔNG nhét địa chỉ email vào token (bỏ 2026-10-06). Ruột token chỉ là base64,
        # AI CŨNG ĐỌC ĐƯỢC — và token này nằm trong URL, tức là lọt vào lịch sử trình
        # duyệt, log máy chủ, log máy chủ thư. Bản cũ mang `em` ở dạng đọc được, trái
        # ngược chính docstring của `_van_tay`. Không cần nó: vân tay `ev` đã băm cả địa
        # chỉ, nên "email đã đổi" vẫn làm token chết y như trước.
        return sign_token(
            {"sub": user.user_id, "ev": _van_tay(user.email, user.email_verified)},
            self._secret,
            self.token_ttl_seconds,
            purpose=PURPOSE_VERIFY,
        )

    def read(self, token: str) -> tuple[str, str]:
        """BƯỚC 1 — kiểm chữ ký, mục đích và hạn dùng. Trả `(user_id, vân tay)`.

        CHƯA kiểm vân tay ở đây: muốn so vân tay thì phải biết trạng thái hiện tại của
        tài khoản, mà muốn biết thì trước hết phải biết là tài khoản NÀO. Tách hai bước
        đúng như `PasswordResetTokenService` — người gọi BẮT BUỘC gọi tiếp `ensure_unused`.

        Token phát trước 2026-10-06 còn mang `em`: bỏ qua, không đọc nữa.
        """
        self.ensure_configured()
        try:
            payload = verify_token(token, self._secret, purpose=PURPOSE_VERIFY)
        except TokenInvalid as exc:
            # Giữ nguyên câu của tầng dưới: nó phân biệt "hỏng" với "hết hạn", và người
            # dùng cần biết nên bấm gửi lại thư hay chỉ gõ nhầm đường dẫn.
            raise InvalidCredentialsError(str(exc))

        user_id = str(payload.get("sub", ""))
        van_tay = str(payload.get("ev", ""))
        if not user_id or not van_tay:
            raise InvalidCredentialsError("Đường dẫn xác minh email không hợp lệ.")
        return user_id, van_tay

    def ensure_unused(self, van_tay_trong_token: str, user: User) -> None:
        """BƯỚC 2 — chốt chặn CHỈ DÙNG MỘT LẦN và chống đổi-email-rồi-bấm-link-cũ.

        So vân tay trong token với trạng thái email HIỆN TẠI của tài khoản. Lệch nghĩa là
        một trong hai chuyện đã xảy ra, và cả hai đều phải chặn:
          - đã xác minh rồi (bấm lại link cũ),
          - đã đổi sang địa chỉ khác (link cũ không được phép đóng dấu cho địa chỉ mới).
        """
        if van_tay_trong_token != _van_tay(user.email or "", user.email_verified):
            raise InvalidCredentialsError(
                "Đường dẫn này không còn hiệu lực — email đã được xác minh hoặc đã đổi. "
                "Hãy yêu cầu gửi lại thư mới."
            )


__all__ = ["EmailVerificationTokenService", "DEFAULT_VERIFY_TTL_SECONDS"]

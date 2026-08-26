"""USE CASE: đăng ký, đăng nhập và đặt lại mật khẩu tài khoản người dùng.

Chỉ ĐIỀU PHỐI. Quy tắc đặt tên/mật khẩu nằm ở `domain/entities/user.py`; băm mật khẩu và
ký token nằm ở `infrastructure/auth/crypto.py`. File này không tự làm hai việc đó.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Protocol

from src.application.errors import InvalidCredentialsError
from src.application.emails import thu_co_nut
from src.application.ports.email_sender import EmailSender
from src.application.ports.user_repository import UserRepository, UsernameAlreadyExists
from src.domain.entities.user import (
    InvalidCredentialsFormat,
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
        email: str = "",
    ) -> tuple[User, str]:
        """Tạo tài khoản mới, trả về (user, token) để đăng ký xong là dùng được luôn.

        `email` BẮT BUỘC — đổi ngày 2026-08-24 theo yêu cầu chủ dự án.

        VÌ SAO ĐỔI (bản cũ ghi "tuỳ chọn... ép nhập chỉ để phòng xa sẽ làm rơi người đăng
        ký"): lý lẽ đó đúng khi email chưa dùng vào việc gì ngoài "phòng xa". Nay đã có
        luồng XÁC MINH EMAIL, nên email là thứ duy nhất chứng minh tài khoản thuộc về một
        người có thật, và cũng là đường DUY NHẤT lấy lại mật khẩu. Tài khoản không email
        mà quên mật khẩu thì mất hẳn — không ai cứu được.

        ⚠️ CHỈ ÁP CHO ĐĂNG KÝ MỚI. Tài khoản cũ tạo trước hôm nay vẫn có thể không có
        email và PHẢI dùng được bình thường — xem `User.can_receive_mail`.
        """
        # Kiểm định dạng TRƯỚC khi băm: băm mất ~0.4s, không nên tốn cho input rác.
        name = validate_username(username)
        validate_password(password)
        # Không còn nhánh "bỏ trống thì thôi": thiếu email là lỗi định dạng -> 400.
        dia_chi = validate_email(email)

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

        # Thư có NÚT BẤM, không để đường dẫn trần giữa dòng — xem `application/emails`.
        thu = thu_co_nut(
            subject="Đặt lại mật khẩu MoodBite",
            tren_nut=[
                f"Chào {user.display_name or user.username},",
                "",
                "Có người vừa yêu cầu đặt lại mật khẩu cho tài khoản MoodBite của bạn "
                f"({user.username}).",
            ],
            nhan_nut="Đặt mật khẩu mới",
            lien_ket=lien_ket,
            duoi_nut=[
                f"Đường dẫn có hiệu lực trong {phut} phút và chỉ dùng được MỘT lần.",
                "",
                "Nếu không phải bạn yêu cầu thì cứ bỏ qua thư này — mật khẩu hiện tại "
                "vẫn giữ nguyên.",
            ],
        )

        self.emails.send(
            to=user.email,
            subject=thu.subject,
            body=thu.text,
            html=thu.html,
        )
        logger.info("Đã gửi thư đặt lại mật khẩu cho %s", user.username)
        return True


class EmailVerificationTokens(Protocol):
    """Hợp đồng token xác minh email. Hai bước, xem `infrastructure/auth/email_verification.py`."""

    def issue(self, user: User) -> str: ...

    def read(self, token: str) -> tuple[str, str, str]:
        """Trả (user_id, email ghi trong thư, vân tay trạng thái)."""
        ...

    def ensure_unused(self, van_tay_trong_token: str, user: User) -> None:
        """Ném lỗi nếu link đã dùng rồi hoặc email đã đổi."""
        ...


@dataclass
class RequestEmailVerificationUseCase:
    """Gửi thư kèm đường dẫn xác minh email cho MỘT tài khoản cụ thể.

    KHÁC `RequestPasswordResetUseCase` ở chỗ KHÔNG phải giấu "tài khoản có tồn tại không":
    ở đây người gọi đã đăng nhập, tức là đã biết thừa tài khoản của chính họ tồn tại.
    Nên chỗ này được phép nói thẳng "bạn chưa khai email" hay "email đã xác minh rồi" —
    giấu đi chỉ làm người dùng bối rối mà không che được bí mật nào.
    """

    emails: EmailSender
    verify_tokens: EmailVerificationTokens
    app_base_url: str
    token_ttl_seconds: int

    def execute(self, user: User) -> bool:
        """Trả True nếu đã gửi thư, False nếu không có gì để gửi."""
        if not user.has_email:
            return False
        if user.email_verified:
            # Đã xác minh rồi thì không gửi lại. Không phải lỗi — chỉ là không có việc gì.
            return False

        token = self.verify_tokens.issue(user)
        # ⚠️ Phải KHỚP `ROUTES.verifyEmail` ở frontend
        # (`frontend/apps/client/src/shared/config/routes.ts`). Lệch một chữ là link
        # trong thư ra 404 — đúng cái bẫy đã ghi ở luồng đặt lại mật khẩu.
        lien_ket = f"{self.app_base_url.rstrip('/')}/verify-email?token={token}"
        gio = max(1, self.token_ttl_seconds // 3600)

        thu = thu_co_nut(
            subject="Xác minh email MoodBite",
            tren_nut=[
                f"Chào {user.display_name or user.username},",
                "",
                "Hãy xác nhận đây đúng là hộp thư của bạn — bấm nút dưới đây là xong, "
                "không cần nhập gì thêm.",
            ],
            nhan_nut="Xác minh email",
            lien_ket=lien_ket,
            duoi_nut=[
                f"Đường dẫn có hiệu lực trong {gio} giờ và chỉ dùng được MỘT lần.",
                "",
                "Xác minh xong, bạn mới lấy lại được mật khẩu qua email nếu lỡ quên.",
                "",
                "Nếu bạn không đăng ký MoodBite thì cứ bỏ qua thư này.",
            ],
        )
        self.emails.send(
            to=user.email,
            subject=thu.subject,
            body=thu.text,
            html=thu.html,
        )
        logger.info("Đã gửi thư xác minh email cho %s", user.username)
        return True

    def try_send(self, user: User) -> bool:
        """Như `execute` nhưng NUỐT lỗi gửi thư. Chỉ dùng ngay sau khi đăng ký.

        VÌ SAO PHẢI CÓ BẢN RIÊNG NÀY: đăng ký xong thì gửi luôn thư xác minh là tiện nhất
        cho người dùng, nhưng máy chủ SMTP hỏng KHÔNG được phép làm hỏng việc tạo tài
        khoản — tài khoản đã ghi vào CSDL rồi, ném lỗi ra lúc này thì người dùng thấy
        "đăng ký thất bại" trong khi họ đã có tài khoản và không đăng ký lại được nữa
        (tên đã bị chiếm). Họ luôn bấm gửi lại thư sau được.
        """
        try:
            return self.execute(user)
        except Exception as exc:                      # noqa: BLE001 - xem docstring
            logger.warning("Không gửi được thư xác minh cho %s: %s", user.username, exc)
            return False


@dataclass
class ConfirmEmailVerificationUseCase:
    """Đóng dấu `email_verified` bằng token trong thư."""

    users: UserRepository
    verify_tokens: EmailVerificationTokens

    def execute(self, token: str) -> User:
        user_id, email_trong_thu, van_tay = self.verify_tokens.read(token)

        user = self.users.get_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError("Đường dẫn xác minh email không hợp lệ.")

        # Bước 2: trạng thái email hiện tại phải khớp lúc phát token -> chặn cả việc
        # bấm lại link cũ lẫn việc đổi email rồi bấm link cũ.
        self.verify_tokens.ensure_unused(van_tay, user)

        if not self.users.mark_email_verified(user.user_id, email_trong_thu):
            # Tới đây mà thất bại nghĩa là email vừa đổi giữa chừng (câu UPDATE có điều
            # kiện `AND email = ?`). Cùng thông điệp với `ensure_unused` vì với người
            # dùng thì đó là cùng một tình huống.
            raise InvalidCredentialsError(
                "Đường dẫn này không còn hiệu lực — email đã được xác minh hoặc đã đổi. "
                "Hãy yêu cầu gửi lại thư mới."
            )

        logger.info("Đã xác minh email cho %s", user.username)
        # Đọc lại để trả về trạng thái MỚI, không trả bản cũ trong bộ nhớ.
        return self.users.get_by_id(user.user_id) or user


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


@dataclass
class ChangePasswordUseCase:
    """Đổi mật khẩu khi ĐANG ĐĂNG NHẬP. Khác hẳn luồng quên mật khẩu.

    VÌ SAO VẪN PHẢI HỎI MẬT KHẨU CŨ dù người dùng đã có token hợp lệ:
    token nằm trong trình duyệt và sống 24 giờ. Ai đó mượn máy lúc chủ máy đi pha cà phê
    là đổi được mật khẩu rồi chiếm luôn tài khoản. Hỏi lại mật khẩu cũ biến "mượn được
    máy" thành "phải biết mật khẩu" — chặn đúng tình huống hay xảy ra nhất.

    ⚠️ Đổi mật khẩu KHÔNG thu hồi được token đang sống ở máy khác. Token ký bằng HMAC là
    stateless, server không giữ danh sách nào để xoá. Muốn thu hồi thật thì phải thêm cột
    `token_version` vào bảng `users` — ĐỔI LƯỢC ĐỒ nên phải chốt trước
    (`docs/API_DECISIONS_PENDING.md`). Router nói rõ giới hạn này cho người dùng.
    """

    users: UserRepository
    verify_password: object       # (password, hash) -> bool
    hash_password: PasswordHasher

    def execute(self, user: User, mat_khau_cu: str, mat_khau_moi: str) -> User:
        if not self.verify_password(mat_khau_cu or "", user.password_hash):
            # Người này đã đăng nhập nên nói thẳng "mật khẩu hiện tại không đúng" là an
            # toàn — không lộ thêm gì về tài khoản nào cả.
            raise InvalidCredentialsError("Mật khẩu hiện tại không đúng.")

        validate_password(mat_khau_moi)

        if mat_khau_moi == mat_khau_cu:
            raise InvalidCredentialsFormat("Mật khẩu mới phải khác mật khẩu cũ.")

        if not self.users.update_password(user.user_id, self.hash_password(mat_khau_moi)):
            raise InvalidCredentialsError("Không tìm thấy tài khoản để đổi mật khẩu.")

        logger.info("Đã đổi mật khẩu (từ trong tài khoản) cho %s", user.username)
        return user


# Chuỗi băm giả, dùng để so khớp khi tài khoản không tồn tại (xem giải thích ở trên).
# Đúng định dạng thật để `verify_password` chạy trọn vẹn số vòng lặp.
_HASH_GIA = (
    "pbkdf2_sha256$600000$"
    "00000000000000000000000000000000$"
    "0000000000000000000000000000000000000000000000000000000000000000"
)


__all__ = [
    "RegisterUserUseCase",
    "LoginUseCase",
    "ChangePasswordUseCase",
    "UsernameAlreadyExists",
]

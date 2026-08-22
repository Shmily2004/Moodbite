"""ADAPTER: gửi thư qua SMTP. Triển khai port `EmailSender`.

VÌ SAO SMTP CHỨ KHÔNG PHẢI DỊCH VỤ GỬI THƯ (SendGrid, Mailgun, Resend...):
chủ dự án KHÔNG có thẻ thanh toán (CLAUDE.md mục 1b). Các dịch vụ đó đều đòi đăng ký kèm
thẻ hoặc xác minh tên miền. Trong khi đó SMTP của Gmail:

  - miễn phí, chỉ cần một tài khoản Gmail sẵn có;
  - KHÔNG cần thẻ, KHÔNG cần tên miền riêng;
  - hạn mức ~500 thư/ngày — thừa sức cho một đồ án demo;
  - `smtplib` nằm trong thư viện chuẩn Python, không thêm phụ thuộc nào.

CÁCH LẤY MẬT KHẨU ỨNG DỤNG (App Password) — KHÔNG dùng mật khẩu Gmail thật:
  1. Bật xác minh 2 bước cho tài khoản Google.
  2. Vào https://myaccount.google.com/apppasswords, tạo một mật khẩu ứng dụng.
  3. Đặt vào biến môi trường `MOODBITE_SMTP_PASSWORD` (16 ký tự, bỏ khoảng trắng).
Mật khẩu ứng dụng thu hồi riêng được và không mở được hộp thư — lộ ra thì thiệt hại có
chặn trên rõ ràng.

⚠️ KHÔNG BAO GIỜ ghi mật khẩu vào mã nguồn hay `.env` đã commit. Xem `.env.example`.
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from src.application.ports.email_sender import EmailSendFailed

logger = logging.getLogger("moodbite.email")

# 15 giây. Máy chủ thư chậm là chuyện thường, nhưng người dùng đang ngồi đợi trang web
# phản hồi — quá mức này thì thà báo lỗi để họ bấm lại còn hơn treo trang.
TIMEOUT_SECONDS = 15


class SmtpEmailSender:
    """Gửi thư chữ thuần qua một máy chủ SMTP có xác thực."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        use_tls: bool = True,
    ) -> None:
        self._host = (host or "").strip()
        self._port = port
        self._username = (username or "").strip()
        self._password = password or ""
        # Thiếu địa chỉ người gửi thì lấy luôn tài khoản đăng nhập — với Gmail hai thứ
        # này gần như luôn trùng nhau, bắt khai hai lần chỉ tổ sai.
        self._sender = (sender or "").strip() or self._username
        self._use_tls = use_tls

    @property
    def is_configured(self) -> bool:
        """Đủ 4 thứ mới gửi được. Thiếu một thứ là coi như TẮT hẳn tính năng."""
        return bool(self._host and self._port and self._username and self._password)

    def send(self, *, to: str, subject: str, body: str) -> None:
        if not self.is_configured:
            # Người gọi phải kiểm `is_configured` trước; tới được đây là lỗi lập trình.
            raise EmailSendFailed("Chưa cấu hình máy chủ thư.")

        thu = EmailMessage()
        thu["From"] = self._sender
        thu["To"] = to
        thu["Subject"] = subject
        thu.set_content(body)

        try:
            with smtplib.SMTP(self._host, self._port, timeout=TIMEOUT_SECONDS) as smtp:
                if self._use_tls:
                    # `create_default_context()` bật sẵn kiểm chứng chỉ và tên miền. Đừng
                    # thay bằng context tự chế để "cho đỡ lỗi" — làm vậy là mở cửa cho tấn
                    # công người-đứng-giữa đọc trộm cả mật khẩu ứng dụng lẫn nội dung thư.
                    smtp.starttls(context=ssl.create_default_context())
                smtp.login(self._username, self._password)
                smtp.send_message(thu)
        except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
            # KHÔNG ghi mật khẩu vào log. Chỉ ghi loại lỗi và máy chủ.
            logger.error("Gửi thư qua %s:%s thất bại: %s", self._host, self._port, exc)
            raise EmailSendFailed(
                "Không gửi được thư. Kiểm tra lại cấu hình MOODBITE_SMTP_* "
                "và kết nối mạng của máy chủ."
            ) from exc

        logger.info("Đã gửi thư tới %s (chủ đề: %s)", to, subject)

    def status(self) -> dict:
        """Cho `/health`. KHÔNG lộ tài khoản hay mật khẩu."""
        return {
            "ready": self.is_configured,
            "source": f"{self._host}:{self._port}" if self._host else None,
            "error": None if self.is_configured else "Chưa đặt MOODBITE_SMTP_*",
        }


__all__ = ["SmtpEmailSender"]

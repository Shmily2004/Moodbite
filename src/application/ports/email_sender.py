"""PORT: gửi thư điện tử.

Application chỉ biết "gửi được một lá thư", KHÔNG biết là qua SMTP của Gmail, qua dịch vụ
nào, hay chỉ ghi ra log lúc chạy test.

VÌ SAO CẦN PORT CHO VIỆC NHỎ NHƯ GỬI THƯ: use case đặt lại mật khẩu phải test được mà
KHÔNG gửi thư thật. Có port thì test tiêm một bản giả và kiểm đúng nội dung thư; không có
port thì hoặc là test spam hộp thư thật, hoặc là không test được.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmailSender(Protocol):
    @property
    def is_configured(self) -> bool:
        """False khi chưa khai báo máy chủ thư — tính năng phải TẮT chứ không giả vờ chạy."""
        ...

    def send(self, *, to: str, subject: str, body: str) -> None:
        """Gửi một lá thư chữ thuần.

        Ném `EmailSendFailed` nếu không gửi được. KHÔNG nuốt lỗi: người dùng bấm "gửi lại
        mật khẩu" mà thư không đi thì họ phải được biết, chứ không phải ngồi đợi mãi một
        lá thư không bao giờ tới.
        """
        ...


class EmailSendFailed(Exception):
    """Không gửi được thư (mạng lỗi, sai mật khẩu ứng dụng, máy chủ từ chối...)."""

"""Lỗi cấp application. Tầng presentation ánh xạ các lỗi này sang HTTP status.

KHÔNG import FastAPI ở đây - application không được biết gì về HTTP.
"""
from __future__ import annotations


class ApplicationError(Exception):
    """Gốc của mọi lỗi nghiệp vụ có thể đoán trước."""


class DataNotReadyError(ApplicationError):
    """Nguồn dữ liệu chưa sẵn sàng (chưa chạy data_pipeline).

    -> HTTP 503. App vẫn chạy ở chế độ degraded thay vì crash khi khởi động.
    """

    def __init__(self, source: str, how_to_fix: str = "") -> None:
        message = f"Dữ liệu chưa sẵn sàng: {source}."
        if how_to_fix:
            message += f" Cách khắc phục: {how_to_fix}"
        super().__init__(message)
        self.source = source


# --- Lỗi xác thực quản trị ---------------------------------------------------
#
# Đặt ở application chứ KHÔNG ở infrastructure/auth, dù bên đó mới là nơi ném ra.
# Lý do là hướng phụ thuộc: `presentation/error_handlers.py` phải bắt được các lỗi này
# để đổi thành mã HTTP, mà presentation KHÔNG được import infrastructure (CLAUDE.md
# mục 2). Cả hai bên cùng import từ application thì hướng phụ thuộc vẫn đúng.


class InvalidCredentialsError(ApplicationError):
    """Sai tài khoản/mật khẩu, hoặc token hỏng/hết hạn. -> HTTP 401 UNAUTHORIZED."""


class PermissionDeniedError(ApplicationError):
    """Đã đăng nhập nhưng KHÔNG đủ quyền. -> HTTP 403 FORBIDDEN.

    Khác hẳn 401. Trả nhầm 401 ở đây khiến client tưởng token hỏng nên đá người dùng ra
    màn hình đăng nhập, đăng nhập lại vẫn hỏng - vòng lặp vô tận. 403 nói đúng sự thật:
    token tốt, người này không được phép.
    """


class AuthNotConfiguredError(ApplicationError):
    """Chưa đặt biến môi trường cho xác thực. -> HTTP 503 kèm hướng dẫn.

    Fail-closed: chưa cấu hình thì TẮT, không bao giờ mặc định thành cho qua.
    """


class AdminNotConfiguredError(AuthNotConfiguredError):
    """Riêng cho trang quản trị. Kế thừa để `error_handlers` chỉ cần một quy tắc chung,
    nhưng vẫn giữ được thông báo riêng (biến môi trường của admin khác của người dùng)."""


class RateLimitExceeded(ApplicationError):
    """Thao tác quá nhanh -> HTTP 429 RATE_LIMITED, kèm header `Retry-After`.

    Định nghĩa ở TẦNG APPLICATION dù nơi ném ra là `infrastructure/auth/rate_limit.py`.
    Lý do y hệt `InvalidCredentialsError` ở trên: `presentation/error_handlers.py` phải
    bắt được lỗi này, mà presentation KHÔNG được import infrastructure (CLAUDE.md mục 2).
    """

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Bạn thao tác quá nhanh. Thử lại sau {retry_after_seconds} giây."
        )

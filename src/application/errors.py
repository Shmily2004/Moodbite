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


class AdminNotConfiguredError(ApplicationError):
    """Chưa đặt biến môi trường cho admin. -> HTTP 503 kèm hướng dẫn.

    Fail-closed: chưa cấu hình thì TẮT, không bao giờ mặc định thành cho qua.
    """

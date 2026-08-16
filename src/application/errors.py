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

"""PORT: nơi ghi BỀN lệnh "admin gỡ lượt báo đóng cửa".

Tách khỏi `InteractionRepository` vì đây là hành động của QUẢN TRỊ, không phải tương tác
người dùng — kho giả ở test luồng người dùng không phải triển khai thêm hàm nó không dùng.
Bản thật (`JsonlInteractionRepository`) triển khai cả hai port trên CÙNG một file nhật ký,
và đó là điều bắt buộc: bộ đếm báo đóng cửa được phát lại từ chính file đó lúc khởi động.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ClosureReportLog(Protocol):
    @property
    def is_ready(self) -> bool:
        ...

    def append_closure_reports_cleared(self, restaurant_id: str, actor: str) -> str:
        """Ghi sự kiện "gỡ mọi lượt báo của quán này". Trả id sự kiện.

        Lỗi ghi phải được NÉM ra, không nuốt: gỡ trong RAM mà không ghi được xuống đĩa thì
        khởi động lại xong quán lại bị ẩn — admin tưởng đã xử lý xong mà thực ra chưa.
        """
        ...

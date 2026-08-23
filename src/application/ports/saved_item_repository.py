"""PORT: hợp đồng lưu "quán/món yêu thích" của người dùng.

Cùng lý do tách port như mọi kho khác: application chỉ biết interface này, không biết dữ
liệu nằm ở SQLite hay đâu. Đổi sang PostgreSQL = viết adapter mới, use case không đổi.

⚠️ Đây là DỮ LIỆU GỐC (mất là mất hẳn) nên nằm chung file CSDL với tài khoản, KHÔNG nằm
ở `moodbite.db` — file đó là dữ liệu dẫn xuất và tài liệu còn khuyến khích xoá đi dựng
lại. Xem `sqlite_user_repository.py` để biết đầy đủ lý do.
"""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from src.domain.entities.saved_item import SavedItem, SavedItemType


@runtime_checkable
class SavedItemRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        ...

    def add(self, item: SavedItem) -> SavedItem:
        """Lưu một mục. Lưu lại thứ đã lưu thì KHÔNG lỗi — chỉ cập nhật tên.

        Cố ý làm idempotent: người dùng bấm tim hai lần vì mạng chậm không đáng nhận một
        thông báo lỗi, và client cũng không phải kiểm tra trước khi gửi.
        """
        ...

    def remove(self, user_id: str, item_type: SavedItemType, item_id: str) -> bool:
        """Bỏ lưu. Trả False nếu vốn không có gì để bỏ."""
        ...

    def list_for_user(
        self, user_id: str, item_type: Optional[SavedItemType] = None
    ) -> List[SavedItem]:
        """Danh sách đã lưu, MỚI NHẤT ĐỨNG ĐẦU."""
        ...

    def count_for_user(
        self, user_id: str, item_type: Optional[SavedItemType] = None
    ) -> int:
        """Đếm nhanh cho trang tài khoản, không phải tải cả danh sách về rồi len()."""
        ...


__all__ = ["SavedItemRepository"]

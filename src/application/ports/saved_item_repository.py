"""PORT: hợp đồng lưu "quán/món yêu thích" của người dùng.

Cùng lý do tách port như mọi kho khác: application chỉ biết interface này, không biết dữ
liệu nằm ở SQLite hay đâu. Đổi sang PostgreSQL = viết adapter mới, use case không đổi.

⚠️ Đây là DỮ LIỆU GỐC (mất là mất hẳn) nên nằm chung file CSDL với tài khoản, KHÔNG nằm
ở `moodbite.db` — file đó là dữ liệu dẫn xuất và tài liệu còn khuyến khích xoá đi dựng
lại. Xem `sqlite_user_repository.py` để biết đầy đủ lý do.
"""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from src.domain.entities.saved_item import SavedItem, SavedItemType, SavedListType


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

    def remove(
        self,
        user_id: str,
        item_type: SavedItemType,
        item_id: str,
        list_type: SavedListType = SavedListType.FAVORITE,
    ) -> bool:
        """Bỏ khỏi MỘT danh sách. Trả False nếu vốn không có gì để bỏ.

        Chỉ động vào đúng danh sách được nêu: bỏ tim một món KHÔNG được xoá luôn dấu
        trang của món đó — đó là hai ý định khác nhau của người dùng.
        """
        ...

    def list_for_user(
        self,
        user_id: str,
        item_type: Optional[SavedItemType] = None,
        list_type: Optional[SavedListType] = None,
    ) -> List[SavedItem]:
        """Danh sách đã lưu, MỚI NHẤT ĐỨNG ĐẦU.

        `list_type=None` nghĩa là LẤY CẢ HAI danh sách. Giao diện cần cả hai trong một
        lần gọi (thẻ món phải biết tim nào bật, dấu trang nào bật), gọi hai vòng chỉ tốn
        thêm một lượt mạng cho cùng một bảng.
        """
        ...

    def count_for_user(
        self,
        user_id: str,
        item_type: Optional[SavedItemType] = None,
        list_type: Optional[SavedListType] = None,
    ) -> int:
        """Đếm nhanh cho trang tài khoản, không phải tải cả danh sách về rồi len()."""
        ...

    def count_distinct_items(
        self, user_id: str, item_type: Optional[SavedItemType] = None
    ) -> int:
        """Đếm số THỨ khác nhau, KHÔNG phải số dòng.

        ⚠️ KHÁC `count_for_user` và đây là chỗ đã sai một lần (2026-08-26): từ khi có hai
        danh sách, một món vừa được thả tim vừa được đánh dấu sẽ nằm ở HAI dòng. Trang
        tài khoản hiện ô "Món đã lưu" và câu hỏi người dùng đặt ra là "tôi đã lưu BAO
        NHIÊU MÓN", nên đếm dòng cho ra 2 trong khi họ chỉ có 1 món — và điểm cấp độ
        cũng bị thổi lên gấp đôi cho cùng một hành vi.
        """
        ...


__all__ = ["SavedItemRepository"]

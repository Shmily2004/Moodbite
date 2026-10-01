"""PORT: hợp đồng lưu "Bộ sưu tập của tôi".

⚠️ MỌI phương thức đều nhận `user_id` và PHẢI giới hạn truy vấn trong phạm vi người đó.
Một `collection_id` của người khác phải được đối xử Y HỆT một mã không tồn tại (trả
`None`/`False`) — adapter không được có nhánh nào để lộ "mã này có, nhưng của người khác".
Nhờ vậy router trả 404 cho cả hai trường hợp và không ai dò được bộ sưu tập của người khác.

Đây là DỮ LIỆU GỐC do người dùng tạo, nên nằm chung file CSDL với tài khoản — cùng lý do
với `saved_item_repository.py`.
"""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from src.domain.entities.collection import Collection, CollectionItem
from src.domain.entities.saved_item import SavedItemType


@runtime_checkable
class CollectionRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        ...

    def list_for_user(self, user_id: str) -> List[Collection]:
        """Mọi bộ sưu tập của một người, KÈM mục bên trong. Bộ mới tạo đứng đầu."""
        ...

    def get(self, user_id: str, collection_id: str) -> Optional[Collection]:
        """Một bộ (kèm mục) — `None` nếu không có HOẶC thuộc người khác."""
        ...

    def count_for_user(self, user_id: str) -> int:
        ...

    def create(self, collection: Collection) -> Collection:
        """Tạo bộ mới (chưa có mục). Trả bản đã gắn `created_at`."""
        ...

    def rename(self, user_id: str, collection_id: str, name: str) -> bool:
        """False nếu không có bộ đó trong phạm vi người dùng."""
        ...

    def delete(self, user_id: str, collection_id: str) -> bool:
        """Xoá bộ VÀ mọi mục bên trong, trong CÙNG một giao dịch."""
        ...

    def add_item(
        self, user_id: str, collection_id: str, item: CollectionItem
    ) -> bool:
        """Thêm mục (idempotent: đã có thì chỉ cập nhật tên, giữ `added_at` cũ).
        False nếu bộ không thuộc người dùng."""
        ...

    def remove_item(
        self,
        user_id: str,
        collection_id: str,
        item_type: SavedItemType,
        item_id: str,
    ) -> bool:
        """Bỏ một mục. False nếu vốn không có mục đó (hoặc bộ không thuộc người dùng)."""
        ...


__all__ = ["CollectionRepository"]

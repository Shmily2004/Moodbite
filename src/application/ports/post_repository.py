"""PORT: hợp đồng lưu BÀI VIẾT (cẩm nang + tin cập nhật).

Đây là nội dung do đội vận hành tạo, không phải dữ liệu của người dùng cuối, nên lưu chung
file CSDL với tài khoản (`moodbite_users.db`) để sao lưu một lần là đủ.

Adapter tự kiểm trùng đường dẫn (`slug`) trong cùng giao dịch ghi, không tin kiểm tra ở
use case: hai request song song cùng thấy "chưa trùng" rồi cùng ghi là bug thật.
"""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from src.domain.entities.post import Post, PostStatus


@runtime_checkable
class PostRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        ...

    def list(self, status: Optional[PostStatus] = None) -> List[Post]:
        """Mọi bài (hoặc chỉ bài có `status`), bài mới cập nhật đứng đầu."""
        ...

    def get(self, post_id: str) -> Optional[Post]:
        ...

    def get_by_slug(self, slug: str) -> Optional[Post]:
        ...

    def slug_taken(self, slug: str, exclude_post_id: Optional[str] = None) -> bool:
        ...

    def create(self, post: Post) -> Post:
        """Ghi bài mới. Trả bản đã gắn `created_at`/`updated_at`."""
        ...

    def update(self, post: Post) -> bool:
        """Ghi đè các trường của bài có cùng `post_id`. False nếu không có bài đó."""
        ...

    def delete(self, post_id: str) -> bool:
        ...


__all__ = ["PostRepository"]

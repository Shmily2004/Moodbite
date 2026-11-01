"""USE CASE: bài viết — đọc công khai và quản trị (tạo · sửa · xoá).

Chỉ ĐIỀU PHỐI. Luật "tiêu đề bao nhiêu ký tự", "bài web bắt buộc có nguồn" nằm ở
`domain/entities/post.py`; việc chống trùng đường dẫn cuối cùng do kho lo (xem port).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Callable, List, Optional

from src.application.errors import ApplicationError, DataNotReadyError
from src.application.ports.post_repository import PostRepository
from src.domain.entities.post import (
    Post,
    PostOrigin,
    PostStatus,
    make_slug,
    validate_post_fields,
)


class PostsNotAvailable(DataNotReadyError):
    """Kho bài viết không mở được -> 503 kèm cách khắc phục."""

    def __init__(self) -> None:
        super().__init__(
            "kho 'bài viết' không mở được",
            "Kiểm tra quyền ghi ở đường dẫn MOODBITE_USERS_DB.",
        )


class PostNotFoundError(ApplicationError):
    """Không có bài này (hoặc bài đang là nháp và người gọi là khách) -> 404.

    Cố ý dùng cùng một lỗi cho "chưa công khai" và "không tồn tại": khách không được biết
    một bài nháp đang tồn tại.
    """

    def __init__(self, ref: str) -> None:
        super().__init__(f"Không tìm thấy bài viết '{ref}'.")
        self.ref = ref


@dataclass(frozen=True)
class PostInput:
    """Dữ liệu admin gửi lên khi tạo hoặc sửa. Đường dẫn (`slug`) KHÔNG nằm ở đây: nó
    được cấp một lần khi tạo và giữ nguyên, để link đã gửi đi không bị gãy khi sửa tiêu đề."""

    title: str
    summary: str
    body: str
    status: PostStatus
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    last_updated: Optional[date] = None
    origin: PostOrigin = PostOrigin.ADMIN


def _new_id() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class _PostUseCase:
    def __init__(self, posts: PostRepository, new_id: Callable[[], str] = _new_id) -> None:
        self._repo = posts
        self._new_id = new_id

    def _ensure_ready(self) -> None:
        if not self._repo.is_ready:
            raise PostsNotAvailable()


class ListPublishedPostsUseCase(_PostUseCase):
    def execute(self) -> List[Post]:
        self._ensure_ready()
        return self._repo.list(status=PostStatus.PUBLISHED)


class GetPublishedPostUseCase(_PostUseCase):
    def execute(self, slug: str) -> Post:
        self._ensure_ready()
        bai = self._repo.get_by_slug(slug)
        # Nháp trả 404 y như không tồn tại — xem `PostNotFoundError`.
        if bai is None or bai.status is not PostStatus.PUBLISHED:
            raise PostNotFoundError(slug)
        return bai


class ListAllPostsUseCase(_PostUseCase):
    def execute(self, status: Optional[PostStatus] = None) -> List[Post]:
        self._ensure_ready()
        return self._repo.list(status=status)


class GetPostUseCase(_PostUseCase):
    def execute(self, post_id: str) -> Post:
        self._ensure_ready()
        bai = self._repo.get(post_id)
        if bai is None:
            raise PostNotFoundError(post_id)
        return bai


class CreatePostUseCase(_PostUseCase):
    def execute(self, data: PostInput) -> Post:
        self._ensure_ready()
        tieu_de, tom_tat, noi_dung, nguon_ten, nguon_url = validate_post_fields(
            title=data.title,
            summary=data.summary,
            body=data.body,
            origin=data.origin,
            source_name=data.source_name,
            source_url=data.source_url,
        )
        bay_gio = _now()
        return self._repo.create(
            Post(
                post_id=self._new_id(),
                slug=self._slug_khong_trung(tieu_de),
                title=tieu_de,
                summary=tom_tat,
                body=noi_dung,
                status=data.status,
                origin=data.origin,
                source_name=nguon_ten,
                source_url=nguon_url,
                last_updated=data.last_updated,
                created_at=bay_gio,
                updated_at=bay_gio,
                published_at=bay_gio if data.status is PostStatus.PUBLISHED else None,
            )
        )

    def _slug_khong_trung(self, tieu_de: str) -> str:
        """`slug`, `slug-2`, `slug-3`... cho đến khi không trùng. Tiêu đề trùng là chuyện
        thường (hai bài cùng tên "Phở Hà Nội"), không được vì thế mà từ chối bài viết."""
        goc = make_slug(tieu_de)
        slug, so = goc, 2
        while self._repo.slug_taken(slug):
            slug = f"{goc}-{so}"
            so += 1
        return slug


class UpdatePostUseCase(_PostUseCase):
    def execute(self, post_id: str, data: PostInput) -> Post:
        self._ensure_ready()
        hien_co = self._repo.get(post_id)
        if hien_co is None:
            raise PostNotFoundError(post_id)
        tieu_de, tom_tat, noi_dung, nguon_ten, nguon_url = validate_post_fields(
            title=data.title,
            summary=data.summary,
            body=data.body,
            origin=hien_co.origin,  # nguồn gốc bài KHÔNG đổi khi sửa
            source_name=data.source_name,
            source_url=data.source_url,
        )
        # Lần đầu chuyển sang công khai mới đóng dấu giờ; về nháp rồi công khai lại thì giữ
        # giờ cũ, để danh sách không nhảy lung tung.
        published_at = hien_co.published_at
        if data.status is PostStatus.PUBLISHED and published_at is None:
            published_at = _now()
        ban_moi = Post(
            post_id=hien_co.post_id,
            slug=hien_co.slug,
            title=tieu_de,
            summary=tom_tat,
            body=noi_dung,
            status=data.status,
            origin=hien_co.origin,
            source_name=nguon_ten,
            source_url=nguon_url,
            last_updated=data.last_updated,
            created_at=hien_co.created_at,
            updated_at=_now(),
            published_at=published_at,
        )
        self._repo.update(ban_moi)
        return ban_moi


class DeletePostUseCase(_PostUseCase):
    def execute(self, post_id: str) -> None:
        self._ensure_ready()
        if not self._repo.delete(post_id):
            raise PostNotFoundError(post_id)

"""Router CÔNG KHAI của bài viết — `/api/v1/posts`. Không cần đăng nhập.

Chỉ trả bài ĐÃ CÔNG KHAI. Bài nháp trả 404 y như bài không tồn tại (xem
`PostNotFoundError`), nên khách không dò được nội dung chưa duyệt.
Router MỎNG: không có luật nghiệp vụ nào ở đây.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.presentation.api.dependencies import Container, get_container
from src.presentation.api.envelope import success
from src.presentation.api.schemas_posts import POST_ERROR_RESPONSES, PostDetailData, PostListData

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostListData, responses=POST_ERROR_RESPONSES,
            summary="Danh sách bài viết đã công khai")
def list_posts(container: Container = Depends(get_container)):
    bai = container.list_published_posts.execute()
    return success({"posts": [b.to_public() for b in bai], "total": len(bai)})


@router.get("/{slug}", response_model=PostDetailData, responses=POST_ERROR_RESPONSES,
            summary="Một bài viết đã công khai, theo đường dẫn")
def get_post(slug: str, container: Container = Depends(get_container)):
    bai = container.get_published_post.execute(slug)
    return success({"post": bai.to_public()})

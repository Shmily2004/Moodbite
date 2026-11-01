"""Router QUẢN TRỊ của bài viết — `/api/v1/admin/posts/*`.

    GET    /api/v1/admin/posts?status=draft|published   mọi bài (kể cả nháp)
    POST   /api/v1/admin/posts                          tạo bài mới (mặc định là nháp)
    GET    /api/v1/admin/posts/{post_id}                một bài
    PUT    /api/v1/admin/posts/{post_id}                sửa (gửi đủ mọi trường)
    DELETE /api/v1/admin/posts/{post_id}                xoá

File RIÊNG thay vì thêm vào `routers/admin.py` (đã ~1000 dòng, CLAUDE.md mục 6). Xác thực
gắn ở CẤP ROUTER như `admin.router`, để endpoint thêm sau không thể quên.
Router MỎNG: kiểm và quy tắc nằm ở `domain/entities/post.py` và use case.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.application.use_cases.manage_posts import PostInput
from src.domain.entities.post import PostOrigin, PostStatus
from src.presentation.api.dependencies import Container, get_container, require_admin
from src.presentation.api.envelope import success
from src.presentation.api.schemas import MessageResponse
from src.presentation.api.schemas_posts import (
    POST_ERROR_RESPONSES,
    PostDetailData,
    PostListData,
    PostWriteRequest,
)

router = APIRouter(
    prefix="/admin/posts", tags=["admin"], dependencies=[Depends(require_admin)]
)


def _to_input(body: PostWriteRequest) -> PostInput:
    return PostInput(
        title=body.title,
        summary=body.summary,
        body=body.body,
        status=PostStatus(body.status),
        source_name=body.source_name,
        source_url=body.source_url,
        last_updated=body.last_updated,
        origin=PostOrigin.ADMIN,
    )


@router.get("", response_model=PostListData, responses=POST_ERROR_RESPONSES,
            summary="Mọi bài viết, kể cả nháp")
def list_posts(
    status: Optional[str] = Query(default=None, pattern="^(draft|published)$"),
    container: Container = Depends(get_container),
):
    loc = PostStatus(status) if status else None
    bai = container.list_all_posts.execute(loc)
    return success({"posts": [b.to_public() for b in bai], "total": len(bai)})


@router.post("", response_model=PostDetailData, status_code=201,
             responses=POST_ERROR_RESPONSES, summary="Tạo bài viết mới")
def create_post(body: PostWriteRequest, container: Container = Depends(get_container)):
    bai = container.create_post.execute(_to_input(body))
    return success({"post": bai.to_public()}, status_code=201)


@router.get("/{post_id}", response_model=PostDetailData, responses=POST_ERROR_RESPONSES,
            summary="Một bài viết (kể cả nháp)")
def get_post(post_id: str, container: Container = Depends(get_container)):
    return success({"post": container.get_post.execute(post_id).to_public()})


@router.put("/{post_id}", response_model=PostDetailData, responses=POST_ERROR_RESPONSES,
            summary="Sửa bài viết")
def update_post(
    post_id: str,
    body: PostWriteRequest,
    container: Container = Depends(get_container),
):
    bai = container.update_post.execute(post_id, _to_input(body))
    return success({"post": bai.to_public()})


@router.delete("/{post_id}", response_model=MessageResponse, responses=POST_ERROR_RESPONSES,
               summary="Xoá bài viết")
def delete_post(post_id: str, container: Container = Depends(get_container)):
    container.delete_post.execute(post_id)
    return success({"message": "Đã xoá bài viết."})


__all__ = ["router"]

"""Schema HTTP cho "Bài viết" (cẩm nang + tin cập nhật).

Chỉ KHAI BÁO KIỂU. Độ dài, nguồn bắt buộc, định dạng đường dẫn... kiểm ở domain
(`validate_post_fields`) để trả câu lỗi tiếng Việt đúng chỗ, không kiểm lặp ở đây.
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

POST_ERROR_RESPONSES = {
    400: {"description": "Dữ liệu bài viết không hợp lệ (INVALID_REQUEST)"},
    404: {"description": "Không có bài viết này (POST_NOT_FOUND)"},
    503: {"description": "Kho bài viết không sẵn sàng (DATA_NOT_READY)"},
}


class PostWriteRequest(BaseModel):
    """Admin gửi lên khi tạo hoặc sửa. KHÔNG có `origin`: bài tạo từ giao diện luôn là
    bài của admin; bài tổng hợp từ web chỉ đi qua script seed, không qua API."""

    title: str = ""
    summary: str = ""
    body: str = ""
    status: Literal["draft", "published"] = "draft"
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    last_updated: Optional[date] = Field(default=None, description="Ngày nội dung được cập nhật")


class PostListData(BaseModel):
    posts: list
    total: int


class PostDetailData(BaseModel):
    post: dict


__all__ = [
    "POST_ERROR_RESPONSES",
    "PostDetailData",
    "PostListData",
    "PostWriteRequest",
]

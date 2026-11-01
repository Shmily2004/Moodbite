"""BÀI VIẾT của MoodBite: cẩm nang ẩm thực Hà Nội và tin cập nhật. Thuần Python.

Hai nguồn gốc (`PostOrigin`), và VÌ SAO PHẢI PHÂN BIỆT:
  - `admin`: quản trị viên tự viết trên web. Chủ bài chịu trách nhiệm nội dung.
  - `web_sample`: tổng hợp từ bài viết công khai trên mạng. Đây là nội dung của người khác
    đã được viết lại, nên PHẢI ghi nguồn (`source_name`, `source_url`) và ngày lấy
    (`last_updated`) — CLAUDE.md mục 4b. Bản mới tạo luôn là NHÁP, admin duyệt rồi mới công
    khai. Không được đưa thẳng vào trang công khai.

Trạng thái `draft` (nháp) chỉ admin thấy. Chỉ `published` mới đi tới trang công khai.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional

from src.domain.errors import DomainValidationError


class InvalidPost(DomainValidationError):
    """Dữ liệu bài viết không hợp lệ -> HTTP 400."""


class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class PostOrigin(str, Enum):
    ADMIN = "admin"
    WEB_SAMPLE = "web_sample"


# Tiêu đề hiện trên thẻ danh sách, 120 ký tự vẫn vừa một dòng trên điện thoại.
MAX_TITLE_LENGTH = 120
# Tóm tắt hiện dưới tiêu đề trên thẻ; dài hơn thì thẻ phải cắt, người đọc không đọc hết.
MAX_SUMMARY_LENGTH = 300
# ~20.000 ký tự là một bài dài rất thoải mái. Chặn để một request không làm phình CSDL.
MAX_BODY_LENGTH = 20_000

SLUG_FALLBACK = "bai-viet"


def make_slug(title: str) -> str:
    """Đường dẫn thân thiện từ tiêu đề: bỏ dấu tiếng Việt, chữ thường, nối bằng `-`.

    `đ` không tách được bằng NFD nên đổi tay trước. Kết quả rỗng (tiêu đề toàn ký tự lạ)
    thì dùng `SLUG_FALLBACK` — use case sẽ thêm hậu tố số để không trùng.
    """
    chuan = unicodedata.normalize("NFD", title.replace("đ", "d").replace("Đ", "D"))
    khong_dau = "".join(c for c in chuan if unicodedata.category(c) != "Mn")
    slug = re.sub(r"[^a-z0-9]+", "-", khong_dau.lower()).strip("-")
    return slug or SLUG_FALLBACK


@dataclass(frozen=True)
class Post:
    post_id: str
    slug: str
    title: str
    summary: str
    body: str
    status: PostStatus
    origin: PostOrigin
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    last_updated: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    def to_public(self) -> dict:
        """Dạng trả cho client. Nguồn đi kèm MỌI bài, kể cả bài admin tự viết (có thể
        để trống), để người đọc biết nội dung từ đâu và độ mới tới đâu."""
        return {
            "post_id": self.post_id,
            "slug": self.slug,
            "title": self.title,
            "summary": self.summary,
            "body": self.body,
            "status": self.status.value,
            "origin": self.origin.value,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def validate_post_fields(
    *,
    title: str,
    summary: str,
    body: str,
    origin: PostOrigin,
    source_name: Optional[str],
    source_url: Optional[str],
) -> tuple[str, str, str, Optional[str], Optional[str]]:
    """Kiểm và làm sạch các trường. Trả về bộ đã làm sạch theo đúng thứ tự tham số.

    Dài quá thì BÁO LỖI, không tự cắt: người viết gõ gì thì phải thấy đúng cái đó được lưu.
    """
    tieu_de = " ".join((title or "").split())
    if not tieu_de:
        raise InvalidPost("Tiêu đề bài viết không được để trống.")
    if len(tieu_de) > MAX_TITLE_LENGTH:
        raise InvalidPost(f"Tiêu đề tối đa {MAX_TITLE_LENGTH} ký tự (đang có {len(tieu_de)}).")

    tom_tat = " ".join((summary or "").split())
    if len(tom_tat) > MAX_SUMMARY_LENGTH:
        raise InvalidPost(
            f"Tóm tắt tối đa {MAX_SUMMARY_LENGTH} ký tự (đang có {len(tom_tat)})."
        )

    noi_dung = (body or "").strip()
    if not noi_dung:
        raise InvalidPost("Nội dung bài viết không được để trống.")
    if len(noi_dung) > MAX_BODY_LENGTH:
        raise InvalidPost(
            f"Nội dung tối đa {MAX_BODY_LENGTH} ký tự (đang có {len(noi_dung)})."
        )

    nguon_ten = " ".join((source_name or "").split()) or None
    nguon_url = (source_url or "").strip() or None
    if nguon_url is not None and not nguon_url.startswith(("https://", "http://")):
        raise InvalidPost("Đường dẫn nguồn phải bắt đầu bằng http:// hoặc https://.")

    # Bài tổng hợp từ web KHÔNG có nguồn thì không được tồn tại: không ghi nguồn tức là
    # không biết nội dung từ đâu, không kiểm chứng được. Quy tắc này nằm ở domain để không
    # ai quên khi thêm đường vào mới.
    if origin is PostOrigin.WEB_SAMPLE and (nguon_ten is None or nguon_url is None):
        raise InvalidPost("Bài tổng hợp từ web phải ghi rõ tên nguồn và đường dẫn nguồn.")

    return tieu_de, tom_tat, noi_dung, nguon_ten, nguon_url


__all__ = [
    "InvalidPost",
    "MAX_BODY_LENGTH",
    "MAX_SUMMARY_LENGTH",
    "MAX_TITLE_LENGTH",
    "Post",
    "PostOrigin",
    "PostStatus",
    "make_slug",
    "validate_post_fields",
]

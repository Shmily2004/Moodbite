"""Quy tắc nghiệp vụ: admin được SỬA những trường nào, và sửa thế nào thì hợp lệ.

Thuần Python — không import framework, không đụng CSDL.

VÌ SAO LÀ QUY TẮC NGHIỆP VỤ CHỨ KHÔNG PHẢI VALIDATION CỦA HTTP:
"trường nào được sửa bằng tay" là một quyết định về DỮ LIỆU, không phải về giao thức.
Nếu để ở schema Pydantic thì mai kia có thêm CLI nhập liệu hay job import hàng loạt,
quy tắc này sẽ phải chép lại lần nữa — đúng kiểu lỗi hai nguồn sự thật mà CLAUDE.md
mục 1b cảnh báo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

# Trường admin ĐƯỢC sửa: đều là thông tin mô tả, người thật kiểm chứng được bằng cách
# gọi điện hoặc tới tận nơi.
EDITABLE_FIELDS = frozenset(
    {"name", "category", "cuisine", "address", "price", "phone", "website", "district"}
)

# Trường admin KHÔNG được sửa, kèm lý do trả về cho client để họ hiểu vì sao bị từ chối.
FORBIDDEN_FIELDS: Dict[str, str] = {
    "rating": "đến từ nguồn thu thập, sửa tay sẽ làm sai lệch số liệu đánh giá",
    "reviews_count": "đến từ nguồn thu thập",
    "mood_scores": "do data_pipeline tính, chạy lại pipeline sẽ ghi đè",
    "experience_cluster_id": "do bước phân cụm (Lớp 1) sinh ra",
    "experience_cluster_label": "do bước phân cụm (Lớp 1) sinh ra",
    "place_id": "là định danh, đổi sẽ làm đứt liên kết với dữ liệu chi tiết",
    "location": "toạ độ đến từ nguồn bản đồ",
    "is_active": "dùng endpoint hide/restore riêng để có thể ghi nhận rõ hành động",
}

# Giá là CHUỖI khoảng giá ("1-100.000 ₫"), KHÔNG phải số — xem CLAUDE.md mục 4 quy tắc 2.
_STRING_FIELDS = frozenset(EDITABLE_FIELDS)

MAX_FIELD_LENGTH = 500


class InvalidEditError(ValueError):
    """Yêu cầu sửa không hợp lệ -> HTTP 400 INVALID_REQUEST."""


@dataclass(frozen=True)
class RestaurantEdit:
    """Tập thay đổi ĐÃ được kiểm tra và chuẩn hoá."""

    changes: Mapping[str, Any]

    @staticmethod
    def from_dict(raw: Mapping[str, Any]) -> "RestaurantEdit":
        if not raw:
            raise InvalidEditError("Không có trường nào để sửa.")

        cleaned: Dict[str, Any] = {}
        for field, value in raw.items():
            if field in FORBIDDEN_FIELDS:
                raise InvalidEditError(
                    f"Không được sửa '{field}': {FORBIDDEN_FIELDS[field]}."
                )
            if field not in EDITABLE_FIELDS:
                raise InvalidEditError(
                    f"Trường '{field}' không sửa được. "
                    f"Các trường cho phép: {', '.join(sorted(EDITABLE_FIELDS))}."
                )

            # None = XOÁ giá trị, khác hẳn chuỗi rỗng. Giữ nguyên ý định đó.
            if value is None:
                cleaned[field] = None
                continue

            if field in _STRING_FIELDS and not isinstance(value, str):
                raise InvalidEditError(
                    f"Trường '{field}' phải là chuỗi, nhận được {type(value).__name__}. "
                    "Riêng 'price' là chuỗi khoảng giá kiểu \"1-100.000 ₫\", không phải số."
                )

            text = value.strip()
            if len(text) > MAX_FIELD_LENGTH:
                raise InvalidEditError(
                    f"Trường '{field}' dài quá {MAX_FIELD_LENGTH} ký tự."
                )
            # Chuỗi rỗng sau khi cắt khoảng trắng = ý muốn xoá giá trị -> None, để không
            # sinh ra ô "" vừa không phải thiếu dữ liệu vừa không phải giá trị thật.
            cleaned[field] = text or None

        if cleaned.get("name", "") is None and "name" in cleaned:
            raise InvalidEditError("Tên quán không được để trống.")

        return RestaurantEdit(changes=cleaned)


__all__ = [
    "RestaurantEdit",
    "InvalidEditError",
    "EDITABLE_FIELDS",
    "FORBIDDEN_FIELDS",
]

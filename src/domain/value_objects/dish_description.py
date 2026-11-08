"""Quy tắc cho MÔ TẢ MÓN do quản trị viên sửa tay. Thuần Python.

VÌ SAO CẦN: trước đây trang quản trị món chỉ đọc, vì `dish_catalog.json` do script sinh ra và
sẽ bị ghi đè. Nay bản sửa tay nằm ở một bảng riêng (`dish_overrides`) và được đọc chồng lên
danh mục gốc. Quy tắc "chuỗi rỗng = gỡ bản sửa" và giới hạn độ dài nằm ở đây, không ở router.
"""
from __future__ import annotations

from typing import Optional

from src.domain.errors import DomainValidationError

# 1000 ký tự: đủ cho một đoạn giới thiệu (mô tả Wikipedia thường dưới 400), đủ chặn việc
# dán nguyên một bài báo vào ô mô tả món.
DESCRIPTION_MAX_LENGTH = 1000


def chuan_hoa_mo_ta(text: Optional[str]) -> Optional[str]:
    """Trả về mô tả đã cắt khoảng trắng, hoặc None nếu phải GỠ bản sửa.

    `None` và chuỗi toàn khoảng trắng đều nghĩa là "không còn bản sửa, dùng lại mô tả gốc".
    Quá dài -> DomainValidationError (router đổi thành 400).
    """
    if text is None:
        return None
    cleaned = text.strip()
    if not cleaned:
        return None
    if len(cleaned) > DESCRIPTION_MAX_LENGTH:
        raise DomainValidationError(
            f"Mô tả dài {len(cleaned)} ký tự, tối đa {DESCRIPTION_MAX_LENGTH}."
        )
    return cleaned

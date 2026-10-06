"""Lỗi gốc của tầng domain. Thuần Python.

VÌ SAO CÓ FILE NÀY (thêm 2026-10-06, sau rà soát bảo mật):
trước đó `error_handlers.py` bắt MỌI `ValueError` rồi trả 400 INVALID_REQUEST. Các lỗi
kiểm dữ liệu của domain (`InvalidEmailFormat`, `InvalidCollection`...) đều kế thừa
`ValueError` nên "chạy được" — nhưng cùng lúc, một `int("abc")` lỡ tay trong code, một
`ValueError` từ thư viện, cũng thành "400 lỗi của bạn". Bug lập trình bị đổ lên đầu client,
không ai ghi traceback, đúng cái CLAUDE.md mục 5 cấm.

Nay: lỗi kiểm dữ liệu CÓ CHỦ ĐÍCH phải kế thừa `DomainValidationError`, và chỉ lớp này
được ánh xạ sang 400. `ValueError` trần -> 500 INTERNAL_ERROR kèm traceback trong log.

Vẫn kế thừa `ValueError` để mọi chỗ đang `except ValueError` (và mọi test đang
`pytest.raises(ValueError)`) không đổi hành vi.
"""
from __future__ import annotations


class DomainValidationError(ValueError):
    """Dữ liệu đầu vào vi phạm một quy tắc nghiệp vụ -> HTTP 400 INVALID_REQUEST.

    Thông điệp của lỗi này ĐƯỢC trả nguyên cho client, nên chỉ viết câu dành cho người
    dùng đọc — không nhét chi tiết nội bộ (đường dẫn, câu SQL, tên biến) vào đây.
    """


__all__ = ["DomainValidationError"]

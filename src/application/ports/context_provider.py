"""PORT: hợp đồng lấy tín hiệu ngữ cảnh thời điểm (giờ, thời tiết).

Đề án mục 4: các tín hiệu này KHÔNG lưu tĩnh mà gọi tại thời điểm tìm kiếm.

Quy tắc quan trọng: lấy tín hiệu THẤT BẠI không được làm hỏng lượt tìm kiếm. Trả về ngữ
cảnh trung lập là đủ - người dùng vẫn nhận được kết quả, chỉ là không có ưu tiên theo
thời tiết.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.value_objects.context_signal import ContextSignal
from src.domain.value_objects.location import Location


@runtime_checkable
class ContextProvider(Protocol):
    def get_context(self, location: Location) -> ContextSignal:
        """Ngữ cảnh hiện tại tại vị trí đó. KHÔNG được ném exception ra ngoài -
        lỗi mạng phải tự xử lý và trả ngữ cảnh trung lập."""
        ...

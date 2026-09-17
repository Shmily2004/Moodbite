"""PORT: hợp đồng GHI sự kiện tương tác.

Hiện lưu vào file JSONL. Khi chuyển sang PostgreSQL chỉ cần viết adapter mới, use case
không đổi một dòng nào.
"""
from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from src.domain.entities.interaction import InteractionEvent
from src.domain.services.interaction_stats import BanGhiTuongTac


@runtime_checkable
class InteractionRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        ...

    def append(self, event: InteractionEvent) -> str:
        """Ghi 1 sự kiện, trả về id của bản ghi."""
        ...

    def read_records(self) -> List[BanGhiTuongTac]:
        """ĐỌC toàn bộ nhật ký dưới dạng bản ghi thống kê — cho màn Tổng quan quản trị.

        Dòng hỏng phải bị BỎ QUA chứ không ném lỗi: một dòng ghi dở không được làm trắng
        trang quản trị. Chỉ gọi từ luồng quản trị (thưa), không bao giờ ở luồng tìm kiếm.
        """
        ...

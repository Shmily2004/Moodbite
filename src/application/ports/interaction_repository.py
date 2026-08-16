"""PORT: hợp đồng GHI sự kiện tương tác.

Hiện lưu vào file JSONL. Khi chuyển sang PostgreSQL chỉ cần viết adapter mới, use case
không đổi một dòng nào.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.entities.interaction import InteractionEvent


@runtime_checkable
class InteractionRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        ...

    def append(self, event: InteractionEvent) -> str:
        """Ghi 1 sự kiện, trả về id của bản ghi."""
        ...

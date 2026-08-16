"""PORT: hợp đồng đoán rule_id món ăn bằng ML.

Trả None nghĩa là "không đoán được" -> tầng gọi tự fallback về khớp rule theo từ khoá.
Đây là cơ chế tuỳ chọn: hệ thống PHẢI chạy được bình thường khi không có model nào.
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class RulePredictor(Protocol):
    @property
    def is_available(self) -> bool:
        """False khi không có model - tầng gọi bỏ qua ML hoàn toàn."""
        ...

    def predict_rule_id(
        self, category: Optional[str], cuisine: Optional[str] = None
    ) -> Optional[str]:
        ...

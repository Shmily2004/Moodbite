"""Sự kiện tương tác của người dùng - NGUỒN NHÃN cho mô hình xếp hạng học có giám sát.

Đề án (Lớp 3) nói xếp hạng nên là mô hình học, không phải công thức trọng số cố định.
Muốn học thì phải có nhãn: "với tập tín hiệu này, người dùng đã thực sự chọn quán nào".
Đó là lý do phải ghi tương tác NGAY TỪ BÂY GIỜ, dù mô hình học chưa tồn tại - không ghi
sớm thì sau này không có dữ liệu để huấn luyện.

Thuần Python - KHÔNG import framework.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ActionType(str, Enum):
    VIEW_DETAIL = "view_detail"
    GET_DIRECTIONS = "get_directions"
    SAVE = "save"
    EXPLICIT_POSITIVE = "explicit_positive"
    EXPLICIT_NEGATIVE = "explicit_negative"


# Ngưỡng coi là "xem thật" thay vì bấm nhầm rồi thoát ngay.
MIN_POSITIVE_DWELL_MS = 3000


@dataclass(frozen=True)
class InteractionEvent:
    session_id: str
    restaurant_id: str
    action_type: ActionType
    search_query_id: Optional[str] = None
    dwell_time_ms: Optional[int] = None
    rank_position: Optional[int] = None

    @property
    def is_positive_signal(self) -> bool:
        """Tính Ở SERVER, không để client tự quyết.

        Client tự suy luận sẽ dẫn tới nhiều cách hiểu khác nhau về cùng một hành vi, và
        nhãn huấn luyện sẽ nhiễu. Giữ đúng một nguồn sự thật (đặc tả API mục 3.4).
        """
        if self.action_type == ActionType.EXPLICIT_NEGATIVE:
            return False
        if self.action_type in (
            ActionType.GET_DIRECTIONS,
            ActionType.SAVE,
            ActionType.EXPLICIT_POSITIVE,
        ):
            return True
        # view_detail chỉ tính là tín hiệu tốt nếu người dùng ở lại đủ lâu.
        if self.action_type == ActionType.VIEW_DETAIL:
            return (self.dwell_time_ms or 0) >= MIN_POSITIVE_DWELL_MS
        return False

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
    # Người dùng báo quán ĐÃ ĐÓNG CỬA. Tách riêng khỏi `explicit_negative` vì hai chuyện
    # khác hẳn nhau: "tôi không thích quán này" là ý kiến cá nhân và là nhãn huấn luyện
    # hợp lệ; "quán này không còn tồn tại" là khẳng định về THỰC TẾ và phải làm quán biến
    # mất với MỌI người. Gộp chung thì hoặc là chê một câu cũng xoá quán, hoặc là báo đóng
    # cửa chẳng có tác dụng gì.
    REPORT_CLOSED = "report_closed"


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
    # TUỲ CHỌN — chỉ có khi người dùng ĐÃ ĐĂNG NHẬP.
    #
    # Vì sao không dùng `session_id` thay thế: session_id là mã ngẫu nhiên của một tab
    # trình duyệt, đổi mỗi lần xoá dữ liệu. Đếm theo nó thì "số quán đã khám phá" của một
    # người bị chia nhỏ ra hàng chục phiên và không bao giờ cộng lại được. Đó chính là lý
    # do trước 2026-08-22 không thể làm được cấp độ/huy hiệu.
    #
    # ⚠️ Giá trị này do SERVER đặt từ token đăng nhập, KHÔNG lấy từ body request. Để client
    # tự khai `user_id` là để bất kỳ ai cũng cộng điểm cho người khác — hoặc cho chính
    # mình bằng cách gọi thẳng API.
    user_id: Optional[str] = None

    @property
    def is_positive_signal(self) -> bool:
        """Tính Ở SERVER, không để client tự quyết.

        Client tự suy luận sẽ dẫn tới nhiều cách hiểu khác nhau về cùng một hành vi, và
        nhãn huấn luyện sẽ nhiễu. Giữ đúng một nguồn sự thật (đặc tả API mục 3.4).
        """
        if self.action_type in (ActionType.EXPLICIT_NEGATIVE, ActionType.REPORT_CLOSED):
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

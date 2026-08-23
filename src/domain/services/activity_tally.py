"""Đếm hoạt động của TỪNG NGƯỜI DÙNG để tính điểm/cấp độ/huy hiệu.

VÌ SAO PHẢI CÓ FILE NÀY
-----------------------
Trước 2026-08-22, `POST /interactions` chỉ ghi `session_id` — một mã ngẫu nhiên của tab
trình duyệt, đổi mỗi lần xoá dữ liệu. Vì vậy KHÔNG có cách nào đếm được "người này đã
khám phá bao nhiêu quán". Đó chính là lý do bốn con số trên bản thiết kế trang tài khoản
(27 · 15 · 18 · 5) không thể dựng được, và cũng là thứ đầu tiên phải sửa để làm cấp độ.
Nay `InteractionEvent` có thêm `user_id` (tuỳ chọn) và file này đếm theo trường đó.

CÁCH LƯU: GIỮ TRONG BỘ NHỚ, DỰNG LẠI TỪ NHẬT KÝ LÚC KHỞI ĐỘNG.
Giống hệt `ClosureReportTally` và vì cùng một lý do: `interactions.jsonl` vốn đã ghi mọi
tương tác, thêm một kho lưu trữ thứ hai cho cùng dữ liệu là tự tạo ra hai nguồn sự thật.
Đọc lại file ở MỖI request thì càng dùng càng chậm — nhật ký chỉ dài thêm chứ không ngắn
đi bao giờ.

ĐẾM THỨ KHÁC NHAU, KHÔNG ĐẾM SỐ LẦN. Xem cùng một quán 30 lần vẫn là 1. Lý do đầy đủ ở
`gamification.py` nguyên tắc 2.

THUẦN PYTHON — đây là quy tắc "cái gì được tính là một lượt khám phá", không phải chuyện
lưu trữ.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Optional, Set

from src.domain.entities.interaction import (
    MIN_POSITIVE_DWELL_MS,
    ActionType,
)
from src.domain.services.gamification import UserActivity


class ActivityTally:
    """Bộ đếm hoạt động theo `user_id`.

    Khách chưa đăng nhập (`user_id` rỗng) bị BỎ QUA hoàn toàn: không có tài khoản thì
    không có cấp độ, và gom hoạt động của mọi khách vào một rổ chung là vô nghĩa.
    """

    __slots__ = ("_viewed", "_directions", "_ratings", "_closures", "_days")

    def __init__(self) -> None:
        # user_id -> tập restaurant_id KHÁC NHAU
        self._viewed: Dict[str, Set[str]] = defaultdict(set)
        self._directions: Dict[str, Set[str]] = defaultdict(set)
        self._ratings: Dict[str, Set[str]] = defaultdict(set)
        self._closures: Dict[str, Set[str]] = defaultdict(set)
        # user_id -> tập NGÀY (chuỗi 'YYYY-MM-DD') có hoạt động
        self._days: Dict[str, Set[str]] = defaultdict(set)

    def record(
        self,
        user_id: Optional[str],
        action_type: ActionType,
        restaurant_id: str,
        day: Optional[str] = None,
        dwell_time_ms: Optional[int] = None,
    ) -> None:
        """Ghi nhận một tương tác. Gọi được nhiều lần với cùng dữ liệu mà không sai số."""
        if not user_id or not restaurant_id:
            return

        if day:
            self._days[user_id].add(day)

        if action_type == ActionType.VIEW_DETAIL:
            # Chỉ tính là "đã khám phá" khi người dùng ở lại đủ lâu — cùng ngưỡng mà
            # `InteractionEvent.is_positive_signal` dùng. Bấm nhầm rồi thoát ngay không
            # phải là khám phá, và nếu tính thì lướt nhanh 50 quán là lên cấp.
            if (dwell_time_ms or 0) >= MIN_POSITIVE_DWELL_MS:
                self._viewed[user_id].add(restaurant_id)
        elif action_type == ActionType.GET_DIRECTIONS:
            self._directions[user_id].add(restaurant_id)
        elif action_type in (ActionType.EXPLICIT_POSITIVE, ActionType.EXPLICIT_NEGATIVE):
            self._ratings[user_id].add(restaurant_id)
        elif action_type == ActionType.REPORT_CLOSED:
            self._closures[user_id].add(restaurant_id)
        # ActionType.SAVE cố tình KHÔNG tính ở đây: lượt lưu đếm từ bảng `saved_items`
        # (nguồn sự thật của "đang lưu"), nếu không thì lưu rồi bỏ lưu vẫn còn điểm.

    def snapshot(self, user_id: str, saved_items: int = 0) -> UserActivity:
        """Số liệu hiện tại của một người.

        `saved_items` truyền TỪ NGOÀI vào vì nó nằm ở bảng `saved_items`, không nằm trong
        nhật ký. Tally không đi đọc kho khác — nó là domain, không biết kho nào tồn tại.
        """
        return UserActivity(
            viewed_restaurants=len(self._viewed.get(user_id, ())),
            directions=len(self._directions.get(user_id, ())),
            saved_items=max(0, int(saved_items)),
            ratings=len(self._ratings.get(user_id, ())),
            closure_reports=len(self._closures.get(user_id, ())),
            active_days=len(self._days.get(user_id, ())),
        )

    @property
    def tracked_users(self) -> int:
        """Số tài khoản đã có ít nhất một hoạt động. Dùng cho /health."""
        return len(self._days)

    def status(self) -> dict:
        return {"ready": True, "tracked_users": self.tracked_users}


__all__ = ["ActivityTally"]

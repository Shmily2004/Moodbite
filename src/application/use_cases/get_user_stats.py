"""USE CASE: số liệu hoạt động + cấp độ + huy hiệu của MỘT người dùng.

Chỉ điều phối: lấy số đếm từ hai nguồn (bộ đếm tương tác + kho yêu thích) rồi giao cho
`domain/services/gamification.py` tính điểm, cấp và huy hiệu. Không có công thức nào ở
đây — công thức là quy tắc nghiệp vụ và phải nằm ở domain (CLAUDE.md mục 2).

⚠️ KHÔNG BAO GIỜ BỊA SỐ. Chưa có hoạt động nào thì trả về 0 thật, và giao diện hiện 0.
Bản thiết kế vẽ sẵn "27 · 15 · 18 · 5"; chép mấy con số đó vào là nói dối người dùng.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.application.ports.saved_item_repository import SavedItemRepository
from src.domain.entities.saved_item import SavedItemType
from src.domain.services.activity_tally import ActivityTally
from src.domain.services.gamification import (
    BadgeProgress,
    LevelProgress,
    UserActivity,
    tinh_cap_do,
    tinh_huy_hieu,
)


@dataclass(frozen=True)
class UserStats:
    activity: UserActivity
    level: LevelProgress
    badges: List[BadgeProgress]
    saved_restaurants: int
    saved_dishes: int


class GetUserStatsUseCase:
    def __init__(
        self,
        activity_tally: ActivityTally,
        saved_items: Optional[SavedItemRepository] = None,
    ) -> None:
        self._tally = activity_tally
        # Cho phép None để test nào không quan tâm tới yêu thích khỏi phải dựng kho.
        self._saved = saved_items

    def execute(self, user_id: str) -> UserStats:
        quan = dishes = 0
        if self._saved is not None and self._saved.is_ready:
            quan = self._saved.count_for_user(user_id, SavedItemType.RESTAURANT)
            dishes = self._saved.count_for_user(user_id, SavedItemType.DISH)

        activity = self._tally.snapshot(user_id, saved_items=quan + dishes)
        return UserStats(
            activity=activity,
            level=tinh_cap_do(activity.points),
            badges=tinh_huy_hieu(activity),
            saved_restaurants=quan,
            saved_dishes=dishes,
        )


__all__ = ["GetUserStatsUseCase", "UserStats"]

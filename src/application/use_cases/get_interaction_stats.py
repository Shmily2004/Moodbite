"""USE CASE: số liệu khối "Hệ thống gợi ý" ở màn Tổng quan quản trị.

Chỉ ĐIỀU PHỐI: đọc bản ghi qua port `InteractionRepository.read_records()` rồi giao cho
`domain/services/interaction_stats.py` đếm.

KHO HỎNG KHÔNG LÀM TRẮNG MÀN TỔNG QUAN. Kho không có `read_records` (bản giả trong test cũ)
hoặc đọc lỗi -> trả `available=False`, giao diện nói "không đọc được nhật ký" thay vì
hiện 0 lượt như thể chưa ai dùng. Hai tình huống đó dẫn tới hai hành động khác nhau.

Vì sao không có CTR: xem docstring `interaction_stats.py` — dự án không ghi lượt hiển thị.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Callable, Optional

from src.domain.services.interaction_stats import ThongKeTuongTac, thong_ke_tuong_tac

logger = logging.getLogger("moodbite.admin")


@dataclass(frozen=True)
class KetQuaThongKeTuongTac:
    available: bool
    thong_ke: Optional[ThongKeTuongTac]


class GetInteractionStatsUseCase:
    def __init__(
        self,
        interaction_repository,
        hom_nay: Optional[Callable[[], date]] = None,
    ) -> None:
        self._repo = interaction_repository
        # Ngày UTC, cùng múi với `created_at` adapter đóng dấu — lệch múi thì lượt lúc
        # 6 giờ sáng giờ Hà Nội sẽ rơi sang "hôm qua" trên biểu đồ.
        self._hom_nay = hom_nay or (lambda: datetime.now(timezone.utc).date())

    def execute(self) -> KetQuaThongKeTuongTac:
        doc = getattr(self._repo, "read_records", None)
        if self._repo is None or not callable(doc):
            return KetQuaThongKeTuongTac(available=False, thong_ke=None)
        try:
            ban_ghi = doc()
        except Exception as exc:  # noqa: BLE001 - xem docstring đầu file
            logger.warning("Không đọc được nhật ký tương tác cho trang quản trị: %s", exc)
            return KetQuaThongKeTuongTac(available=False, thong_ke=None)
        return KetQuaThongKeTuongTac(
            available=True, thong_ke=thong_ke_tuong_tac(ban_ghi, self._hom_nay())
        )


__all__ = ["GetInteractionStatsUseCase", "KetQuaThongKeTuongTac"]

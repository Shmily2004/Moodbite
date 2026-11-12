"""USE CASE quản trị: hàng chờ "quán bị khách báo đóng cửa" (UC21 trong biểu đồ).

Theo biểu đồ `UC21_xem_xet_bao_dong_cua`: quản trị mở danh sách, kiểm tra, rồi quyết định.
Quán thật sự đã đóng -> ẩn quán (`hide_restaurant`); không thì gỡ lượt báo. Lượt báo của
khách KHÔNG tự ẩn quán (đổi từ 2026-11-12, xem `domain/services/closure_reports.py`).

VÌ SAO CẦN (rà soát 2026-10-06): trước file này admin KHÔNG có cách nào bỏ ẩn một quán bị
ẩn vì lượt báo:
  - `ClosureReportTally` không có hàm xoá;
  - nút "Khôi phục" chỉ đặt `is_active=1` — mà quán bị báo vẫn đang `is_active=1`;
  - lượt báo được phát lại từ `interactions.jsonl` mỗi lần khởi động.
Kết hợp với việc lượt báo từng giả mạo được (đếm theo session_id do client đặt), một
người là đủ ẩn VĨNH VIỄN bất kỳ quán nào.

Chỉ ĐIỀU PHỐI: quy tắc đếm nằm ở `domain/services/closure_reports.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.application.errors import DataNotReadyError
from src.application.ports.closure_report_log import ClosureReportLog
from src.application.ports.restaurant_repository import RestaurantRepository
from src.application.use_cases.log_interaction import RestaurantNotFoundError
from src.domain.services.closure_reports import ClosureReportTally


@dataclass(frozen=True)
class ClosureReportRow:
    restaurant_id: str
    # `None` = quán không còn trong dữ liệu (đã bị xoá khỏi dataset). KHÔNG bịa tên.
    name: Optional[str]
    report_count: int
    # Quán ĐANG bị quản trị ẩn (`is_active=0`). Lượt báo không đặt cờ này nữa.
    is_hidden: bool


@dataclass(frozen=True)
class ClearedClosureReports:
    restaurant_id: str
    cleared_reports: int
    # Gỡ lượt báo KHÔNG đổi trạng thái ẩn của quán. Trả về trạng thái thật để client khỏi
    # tự suy luận.
    is_hidden: bool


def _tra_quan(restaurant_id: str, restaurants, admin_restaurants):
    """Quán (kể cả quán admin đã ẩn), hoặc None nếu không còn trong dữ liệu."""
    quan = restaurants.get_by_place_id(restaurant_id) if restaurants is not None else None
    if quan is None and admin_restaurants is not None:
        quan = admin_restaurants.get_for_admin(restaurant_id)
    return quan


class ListClosureReportsUseCase:
    """Hàng chờ: quán nào đang bị báo, bao nhiêu người báo, đã bị admin ẩn chưa."""

    def __init__(
        self,
        tally: ClosureReportTally,
        restaurants: Optional[RestaurantRepository] = None,
        admin_restaurants: Optional[object] = None,
    ) -> None:
        self._tally = tally
        self._restaurants = restaurants
        self._admin_restaurants = admin_restaurants

    def execute(self) -> List[ClosureReportRow]:
        rows = []
        for place_id, so in self._tally.reported_counts().items():
            quan = _tra_quan(place_id, self._restaurants, self._admin_restaurants)
            rows.append(ClosureReportRow(
                restaurant_id=place_id,
                name=quan.name if quan is not None else None,
                report_count=so,
                is_hidden=quan is not None and not quan.is_visible,
            ))
        # Quán CHƯA XỬ LÝ lên đầu (admin còn phải quyết định); rồi theo số người báo giảm
        # dần, cuối cùng theo mã để thứ tự ổn định giữa các lần tải trang.
        rows.sort(key=lambda r: (r.is_hidden, -r.report_count, r.restaurant_id))
        return rows


class ClearClosureReportsUseCase:
    """Admin gỡ MỌI lượt báo đóng cửa của một quán.

    THỨ TỰ BẮT BUỘC: ghi nhật ký -> xoá bộ đếm trong RAM -> ghi nhật ký quản trị.
    Ngược lại (xoá RAM trước) mà ghi đĩa hỏng thì quán hiện lại NGAY nhưng ẩn lại sau lần
    khởi động kế tiếp — admin tưởng đã xong mà không phải. Cùng nguyên tắc với
    `LogInteractionUseCase`: bộ đếm phải luôn dựng lại được từ nhật ký trên đĩa.
    """

    def __init__(
        self,
        tally: ClosureReportTally,
        log: ClosureReportLog,
        restaurants: Optional[RestaurantRepository] = None,
        admin_restaurants: Optional[object] = None,
        audit: Optional[object] = None,
    ) -> None:
        self._tally = tally
        self._log = log
        self._restaurants = restaurants
        self._admin_restaurants = admin_restaurants
        # `GhiNhatKyUseCase` — tuỳ chọn, và tự nuốt lỗi của chính nó (xem
        # `manage_audit_log.py`): mất một dòng nhật ký không được làm hỏng thao tác gỡ.
        self._audit = audit

    def execute(self, restaurant_id: str, actor: str) -> ClearedClosureReports:
        ma = (restaurant_id or "").strip()
        so_nguoi_bao = self._tally.report_count(ma)
        quan = _tra_quan(ma, self._restaurants, self._admin_restaurants)
        ten = quan.name if quan is not None else None
        # 404 chỉ khi KHÔNG có cả quán lẫn lượt báo. Quán đã bị xoá khỏi dataset nhưng
        # còn lượt báo treo thì vẫn phải gỡ được, nếu không danh sách "đang bị báo" có
        # dòng không bao giờ dọn nổi.
        if quan is None and so_nguoi_bao == 0:
            raise RestaurantNotFoundError(ma)

        if not getattr(self._log, "is_ready", False):
            raise DataNotReadyError(
                "nhật ký tương tác không ghi được",
                "kiểm tra quyền ghi ở đường dẫn MOODBITE_INTERACTIONS rồi thử lại",
            )
        self._log.append_closure_reports_cleared(ma, actor=actor)
        da_go = self._tally.clear(ma)

        if self._audit is not None:
            self._audit.ghi(
                actor=actor,
                action="clear_closure_reports",
                target_type="restaurant",
                target_id=ma,
                summary=(
                    f'Gỡ {da_go} lượt báo đóng cửa của "{ten}"' if ten
                    else f"Gỡ {da_go} lượt báo đóng cửa (quán không còn trong dữ liệu)"
                ),
            )
        return ClearedClosureReports(
            restaurant_id=ma,
            cleared_reports=da_go,
            is_hidden=quan is not None and not quan.is_visible,
        )


__all__ = [
    "ClosureReportRow",
    "ClearedClosureReports",
    "ListClosureReportsUseCase",
    "ClearClosureReportsUseCase",
]

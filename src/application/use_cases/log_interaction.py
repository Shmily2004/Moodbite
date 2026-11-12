"""USE CASE: ghi nhận tương tác của người dùng (đặc tả API mục 3.4).

Đây là bước chuẩn bị cho mô hình xếp hạng học có giám sát ở giai đoạn sau. Không có dữ
liệu này thì mãi mãi phải dùng công thức trọng số cố định.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.application.errors import ApplicationError
from src.application.ports.interaction_repository import InteractionRepository
from src.application.ports.restaurant_repository import RestaurantRepository
from src.domain.entities.interaction import ActionType, InteractionEvent
from src.domain.services.activity_tally import ActivityTally
from src.domain.services.closure_reports import ClosureReportTally

logger = logging.getLogger("moodbite.interactions")


class RestaurantNotFoundError(ApplicationError):
    """restaurant_id không tồn tại hoặc đã bị ẩn (is_active=false) -> HTTP 404."""

    def __init__(self, restaurant_id: str) -> None:
        # Nhận MÃ QUÁN, không nhận câu thông báo: câu đã ghép sẵn ở đây. Từng có 5 chỗ gọi
        # truyền "Không tìm thấy quán: <id>" vào -> message lặp chữ và `details.restaurant_id`
        # chứa cả câu (sửa 2026-10-13).
        super().__init__(f"Không tìm thấy nhà hàng: {restaurant_id}")
        self.restaurant_id = restaurant_id


class InvalidInteractionError(ApplicationError):
    """Dữ liệu tương tác không hợp lệ -> HTTP 400."""


@dataclass(frozen=True)
class LogInteractionCommand:
    session_id: str
    restaurant_id: str
    action_type: str
    search_query_id: Optional[str] = None
    dwell_time_ms: Optional[int] = None
    rank_position: Optional[int] = None
    # Do ROUTER lấy từ token đăng nhập rồi truyền vào, KHÔNG lấy từ body request —
    # xem ghi chú ở `domain/entities/interaction.py`.
    user_id: Optional[str] = None
    # Khoá NGƯỜI BÁO cho `report_closed`, do router tính từ IP đã băm — KHÔNG lấy từ body,
    # cùng lý do với `user_id`. `None` (lời gọi không qua HTTP: script, test) thì lượt báo
    # vẫn được GHI vào nhật ký nhưng KHÔNG được đếm để ẩn quán: không xác minh được ai báo
    # thì không được phép làm một quán biến mất với mọi người.
    reporter_key: Optional[str] = None


@dataclass(frozen=True)
class LoggedInteraction:
    interaction_event_id: str
    is_positive_signal: bool


class LogInteractionUseCase:
    def __init__(
        self,
        interactions: InteractionRepository,
        restaurants: RestaurantRepository,
        closure_tally: Optional[ClosureReportTally] = None,
        activity_tally: Optional[ActivityTally] = None,
    ) -> None:
        self._interactions = interactions
        self._restaurants = restaurants
        # Không bắt buộc: bộ test nào không quan tâm tới báo đóng cửa thì bỏ trống được,
        # và use case vẫn ghi tương tác bình thường.
        self._closure_tally = closure_tally
        # Cũng không bắt buộc, cùng lý do. Đây là bộ đếm "lượt khám phá" cho cấp độ.
        self._activity_tally = activity_tally

    def execute(self, command: LogInteractionCommand) -> LoggedInteraction:
        try:
            action = ActionType(command.action_type)
        except ValueError:
            raise InvalidInteractionError(
                f"action_type '{command.action_type}' không hợp lệ. "
                f"Hợp lệ: {[a.value for a in ActionType]}"
            )

        # dwell_time_ms bắt buộc với view_detail, vì nếu không có thì không phân biệt được
        # "xem thật" với "bấm nhầm rồi thoát" - nhãn huấn luyện sẽ sai.
        if action == ActionType.VIEW_DETAIL and command.dwell_time_ms is None:
            raise InvalidInteractionError(
                "Thiếu dwell_time_ms - bắt buộc khi action_type = view_detail."
            )

        if not command.session_id:
            raise InvalidInteractionError("Thiếu session_id.")

        # Chỉ ghi tương tác cho quán có thật, nếu không dữ liệu huấn luyện sẽ có nhãn rác.
        if self._restaurants.is_ready:
            restaurant = self._restaurants.get_by_place_id(command.restaurant_id)
            if restaurant is None or not restaurant.is_visible:
                raise RestaurantNotFoundError(command.restaurant_id)

        la_bao_dong_cua = action == ActionType.REPORT_CLOSED
        event = InteractionEvent(
            session_id=command.session_id,
            restaurant_id=command.restaurant_id,
            action_type=action,
            search_query_id=command.search_query_id,
            dwell_time_ms=command.dwell_time_ms,
            rank_position=command.rank_position,
            user_id=command.user_id,
            # Chỉ lượt báo đóng cửa mới mang khoá người báo — xem `InteractionEvent`.
            reporter_key=command.reporter_key if la_bao_dong_cua else None,
        )
        event_id = self._interactions.append(event)

        # GHI VÀO NHẬT KÝ TRƯỚC, cập nhật bộ đếm SAU.
        # Ngược lại thì một lần ghi file hỏng sẽ để lại lượt báo chỉ tồn tại trong RAM:
        # quán bị ẩn ngay bây giờ nhưng hiện lại sau khi khởi động lại, và không ai truy
        # được vì sao. Bộ đếm phải luôn dựng lại được từ nhật ký.
        #
        # ĐẾM THEO `reporter_key`, KHÔNG theo `session_id` (sửa 2026-10-06): session_id do
        # client tự đặt, 3 session_id bịa từng đủ ẩn bất kỳ quán nào. Xem
        # `domain/services/closure_reports.py`.
        if la_bao_dong_cua and self._closure_tally is not None:
            if command.reporter_key:
                so_nguoi = self._closure_tally.record(
                    command.restaurant_id, command.reporter_key
                )
                logger.info(
                    "Quán %s được báo đã đóng cửa (%d người báo, chờ quản trị xem xét)",
                    command.restaurant_id, so_nguoi,
                )
            else:
                logger.warning(
                    "Lượt báo đóng cửa quán %s không có khoá người báo -> chỉ ghi nhật "
                    "ký, KHÔNG đếm để ẩn quán.", command.restaurant_id,
                )

        # Cộng vào bộ đếm hoạt động SAU khi đã ghi nhật ký, cùng lý do như bộ đếm đóng
        # cửa ở trên: bộ đếm trong RAM phải luôn dựng lại được từ nhật ký trên đĩa.
        # Khách chưa đăng nhập (`user_id` rỗng) thì tally tự bỏ qua.
        if self._activity_tally is not None:
            self._activity_tally.record(
                user_id=command.user_id,
                action_type=action,
                restaurant_id=command.restaurant_id,
                day=datetime.now(timezone.utc).date().isoformat(),
                dwell_time_ms=command.dwell_time_ms,
            )

        return LoggedInteraction(
            interaction_event_id=event_id,
            is_positive_signal=event.is_positive_signal,
        )

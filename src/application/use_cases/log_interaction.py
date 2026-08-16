"""USE CASE: ghi nhận tương tác của người dùng (đặc tả API mục 3.4).

Đây là bước chuẩn bị cho mô hình xếp hạng học có giám sát ở giai đoạn sau. Không có dữ
liệu này thì mãi mãi phải dùng công thức trọng số cố định.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.application.errors import ApplicationError
from src.application.ports.interaction_repository import InteractionRepository
from src.application.ports.restaurant_repository import RestaurantRepository
from src.domain.entities.interaction import ActionType, InteractionEvent


class RestaurantNotFoundError(ApplicationError):
    """restaurant_id không tồn tại hoặc đã bị ẩn (is_active=false) -> HTTP 404."""

    def __init__(self, restaurant_id: str) -> None:
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


@dataclass(frozen=True)
class LoggedInteraction:
    interaction_event_id: str
    is_positive_signal: bool


class LogInteractionUseCase:
    def __init__(
        self,
        interactions: InteractionRepository,
        restaurants: RestaurantRepository,
    ) -> None:
        self._interactions = interactions
        self._restaurants = restaurants

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
            if restaurant is None or not restaurant.is_active:
                raise RestaurantNotFoundError(command.restaurant_id)

        event = InteractionEvent(
            session_id=command.session_id,
            restaurant_id=command.restaurant_id,
            action_type=action,
            search_query_id=command.search_query_id,
            dwell_time_ms=command.dwell_time_ms,
            rank_position=command.rank_position,
        )
        event_id = self._interactions.append(event)
        return LoggedInteraction(
            interaction_event_id=event_id,
            is_positive_signal=event.is_positive_signal,
        )

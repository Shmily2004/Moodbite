"""Router ghi nhận tương tác - đặc tả API mục 3.4.

Đây là nguồn dữ liệu NHÃN cho mô hình xếp hạng học có giám sát ở giai đoạn sau.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.application.use_cases.log_interaction import (
    LogInteractionCommand,
    LogInteractionUseCase,
)
from src.presentation.api.dependencies import get_log_interaction
from src.presentation.api.envelope import success
from src.presentation.api.schemas import InteractionRequest, InteractionResponseData

router = APIRouter(tags=["interactions"])


@router.post("/interactions", response_model=None, status_code=201)
def log_interaction(
    body: InteractionRequest,
    use_case: LogInteractionUseCase = Depends(get_log_interaction),
):
    """Ghi một sự kiện tương tác gắn với một nhà hàng cụ thể.

    `is_positive_signal` được tính Ở SERVER theo quy tắc thống nhất, không để client tự
    suy luận - nếu không, nhãn huấn luyện sẽ nhiễu.
    """
    logged = use_case.execute(
        LogInteractionCommand(
            session_id=body.session_id,
            restaurant_id=body.restaurant_id,
            action_type=body.action_type.value,
            search_query_id=body.search_query_id,
            dwell_time_ms=body.dwell_time_ms,
            rank_position=body.rank_position,
        )
    )
    payload = InteractionResponseData(
        interaction_event_id=logged.interaction_event_id,
        is_positive_signal=logged.is_positive_signal,
    )
    return success(payload.model_dump(), status_code=201)

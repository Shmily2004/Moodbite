"""Router ghi nhận tương tác - đặc tả API mục 3.4.

Đây là nguồn dữ liệu NHÃN cho mô hình xếp hạng học có giám sát ở giai đoạn sau.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request

from src.application.use_cases.log_interaction import (
    LogInteractionCommand,
    LogInteractionUseCase,
)
from src.domain.entities.interaction import ActionType
from src.domain.entities.user import User
from src.presentation.api.dependencies import (
    Container,
    closure_reporter_key,
    get_container,
    get_log_interaction,
    get_optional_user,
    limit_interaction_rate,
)
from src.presentation.api.envelope import success
from src.presentation.api.schemas import (
    ERROR_RESPONSES,
    InteractionRequest,
    InteractionResponse,
    InteractionResponseData,
)

router = APIRouter(tags=["interactions"])


@router.post("/interactions", response_model=InteractionResponse, status_code=201,
             responses=ERROR_RESPONSES)
def log_interaction(
    body: InteractionRequest,
    request: Request,
    use_case: LogInteractionUseCase = Depends(get_log_interaction),
    user: Optional[User] = Depends(get_optional_user),
    container: Container = Depends(get_container),
):
    """Ghi một sự kiện tương tác gắn với một nhà hàng cụ thể.

    `is_positive_signal` được tính Ở SERVER theo quy tắc thống nhất, không để client tự
    suy luận - nếu không, nhãn huấn luyện sẽ nhiễu.

    KHÁCH VẪN GỌI ĐƯỢC. Đã đăng nhập thì tương tác được gắn thêm `user_id` để đếm "lượt
    khám phá" cho cấp độ. `user_id` lấy TỪ TOKEN, không lấy từ body — nếu không thì ai
    cũng tự cộng điểm cho mình bằng cách gọi thẳng API.

    GIỚI HẠN TẦN SUẤT theo IP (2026-10-06): vượt -> 429 RATE_LIMITED + `Retry-After`.
    `report_closed` có hạn mức RIÊNG, chặt hơn hẳn — một lượt báo đưa quán vào hàng chờ
    quản trị (UC06). Lượt báo được đếm theo KHOÁ NGƯỜI BÁO (IP đã băm) do server tính,
    KHÔNG theo `session_id` client gửi lên, để một người không chiếm hàng chờ bằng nhiều
    session_id.
    """
    limit_interaction_rate(request, body.action_type, container)
    la_bao_dong_cua = body.action_type == ActionType.REPORT_CLOSED
    logged = use_case.execute(
        LogInteractionCommand(
            session_id=body.session_id,
            restaurant_id=body.restaurant_id,
            action_type=body.action_type.value,
            search_query_id=body.search_query_id,
            dwell_time_ms=body.dwell_time_ms,
            rank_position=body.rank_position,
            user_id=user.user_id if user is not None else None,
            reporter_key=(
                closure_reporter_key(request, container) if la_bao_dong_cua else None
            ),
        )
    )
    payload = InteractionResponseData(
        interaction_event_id=logged.interaction_event_id,
        is_positive_signal=logged.is_positive_signal,
    )
    return success(payload.model_dump(), status_code=201)

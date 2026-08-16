"""Router thông tin hệ thống: /health và /moods - đặc tả API mục 3.5.

/health trả trạng thái TỪNG nguồn dữ liệu kèm lý do lỗi, để chẩn đoán được ngay
"vì sao endpoint kia trả 503" mà không cần đọc log.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.domain.value_objects.mood import SUPPORTED_MOODS
from src.presentation.api.dependencies import Container, get_container
from src.presentation.api.envelope import success
from src.presentation.api.schemas import HealthData, MoodsData

router = APIRouter(tags=["meta"])

API_VERSION = "v1"


@router.get("/health", response_model=None)
def health(container: Container = Depends(get_container)):
    services = container.health()
    core_ready = services["restaurants"].get("ready", False)
    payload = HealthData(
        status="ok" if core_ready else "degraded",
        api_version=API_VERSION,
        services=services,
    )
    return success(payload.model_dump())


@router.get("/moods", response_model=None)
def moods():
    """Các mood dùng cho lối tắt `mood` của POST /search.

    Đề án ưu tiên tìm kiếm bằng câu tự do; danh sách này chỉ phục vụ nút bấm nhanh.
    """
    payload = MoodsData(
        supported_moods=list(SUPPORTED_MOODS),
        description=(
            "Lối tắt tuỳ chọn cho field `mood` của POST /api/v1/search. "
            "Cách dùng được khuyến nghị là gõ nhu cầu tự do vào `query_text`."
        ),
    )
    return success(payload.model_dump())

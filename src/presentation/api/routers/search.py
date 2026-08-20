"""Router tìm kiếm & xếp hạng - đặc tả API mục 3.1.

Router chỉ làm 3 việc: nhận request, gọi use case, bọc response vào envelope.
KHÔNG có logic nghiệp vụ ở đây.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.application.use_cases.search_restaurants import (
    SearchQuery,
    SearchRestaurantsUseCase,
)
from src.presentation.api.dependencies import get_search_restaurants
from src.presentation.api.envelope import success
from src.presentation.api.result_mapping import search_result_to_dict
from src.presentation.api.schemas import (
    ERROR_RESPONSES,
    SearchRequest,
    SearchResponse,
    SearchResponseData,
)

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse, responses=ERROR_RESPONSES,
             summary="Tìm kiếm & xếp hạng nhà hàng")
def search(
    body: SearchRequest,
    use_case: SearchRestaurantsUseCase = Depends(get_search_restaurants),
):
    """Nhận nhu cầu bằng ngôn ngữ tự nhiên kèm ràng buộc, trả danh sách đã xếp hạng.

    Mỗi kết quả kèm `suggested_dish` (Lớp 5 của đề án) - gợi ý MÓN đi liền với quán, thay
    vì bắt client gọi thêm một endpoint khác và tự ghép hai danh sách.
    """
    result = use_case.execute(
        SearchQuery(
            session_id=body.session_id,
            latitude=body.latitude,
            longitude=body.longitude,
            query_text=body.query_text,
            mood=body.mood,
            max_distance_km=body.max_distance_km,
            dietary_restrictions=body.dietary_restrictions,
            opening_hours_constraint=body.opening_hours_constraint,
            district=body.district,
            limit=body.limit,
        )
    )

    payload = SearchResponseData(
        search_query_id=result.search_query_id,
        results=[search_result_to_dict(item) for item in result.results],
        context=result.context,
        warnings=result.warnings,
    )
    return success(payload.model_dump())

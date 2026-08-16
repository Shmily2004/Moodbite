"""Router chi tiết 1 nhà hàng - đặc tả API mục 3.2."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.application.use_cases.get_restaurant_details import (
    GetRestaurantDetailsUseCase,
)
from src.presentation.api.dependencies import get_restaurant_details_use_case
from src.presentation.api.envelope import success
from src.presentation.api.schemas import (
    ERROR_RESPONSES,
    RestaurantDetailData,
    RestaurantDetailResponse,
)

router = APIRouter(tags=["restaurants"])


@router.get("/restaurants/{restaurant_id}", response_model=RestaurantDetailResponse,
            responses=ERROR_RESPONSES)
def restaurant_detail(
    restaurant_id: str,
    use_case: GetRestaurantDetailsUseCase = Depends(get_restaurant_details_use_case),
):
    """Chi tiết 1 quán: giá, review thật, ảnh, không gian, giờ mở cửa.

    `restaurant_id` lấy từ field `restaurant_id` trong kết quả của POST /api/v1/search.

    Quán chưa cào được chi tiết trả 200 kèm `has_details: false` (KHÔNG phải 404) - quán
    vẫn tồn tại và vẫn được đề xuất, chỉ là chưa có dữ liệu bổ sung.
    """
    d = use_case.execute(restaurant_id)
    payload = RestaurantDetailData(
        restaurant_id=d.place_id,
        has_details=d.has_details,
        reason=d.reason,
        name=d.name,
        price_range=d.price,
        atmosphere=d.atmosphere,
        opening_hours=d.opening_hours,
        images=d.images,
        reviews=d.reviews,
        menu_url=d.menu_url,
        website=d.website,
        google_maps_url=d.google_maps_url,
    )
    return success(payload.model_dump())

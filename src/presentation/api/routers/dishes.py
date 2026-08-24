"""Router MÓN ĂN - luồng "chọn món trước, tìm quán sau".

    POST /api/v1/dishes/suggest          bộ lọc  -> danh sách MÓN
    GET  /api/v1/dishes/{id}             chi tiết 1 món (GIỚI THIỆU NGẮN)
    GET  /api/v1/dishes/{id}/restaurants món     -> quán gần đây bán món đó

Router MỎNG đúng CLAUDE.md mục 3: nhận HTTP, gọi use case, bọc envelope. Không có quy tắc
nghiệp vụ ở đây - lọc/chấm điểm nằm ở `domain/services/dish_ranking.py`.

VÌ SAO `/dishes/{id}/restaurants` TÁCH RIÊNG khỏi `POST /search`: đây là hai câu hỏi khác
nhau. `/search` hỏi "quán nào hợp nhu cầu của tôi", còn cái này hỏi "quán nào bán ĐÚNG món
này". Nhồi chung vào `/search` sẽ phải thêm một tham số làm đổi hẳn ý nghĩa của mọi tham
số còn lại.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.application.use_cases.find_restaurants_for_dish import (
    DishNotFoundError,
    FindRestaurantsForDishUseCase,
    RestaurantsForDishQuery,
)
from src.application.use_cases.suggest_dishes import (
    DishSuggestionQuery,
    SuggestDishesUseCase,
)
from src.domain.value_objects.location import HANOI_CENTER_LAT, HANOI_CENTER_LNG
from src.domain.services.search_ranking import DEFAULT_MAX_DISTANCE_KM
from src.presentation.api.dependencies import (
    get_find_restaurants_for_dish,
    get_suggest_dishes,
)
from src.presentation.api.envelope import success
from src.presentation.api.result_mapping import search_result_to_dict
from src.presentation.api.schemas import (
    ERROR_RESPONSES,
    DishDetailResponse,
    DishItemSchema,
    DishSuggestRequest,
    DishSuggestResponse,
    DishSuggestResponseData,
    SearchResponse,
    SearchResponseData,
)

router = APIRouter(tags=["dishes"])


def _dish_item_dict(item) -> dict:
    """`SuggestedDishItem` -> dict đúng hợp đồng API (snake_case)."""
    return {
        "dish_id": item.dish_id,
        "name": item.name,
        "cuisine": item.cuisine,
        "spice_level": item.spice_level,
        "temperature": item.temperature,
        "cooking_method": item.cooking_method,
        "meal_times": list(item.meal_times),
        "has_description": item.has_description,
        "description": item.description,
        "image_url": item.image_url,
        "nearest_restaurant_km": item.nearest_restaurant_km,
        "restaurant_count": item.restaurant_count,
        "rank_position": item.rank_position,
        "score": item.score,
        "reasons": list(item.reasons),
        "source": item.source,
        "source_url": item.source_url,
        "data_confidence": item.data_confidence,
    }


@router.post("/dishes/suggest", response_model=DishSuggestResponse,
             responses=ERROR_RESPONSES, summary="Gợi ý MÓN theo bộ lọc + ngữ cảnh")
def suggest_dishes(
    body: DishSuggestRequest,
    use_case: SuggestDishesUseCase = Depends(get_suggest_dishes),
):
    """Trang chủ: nhận bộ lọc, trả danh sách MÓN đã xếp hạng.

    Món không có quán nào trong bán kính bị ẨN, và số món bị ẩn được nói rõ ở
    `data.warnings` - im lặng bỏ bớt kết quả là lỗi `/suggest-dish` cũ từng mắc.
    """
    result = use_case.execute(
        DishSuggestionQuery(
            session_id=body.session_id,
            latitude=body.latitude,
            longitude=body.longitude,
            cooking_methods=body.cooking_methods,
            temperatures=body.temperatures,
            cuisines=body.cuisines,
            meal_times=body.meal_times,
            max_spice_level=body.max_spice_level,
            mood=body.mood,
            weather=body.weather,
            max_distance_km=body.max_distance_km,
            limit=body.limit,
            only_categories=body.only_categories,
        )
    )
    payload = DishSuggestResponseData(
        search_query_id=result.search_query_id,
        results=[_dish_item_dict(item) for item in result.results],
        context=result.context,
        warnings=result.warnings,
    )
    return success(payload.model_dump())


@router.get("/dishes/{dish_id}", response_model=DishDetailResponse,
            responses=ERROR_RESPONSES, summary="Chi tiết 1 món (giới thiệu ngắn)")
def dish_detail(
    dish_id: str,
    latitude: float = Query(default=HANOI_CENTER_LAT, ge=-90, le=90),
    longitude: float = Query(default=HANOI_CENTER_LNG, ge=-180, le=180),
    max_distance_km: float = Query(default=DEFAULT_MAX_DISTANCE_KM, gt=0, le=100),
    use_case: SuggestDishesUseCase = Depends(get_suggest_dishes),
):
    """Giới thiệu ngắn về món + số quán bán món này gần bạn.

    `description` rỗng kèm `has_description: false` nghĩa là CHƯA TRA ĐƯỢC nguồn nào, và
    giao diện phải nói đúng như vậy - không được để một khoảng trắng như thể món này không
    có gì để giới thiệu (CLAUDE.md mục 4 quy tắc 1).

    Nhận toạ độ vì `restaurant_count` phải tính theo bán kính của NGƯỜI ĐANG XEM: món có
    1700 quán toàn thành phố nhưng 0 quán quanh đây vẫn là ngõ cụt.
    """
    # Dùng lại use case gợi ý với `include_unavailable=True`: trang chi tiết phải mở được
    # kể cả khi món không có quán nào gần (người dùng có thể vào từ liên kết đã chia sẻ).
    result = use_case.execute(
        DishSuggestionQuery(
            session_id=f"dish-detail:{dish_id}",
            latitude=latitude,
            longitude=longitude,
            max_distance_km=max_distance_km,
            include_unavailable=True,
            # Trang chi tiết phải mở được CẢ danh mục lẫn món cụ thể — người dùng có thể
            # vào từ liên kết đã chia sẻ. Nên KHÔNG lọc theo `only_categories` ở đây.
            only_categories=False,
            limit=100,
        )
    )
    item = next((r for r in result.results if r.dish_id == dish_id), None)
    if item is None:
        raise DishNotFoundError(dish_id)
    return success(DishItemSchema(**_dish_item_dict(item)).model_dump())


@router.get("/dishes/{dish_id}/restaurants", response_model=SearchResponse,
            responses=ERROR_RESPONSES, summary="Quán gần đây bán món này")
def restaurants_for_dish(
    dish_id: str,
    session_id: str = Query(...),
    latitude: float = Query(default=HANOI_CENTER_LAT, ge=-90, le=90),
    longitude: float = Query(default=HANOI_CENTER_LNG, ge=-180, le=180),
    max_distance_km: float = Query(default=DEFAULT_MAX_DISTANCE_KM, gt=0, le=100),
    mood: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    use_case: FindRestaurantsForDishUseCase = Depends(get_find_restaurants_for_dish),
):
    """Danh sách quán bán món đã chọn, xếp hạng theo khoảng cách + đánh giá + ngữ cảnh.

    Trả về ĐÚNG kiểu của `POST /search` để client dùng lại một component thẻ quán duy nhất.
    """
    result = use_case.execute(
        RestaurantsForDishQuery(
            session_id=session_id,
            dish_id=dish_id,
            latitude=latitude,
            longitude=longitude,
            max_distance_km=max_distance_km,
            mood=mood,
            limit=limit,
        )
    )
    payload = SearchResponseData(
        search_query_id=result.search_query_id,
        results=[search_result_to_dict(item) for item in result.results],
        context=result.context,
        warnings=result.warnings,
    )
    return success(payload.model_dump())


@router.get("/dishes/{dish_id}", response_model=DishDetailResponse,
            responses=ERROR_RESPONSES, summary="Chi tiết 1 món (giới thiệu ngắn)")
def dish_detail(
    dish_id: str,
    latitude: float = Query(default=HANOI_CENTER_LAT, ge=-90, le=90),
    longitude: float = Query(default=HANOI_CENTER_LNG, ge=-180, le=180),
    max_distance_km: float = Query(default=DEFAULT_MAX_DISTANCE_KM, gt=0, le=100),
    use_case: SuggestDishesUseCase = Depends(get_suggest_dishes),
):
    """Giới thiệu ngắn về món + số quán bán món này gần bạn.

    `description` rỗng kèm `has_description: false` nghĩa là CHƯA TRA ĐƯỢC nguồn nào, và
    giao diện phải nói đúng như vậy - không được để một khoảng trắng như thể món này không
    có gì để giới thiệu (CLAUDE.md mục 4 quy tắc 1).

    Nhận toạ độ vì `restaurant_count` phải tính theo bán kính của NGƯỜI ĐANG XEM: món có
    1700 quán toàn thành phố nhưng 0 quán quanh đây vẫn là ngõ cụt.
    """
    # Dùng lại use case gợi ý với `include_unavailable=True`: trang chi tiết phải mở được
    # kể cả khi món không có quán nào gần (người dùng có thể vào từ liên kết đã chia sẻ).
    result = use_case.execute(
        DishSuggestionQuery(
            session_id=f"dish-detail:{dish_id}",
            latitude=latitude,
            longitude=longitude,
            max_distance_km=max_distance_km,
            include_unavailable=True,
            limit=100,
        )
    )
    item = next((r for r in result.results if r.dish_id == dish_id), None)
    if item is None:
        raise DishNotFoundError(dish_id)
    return success(DishItemSchema(**_dish_item_dict(item)).model_dump())


@router.get("/dishes/{dish_id}/restaurants", response_model=SearchResponse,
            responses=ERROR_RESPONSES, summary="Quán gần đây bán món này")
def restaurants_for_dish(
    dish_id: str,
    session_id: str = Query(...),
    latitude: float = Query(default=HANOI_CENTER_LAT, ge=-90, le=90),
    longitude: float = Query(default=HANOI_CENTER_LNG, ge=-180, le=180),
    max_distance_km: float = Query(default=DEFAULT_MAX_DISTANCE_KM, gt=0, le=100),
    mood: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    use_case: FindRestaurantsForDishUseCase = Depends(get_find_restaurants_for_dish),
):
    """Danh sách quán bán món đã chọn, xếp hạng theo khoảng cách + đánh giá + ngữ cảnh.

    Trả về ĐÚNG kiểu của `POST /search` để client dùng lại một component thẻ quán duy nhất.
    """
    result = use_case.execute(
        RestaurantsForDishQuery(
            session_id=session_id,
            dish_id=dish_id,
            latitude=latitude,
            longitude=longitude,
            max_distance_km=max_distance_km,
            mood=mood,
            limit=limit,
        )
    )
    payload = SearchResponseData(
        search_query_id=result.search_query_id,
        results=[
            {
                "restaurant_id": item.restaurant_id,
                "name": item.name,
                "category": item.category,
                "address": item.address,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "distance_m": item.distance_m,
                "price_range": item.price_range,
                "rating": item.rating,
                "user_ratings_total": item.user_ratings_total,
                "rank_position": item.rank_position,
                "predicted_score": item.predicted_score,
                "match_source": item.match_source,
                "thumbnail_url": item.thumbnail_url,
                "district": item.district,
                "dietary": item.dietary,
                "amenities": item.amenities,
                "source": item.source,
                "experience_cluster_id": item.experience_cluster_id,
                "experience_cluster_label": item.experience_cluster_label,
                "suggested_dish": {
                    "dish_id": item.suggested_dish.dish_id,
                    "name": item.suggested_dish.name,
                    "cuisine": item.suggested_dish.cuisine,
                    "spice_level": item.suggested_dish.spice_level,
                    "temperature": item.suggested_dish.temperature,
                    "confidence": item.suggested_dish.confidence,
                    "reason": item.suggested_dish.reason,
                } if item.suggested_dish else None,
            }
            for item in result.results
        ],
        context=result.context,
        warnings=result.warnings,
    )
    return success(payload.model_dump())

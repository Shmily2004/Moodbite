"""USE CASE: chọn một MÓN rồi tìm QUÁN gần đây bán món đó.

Bước 3 của luồng mới:

    bộ lọc -> danh sách món -> chi tiết món -> QUÁN GẦN ĐÂY -> review
                                              ^^^^^^^^^^^^^ use case này

TRẢ VỀ ĐÚNG KIỂU `SearchResultItem` của use case tìm quán cũ. Cố ý: giao diện đã có
`RestaurantCard` hiển thị kiểu đó, và người dùng cũng mong hai danh sách quán trông giống
nhau. Thêm một kiểu thứ hai gần-giống-nhưng-khác chỉ tạo ra hai nhánh render phải cùng sửa.

XẾP HẠNG DÙNG LẠI `search_ranking.rank_restaurants` - không viết công thức thứ hai. Khác
biệt duy nhất: tập quán đầu vào đã được lọc sẵn theo món, và `suggested_dish` là món người
dùng ĐÃ CHỌN chứ không phải suy đoán.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import List, Mapping, Optional, Sequence

from src.application.errors import ApplicationError, DataNotReadyError
from src.application.ports.context_provider import ContextProvider
from src.application.ports.dish_catalog_repository import DishCatalogRepository
from src.application.use_cases.search_restaurants import (
    SearchResult,
    SearchResultItem,
    SuggestedDish,
)
from src.domain.entities.dish import Dish
from src.domain.services import search_ranking
from src.domain.services.search_ranking import DEFAULT_MAX_DISTANCE_KM
from src.domain.value_objects.context_signal import NEUTRAL_CONTEXT, ContextSignal
from src.domain.value_objects.location import (
    HANOI_CENTER_LAT,
    HANOI_CENTER_LNG,
    Location,
)
from src.domain.value_objects.mood import MOOD_PROFILES, normalize_mood

DEFAULT_LIMIT = 20
MAX_LIMIT = 50

# Món người dùng tự chọn thì độ tin cậy KHÔNG phải là suy đoán nữa: ta biết chắc quán này
# khớp từ khoá của món. Vẫn không dám nói là "có trong thực đơn" - ta chưa bao giờ đọc
# thực đơn thật của quán (CLAUDE.md mục 4 quy tắc 4).
DISH_MATCH_CONFIDENCE = "specific"
DISH_MATCH_REASON = "quán khớp từ khoá của món bạn chọn, chưa phải thực đơn thật"


class DishNotFoundError(ApplicationError):
    """dish_id không tồn tại hoặc đã bị ẩn -> HTTP 404."""

    def __init__(self, dish_id: str) -> None:
        super().__init__(f"Không tìm thấy món: {dish_id}")
        self.dish_id = dish_id


@dataclass(frozen=True)
class RestaurantsForDishQuery:
    session_id: str
    dish_id: str
    latitude: float = HANOI_CENTER_LAT
    longitude: float = HANOI_CENTER_LNG
    max_distance_km: Optional[float] = DEFAULT_MAX_DISTANCE_KM
    mood: Optional[str] = None
    limit: int = DEFAULT_LIMIT


class FindRestaurantsForDishUseCase:
    def __init__(
        self,
        catalog: DishCatalogRepository,
        dish_restaurant_index: Mapping[str, Sequence],
        context_provider: Optional[ContextProvider] = None,
    ) -> None:
        self._catalog = catalog
        self._index = dish_restaurant_index
        self._context_provider = context_provider

    def execute(self, query: RestaurantsForDishQuery) -> SearchResult:
        if not self._catalog.is_ready:
            raise DataNotReadyError(
                "danh mục món ăn", "chạy python scripts/build_dish_catalog.py"
            )

        dish = self._catalog.get_dish(query.dish_id)
        if dish is None:
            raise DishNotFoundError(query.dish_id)

        warnings: List[str] = []
        origin = Location(lat=query.latitude, lng=query.longitude)
        context = self._resolve_context(origin)

        candidates = list(self._index.get(dish.identifier, ()))
        if not candidates:
            # Không có quán nào là kết quả THẬT, không phải lỗi. Nói rõ thay vì trả 404:
            # món vẫn tồn tại, chỉ là chưa quán nào trong dataset khớp.
            warnings.append(
                f"Chưa có quán nào trong dữ liệu khớp món '{dish.name}'. "
                "Dữ liệu quán được đối chiếu theo TÊN QUÁN, nên quán có bán nhưng không "
                "ghi tên món thì không tìm ra được."
            )

        ranked = search_ranking.rank_restaurants(
            restaurants=candidates,
            origin=origin,
            mood_weights=self._mood_weights(query.mood, warnings),
            context=context,
            max_distance_km=query.max_distance_km,
            limit=max(1, min(query.limit, MAX_LIMIT)),
        )

        self._warn_if_radius_was_widened(ranked, query, dish, warnings)

        return SearchResult(
            search_query_id=str(uuid.uuid4()),
            results=[self._to_item(r, dish) for r in ranked],
            context=context.describe(),
            warnings=warnings,
        )

    # --- các bước con -------------------------------------------------------

    def _resolve_context(self, origin: Location) -> ContextSignal:
        if self._context_provider is None:
            return NEUTRAL_CONTEXT
        try:
            return self._context_provider.get_context(origin)
        except Exception:
            return NEUTRAL_CONTEXT

    @staticmethod
    def _warn_if_radius_was_widened(
        ranked: List,
        query: RestaurantsForDishQuery,
        dish: Dish,
        warnings: List[str],
    ) -> None:
        """Nói ra khi kết quả nằm NGOÀI bán kính người dùng chọn.

        `search_ranking.rank_restaurants` CỐ Ý bỏ lọc bán kính khi lọc xong không còn gì -
        thà gợi ý quán xa còn hơn trả màn hình trắng. Quy tắc đó đúng, nhưng nếu im lặng
        thì người dùng tưởng quán cách 40km là "gần đây" (CLAUDE.md mục 5: không được
        lặng lẽ bỏ qua tham số client gửi lên).
        """
        if query.max_distance_km is None or not ranked:
            return

        limit_m = query.max_distance_km * 1000
        if all(r.distance_km * 1000 > limit_m for r in ranked):
            nearest_km = min(r.distance_km for r in ranked)
            warnings.append(
                f"Không có quán nào bán '{dish.name}' trong bán kính "
                f"{query.max_distance_km} km. Đang hiện quán gần nhất, cách khoảng "
                f"{nearest_km:.1f} km."
            )

    @staticmethod
    def _mood_weights(mood: Optional[str], warnings: List[str]):
        if not mood:
            return None
        try:
            return dict(MOOD_PROFILES[normalize_mood(mood)])
        except Exception:
            warnings.append(
                f"Bỏ qua mood '{mood}' vì không hợp lệ. Hợp lệ: {list(MOOD_PROFILES)}"
            )
            return None

    @staticmethod
    def _to_item(ranked: search_ranking.RankedRestaurant, dish: Dish) -> SearchResultItem:
        restaurant = ranked.restaurant
        return SearchResultItem(
            restaurant_id=restaurant.place_id,
            name=restaurant.name,
            category=restaurant.category,
            address=restaurant.address,
            thumbnail_url=restaurant.thumbnail_url,
            latitude=restaurant.location.lat,
            longitude=restaurant.location.lng,
            distance_m=int(round(ranked.distance_km * 1000)),
            # `price` là CHUỖI khoảng giá - ép float là bug đã từng xảy ra.
            price_range=restaurant.price,
            # `None` giữ nguyên `None`: "chưa có đánh giá" khác hẳn "0 sao".
            rating=restaurant.rating,
            user_ratings_total=restaurant.reviews_count,
            rank_position=ranked.rank_position,
            predicted_score=ranked.predicted_score,
            match_source=ranked.match_source,
            district=restaurant.district,
            dietary=list(restaurant.dietary),
            amenities=list(restaurant.amenities),
            source=restaurant.source,
            experience_cluster_id=restaurant.experience_cluster_id,
            experience_cluster_label=restaurant.experience_cluster_label,
            suggested_dish=SuggestedDish(
                dish_id=dish.identifier,
                name=dish.name,
                cuisine=dish.cuisine,
                spice_level=dish.spice_level,
                temperature=dish.temperature,
                confidence=DISH_MATCH_CONFIDENCE,
                reason=DISH_MATCH_REASON,
            ),
        )

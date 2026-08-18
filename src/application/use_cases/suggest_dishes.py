"""USE CASE: trang chủ - người dùng chọn bộ lọc, hệ thống trả về DANH SÁCH MÓN.

Đây là bước 1 của luồng mới (chốt với chủ dự án 2026-08-18):

    bộ lọc  ->  DANH SÁCH MÓN  ->  chi tiết món (thành phần)  ->  quán gần đây  ->  review
    ^^^^^^^^^^^^^^^^^^^^^^^^^^ use case này

Chỉ ĐIỀU PHỐI, không chứa quy tắc nghiệp vụ: việc lọc và chấm điểm nằm ở
`domain/services/dish_ranking.py`, việc đối chiếu món-quán nằm ở `domain/services/dish_matching.py`.

VÌ SAO ĐẾM QUÁN Ở ĐÂY MÀ KHÔNG DÙNG SỐ ĐÃ TÍNH SẴN TRONG dish_catalog.json:
số trong file là đếm trên TOÀN dataset, còn người dùng đang đứng ở một chỗ cụ thể với bán
kính cụ thể. Món có 1700 quán toàn thành phố nhưng 0 quán trong bán kính 2km vẫn là ngõ
cụt với người đang đói.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence

from src.application.errors import DataNotReadyError
from src.application.ports.context_provider import ContextProvider
from src.application.ports.dish_catalog_repository import DishCatalogRepository
from src.domain.entities.dish import Dish
from src.domain.services import dish_ranking
from src.domain.services.dish_ranking import DishFilter
from src.domain.services.search_ranking import DEFAULT_MAX_DISTANCE_KM
from src.domain.value_objects.context_signal import NEUTRAL_CONTEXT, ContextSignal
from src.domain.value_objects.location import (
    HANOI_CENTER_LAT,
    HANOI_CENTER_LNG,
    Location,
)

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


@dataclass(frozen=True)
class DishSuggestionQuery:
    session_id: str
    latitude: float = HANOI_CENTER_LAT
    longitude: float = HANOI_CENTER_LNG
    cooking_methods: List[str] = field(default_factory=list)
    temperatures: List[str] = field(default_factory=list)
    cuisines: List[str] = field(default_factory=list)
    meal_times: List[str] = field(default_factory=list)
    max_spice_level: Optional[int] = None
    mood: Optional[str] = None
    # Người dùng TỰ khai thời tiết ("nay trời mưa"), ghi đè số đo tự động.
    weather: Optional[str] = None
    max_distance_km: Optional[float] = DEFAULT_MAX_DISTANCE_KM
    limit: int = DEFAULT_LIMIT
    # Hiện cả món không có quán nào gần đây. Mặc định TẮT vì với người dùng đó là ngõ cụt;
    # bật lên khi trang quản trị cần nhìn thấy toàn bộ danh mục.
    include_unavailable: bool = False


@dataclass(frozen=True)
class SuggestedDishItem:
    dish_id: str
    name: str
    cuisine: Optional[str]
    spice_level: Optional[int]
    temperature: Optional[str]
    cooking_method: Optional[str]
    meal_times: List[str]
    ingredients: List[str]
    # Tách riêng khỏi `ingredients` để giao diện không phải tự đoán: rỗng nghĩa là CHƯA CÓ
    # DỮ LIỆU, không phải "món này không cần nguyên liệu".
    has_ingredients: bool
    description: Optional[str]
    image_url: Optional[str]
    restaurant_count: int
    rank_position: int
    score: float
    reasons: List[str]
    source: Optional[str]
    source_url: Optional[str]
    data_confidence: Optional[str]


@dataclass(frozen=True)
class DishSuggestionResult:
    search_query_id: str
    results: List[SuggestedDishItem]
    context: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SuggestDishesUseCase:
    def __init__(
        self,
        catalog: DishCatalogRepository,
        dish_restaurant_index: Mapping[str, Sequence],
        context_provider: Optional[ContextProvider] = None,
    ) -> None:
        self._catalog = catalog
        self._index = dish_restaurant_index
        self._context_provider = context_provider

    def execute(self, query: DishSuggestionQuery) -> DishSuggestionResult:
        if not self._catalog.is_ready:
            raise DataNotReadyError(
                "danh mục món ăn",
                "chạy python scripts/build_dish_catalog.py",
            )

        warnings: List[str] = []
        origin = Location(lat=query.latitude, lng=query.longitude)
        context = self._resolve_context(origin)

        dishes = self._catalog.list_dishes()
        counts = self._count_nearby(dishes, origin, query.max_distance_km)

        available = self._drop_dead_ends(dishes, counts, query, warnings)
        dish_filter = self._to_filter(query)
        candidates = dish_ranking.filter_dishes(available, dish_filter)

        ranked = dish_ranking.rank_dishes(
            dishes=candidates,
            f=dish_filter,
            context=context,
            restaurant_counts=counts,
            limit=max(1, min(query.limit, MAX_LIMIT)),
        )

        return DishSuggestionResult(
            search_query_id=str(uuid.uuid4()),
            results=[self._to_item(r) for r in ranked],
            context=context.describe(),
            warnings=warnings,
        )

    # --- các bước con -------------------------------------------------------

    @staticmethod
    def _to_filter(query: DishSuggestionQuery) -> DishFilter:
        return DishFilter(
            cooking_methods=list(query.cooking_methods),
            temperatures=list(query.temperatures),
            cuisines=list(query.cuisines),
            meal_times=list(query.meal_times),
            max_spice_level=query.max_spice_level,
            mood=query.mood,
            weather=query.weather,
        )

    def _resolve_context(self, origin: Location) -> ContextSignal:
        """Ngữ cảnh hỏng KHÔNG được làm hỏng lượt tìm (CLAUDE.md mục 4 quy tắc 7)."""
        if self._context_provider is None:
            return NEUTRAL_CONTEXT
        try:
            return self._context_provider.get_context(origin)
        except Exception:
            return NEUTRAL_CONTEXT

    def _count_nearby(
        self, dishes: Sequence[Dish], origin: Location, max_distance_km: Optional[float]
    ) -> Dict[str, int]:
        """Số quán bán từng món TRONG BÁN KÍNH người dùng chọn.

        Quán thiếu toạ độ không đếm được nên bị bỏ qua ở đây - nhưng đó là trường hợp
        không xảy ra trên dataset hiện tại (lat/lng là cột bắt buộc của pipeline).
        """
        counts: Dict[str, int] = {}
        for dish in dishes:
            nearby = 0
            for restaurant in self._index.get(dish.identifier, ()):
                if not restaurant.is_active:
                    continue
                if max_distance_km is None:
                    nearby += 1
                elif origin.distance_km(restaurant.location) <= max_distance_km:
                    nearby += 1
            counts[dish.identifier] = nearby
        return counts

    @staticmethod
    def _drop_dead_ends(
        dishes: Sequence[Dish],
        counts: Mapping[str, int],
        query: DishSuggestionQuery,
        warnings: List[str],
    ) -> List[Dish]:
        """Bỏ món không có quán nào gần đây.

        Bấm vào một món rồi nhận danh sách quán rỗng là trải nghiệm tệ nhất của luồng này -
        người dùng đã bỏ công chọn mà không đi tới đâu. Thà đừng hiện món đó.

        Nhưng phải NÓI RA đã giấu bao nhiêu món, kèm cách nới điều kiện: im lặng bỏ bớt
        kết quả là đúng cái lỗi `/suggest-dish` cũ từng mắc (CLAUDE.md mục 5).
        """
        if query.include_unavailable:
            return list(dishes)

        available = [d for d in dishes if counts.get(d.identifier, 0) > 0]
        hidden = len(dishes) - len(available)
        if hidden:
            warnings.append(
                f"Đã ẩn {hidden} món không có quán nào trong bán kính "
                f"{query.max_distance_km} km. Mở rộng bán kính để thấy thêm."
            )
        # Ẩn hết thì trả lại nguyên danh sách: màn hình trắng còn tệ hơn món ở xa.
        return available or list(dishes)

    @staticmethod
    def _to_item(ranked: dish_ranking.RankedDish) -> SuggestedDishItem:
        dish = ranked.dish
        return SuggestedDishItem(
            dish_id=dish.identifier,
            name=dish.name,
            cuisine=dish.cuisine,
            spice_level=dish.spice_level,
            temperature=dish.temperature,
            cooking_method=dish.cooking_method,
            meal_times=list(dish.meal_times),
            ingredients=list(dish.ingredients),
            has_ingredients=dish.has_ingredients,
            description=dish.description,
            image_url=dish.image_url,
            restaurant_count=ranked.restaurant_count,
            rank_position=ranked.rank_position,
            score=ranked.score,
            reasons=list(ranked.reasons),
            source=dish.source,
            source_url=dish.source_url,
            data_confidence=dish.data_confidence,
        )

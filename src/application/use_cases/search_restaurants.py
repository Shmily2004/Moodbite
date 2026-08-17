"""USE CASE CHÍNH: tìm kiếm + xếp hạng nhà hàng theo ngữ cảnh (đặc tả API mục 3.1).

Thay thế cặp endpoint cũ (`/recommend` + `/suggest-dish`). Lý do gộp: đặc tả API mục 4
nói rõ gợi ý MÓN không phải thực thể độc lập mà là một trường trên từng kết quả tìm kiếm.
Tách 2 endpoint khiến client phải gọi 2 lần cho cùng một nhu cầu, và 2 lần đó có thể trả
về 2 tập quán khác nhau - người dùng thấy món của quán không nằm trong danh sách quán.

Luồng (đúng thứ tự đề án mục 3):
    câu tự do  →  đoán mood + lấy ngữ cảnh thời điểm
               →  lọc ràng buộc cứng (bán kính, giờ mở cửa)
               →  xếp hạng tổng hợp (Lớp 3)
               →  gắn món gợi ý cho từng quán (Lớp 5)
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.application.errors import DataNotReadyError
from src.application.ports.context_provider import ContextProvider
from src.application.ports.dish_knowledge_repository import DishKnowledgeRepository
from src.application.ports.restaurant_repository import RestaurantRepository
from src.application.ports.rule_predictor import RulePredictor
from src.application.ports.semantic_search import SemanticSearchPort
from src.domain.entities.dish import CONFIDENCE_ML, Dish
from src.domain.entities.restaurant import Restaurant
from src.domain.services import search_ranking, text_relevance
from src.domain.services.search_ranking import DEFAULT_MAX_DISTANCE_KM
from src.domain.value_objects.opening_hours import parse_opening_hours
from src.domain.value_objects.text import normalize
from src.domain.value_objects.context_signal import NEUTRAL_CONTEXT, ContextSignal
from src.domain.value_objects.location import HANOI_CENTER_LAT, HANOI_CENTER_LNG, Location
from src.domain.value_objects.mood import MOOD_PROFILES, normalize_mood

DEFAULT_LIMIT = 10
MAX_LIMIT = 50


@dataclass(frozen=True)
class SearchQuery:
    session_id: str
    latitude: float = HANOI_CENTER_LAT
    longitude: float = HANOI_CENTER_LNG
    query_text: Optional[str] = None
    # `mood` là lối tắt tuỳ chọn cho client muốn dùng nút bấm thay vì gõ câu.
    # Đề án ưu tiên câu tự do, nên đây chỉ là bổ trợ, không bắt buộc.
    mood: Optional[str] = None
    max_distance_km: Optional[float] = DEFAULT_MAX_DISTANCE_KM
    dietary_restrictions: List[str] = field(default_factory=list)
    opening_hours_constraint: Optional[str] = None
    # Lọc theo quận/huyện, VD "Cầu Giấy". Không khớp quán nào -> bỏ lọc thay vì trả rỗng.
    district: Optional[str] = None
    limit: int = DEFAULT_LIMIT


@dataclass(frozen=True)
class SuggestedDish:
    dish_id: str
    name: str
    cuisine: Optional[str]
    spice_level: Optional[int]
    temperature: Optional[str]
    confidence: str
    reason: Optional[str] = None


@dataclass(frozen=True)
class SearchResultItem:
    restaurant_id: Optional[str]
    name: str
    category: Optional[str]
    address: Optional[str]
    latitude: float
    longitude: float
    distance_m: int
    price_range: Optional[str]
    rating: Optional[float]
    user_ratings_total: Optional[int]
    rank_position: int
    predicted_score: float
    match_source: str
    district: Optional[str] = None
    # Ảnh đại diện. None = quán chưa có ảnh (78.5% quán) - KHÔNG phải lỗi.
    thumbnail_url: Optional[str] = None
    dietary: List[str] = field(default_factory=list)
    amenities: List[str] = field(default_factory=list)
    source: Optional[str] = None
    experience_cluster_id: Optional[int] = None
    experience_cluster_label: Optional[str] = None
    suggested_dish: Optional[SuggestedDish] = None


@dataclass(frozen=True)
class SearchResult:
    search_query_id: str
    results: List[SearchResultItem]
    context: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SearchRestaurantsUseCase:
    def __init__(
        self,
        restaurants: RestaurantRepository,
        dish_knowledge: DishKnowledgeRepository,
        context_provider: Optional[ContextProvider] = None,
        rule_predictor: Optional[RulePredictor] = None,
        semantic_search: Optional[SemanticSearchPort] = None,
    ) -> None:
        self._restaurants = restaurants
        self._dish_knowledge = dish_knowledge
        self._context_provider = context_provider
        self._rule_predictor = rule_predictor
        self._semantic_search = semantic_search

    def execute(self, query: SearchQuery) -> SearchResult:
        if not self._restaurants.is_ready:
            raise DataNotReadyError(
                "dataset quán ăn",
                "chạy python -m data_pipeline.merge_and_prepare_raw && "
                "python -m data_pipeline.data_cleaning && "
                "python -m data_pipeline.feature_engineering",
            )

        warnings: List[str] = []
        origin = Location(lat=query.latitude, lng=query.longitude)

        mood_weights = self._resolve_mood_weights(query, warnings)
        context = self._resolve_context(origin)

        candidates = self._apply_hard_filters(
            self._restaurants.list_all(), query, context, warnings
        )

        ranked = search_ranking.rank_restaurants(
            restaurants=candidates,
            origin=origin,
            query_text=query.query_text,
            mood_weights=mood_weights,
            context=context,
            max_distance_km=query.max_distance_km,
            limit=max(1, min(query.limit, MAX_LIMIT)),
            semantic_scores=self._semantic_scores(query.query_text),
        )

        if query.query_text and not any(r.text_score > 0 for r in ranked):
            warnings.append(
                "Không quán nào khớp trực tiếp nội dung tìm kiếm - kết quả dưới đây xếp "
                "theo mức phù hợp chung, khoảng cách và đánh giá."
            )

        results = [
            self._to_item(r) for r in ranked
        ]

        return SearchResult(
            search_query_id=str(uuid.uuid4()),
            results=results,
            context=context.describe(),
            warnings=warnings,
        )

    # --- các bước con -------------------------------------------------------

    def _resolve_mood_weights(
        self, query: SearchQuery, warnings: List[str]
    ) -> Optional[Dict[str, float]]:
        """Ưu tiên mood suy ra từ CÂU TỰ DO; nếu câu không gợi mood nào thì mới dùng
        tham số `mood` (nút bấm) nếu client có gửi."""
        inferred = text_relevance.infer_mood_weights(query.query_text)
        if inferred:
            return inferred

        if query.mood:
            try:
                return dict(MOOD_PROFILES[normalize_mood(query.mood)])
            except Exception:
                warnings.append(
                    f"Bỏ qua mood '{query.mood}' vì không hợp lệ. "
                    f"Hợp lệ: {list(MOOD_PROFILES)}"
                )
        return None

    def _semantic_scores(self, query_text: Optional[str]) -> Dict[str, float]:
        """Điểm tương đồng ngữ nghĩa (Lớp 2). Adapter hỏng/chưa sẵn sàng -> trả rỗng,
        hệ thống tự lui về khớp từ khoá thay vì hỏng cả lượt tìm kiếm."""
        if not query_text or self._semantic_search is None:
            return {}
        try:
            if not self._semantic_search.is_ready:
                return {}
            return self._semantic_search.similarity(query_text)
        except Exception:
            return {}

    def _resolve_context(self, origin: Location) -> ContextSignal:
        if self._context_provider is None:
            return NEUTRAL_CONTEXT
        try:
            return self._context_provider.get_context(origin)
        except Exception:
            # Ngữ cảnh chỉ là tín hiệu phụ - hỏng thì bỏ qua, KHÔNG làm hỏng lượt tìm kiếm.
            return NEUTRAL_CONTEXT

    def _apply_hard_filters(
        self,
        restaurants: List[Restaurant],
        query: SearchQuery,
        context: ContextSignal,
        warnings: List[str],
    ) -> List[Restaurant]:
        """Ràng buộc cứng. Quy tắc chung: THIẾU DỮ LIỆU KHÔNG BỊ LOẠI.

        Lọc bỏ quán chỉ vì chưa cào được giờ mở cửa sẽ xoá sổ phần lớn dataset - người
        dùng mất lựa chọn vì hạn chế THU THẬP, không phải vì quán không phù hợp.
        """
        result = restaurants

        if query.dietary_restrictions:
            result, dropped = self._filter_dietary(result, query.dietary_restrictions)
            known = sum(1 for r in result if r.dietary)
            warnings.append(
                f"Lọc chế độ ăn {query.dietary_restrictions}: dữ liệu này rất thưa, "
                f"chỉ {known} quán trong kết quả có khai báo. Quán chưa khai báo vẫn "
                f"được giữ lại (đã loại {dropped} quán khai báo KHÁC yêu cầu)."
            )

        if query.opening_hours_constraint:
            result, dropped, known = self._filter_opening_hours(
                result, query.opening_hours_constraint, context
            )
            if known == 0:
                warnings.append(
                    "Không quán nào trong kết quả có dữ liệu giờ mở cửa - bỏ qua bộ lọc "
                    "thời gian thay vì trả về danh sách rỗng."
                )
            else:
                warnings.append(
                    f"Lọc theo giờ mở cửa: {known} quán có dữ liệu, đã loại {dropped} quán "
                    f"đang đóng cửa. Quán chưa có dữ liệu giờ vẫn được giữ lại."
                )

        if query.district:
            result, matched = self._filter_district(result, query.district)
            if matched == 0:
                warnings.append(
                    f"Không tìm thấy quán nào ở '{query.district}' - đã bỏ qua bộ lọc quận."
                )

        return result

    @staticmethod
    def _filter_dietary(
        restaurants: List[Restaurant], wanted: List[str]
    ) -> tuple[List[Restaurant], int]:
        """Giữ quán khớp chế độ ăn HOẶC chưa khai báo gì.

        Quán không khai báo `dietary` KHÔNG bị loại: thiếu khai báo nghĩa là chưa biết,
        không phải "không phục vụ".
        """
        wanted_set = {w.strip().lower() for w in wanted if w and w.strip()}
        if not wanted_set:
            return restaurants, 0
        kept = [
            r for r in restaurants
            if not r.dietary or wanted_set & {d.lower() for d in r.dietary}
        ]
        return kept, len(restaurants) - len(kept)

    @staticmethod
    def _filter_opening_hours(
        restaurants: List[Restaurant], constraint: str, context: ContextSignal
    ) -> tuple[List[Restaurant], int, int]:
        """(danh sách giữ lại, số bị loại, số quán có dữ liệu giờ).

        `constraint` = "now" hoặc "HH:mm". Không xác định được thời điểm -> không lọc.
        """
        weekday = context.weekday
        if weekday is None:
            return restaurants, 0, 0

        target = constraint.strip().lower()
        if target == "now":
            minute = context.minute_of_day
        else:
            match = re.match(r"^(\d{1,2}):(\d{2})$", target)
            minute = int(match.group(1)) * 60 + int(match.group(2)) if match else None
        if minute is None:
            return restaurants, 0, 0

        kept: List[Restaurant] = []
        known = 0
        for restaurant in restaurants:
            schedule = parse_opening_hours(restaurant.opening_hours)
            if schedule is None or schedule.is_empty:
                kept.append(restaurant)   # KHÔNG BIẾT -> giữ lại
                continue
            known += 1
            if schedule.is_open_at(weekday, minute):
                kept.append(restaurant)

        # Lọc xong mà rỗng thì bỏ lọc - thà gợi ý quán chưa rõ giờ còn hơn không có gì.
        if not kept:
            return restaurants, 0, known
        return kept, len(restaurants) - len(kept), known

    @staticmethod
    def _filter_district(
        restaurants: List[Restaurant], district: str
    ) -> tuple[List[Restaurant], int]:
        wanted = normalize(district)
        matched = [
            r for r in restaurants if r.district and normalize(r.district) == wanted
        ]
        # Không có quán nào khớp -> bỏ lọc thay vì trả rỗng.
        return (matched, len(matched)) if matched else (restaurants, 0)

    def _to_item(self, ranked: search_ranking.RankedRestaurant) -> SearchResultItem:
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
            price_range=restaurant.price,
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
            suggested_dish=self._suggest_dish(restaurant),
        )

    def _suggest_dish(self, restaurant: Restaurant) -> Optional[SuggestedDish]:
        """Lớp 5 của đề án: gợi ý MÓN đi kèm từng quán, không phải danh sách rời."""
        rule = None
        confidence = None

        if self._rule_predictor is not None and self._rule_predictor.is_available:
            predicted_id = self._rule_predictor.predict_rule_id(
                restaurant.category, restaurant.cuisine
            )
            if predicted_id:
                rule = next(
                    (r for r in self._dish_knowledge.list_rules() if r.id == predicted_id),
                    None,
                )
                if rule:
                    confidence = CONFIDENCE_ML

        if rule is None:
            # TÊN QUÁN trước, LOẠI HÌNH sau. Đo trên dataset thật: 144 quán có "phở" trong
            # TÊN nhưng chỉ 14 quán có "phở" trong categoryName - tên quán mang tín hiệu
            # món ăn gấp ~10 lần.
            #
            # Bug thật khi chỉ dùng categoryName: quán "Bún Chả - Nem Cua Bê" bị Google
            # gắn nhãn "Nhà hàng ăn nhanh" nên được gợi ý món... "Gà rán".
            rule = self._dish_knowledge.match_rule_for_category(restaurant.name)
            if rule is None:
                rule = self._dish_knowledge.match_rule_for_category(restaurant.category)

        if rule is None or not rule.dishes:
            return None

        dish: Dish = rule.dishes[0]
        return SuggestedDish(
            dish_id=f"{rule.id}:{text_relevance.normalize(dish.name).replace(' ', '-')}",
            name=dish.name,
            cuisine=dish.cuisine,
            spice_level=dish.spice_level,
            temperature=dish.temperature,
            confidence=confidence or rule.confidence,
            reason=(
                "suy luận từ loại hình quán, chưa phải thực đơn thật"
                if (confidence or rule.confidence) != "specific"
                else "khớp loại hình cụ thể của quán"
            ),
        )

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
from dataclasses import dataclass, replace
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
from src.domain.services import dish_matching, search_ranking
from src.domain.services.closure_reports import ClosureReportTally
from src.domain.services.search_ranking import DEFAULT_MAX_DISTANCE_KM
from src.domain.value_objects.context_signal import NEUTRAL_CONTEXT, ContextSignal
from src.domain.value_objects.location import (
    HANOI_CENTER_LAT,
    HANOI_CENTER_LNG,
    Location,
)
from src.domain.value_objects.mood import MOOD_PROFILES, normalize_mood
from src.domain.value_objects.price import has_known_price

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
    # Công tắc "Chỉ hiện quán có ghi giá" (bản vẽ `Filler.png`). Xem `_loc_theo_gia` về
    # việc vì sao nó phải kèm cảnh báo thay vì lặng lẽ cắt danh sách.
    only_with_price: bool = False


class FindRestaurantsForDishUseCase:
    def __init__(
        self,
        catalog: DishCatalogRepository,
        dish_restaurant_index: Mapping[str, Sequence],
        context_provider: Optional[ContextProvider] = None,
        closure_tally: Optional[ClosureReportTally] = None,
    ) -> None:
        self._catalog = catalog
        self._index = dish_restaurant_index
        self._context_provider = context_provider
        self._closure_tally = closure_tally

    @property
    def _bi_bao_dong(self):
        """Vị từ "quán này đã bị báo đóng cửa chưa", đưa xuống tầng xếp hạng.

        `None` khi chưa lắp bộ đếm, và `rank_restaurants` hiểu `None` là không lọc gì thêm.
        """
        return self._closure_tally.is_reported_closed if self._closure_tally else None

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

        tat_ca = list(self._index.get(dish.identifier, ()))
        matches = self._loc_theo_gia(tat_ca, query, warnings)
        # Câu này nói về CHỈ MỤC MÓN-QUÁN, nên phải hỏi `tat_ca` chứ không phải `matches`:
        # khi bộ lọc giá vét sạch danh sách thì lý do là THIẾU DỮ LIỆU GIÁ, và
        # `_loc_theo_gia` đã nói đúng lý do đó rồi. Dán thêm câu "chưa quán nào khớp món"
        # vào đấy là đổ tội cho khâu đối chiếu tên quán, một chẩn đoán sai.
        if not tat_ca:
            # Không có quán nào là kết quả THẬT, không phải lỗi. Nói rõ thay vì trả 404:
            # món vẫn tồn tại, chỉ là chưa quán nào trong dataset khớp.
            warnings.append(
                f"Chưa có quán nào trong dữ liệu khớp món '{dish.name}'. "
                "Dữ liệu quán được đối chiếu theo TÊN QUÁN, nên quán có bán nhưng không "
                "ghi tên món thì không tìm ra được."
            )

        # XẾP HAI TẦNG. Quán có TÊN chứa tên món luôn đứng trên quán chỉ được review nhắc
        # tới, bất kể điểm xếp hạng - vì hai tín hiệu này khác hẳn nhau về độ tin cậy.
        #
        # Bug thật khi trộn chung (đo trên 40.720 quán): trang món "Bún chả" xếp
        # "Nhà Hàng Hoàng" (870m, chỉ có review nhắc) TRÊN "Bun Cha Nem Cua Be" (310m,
        # tên quán ghi rõ) chỉ vì quán trước có điểm đánh giá còn quán sau chưa có.
        limit = max(1, min(query.limit, MAX_LIMIT))
        mood_weights = self._mood_weights(query.mood, warnings)

        # BA TẦNG, xếp lần lượt: tên quán ghi ĐÚNG TÊN MÓN -> khớp từ khoá chung ->
        # chỉ được review nhắc tới. Tầng dưới chỉ được dùng khi tầng trên chưa đủ `limit`.
        #
        # Tầng 1 tồn tại vì Phở bò / Phở gà / Phở dùng chung từ khoá "phở", nên nếu chỉ có
        # hai tầng thì ba trang món trả về danh sách hệt nhau và việc "chọn món" thành vô
        # nghĩa. Có tầng 1 thì trang Phở gà đẩy 202 quán ghi rõ "phở gà" lên trước.
        theo_tang: dict = {}
        for m in matches:
            theo_tang.setdefault(m.strength, []).append(m.restaurant)
        # NGUỒN KHỚP THẬT của từng quán, lấy từ chỉ mục món. Bug thật 2026-09-16: trang món
        # trả `match_source="mood"` cho MỌI quán dù không gửi mood - vì ở đây xếp hạng
        # không có câu tìm kiếm nên danh sách nguồn rỗng, và `RankedRestaurant` gán nhãn
        # mặc định "mood" cho danh sách rỗng. Tra theo `id()` vì chỉ mục giữ đúng đối
        # tượng quán được đưa vào xếp hạng (không phải bản sao).
        nguon_khop = {id(m.restaurant): m.match_source for m in matches}

        ranked: List = []
        so_quan_yeu = 0
        for strength in sorted(theo_tang, reverse=True):
            if len(ranked) >= limit:
                break
            phan = search_ranking.rank_restaurants(
                restaurants=theo_tang[strength], origin=origin,
                mood_weights=mood_weights, context=context,
                max_distance_km=query.max_distance_km, limit=limit - len(ranked),
                is_reported_closed=self._bi_bao_dong,
            )
            if strength == dish_matching.MATCH_STRENGTH[dish_matching.MATCHED_BY_REVIEW]:
                so_quan_yeu = len(phan)
            # Đánh lại số thứ tự cho liền mạch sau khi ghép các tầng.
            ranked = ranked + [
                replace(
                    item,
                    rank_position=len(ranked) + i + 1,
                    match_sources=self._match_sources(
                        nguon_khop.get(id(item.restaurant)), mood_weights
                    ),
                )
                for i, item in enumerate(phan)
            ]

        if so_quan_yeu:
            warnings.append(
                f"{so_quan_yeu} quán ở cuối danh sách chỉ được NHẮC TỚI trong review "
                f"là có '{dish.name}', chưa chắc chắn bằng quán ghi rõ tên món."
            )

        self._warn_if_matched_by_category(ranked, nguon_khop, dish, warnings)

        self._warn_if_radius_was_widened(ranked, query, dish, warnings)

        return SearchResult(
            search_query_id=str(uuid.uuid4()),
            results=[self._to_item(r, dish) for r in ranked],
            context=context.describe(),
            warnings=warnings,
        )

    # --- các bước con -------------------------------------------------------

    @staticmethod
    def _loc_theo_gia(matches, query: RestaurantsForDishQuery, warnings: List[str]):
        """Giữ lại quán ĐỌC ĐƯỢC giá, và nói ra đã bỏ bao nhiêu quán.

        ⚠️ ĐÂY LÀ BỘ LỌC ĐẮT NHẤT CỦA SẢN PHẨM. Đo 2026-09-23: chỉ 671/52.872 quán (1,3%)
        có ô giá đọc được, và trong bán kính 10km quanh trung tâm Hà Nội thì 47.571 cặp
        quán-món chỉ còn 1.293 (2,7%). Ba nguồn quán chính (OSM, Overture, Wikidata) đều
        KHÔNG có trường giá; giá chỉ đến từ lớp làm giàu Apify.

        Vì vậy phải NÓI RA con số bị bỏ. Danh sách 40 quán tụt còn 1 mà không giải thích
        thì người dùng kết luận sai là "món này hiếm quán bán", trong khi sự thật là ta
        thiếu dữ liệu giá (CLAUDE.md mục 4 quy tắc 1 và mục 5).
        """
        if not query.only_with_price:
            return matches

        giu = [m for m in matches if has_known_price(m.restaurant.price)]
        bo = len(matches) - len(giu)
        if bo:
            warnings.append(
                f"Đang bật “chỉ quán có ghi giá”: đã bỏ {bo} quán vì dữ liệu chưa có giá "
                "của họ. Chưa có giá nghĩa là ta CHƯA BIẾT, không phải quán không niêm "
                "yết — tắt công tắc này để xem đầy đủ."
            )
        return giu

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
    def _warn_if_matched_by_category(
        ranked: List,
        nguon_khop: Mapping[int, Optional[str]],
        dish: Dish,
        warnings: List[str],
    ) -> None:
        """Nói ra số quán chỉ khớp bằng LOẠI HÌNH, không phải bằng tên quán.

        VÌ SAO CẦN (đo 2026-09-23 trên dữ liệu thật): trong chỉ mục món-quán có 32.118 cặp
        khớp bằng TÊN quán và 14.353 cặp chỉ khớp bằng `categoryName` — nhưng cả hai nằm
        CÙNG một bậc `MATCH_STRENGTH`, nên khi xếp hạng chúng cạnh tranh ngang nhau. Đo
        trên 120 trang món: 10 trang có quán chỉ khớp loại hình lọt top-20 trong khi vẫn
        còn quán khớp tên (71 quán). Bật bộ lọc "chỉ quán có ghi giá" thì tỷ lệ này thành
        áp đảo: trang "Gà rán" còn lại 62 quán thì CẢ 62 đều là khớp loại hình, đầu danh
        sách là quán trứng nướng và bánh tráng.

        CLAUDE.md mục 4 quy tắc 6 đã chốt "ưu tiên TÊN QUÁN hơn `categoryName`", nhưng bậc
        xếp hạng hiện chưa thực hiện điều đó. Sửa bậc sẽ đổi thứ tự trên diện rộng nên phải
        hỏi chủ dự án trước; trong lúc chờ, ít nhất KHÔNG ĐƯỢC im lặng — thẻ quán đã ghi
        "Khớp loại hình" nhưng không ai đếm hộ người dùng xem cả danh sách yếu tới mức nào.
        """
        so_quan = sum(
            1 for r in ranked if nguon_khop.get(id(r.restaurant)) == dish_matching.FIELD_CATEGORY
        )
        if not so_quan:
            return
        if so_quan == len(ranked):
            warnings.append(
                f"CẢ {so_quan} quán trong danh sách chỉ khớp theo LOẠI HÌNH quán "
                f"(ví dụ 'Nhà hàng ăn nhanh'), không quán nào ghi '{dish.name}' trong tên. "
                "Đây là tín hiệu yếu — rất có thể quán không bán đúng món bạn chọn."
            )
        else:
            warnings.append(
                f"{so_quan} quán trong danh sách chỉ khớp theo LOẠI HÌNH quán, không phải "
                f"theo tên quán — yếu hơn quán ghi rõ '{dish.name}'."
            )

    @staticmethod
    def _match_sources(dish_match_source: Optional[str], mood_weights) -> List[str]:
        """Nguồn khớp món + "mood" CHỈ KHI người dùng thật sự gửi mood hợp lệ."""
        sources = [dish_match_source] if dish_match_source else []
        if mood_weights:
            sources.append("mood")
        return sources

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
            temporarily_closed=restaurant.temporarily_closed,
            source_updated_at=restaurant.source_updated_at,
            source_datasets=list(restaurant.source_datasets),
            surveyed_at=restaurant.surveyed_at,
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

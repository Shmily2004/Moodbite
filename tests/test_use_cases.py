"""Test tầng application: use case chạy với repository GIẢ, không đụng file thật."""
import pytest

from src.application.errors import DataNotReadyError
from src.application.use_cases.get_restaurant_details import (
    GetRestaurantDetailsUseCase,
)
from src.application.use_cases.log_interaction import (
    InvalidInteractionError,
    LogInteractionCommand,
    LogInteractionUseCase,
    RestaurantNotFoundError,
)
from src.application.use_cases.search_restaurants import (
    SearchQuery,
    SearchRestaurantsUseCase,
)
from src.domain.entities.interaction import ActionType, InteractionEvent
from tests.fakes import (
    GENERIC_RULE,
    PHO_RULE,
    BrokenContextProvider,
    FakeDetailsRepo,
    FakeDishKnowledge,
    FakeInteractionRepo,
    FakeRestaurantRepo,
    StubPredictor,
    make_restaurant,
)

SESSION = "3f9a0000-0000-4000-8000-000000000000"


def build_search(restaurants, rules=None, predictor=None, context=None):
    return SearchRestaurantsUseCase(
        restaurants=FakeRestaurantRepo(restaurants),
        dish_knowledge=FakeDishKnowledge(rules or [PHO_RULE, GENERIC_RULE]),
        context_provider=context,
        rule_predictor=predictor,
    )


# --- SearchRestaurantsUseCase ------------------------------------------------


def test_search_returns_ranked_results_with_query_id():
    use_case = build_search([make_restaurant("A"), make_restaurant("B", lat=21.05)])
    result = use_case.execute(SearchQuery(session_id=SESSION))
    assert result.search_query_id
    assert [r.rank_position for r in result.results] == [1, 2]


def test_search_nests_dish_inside_each_result():
    """Đặc tả API mục 4: món KHÔNG phải endpoint riêng, mà là trường trên từng kết quả."""
    use_case = build_search([make_restaurant("Quan Pho", category="Nhà hàng phở")])
    result = use_case.execute(SearchQuery(session_id=SESSION))
    dish = result.results[0].suggested_dish
    assert dish is not None
    assert dish.name == "Phở bò"
    assert dish.confidence == "specific"


def test_search_marks_ml_confidence_when_predictor_used():
    use_case = build_search(
        [make_restaurant("Quan Pho", category="Quán phở")],
        predictor=StubPredictor({"Quán phở": "pho"}),
    )
    result = use_case.execute(SearchQuery(session_id=SESSION))
    assert result.results[0].suggested_dish.confidence == "ml"


def test_search_free_text_beats_mood_shortcut():
    """Câu tự do là thứ người dùng CHỦ ĐỘNG nói ra -> ưu tiên hơn nút mood."""
    cozy = make_restaurant("Quan Am Cung", comfort_cozy_score=1.0)
    fresh = make_restaurant("Salad Bar", fresh_healthy_score=1.0)
    use_case = build_search([cozy, fresh])

    result = use_case.execute(
        SearchQuery(session_id=SESSION, query_text="đang buồn muốn ăn ấm bụng", mood="happy")
    )
    assert result.results[0].name == "Quan Am Cung"


def test_search_warns_instead_of_silently_ignoring_dietary_filter():
    """Dataset không có dữ liệu chế độ ăn - phải NÓI RÕ thay vì lặng lẽ bỏ qua."""
    use_case = build_search([make_restaurant("A")])
    result = use_case.execute(
        SearchQuery(session_id=SESSION, dietary_restrictions=["vegetarian"])
    )
    assert any("chế độ ăn" in w for w in result.warnings)


def test_search_warns_when_nothing_matches_the_text():
    use_case = build_search([make_restaurant("A", category="Quán ăn")])
    result = use_case.execute(
        SearchQuery(session_id=SESSION, query_text="zzzqqq khong ton tai")
    )
    assert result.results, "vẫn phải trả kết quả thay vì rỗng"
    assert any("không khớp" in w.lower() or "Không quán nào" in w for w in result.warnings)


def test_search_survives_broken_context_provider():
    """API thời tiết hỏng KHÔNG được làm hỏng lượt tìm kiếm."""
    use_case = build_search([make_restaurant("A")], context=BrokenContextProvider())
    result = use_case.execute(SearchQuery(session_id=SESSION))
    assert len(result.results) == 1


def test_search_invalid_mood_shortcut_warns_but_still_returns():
    use_case = build_search([make_restaurant("A")])
    result = use_case.execute(SearchQuery(session_id=SESSION, mood="hungry"))
    assert result.results
    assert any("hungry" in w for w in result.warnings)


def test_search_raises_when_data_not_ready():
    use_case = SearchRestaurantsUseCase(
        restaurants=FakeRestaurantRepo([], ready=False),
        dish_knowledge=FakeDishKnowledge([]),
    )
    with pytest.raises(DataNotReadyError):
        use_case.execute(SearchQuery(session_id=SESSION))


def test_search_distance_reported_in_metres():
    use_case = build_search([make_restaurant("A", lat=21.0285, lng=105.8542)])
    result = use_case.execute(
        SearchQuery(session_id=SESSION, latitude=21.0285, longitude=105.8542)
    )
    assert result.results[0].distance_m == 0


# --- LogInteractionUseCase ---------------------------------------------------


def build_log(restaurants=None):
    repo = FakeInteractionRepo()
    use_case = LogInteractionUseCase(
        interactions=repo,
        restaurants=FakeRestaurantRepo(restaurants or [make_restaurant("A")]),
    )
    return use_case, repo


def test_log_interaction_writes_event():
    use_case, repo = build_log()
    logged = use_case.execute(
        LogInteractionCommand(
            session_id=SESSION, restaurant_id="id-A", action_type="save"
        )
    )
    assert logged.interaction_event_id
    assert logged.is_positive_signal is True
    assert len(repo.events) == 1


def test_view_detail_requires_dwell_time():
    """Không có dwell_time thì không phân biệt được "xem thật" với "bấm nhầm"."""
    use_case, _ = build_log()
    with pytest.raises(InvalidInteractionError):
        use_case.execute(
            LogInteractionCommand(
                session_id=SESSION, restaurant_id="id-A", action_type="view_detail"
            )
        )


def test_short_view_is_not_a_positive_signal():
    use_case, _ = build_log()
    quick = use_case.execute(
        LogInteractionCommand(
            session_id=SESSION, restaurant_id="id-A",
            action_type="view_detail", dwell_time_ms=500,
        )
    )
    assert quick.is_positive_signal is False

    long = use_case.execute(
        LogInteractionCommand(
            session_id=SESSION, restaurant_id="id-A",
            action_type="view_detail", dwell_time_ms=9000,
        )
    )
    assert long.is_positive_signal is True


def test_explicit_negative_is_not_positive():
    use_case, _ = build_log()
    logged = use_case.execute(
        LogInteractionCommand(
            session_id=SESSION, restaurant_id="id-A", action_type="explicit_negative"
        )
    )
    assert logged.is_positive_signal is False


def test_unknown_action_type_rejected():
    use_case, _ = build_log()
    with pytest.raises(InvalidInteractionError):
        use_case.execute(
            LogInteractionCommand(
                session_id=SESSION, restaurant_id="id-A", action_type="teleport"
            )
        )


def test_interaction_for_unknown_restaurant_rejected():
    """Ghi tương tác cho quán không tồn tại sẽ tạo nhãn rác cho mô hình sau này."""
    use_case, _ = build_log()
    with pytest.raises(RestaurantNotFoundError):
        use_case.execute(
            LogInteractionCommand(
                session_id=SESSION, restaurant_id="khong-ton-tai", action_type="save"
            )
        )


def test_interaction_for_soft_deleted_restaurant_rejected():
    use_case, _ = build_log([make_restaurant("An", is_active=False)])
    with pytest.raises(RestaurantNotFoundError):
        use_case.execute(
            LogInteractionCommand(
                session_id=SESSION, restaurant_id="id-An", action_type="save"
            )
        )


def test_missing_session_id_rejected():
    use_case, _ = build_log()
    with pytest.raises(InvalidInteractionError):
        use_case.execute(
            LogInteractionCommand(session_id="", restaurant_id="id-A", action_type="save")
        )


def test_is_positive_signal_computed_on_entity():
    event = InteractionEvent(
        session_id=SESSION, restaurant_id="r1", action_type=ActionType.GET_DIRECTIONS
    )
    assert event.is_positive_signal is True


# --- GetRestaurantDetailsUseCase ---------------------------------------------


def test_details_returns_has_details_false_instead_of_404():
    out = GetRestaurantDetailsUseCase(FakeDetailsRepo({})).execute("unknown-id")
    assert out.has_details is False
    assert out.reason
    assert out.place_id == "unknown-id"


def test_details_maps_raw_fields():
    raw = {
        "title": "Quán A",
        "price": "100-200 N ₫",
        "imageUrls": ["http://img/1.jpg"],
        "reviews": [{"stars": 5, "text": "ngon"}],
        "url": "http://maps.google/x",
    }
    out = GetRestaurantDetailsUseCase(FakeDetailsRepo({"p1": raw})).execute("p1")
    assert out.has_details is True
    assert out.name == "Quán A"
    assert out.price == "100-200 N ₫"
    assert out.google_maps_url == "http://maps.google/x"


def test_details_raises_when_source_not_ready():
    with pytest.raises(DataNotReadyError):
        GetRestaurantDetailsUseCase(FakeDetailsRepo({}, ready=False)).execute("p1")


# --- Bộ lọc ràng buộc cứng ---------------------------------------------------


def _ctx(weekday=0, minute=12 * 60):
    from src.domain.value_objects.context_signal import ContextSignal
    from tests.fakes import FixedContextProvider

    return FixedContextProvider(ContextSignal(weekday=weekday, minute_of_day=minute))


def test_opening_hours_filter_removes_closed_restaurants():
    """Quán ĐANG ĐÓNG phải bị loại khi client yêu cầu 'now'."""
    open_now = make_restaurant("Dang Mo", opening_hours="Mo-Su 06:00-22:00")
    closed_now = make_restaurant("Dang Dong", opening_hours="Mo-Su 18:00-23:00")
    use_case = build_search([open_now, closed_now], context=_ctx(minute=12 * 60))

    result = use_case.execute(
        SearchQuery(session_id=SESSION, opening_hours_constraint="now")
    )
    assert [r.name for r in result.results] == ["Dang Mo"]


def test_opening_hours_filter_keeps_restaurants_without_data():
    """Chỉ ~25% quán có dữ liệu giờ. Loại quán thiếu dữ liệu = xoá 3/4 dataset."""
    known = make_restaurant("Co Gio", opening_hours="Mo-Su 06:00-22:00")
    unknown = make_restaurant("Khong Ro Gio", opening_hours=None)
    use_case = build_search([known, unknown], context=_ctx(minute=12 * 60))

    names = [
        r.name
        for r in use_case.execute(
            SearchQuery(session_id=SESSION, opening_hours_constraint="now")
        ).results
    ]
    assert "Khong Ro Gio" in names, "thiếu dữ liệu KHÔNG được coi là đóng cửa"


def test_opening_hours_filter_accepts_explicit_time():
    late = make_restaurant("Quan Dem", opening_hours="Mo-Su 18:00-02:00")
    morning = make_restaurant("Quan Sang", opening_hours="Mo-Su 06:00-11:00")
    use_case = build_search([late, morning], context=_ctx(weekday=0))

    result = use_case.execute(
        SearchQuery(session_id=SESSION, opening_hours_constraint="20:00")
    )
    assert [r.name for r in result.results] == ["Quan Dem"]


def test_opening_hours_filter_skipped_when_everything_would_be_removed():
    """Thà bỏ lọc còn hơn trả về danh sách rỗng."""
    closed = make_restaurant("Dong Het", opening_hours="Mo-Su 18:00-23:00")
    use_case = build_search([closed], context=_ctx(minute=9 * 60))
    result = use_case.execute(
        SearchQuery(session_id=SESSION, opening_hours_constraint="now")
    )
    assert len(result.results) == 1


def test_dietary_filter_keeps_matching_and_undeclared():
    veg = make_restaurant("Quan Chay", dietary=["vegetarian"])
    meat = make_restaurant("Quan Thit", dietary=["halal"])
    unknown = make_restaurant("Chua Khai Bao")
    use_case = build_search([veg, meat, unknown])

    names = [
        r.name
        for r in use_case.execute(
            SearchQuery(session_id=SESSION, dietary_restrictions=["vegetarian"])
        ).results
    ]
    assert "Quan Chay" in names
    assert "Chua Khai Bao" in names, "chưa khai báo != không phục vụ"
    assert "Quan Thit" not in names, "khai báo KHÁC yêu cầu thì loại"


def test_district_filter_matches_ignoring_accents_and_case():
    cau_giay = make_restaurant("Quan CG", district="Phường Cầu Giấy")
    hoan_kiem = make_restaurant("Quan HK", district="Phường Hoàn Kiếm")
    use_case = build_search([cau_giay, hoan_kiem])

    names = [
        r.name
        for r in use_case.execute(
            SearchQuery(session_id=SESSION, district="phuong cau giay")
        ).results
    ]
    assert names == ["Quan CG"]


def test_district_filter_skipped_when_no_match():
    use_case = build_search([make_restaurant("A", district="Phường Cầu Giấy")])
    result = use_case.execute(SearchQuery(session_id=SESSION, district="Không Tồn Tại"))
    assert len(result.results) == 1
    assert any("bỏ qua bộ lọc quận" in w for w in result.warnings)


def test_search_result_exposes_provenance_fields():
    """Client phải biết quán này ở đâu ra để hiển thị minh bạch."""
    r = make_restaurant("A", district="Phường Tây Hồ", source="openstreetmap",
                        dietary=["vegan"], amenities=["wifi"])
    item = build_search([r]).execute(SearchQuery(session_id=SESSION)).results[0]
    assert item.district == "Phường Tây Hồ"
    assert item.source == "openstreetmap"
    assert item.dietary == ["vegan"]
    assert item.amenities == ["wifi"]

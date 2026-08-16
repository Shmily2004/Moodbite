"""Khoá lại quy tắc XẾP HẠNG và SO KHỚP VĂN BẢN - tầng domain, thuần Python.

Không cần file dữ liệu, không cần FastAPI, không cần mạng.
"""
import pytest

from src.domain.services import search_ranking, text_relevance
from src.domain.services.search_ranking import DEFAULT_MAX_DISTANCE_KM
from src.domain.value_objects.context_signal import (
    ContextSignal,
    MealTime,
    WeatherCondition,
)
from src.domain.value_objects.location import Location
from src.domain.value_objects.mood import (
    MOOD_PROFILES,
    MOOD_SCORE_COLUMNS,
    MOOD_TO_SCORE_COLUMN,
    UnsupportedMoodError,
    normalize_mood,
)
from tests.fakes import make_restaurant

HOAN_KIEM = Location(lat=21.0285, lng=105.8542)


def rank(restaurants, **kwargs):
    kwargs.setdefault("limit", 10)
    return search_ranking.rank_restaurants(
        restaurants=restaurants, origin=HOAN_KIEM, **kwargs
    )


# --- So khớp câu tìm kiếm tự do ----------------------------------------------


def test_whole_word_matching_not_substring():
    """Bug thật: khớp CHUỖI CON làm "bo" khớp cả "bột", "bọt", "bong"..., khiến truy vấn
    "phở bò" trả về quán bánh tráng. Phải khớp theo TỪ NGUYÊN VẸN."""
    pho = make_restaurant("Phở Bò 83", category="Nhà hàng phở")
    banh_trang = make_restaurant(
        "Bánh Tráng Bé My", category="Quán ăn",
        review_text="bột ngon, nước bọt, bong bóng",
    )
    assert text_relevance.relevance(pho, "phở bò").score > 0
    assert text_relevance.relevance(banh_trang, "phở bò").score == 0.0


def test_accent_stripping_can_collide_but_ranking_still_correct():
    """ĐÁNH ĐỔI CÓ CHỦ ĐÍCH: bỏ dấu để người gõ "pho bo" tìm được "Phở Bò", nhưng khi đó
    "bỏ" và "bò" cùng thành "bo" nên vẫn khớp nhau.

    Điều PHẢI đúng là THỨ HẠNG: quán tên đúng luôn đứng trên quán chỉ trùng âm.
    """
    pho = make_restaurant("Phở Bò 83", category="Nhà hàng phở")
    collide = make_restaurant(
        "Quán Ăn Vặt", category="Quán ăn", review_text="bỏ thêm trứng rất ngon"
    )
    assert text_relevance.relevance(collide, "phở bò").score > 0  # va chạm là có thật
    out = rank([collide, pho], query_text="phở bò", max_distance_km=None)
    assert out[0].restaurant.name == "Phở Bò 83"


def test_restaurant_name_outranks_incidental_review_mention():
    """Quán TÊN "Phở Bò" phải thắng quán chỉ tình cờ nhắc "phở bò" trong review."""
    named = make_restaurant("Phở Bò 83", category="Nhà hàng phở")
    mentioned = make_restaurant(
        "Quán Nhậu Bình Dân", category="Quán ăn",
        review_text="hôm trước ăn phở bò ở đâu đó cũng được",
    )
    out = rank([named, mentioned], query_text="phở bò", max_distance_km=None)
    assert out[0].restaurant.name == "Phở Bò 83"


def test_relevance_is_zero_without_query():
    r = make_restaurant("A")
    assert text_relevance.relevance(r, None).score == 0.0
    assert text_relevance.relevance(r, "   ").score == 0.0


def test_accent_insensitive_matching():
    """Người dùng gõ không dấu vẫn phải tìm được."""
    r = make_restaurant("Phở Thìn", category="Nhà hàng phở")
    assert text_relevance.relevance(r, "pho thin").score > 0


def test_match_source_reports_where_it_matched():
    """Giao diện phải nói thật vì sao quán này được gợi ý."""
    r = make_restaurant("Cà Phê AnAn", category="Quán cà phê")
    out = rank([r], query_text="cà phê", max_distance_km=None)
    assert "name" in out[0].match_sources or "category" in out[0].match_sources


def test_infer_mood_from_free_text():
    """Cầu nối cho 92% quán KHÔNG có review: hiểu ý câu rồi dùng mood-score có sẵn."""
    weights = text_relevance.infer_mood_weights("muốn ăn gì đó ấm bụng vì đang buồn")
    assert weights and weights.get("comfort_cozy_score", 0) > 0

    assert text_relevance.infer_mood_weights("abcxyz") is None
    assert text_relevance.infer_mood_weights(None) is None


# --- Xếp hạng ----------------------------------------------------------------


def test_distance_breaks_tie_between_equal_restaurants():
    near = make_restaurant("Gan", lat=21.03, lng=105.85)
    far = make_restaurant("Xa", lat=21.10, lng=105.90)
    out = rank([near, far])
    assert [r.restaurant.name for r in out] == ["Gan", "Xa"]


def test_far_restaurant_excluded_by_default_radius():
    """Quán cách ~31km vẫn lọt top vì khoảng cách chỉ là tiêu chí phụ."""
    far = make_restaurant("Xa Tit Tap", lat=20.90, lng=105.57, comfort_cozy_score=1.0)
    near = make_restaurant("Gan Nha", lat=21.03, lng=105.85, comfort_cozy_score=0.2)
    names = [r.restaurant.name for r in rank([far, near])]
    assert names == ["Gan Nha"]


def test_radius_filter_skipped_when_it_would_empty_results():
    """Thà gợi ý quán xa còn hơn trả về danh sách rỗng."""
    only = make_restaurant("Chi Co Quan Nay", lat=20.90, lng=105.57)
    out = rank([only], max_distance_km=1.0)
    assert [r.restaurant.name for r in out] == ["Chi Co Quan Nay"]


def test_missing_rating_uses_neutral_not_zero():
    """Quán chưa có đánh giá KHÔNG phải quán dở (quy tắc Cold Start)."""
    no_rating = make_restaurant("Chua Danh Gia", rating=None)
    low_rating = make_restaurant("Danh Gia Thap", rating=1.0)
    out = rank([low_rating, no_rating])
    assert out[0].restaurant.name == "Chua Danh Gia"
    # Giá trị TRẢ VỀ vẫn phải là None, không bị biến thành số.
    assert out[0].restaurant.rating is None


def test_soft_deleted_restaurant_never_returned():
    """is_active=false phải bị ẩn hoàn toàn khỏi kết quả người dùng."""
    hidden = make_restaurant("Da An", is_active=False, comfort_cozy_score=1.0)
    visible = make_restaurant("Con Hoat Dong")
    names = [r.restaurant.name for r in rank([hidden, visible])]
    assert names == ["Con Hoat Dong"]


def test_predicted_score_stays_in_zero_one():
    r = make_restaurant("A", rating=5.0, comfort_cozy_score=1.0)
    out = rank([r], query_text="ấm cúng", mood_weights=MOOD_PROFILES["sad"])
    assert 0.0 <= out[0].predicted_score <= 1.0


def test_rank_position_starts_at_one_and_is_sequential():
    out = rank([make_restaurant(f"R{i}", lat=21.03 + i / 1000) for i in range(3)])
    assert [r.rank_position for r in out] == [1, 2, 3]


def test_limit_is_respected():
    out = rank([make_restaurant(f"R{i}") for i in range(20)], limit=5)
    assert len(out) == 5


# --- Tín hiệu ngữ cảnh -------------------------------------------------------


def test_rain_biases_towards_comfort_food():
    """Đề án: cùng một quán hợp lúc nắng nhưng không hợp lúc mưa."""
    cozy = make_restaurant("Quan Lau Am", comfort_cozy_score=1.0)
    fresh = make_restaurant("Salad Bar", fresh_healthy_score=1.0)

    rainy = ContextSignal(weather=WeatherCondition.RAIN, temperature_c=18)
    names = [r.restaurant.name for r in rank([cozy, fresh], context=rainy)]
    assert names[0] == "Quan Lau Am"

    hot = ContextSignal(weather=WeatherCondition.CLEAR, temperature_c=35)
    names = [r.restaurant.name for r in rank([cozy, fresh], context=hot)]
    assert names[0] == "Salad Bar"


def test_meal_time_derived_from_hour():
    assert MealTime.from_hour(7) == MealTime.BREAKFAST
    assert MealTime.from_hour(12) == MealTime.LUNCH
    assert MealTime.from_hour(19) == MealTime.DINNER
    assert MealTime.from_hour(2) == MealTime.LATE_NIGHT


def test_neutral_context_has_no_bias():
    assert ContextSignal().mood_bias() == {}


def test_context_describe_is_human_readable():
    ctx = ContextSignal(
        meal_time=MealTime.DINNER, weather=WeatherCondition.RAIN, temperature_c=24
    )
    described = ctx.describe()
    assert "buổi tối" in described and "trời mưa" in described


# --- Mood --------------------------------------------------------------------


def test_every_mood_score_column_is_used_by_some_mood():
    """cheap_budget_score và quick_fast_score từng được tính ra nhưng không mood nào dùng."""
    used = {col for weights in MOOD_PROFILES.values() for col in weights}
    assert used == set(MOOD_SCORE_COLUMNS)


def test_sad_and_relaxed_are_distinguishable():
    cheap_cozy = make_restaurant("Quan Re", comfort_cozy_score=0.8, cheap_budget_score=0.9)
    pricey_cozy = make_restaurant("Cafe San Vuon", comfort_cozy_score=0.8, cheap_budget_score=0.0)
    sad = [r.restaurant.name for r in rank([cheap_cozy, pricey_cozy], mood_weights=MOOD_PROFILES["sad"])]
    relaxed = [r.restaurant.name for r in rank([cheap_cozy, pricey_cozy], mood_weights=MOOD_PROFILES["relaxed"])]
    assert sad != relaxed


def test_unknown_mood_raises():
    with pytest.raises(UnsupportedMoodError):
        normalize_mood("hungry")


def test_mood_is_case_insensitive_and_trimmed():
    assert normalize_mood("  SAD ") == "sad"


def test_primary_column_mapping_exposed():
    assert set(MOOD_TO_SCORE_COLUMN) == set(MOOD_PROFILES)


# --- Khoảng cách -------------------------------------------------------------


def test_distance_is_symmetric_and_zero_at_same_point():
    assert HOAN_KIEM.distance_km(HOAN_KIEM) == pytest.approx(0.0)
    other = Location(lat=21.03, lng=105.85)
    assert HOAN_KIEM.distance_km(other) == pytest.approx(other.distance_km(HOAN_KIEM))


def test_invalid_coordinates_rejected():
    with pytest.raises(ValueError):
        Location(lat=91.0, lng=0.0)
    with pytest.raises(ValueError):
        Location(lat=0.0, lng=181.0)


def test_default_radius_is_ten_km():
    assert DEFAULT_MAX_DISTANCE_KM == 10.0


# --- So khớp rule món ăn (domain/value_objects/text.py) ----------------------


def test_dish_rule_matches_unaccented_restaurant_name():
    """Nhiều quán tự đặt tên không dấu ("Pho Bo", "O Bun Cha") - phải khớp được."""
    from src.domain.entities.dish import Dish, DishRule

    rule = DishRule(id="pho", confidence="specific", match_category=["phở"],
                    dishes=[Dish(name="Phở bò")])
    assert rule.matches_text("Pho Bo") is True
    assert rule.matches_text("Phở Thìn Bờ Hồ") is True


def test_dish_rule_does_not_match_across_word_boundaries():
    """Bỏ dấu xong "ốc" thành "oc"; khớp chuỗi con sẽ khớp luôn "Ngọc"/"Cốc"/"Học"
    -> gợi ý món ốc cho quán chè."""
    from src.domain.entities.dish import Dish, DishRule

    rule = DishRule(id="oc", confidence="specific", match_category=["ốc"],
                    dishes=[Dish(name="Ốc luộc")])
    assert rule.matches_text("Quán Ốc Vi Sài Gòn") is True
    for false_positive in ("Chè Ngọc Anh", "Cốc Cốc Cafe", "Học viện ăn uống"):
        assert rule.matches_text(false_positive) is False, false_positive


def test_multi_word_keyword_matches_only_as_contiguous_phrase():
    from src.domain.entities.dish import Dish, DishRule

    rule = DishRule(id="bun_cha", confidence="specific", match_category=["bún chả"],
                    dishes=[Dish(name="Bún chả")])
    assert rule.matches_text("Quán Bún Chả Hương Liên") is True
    # "bún" và "chả" rời rạc, không liền nhau -> không được coi là bún chả.
    assert rule.matches_text("Bún riêu và chả cá") is False


def test_single_character_keyword_is_not_dropped():
    """Bug thật: bộ lọc "bỏ từ 1 ký tự" nuốt mất "ý" trong rule "nhà hàng ý", khiến rule
    đồ Ý rút gọn thành "nhà hàng" và khớp MỌI quán -> nhà hàng Nhật/Quảng Đông đều bị
    gợi ý "Mì Ý sốt bò bằm"."""
    from src.domain.entities.dish import Dish, DishRule

    rule = DishRule(id="y", confidence="specific", match_category=["nhà hàng ý"],
                    dishes=[Dish(name="Mì Ý sốt bò bằm")])
    assert rule.matches_text("Nhà hàng Ý Bella") is True
    assert rule.matches_text("Nhà hàng") is False, "rule đồ Ý không được khớp quán chung chung"
    assert rule.matches_text("HIRYU Japanese Restaurant") is False

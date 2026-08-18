"""Khoá lại quy tắc LỌC và XẾP HẠNG MÓN ĂN - tầng domain, thuần Python.

Không cần file dữ liệu, không cần FastAPI, không cần mạng. Nếu một test ở đây bắt buộc
phải import pandas/fastapi mới chạy được thì quy tắc đang nằm sai tầng (CLAUDE.md mục 2).
"""
import pytest

from src.domain.entities.dish import (
    MEAL_BREAKFAST,
    MEAL_DINNER,
    METHOD_GRILLED,
    METHOD_RAW,
    METHOD_SOUP,
    Dish,
    slugify_dish,
)
from src.domain.services import dish_ranking
from src.domain.services.dish_ranking import (
    NEUTRAL_SCORE,
    DishFilter,
    filter_dishes,
    rank_dishes,
)
from src.domain.value_objects.context_signal import (
    NEUTRAL_CONTEXT,
    ContextSignal,
    MealTime,
    WeatherCondition,
)

RAINY = ContextSignal(weather=WeatherCondition.RAIN)
HOT_DAY = ContextSignal(weather=WeatherCondition.CLEAR, temperature_c=35.0)


def make_dish(name, **kwargs):
    """Món tối giản. Mặc định KHÔNG điền gì thêm để mỗi test tự nói rõ nó quan tâm field nào."""
    return Dish(name=name, **kwargs)


def rank(dishes, f=None, context=NEUTRAL_CONTEXT, counts=None, **kwargs):
    return rank_dishes(
        dishes=dishes,
        f=f or DishFilter(),
        context=context,
        restaurant_counts=counts if counts is not None else {},
        **kwargs,
    )


# --- Hằng số xếp hạng --------------------------------------------------------


def test_weights_sum_to_one():
    """TỔNG TRỌNG SỐ = 1.0, nếu không `score` sẽ vượt ra ngoài [0,1] và mọi nhãn hiển thị
    ở frontend (thanh mức phù hợp) đều sai. Đổi trọng số phải đổi cả test này."""
    total = (
        dish_ranking.W_FILTER
        + dish_ranking.W_CONTEXT
        + dish_ranking.W_MOOD
        + dish_ranking.W_AVAILABILITY
    )
    assert total == pytest.approx(1.0)


def test_score_always_within_zero_and_one():
    dishes = [
        make_dish("Phở bò", temperature="hot", cooking_method=METHOD_SOUP,
                  mood_keywords=["comfort"], meal_times=[MEAL_BREAKFAST]),
        make_dish("Gỏi cuốn", temperature="cold", cooking_method=METHOD_RAW),
        make_dish("Món chưa nhập gì"),
    ]
    f = DishFilter(cooking_methods=[METHOD_SOUP], temperatures=["hot"],
                   mood="sad", weather="rain")
    for ranked in rank(dishes, f, RAINY, counts={"pho-bo": 40}):
        assert 0.0 <= ranked.score <= 1.0


# --- Bộ lọc CỨNG -------------------------------------------------------------


def test_hard_filter_removes_mismatching_dish():
    """Bấm "đồ nướng" thì phở phải biến mất - đó là điều người dùng vừa yêu cầu."""
    pho = make_dish("Phở bò", cooking_method=METHOD_SOUP)
    nuong = make_dish("Thịt nướng", cooking_method=METHOD_GRILLED)

    kept = filter_dishes([pho, nuong], DishFilter(cooking_methods=[METHOD_GRILLED]))

    assert kept == [nuong]


def test_hard_filter_keeps_dish_with_missing_data():
    """CHƯA BIẾT khác hẳn BIẾT LÀ KHÔNG PHẢI.

    Món chưa nhập `cooking_method` vẫn phải qua được bộ lọc, nếu không ta đang trừng phạt
    món chỉ vì mình chưa nhập đủ dữ liệu - đúng nguyên tắc đã áp cho quán thiếu giờ mở cửa.
    """
    chua_biet = make_dish("Món chưa nhập cách chế biến")
    nuong = make_dish("Thịt nướng", cooking_method=METHOD_GRILLED)

    kept = filter_dishes([chua_biet, nuong], DishFilter(cooking_methods=[METHOD_GRILLED]))

    assert chua_biet in kept


def test_empty_filter_keeps_everything():
    dishes = [make_dish("A"), make_dish("B", cooking_method=METHOD_SOUP)]
    assert filter_dishes(dishes, DishFilter()) == dishes


def test_filter_that_matches_nothing_falls_back_instead_of_white_screen():
    """Lọc xong rỗng -> trả nguyên danh sách. Thà đề xuất món chưa chắc khớp còn hơn đưa
    người dùng vào màn hình trắng không có lối ra."""
    dishes = [
        make_dish("Phở bò", cooking_method=METHOD_SOUP),
        make_dish("Bún riêu", cooking_method=METHOD_SOUP),
    ]
    kept = filter_dishes(dishes, DishFilter(cooking_methods=[METHOD_GRILLED]))
    assert kept == dishes


def test_spice_filter_uses_upper_bound():
    cay = make_dish("Bún bò Huế", spice_level=3)
    khong_cay = make_dish("Phở gà", spice_level=0)

    kept = filter_dishes([cay, khong_cay], DishFilter(max_spice_level=1))

    assert kept == [khong_cay]


# --- Ngữ cảnh: TRỜI MƯA ------------------------------------------------------


def test_rain_ranks_hot_soup_above_cold_raw_dish():
    """Quy tắc đề án: cùng một thứ hợp lúc nắng có thể không hợp lúc mưa."""
    pho = make_dish("Phở bò", temperature="hot", cooking_method=METHOD_SOUP)
    goi = make_dish("Gỏi cuốn", temperature="cold", cooking_method=METHOD_RAW)

    ranked = rank([goi, pho], context=RAINY)

    assert ranked[0].dish.name == "Phở bò"
    assert any("mưa" in reason for reason in ranked[0].reasons)


def test_hot_weather_prefers_cold_dish():
    kem = make_dish("Kem", temperature="cold")
    lau = make_dish("Lẩu", temperature="hot")

    ranked = rank([lau, kem], context=HOT_DAY)

    assert ranked[0].dish.name == "Kem"


def test_user_declared_weather_overrides_measured_weather():
    """Người dùng đang đứng ngoài đường, họ biết trời mưa rõ hơn API thời tiết."""
    pho = make_dish("Phở bò", temperature="hot", cooking_method=METHOD_SOUP)
    kem = make_dish("Kem", temperature="cold")

    # Đo được là trời quang, nhưng người dùng tự khai "mưa".
    ranked = rank([kem, pho], DishFilter(weather="rain"), context=HOT_DAY)

    assert ranked[0].dish.name == "Phở bò"


def test_invalid_weather_string_falls_back_without_crashing():
    """Tín hiệu ngữ cảnh hỏng KHÔNG được làm hỏng lượt tìm (CLAUDE.md mục 4 quy tắc 7)."""
    f = DishFilter(weather="mua-to-qua")
    assert dish_ranking.effective_weather(f, RAINY) == WeatherCondition.RAIN

    ranked = rank([make_dish("Phở bò")], f, RAINY)
    assert len(ranked) == 1


# --- Số quán bán món ---------------------------------------------------------


def test_dish_without_any_restaurant_ranks_below_identical_available_dish():
    """Món không tìm được quán là NGÕ CỤT với người dùng, dù nó hợp bộ lọc tới đâu."""
    co_quan = make_dish("Phở bò", temperature="hot")
    khong_quan = make_dish("Phở bò hiếm", temperature="hot")

    ranked = rank([khong_quan, co_quan], counts={"pho-bo": 30})

    assert ranked[0].dish.name == "Phở bò"
    assert ranked[0].restaurant_count == 30
    assert ranked[1].restaurant_count == 0


def test_availability_saturates_instead_of_growing_forever():
    """5 quán so với 1 quán là khác biệt thật; 120 quán so với 60 quán thì không - người
    dùng đằng nào cũng chỉ xem chục quán gần nhất."""
    assert dish_ranking._score_availability(0) == 0.0
    assert dish_ranking._score_availability(5) == pytest.approx(0.5)
    assert dish_ranking._score_availability(1000) < 1.0


# --- Tính tất định -----------------------------------------------------------


def test_ties_are_broken_by_name_so_order_is_stable():
    """Nhiều món cùng thiếu dữ liệu -> cùng điểm trung tính. Không chốt thứ tự phụ thì
    mỗi lần gọi ra một thứ tự khác và test sẽ chập chờn."""
    dishes = [make_dish("Xôi"), make_dish("Bánh mì"), make_dish("Cháo")]

    names = [r.dish.name for r in rank(dishes)]

    assert names == sorted(names)
    assert [r.rank_position for r in rank(dishes)] == [1, 2, 3]


def test_limit_is_respected():
    dishes = [make_dish(f"Món {i}") for i in range(30)]
    assert len(rank(dishes, limit=5)) == 5


# --- Bữa trong ngày ----------------------------------------------------------


def test_meal_time_matching_current_hour_gets_bonus():
    sang = make_dish("Xôi", meal_times=[MEAL_BREAKFAST])
    toi = make_dish("Lẩu", meal_times=[MEAL_DINNER])

    ranked = rank([toi, sang], context=ContextSignal(meal_time=MealTime.BREAKFAST))

    assert ranked[0].dish.name == "Xôi"


def test_afternoon_is_not_forced_into_a_meal():
    """Buổi chiều không phải bữa chính. Ép vào "trưa" hay "tối" đều làm lệch điểm."""
    assert dish_ranking._meal_time_key(MealTime.AFTERNOON) is None


# --- Mood --------------------------------------------------------------------


def test_dish_without_mood_tags_stays_neutral_not_zero():
    """Món chưa gắn tag mood là THIẾU DỮ LIỆU, không phải "không hợp"."""
    score, _ = dish_ranking._score_mood(make_dish("Món mới"), "sad")
    assert score == NEUTRAL_SCORE


def test_matching_mood_beats_mismatching_mood():
    comfort = make_dish("Cháo", mood_keywords=["comfort", "cozy"])
    fresh = make_dish("Salad", mood_keywords=["fresh"])

    ranked = rank([fresh, comfort], DishFilter(mood="sad"))

    assert ranked[0].dish.name == "Cháo"


# --- Entity Dish -------------------------------------------------------------


def test_slug_strips_accents_so_urls_stay_readable():
    assert slugify_dish("Phở Bò") == "pho-bo"
    assert slugify_dish("Bún đậu mắm tôm") == "bun-dau-mam-tom"


def test_identifier_falls_back_to_slug_of_name():
    assert make_dish("Phở bò").identifier == "pho-bo"
    assert make_dish("Phở bò", dish_id="pho-dac-biet").identifier == "pho-dac-biet"


def test_restaurant_matching_uses_whole_words_not_substrings():
    """Bug thật đã xảy ra ở chiều ngược lại: "oc" khớp "Ngọc" -> quán chè bị gợi ý món ốc.
    Chiều món -> quán dùng chung `contains_phrase` nên không được tái phạm."""
    oc = make_dish("Ốc")

    assert oc.matches_restaurant_text("Quán Ốc Hương")
    assert not oc.matches_restaurant_text("Chè Ngọc Anh")


def test_match_keywords_allow_admin_to_add_variants():
    """"Bún bò Huế" cũng nên khớp quán chỉ ghi "bún bò"."""
    dish = make_dish("Bún bò Huế", match_keywords=["bún bò huế", "bún bò"])

    assert dish.matches_restaurant_text("Bún Bò Gánh")


def test_has_ingredients_distinguishes_missing_from_empty():
    """UI phải nói "chưa có dữ liệu thành phần" chứ không hiện danh sách rỗng."""
    assert not make_dish("Món mới").has_ingredients
    assert make_dish("Phở bò", ingredients=["bánh phở", "thịt bò"]).has_ingredients

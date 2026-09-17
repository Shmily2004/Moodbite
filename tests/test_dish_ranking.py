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


# Bug thật 2026-09-16 (gọi API thật): mood "sad" và "excited" ra top-5 gần như y hệt
# (Đồ nhắm, Gà rán, Lẩu Thái...), điểm chỉ lệch ở chữ số thứ 4; "sad" và "relaxed" trùng
# 10/10 món. Nguyên nhân: `_score_mood` cũ là NHỊ PHÂN (có chung 1 tag -> 1.0), món tag
# ['cozy','spicy'] ăn trọn điểm cho CẢ sad lẫn excited, và sad/relaxed dùng CÙNG bộ tag.

CHAO = make_dish("Cháo nóng", mood_keywords=["comfort", "cozy"], temperature="hot",
                 cooking_method=METHOD_SOUP, spice_level=0, portion_size="regular")
LAU_THAI = make_dish("Lẩu Thái", mood_keywords=["spicy", "cozy"], temperature="hot",
                     cooking_method=METHOD_SOUP, spice_level=3, portion_size="heavy")
DO_NHAM = make_dish("Đồ nhắm", mood_keywords=["cozy", "spicy"], temperature="hot",
                    spice_level=1, portion_size="regular")
SALAD = make_dish("Salad", mood_keywords=["fresh"], temperature="cold",
                  cooking_method="tron", spice_level=0)
TRA_SUA = make_dish("Trà sữa trân châu", mood_keywords=["sweet"], temperature="cold",
                    spice_level=0, meal_times=["an_vat"])
MON_THEO_MOOD = [CHAO, LAU_THAI, DO_NHAM, SALAD, TRA_SUA]


@pytest.mark.parametrize("mood, expected_top", [
    ("sad", "Cháo nóng"),
    ("excited", "Lẩu Thái"),
    ("happy", "Salad"),
    ("relaxed", "Trà sữa trân châu"),
])
def test_moi_mood_dua_mot_mon_khac_len_dau(mood, expected_top):
    ranked = rank(MON_THEO_MOOD, DishFilter(mood=mood))
    assert ranked[0].dish.name == expected_top


def test_mood_cham_diem_co_BAC_khong_nhi_phan():
    """Hai món cùng có tag 'cozy' không được bằng điểm nhau cho mood sad."""
    chao, _ = dish_ranking._score_mood(CHAO, "sad")
    do_nham, _ = dish_ranking._score_mood(DO_NHAM, "sad")
    lau_thai, _ = dish_ranking._score_mood(LAU_THAI, "sad")
    assert chao > do_nham
    assert chao > lau_thai


def test_do_nham_khong_dung_dau_khi_buon():
    """Đồ nhắm (tag cozy+spicy) từng đứng #1 cho sad. Không loại cứng - chỉ là ánh xạ
    thuộc tính không còn cho nó trọn điểm."""
    ranked = rank(MON_THEO_MOOD, DishFilter(mood="sad"))
    assert ranked[0].dish.name != "Đồ nhắm"


def test_mood_affinity_chi_dung_gia_tri_thuoc_tinh_co_that():
    """Khoá ánh xạ vào đúng bộ giá trị của entity: đổi tên hằng số bên Dish mà quên sửa
    ánh xạ thì mood âm thầm mất tác dụng."""
    from src.domain.entities.dish import COOKING_METHODS, MEAL_TIMES
    from src.domain.value_objects.mood import (
        DISH_MOOD_KEYWORDS,
        MOOD_DISH_AFFINITY,
        SUPPORTED_MOODS,
    )

    assert set(MOOD_DISH_AFFINITY) == set(SUPPORTED_MOODS)
    for features in MOOD_DISH_AFFINITY.values():
        for feature in features:
            kind, _, value = feature.partition(":")
            allowed = {
                "kw": DISH_MOOD_KEYWORDS,
                "temp": {"hot", "cold", "room"},
                "method": set(COOKING_METHODS),
                "meal": set(MEAL_TIMES),
                "portion": {"light", "small", "regular", "heavy"},
                "spice": {"none", "hot"},
            }[kind]
            assert value in allowed, feature


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


def test_has_description_distinguishes_missing_from_empty():
    """UI phải nói "chưa có dữ liệu" chứ không để một khoảng trắng."""
    assert not make_dish("Món mới").has_description
    assert make_dish("Phở bò", description="Phở bò là món nước.").has_description


def test_blank_description_counts_as_missing():
    """Chuỗi toàn khoảng trắng KHÔNG phải là có dữ liệu - nếu không UI sẽ hiện một vùng
    trống trơn mà vẫn tưởng là đã có giới thiệu."""
    assert not make_dish("Món mới", description="   ").has_description


# --- Đối chiếu MÓN <-> QUÁN (dish_matching) ----------------------------------


def test_review_mention_links_dish_to_restaurant():
    """Đề án mục 7: quán không ghi tên món lên biển hiệu thì trích từ NỘI DUNG REVIEW.

    Đây là cách duy nhất tìm ra quán bán "bún thang" mà lại tên là "Quán Ăn Ngon".
    """
    from src.domain.services.dish_matching import build_dish_restaurant_index
    from tests.fakes import make_restaurant

    quan = make_restaurant(
        "Quán Ăn Ngon", review_text="Bún thang ở đây ngon, nước dùng thanh."
    )
    dish = Dish(name="Bún thang", dish_id="bun-thang", match_keywords=["bún thang"])

    index = build_dish_restaurant_index([dish], [quan])

    assert [m.restaurant for m in index["bun-thang"]] == [quan]


def test_single_word_dish_never_matches_review():
    """Tên MỘT TỪ không được khớp vào review.

    Review dài trung bình 670 ký tự và nhắc "cơm", "bún", "trà" ở khắp nơi - cho khớp thì
    món đó bị gán cho hàng nghìn quán không liên quan. Chỉ tên từ 2 từ trở lên mới đủ đặc
    trưng để tin.
    """
    from src.domain.services.dish_matching import build_dish_restaurant_index
    from tests.fakes import make_restaurant

    quan = make_restaurant("Quán Bia Hải", review_text="Ăn cơm ở đây cũng được.")
    com = Dish(name="Cơm", dish_id="com", match_keywords=["cơm"])

    index = build_dish_restaurant_index([com], [quan])

    assert index["com"] == []


def test_restaurant_without_review_is_not_penalised():
    """Quán chưa cào được review KHÔNG bị coi là "không bán món nào" - nó chỉ là thiếu
    dữ liệu, và vẫn phải khớp được qua TÊN QUÁN như thường."""
    from src.domain.services.dish_matching import build_dish_restaurant_index
    from tests.fakes import make_restaurant

    quan = make_restaurant("Bún Thang Bà Đức", review_text=None)
    dish = Dish(name="Bún thang", dish_id="bun-thang", match_keywords=["bún thang"])

    index = build_dish_restaurant_index([dish], [quan])

    assert [m.restaurant for m in index["bun-thang"]] == [quan]


def test_reviews_can_be_turned_off():
    """Tắt được để so sánh tín hiệu tên quán với tín hiệu review khi đo đạc."""
    from src.domain.services.dish_matching import build_dish_restaurant_index
    from tests.fakes import make_restaurant

    quan = make_restaurant("Quán Ăn Ngon", review_text="Bún thang ở đây ngon.")
    dish = Dish(name="Bún thang", dish_id="bun-thang", match_keywords=["bún thang"])

    assert build_dish_restaurant_index([dish], [quan], use_reviews=False)["bun-thang"] == []


def test_phrase_does_not_span_name_and_category_boundary():
    """Tên quán kết thúc bằng "bún" + loại hình mở đầu bằng "chả" KHÔNG được khớp "bún chả".

    Nối hai chuỗi lại rồi khớp là cách tạo ra dương tính giả kiểu này.
    """
    from src.domain.services.dish_matching import build_dish_restaurant_index
    from tests.fakes import make_restaurant

    quan = make_restaurant("Quán Bún", category="Chả cá nướng")
    dish = Dish(name="Bún chả", dish_id="bun-cha", match_keywords=["bún chả"])

    index = build_dish_restaurant_index([dish], [quan], use_reviews=False)

    assert index["bun-cha"] == []

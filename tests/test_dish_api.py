"""Test HỢP ĐỒNG HTTP của luồng "chọn món trước, tìm quán sau".

Ba endpoint, đúng thứ tự người dùng đi qua:
    POST /api/v1/dishes/suggest            bộ lọc -> danh sách MÓN
    GET  /api/v1/dishes/{id}               chi tiết món (GIỚI THIỆU NGẮN)
    GET  /api/v1/dishes/{id}/restaurants   món -> quán gần đây

Dùng repository GIẢ, không đọc dataset thật: test phải chạy được kể cả trên máy chưa chạy
`python scripts/build_dish_catalog.py`.
"""
import pytest
from fastapi.testclient import TestClient

from src.application.use_cases.get_restaurant_details import GetRestaurantDetailsUseCase
from src.application.use_cases.log_interaction import LogInteractionUseCase
from src.application.use_cases.search_restaurants import SearchRestaurantsUseCase
from src.domain.entities.dish import METHOD_GRILLED, METHOD_SOUP, Dish
from src.infrastructure.auth.admin_auth import AdminAuthService
from src.presentation.api.dependencies import Container
from src.presentation.api.main import create_app
from tests.fakes import (
    FakeDetailsRepo,
    FakeDishCatalog,
    FakeDishKnowledge,
    FakeInteractionRepo,
    FakeRestaurantRepo,
    FixedContextProvider,
    GENERIC_RULE,
    PHO_RULE,
    UnavailablePredictor,
    attach_closure_tally,
    attach_user_activity,
    attach_disabled_auth,
    attach_dish_catalog,
    make_restaurant,
)

API = "/api/v1"
SESSION = "3f9a0000-0000-4000-8000-000000000000"

BUN_CHA = Dish(
    name="Bún chả",
    dish_id="bun-cha",
    cuisine="Việt Nam",
    temperature="hot",
    cooking_method=METHOD_GRILLED,
    description="Bún chả là món Hà Nội gồm chả thịt lợn nướng than, ăn kèm bún và rau sống.",
    match_keywords=["bún chả"],
    source="manual",
)
PHO_BO = Dish(
    name="Phở bò",
    dish_id="pho-bo",
    cuisine="Việt Nam",
    temperature="hot",
    cooking_method=METHOD_SOUP,
    description="Phở bò là món nước dùng ninh từ xương bò, ăn cùng bánh phở và thịt bò.",
    match_keywords=["phở"],
    source="manual",
)
# Món CHƯA tra được giới thiệu - phải phân biệt được với "món không có gì để nói".
MON_THIEU_DU_LIEU = Dish(
    name="Món chưa tra được",
    dish_id="mon-thieu",
    temperature="hot",
    match_keywords=["không-quán-nào-tên-thế-này"],
)


class NullSemanticSearch:
    is_ready = False

    def similarity(self, query_text):
        return {}

    def status(self):
        return {"ready": False, "reason": "tat trong test"}


def make_client(dishes=None, index=None, catalog_ready=True):
    """Container giả có phần MÓN được lắp thật, phần còn lại tối thiểu."""
    quan_bun_cha = make_restaurant("Bún Chả Hương Liên", lat=21.0285, lng=105.8542)
    quan_pho = make_restaurant("Phở Thìn", lat=21.0290, lng=105.8550)
    repo = FakeRestaurantRepo([quan_bun_cha, quan_pho])
    knowledge = FakeDishKnowledge([PHO_RULE, GENERIC_RULE])
    details_repo = FakeDetailsRepo({})
    interactions = FakeInteractionRepo()
    predictor = UnavailablePredictor()
    context = FixedContextProvider()

    c = attach_closure_tally(Container.__new__(Container))
    # Thư mục tạm tự sinh: mấy bộ test này không nói gì về yêu thích/cấp độ,
    # chỉ cần container có đủ trường để /health không nổ.
    attach_user_activity(c)
    c.settings = None
    c.restaurant_repository = repo
    c.details_repository = details_repo
    c.dish_knowledge_repository = knowledge
    c.interaction_repository = interactions
    c.rule_predictor = predictor
    c.context_provider = context
    c.semantic_search = NullSemanticSearch()
    c.search_restaurants = SearchRestaurantsUseCase(repo, knowledge, context, predictor)
    c.get_restaurant_details = GetRestaurantDetailsUseCase(details_repo, repo)
    c.log_interaction = LogInteractionUseCase(interactions, repo)
    c.admin_auth = AdminAuthService("", "", "")
    c.admin_restaurants = None
    c.list_restaurants_for_admin = None
    c.update_restaurant = None
    c.set_restaurant_visibility = None
    attach_disabled_auth(c)

    catalog = FakeDishCatalog(
        dishes if dishes is not None else [BUN_CHA, PHO_BO], ready=catalog_ready
    )
    attach_dish_catalog(
        c,
        dishes=catalog,
        index=index if index is not None
        else {"bun-cha": [quan_bun_cha], "pho-bo": [quan_pho]},
        context_provider=context,
    )
    return TestClient(create_app(container=c), raise_server_exceptions=False)


@pytest.fixture
def client():
    return make_client()


def suggest(client, **body):
    body.setdefault("session_id", SESSION)
    return client.post(f"{API}/dishes/suggest", json=body)


# --- POST /dishes/suggest ----------------------------------------------------


def test_suggest_returns_dishes_not_restaurants(client):
    """Trang chủ trả về MÓN. Đây là khác biệt cốt lõi của luồng mới."""
    response = suggest(client)

    assert response.status_code == 200
    data = response.json()["data"]
    names = {item["name"] for item in data["results"]}
    assert names == {"Bún chả", "Phở bò"}
    # Mỗi món phải kèm số quán ĐO ĐƯỢC, để người dùng biết bấm vào có dẫn tới đâu không.
    assert all("restaurant_count" in item for item in data["results"])


def test_grilled_filter_excludes_soup_dish(client):
    """Bấm "đồ nướng" thì phở phải biến mất - đó là điều người dùng vừa yêu cầu."""
    data = suggest(client, cooking_methods=["nuong"]).json()["data"]

    names = [item["name"] for item in data["results"]]
    assert names == ["Bún chả"]


def test_rain_puts_hot_soup_first(client):
    """Người dùng TỰ khai trời mưa -> món nước nóng lên đầu."""
    data = suggest(client, weather="rain").json()["data"]

    assert data["results"][0]["name"] == "Phở bò"
    assert any("mưa" in reason for reason in data["results"][0]["reasons"])


def test_dish_without_nearby_restaurant_is_hidden_and_announced(client):
    """Ẩn món ngõ cụt là ĐÚNG, nhưng im lặng ẩn thì KHÔNG.

    Đây đúng là lỗi `/suggest-dish` cũ từng mắc: lặng lẽ bỏ qua ràng buộc của client.
    """
    client = make_client(
        dishes=[BUN_CHA, MON_THIEU_DU_LIEU],
        index={"bun-cha": [make_restaurant("Bún Chả Hương Liên")], "mon-thieu": []},
    )
    data = suggest(client).json()["data"]

    assert [item["name"] for item in data["results"]] == ["Bún chả"]
    # Món này không có quán ở ĐÂU CẢ -> phải nói đúng lý do, KHÔNG khuyên nới bán kính.
    assert any("chưa tìm được quán nào" in w for w in data["warnings"])
    assert not any("Mở rộng bán kính" in w for w in data["warnings"])


def test_dish_hidden_because_too_far_suggests_widening(client):
    """Món CÓ quán nhưng ở xa -> lời khuyên "mở rộng bán kính" là hữu ích và đúng.

    Phân biệt với ca trên: khuyên nới bán kính cho món mà cả kho không có quán nào bán là
    nói dối - mở tới đâu cũng không thấy.
    """
    xa = make_restaurant("Bún Chả Xa Tít", lat=21.5000, lng=106.5000)
    client = make_client(dishes=[BUN_CHA], index={"bun-cha": [xa]})

    data = suggest(client, max_distance_km=2).json()["data"]

    assert any("Mở rộng bán kính" in w for w in data["warnings"])


def test_invalid_weather_does_not_break_the_search(client):
    """Tín hiệu ngữ cảnh hỏng KHÔNG được làm hỏng lượt tìm (CLAUDE.md mục 4 quy tắc 7)."""
    response = suggest(client, weather="mua-rat-to")

    assert response.status_code == 200
    assert response.json()["data"]["results"]


def test_catalog_not_built_returns_503_with_fix_instruction():
    """Chưa chạy script dựng danh mục -> 503 KÈM lệnh cần chạy, không phải 500."""
    client = make_client(catalog_ready=False)

    response = suggest(client)

    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "DATA_NOT_READY"
    assert "build_dish_catalog" in error["message"]


# --- GET /dishes/{id} --------------------------------------------------------


def test_dish_detail_returns_short_intro(client):
    """Bước 2 của luồng: bấm vào món thì hiện GIỚI THIỆU NGẮN về món đó."""
    data = client.get(f"{API}/dishes/bun-cha").json()["data"]

    assert data["name"] == "Bún chả"
    assert data["has_description"] is True
    assert "Bún chả" in data["description"]
    # Xuất xứ dữ liệu phải trả về để giao diện nói được đoạn giới thiệu này ở đâu ra.
    assert data["source"] == "manual"


def test_dish_without_intro_says_so_instead_of_blank(client):
    """Rỗng nghĩa là CHƯA TRA ĐƯỢC, không phải "món này không có gì để nói".

    `has_description` tồn tại để giao diện không phải tự đoán từ chuỗi rỗng.
    """
    client = make_client(dishes=[MON_THIEU_DU_LIEU], index={"mon-thieu": []})

    data = client.get(f"{API}/dishes/mon-thieu").json()["data"]

    assert data["description"] is None
    assert data["has_description"] is False


def test_dish_detail_opens_even_when_no_restaurant_nearby(client):
    """Mở được từ liên kết đã chia sẻ, kể cả khi quanh đây không có quán nào bán."""
    client = make_client(dishes=[MON_THIEU_DU_LIEU], index={"mon-thieu": []})

    response = client.get(f"{API}/dishes/mon-thieu")

    assert response.status_code == 200
    assert response.json()["data"]["restaurant_count"] == 0


def test_unknown_dish_returns_404_with_its_own_code(client):
    """Mã RIÊNG, không dùng chung với RESTAURANT_NOT_FOUND: client xử lý hai ca khác nhau."""
    response = client.get(f"{API}/dishes/mon-khong-ton-tai")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DISH_NOT_FOUND"


# --- GET /dishes/{id}/restaurants --------------------------------------------


def test_restaurants_for_dish_returns_matching_restaurants(client):
    """Bước 3: chọn món rồi ra danh sách quán."""
    response = client.get(
        f"{API}/dishes/bun-cha/restaurants", params={"session_id": SESSION}
    )

    assert response.status_code == 200
    results = response.json()["data"]["results"]
    assert [r["name"] for r in results] == ["Bún Chả Hương Liên"]


def test_restaurants_for_dish_carries_the_chosen_dish(client):
    """`suggested_dish` là món người dùng ĐÃ CHỌN, không phải suy đoán từ loại hình quán."""
    results = client.get(
        f"{API}/dishes/bun-cha/restaurants", params={"session_id": SESSION}
    ).json()["data"]["results"]

    dish = results[0]["suggested_dish"]
    assert dish["dish_id"] == "bun-cha"
    assert dish["confidence"] == "specific"


def test_restaurants_for_dish_uses_same_shape_as_search(client):
    """Trả đúng kiểu của POST /search để client dùng lại MỘT component thẻ quán."""
    results = client.get(
        f"{API}/dishes/bun-cha/restaurants", params={"session_id": SESSION}
    ).json()["data"]["results"]

    for field in ("restaurant_id", "distance_m", "predicted_score", "rank_position",
                  "price_range", "rating", "match_source"):
        assert field in results[0], f"thiếu field {field} - khác hợp đồng của /search"


def test_dish_with_no_restaurant_returns_200_and_explains(client):
    """Không có quán nào là KẾT QUẢ THẬT, không phải lỗi -> 200 kèm lời giải thích."""
    client = make_client(dishes=[MON_THIEU_DU_LIEU], index={"mon-thieu": []})

    response = client.get(
        f"{API}/dishes/mon-thieu/restaurants", params={"session_id": SESSION}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["results"] == []
    assert any("Chưa có quán nào" in w for w in data["warnings"])


def test_restaurants_for_unknown_dish_returns_404(client):
    response = client.get(
        f"{API}/dishes/khong-ton-tai/restaurants", params={"session_id": SESSION}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DISH_NOT_FOUND"


def test_far_restaurant_is_shown_but_the_widened_radius_is_announced(client):
    """Quán duy nhất nằm ngoài bán kính -> VẪN hiện, nhưng phải NÓI RA.

    `search_ranking` cố tình bỏ lọc bán kính khi lọc xong không còn gì (thà gợi ý quán xa
    còn hơn màn hình trắng). Quy tắc đó đúng, nhưng im lặng thì người dùng tưởng quán cách
    50km là "gần đây" - đúng kiểu bug `/suggest-dish` cũ gợi ý quán cách 46km.
    """
    xa = make_restaurant("Bún Chả Xa Tít", lat=21.5000, lng=106.5000)
    client = make_client(dishes=[BUN_CHA], index={"bun-cha": [xa]})

    data = client.get(
        f"{API}/dishes/bun-cha/restaurants",
        params={"session_id": SESSION, "max_distance_km": 2},
    ).json()["data"]

    assert [r["name"] for r in data["results"]] == ["Bún Chả Xa Tít"]
    assert any("bán kính" in w for w in data["warnings"])


def test_nearby_restaurant_does_not_trigger_the_radius_warning(client):
    """Cảnh báo chỉ xuất hiện khi THẬT SỰ phải nới bán kính - không phải mọi lượt tìm."""
    data = client.get(
        f"{API}/dishes/bun-cha/restaurants",
        params={"session_id": SESSION, "max_distance_km": 5},
    ).json()["data"]

    assert data["results"]
    assert not any("bán kính" in w for w in data["warnings"])


def test_name_matched_restaurant_outranks_review_only_match(client):
    """Quán có TÊN chứa tên món phải đứng TRÊN quán chỉ được review nhắc tới.

    Bug thật trên dữ liệu 40.720 quán: trang món "Bún chả" xếp "Nhà Hàng Hoàng" (870m,
    chỉ có review nhắc, nhưng CÓ điểm đánh giá) lên trên "Bun Cha Nem Cua Be" (310m, tên
    quán ghi rõ nhưng CHƯA có đánh giá). Hai tín hiệu này không đáng tin như nhau, nên
    không được để điểm xếp hạng trộn chúng vào nhau.
    """
    from src.domain.services.dish_matching import (
        MATCHED_BY_NAME,
        MATCHED_BY_REVIEW,
        DishMatch,
    )

    # Quán chỉ được review nhắc: GẦN HƠN và CÓ đánh giá -> mọi tín hiệu đều thắng...
    review_only = make_restaurant("Nhà Hàng Hoàng", lat=21.0286, lng=105.8543, rating=4.8)
    # ...còn quán ghi rõ tên món thì xa hơn và chưa có đánh giá.
    named = make_restaurant("Bún Chả Nem Cua Bể", lat=21.0350, lng=105.8600, rating=None)

    client = make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [
            DishMatch(review_only, MATCHED_BY_REVIEW),
            DishMatch(named, MATCHED_BY_NAME),
        ]},
    )

    data = client.get(
        f"{API}/dishes/bun-cha/restaurants", params={"session_id": SESSION}
    ).json()["data"]

    names = [r["name"] for r in data["results"]]
    assert names[0] == "Bún Chả Nem Cua Bể", f"tin hieu ten quan phai thang: {names}"
    # Và phải NÓI RA rằng phần đuôi danh sách yếu hơn.
    assert any("NHẮC TỚI trong review" in w for w in data["warnings"])


def test_rank_positions_stay_continuous_across_the_two_tiers(client):
    """Ghép hai tầng xong thì số thứ tự phải liền mạch 1,2,3 - không được nhảy cóc."""
    from src.domain.services.dish_matching import (
        MATCHED_BY_NAME,
        MATCHED_BY_REVIEW,
        DishMatch,
    )

    client = make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [
            DishMatch(make_restaurant("Bún Chả A"), MATCHED_BY_NAME),
            DishMatch(make_restaurant("Quán B"), MATCHED_BY_REVIEW),
            DishMatch(make_restaurant("Quán C"), MATCHED_BY_REVIEW),
        ]},
    )

    data = client.get(
        f"{API}/dishes/bun-cha/restaurants", params={"session_id": SESSION}
    ).json()["data"]

    assert [r["rank_position"] for r in data["results"]] == [1, 2, 3]

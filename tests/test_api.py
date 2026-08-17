"""Test tầng presentation qua HTTP thật (TestClient), theo đặc tả API.

VÌ SAO FILE NÀY QUAN TRỌNG: trước đây app KHÔNG khởi động được (dùng @app.exception_handler
trước khi `app` tồn tại -> NameError) nhưng toàn bộ test vẫn xanh, vì không test nào import
app. Test dưới đây khoá lại lỗ hổng đó: nếu app không dựng được, CI phải đỏ ngay.
"""
import pytest
from fastapi.testclient import TestClient

from src.application.use_cases.get_restaurant_details import GetRestaurantDetailsUseCase
from src.application.use_cases.log_interaction import LogInteractionUseCase
from src.application.use_cases.search_restaurants import SearchRestaurantsUseCase
from src.infrastructure.auth.admin_auth import AdminAuthService
from src.presentation.api.dependencies import Container
from src.presentation.api.main import create_app
from tests.fakes import (
    GENERIC_RULE,
    PHO_RULE,
    FakeDetailsRepo,
    FakeDishKnowledge,
    FakeInteractionRepo,
    FakeRestaurantRepo,
    FixedContextProvider,
    UnavailablePredictor,
    make_restaurant,
)

SESSION = "3f9a0000-0000-4000-8000-000000000000"
API = "/api/v1"


class NullSemanticSearch:
    """Tắt tìm kiếm ngữ nghĩa trong test API: test ở đây kiểm HỢP ĐỒNG HTTP, không
    kiểm chất lượng xếp hạng - dựng chỉ mục TF-IDF chỉ làm test chậm và giòn."""

    is_ready = False

    def similarity(self, query_text):
        return {}

    def status(self):
        return {"ready": False, "reason": "tat trong test"}


def _container(restaurants=None, details=None, restaurants_ready=True):
    restaurants = restaurants if restaurants is not None else [
        make_restaurant(
            "Quan Pho", category="Nhà hàng phở", price="100-200 N ₫",
            rating=4.5, reviews_count=12, comfort_cozy_score=0.9,
        )
    ]
    repo = FakeRestaurantRepo(restaurants, ready=restaurants_ready)
    knowledge = FakeDishKnowledge([PHO_RULE, GENERIC_RULE])
    details_repo = FakeDetailsRepo(details or {})
    interactions = FakeInteractionRepo()
    predictor = UnavailablePredictor()
    context = FixedContextProvider()

    c = Container.__new__(Container)
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
    # Quản trị TẮT trong bộ test này: đây là test cho luồng NGƯỜI DÙNG CUỐI. Trạng thái
    # "chưa cấu hình" cũng đúng là mặc định khi chạy thật. Luồng admin có file riêng
    # (`tests/test_admin_api.py`).
    c.admin_auth = AdminAuthService(username="", password_hash="", token_secret="")
    c.admin_restaurants = None
    c.list_restaurants_for_admin = None
    c.update_restaurant = None
    c.set_restaurant_visibility = None
    return c


def make_client(**kwargs):
    # Tiêm container giả: create_app() tự lắp sẽ đọc cả dataset thật (~1.5s) rồi bị
    # ghi đè ngay sau đó.
    app = create_app(container=_container(**kwargs))
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client():
    return make_client()


def test_app_can_be_created():
    """Test tối thiểu nhưng đắt giá nhất: app phải dựng được."""
    assert create_app() is not None


# --- Envelope (đặc tả API mục 1.5) -------------------------------------------


def test_success_is_wrapped_in_data(client):
    body = client.get(f"{API}/health").json()
    assert "data" in body and "error" not in body


def test_error_is_wrapped_with_code(client):
    resp = client.post(f"{API}/search", json={})  # thiếu session_id
    assert resp.status_code == 400
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "INVALID_REQUEST"
    assert "message" in body["error"] and "details" in body["error"]


# --- POST /search ------------------------------------------------------------


def test_search_returns_snake_case_restaurant_id(client):
    """Đặc tả API mục 1.3: snake_case, KHÔNG phải camelCase placeId."""
    resp = client.post(f"{API}/search", json={"session_id": SESSION, "limit": 1})
    assert resp.status_code == 200
    item = resp.json()["data"]["results"][0]
    assert "restaurant_id" in item
    assert "placeId" not in item


def test_search_result_shape_matches_spec(client):
    item = client.post(
        f"{API}/search", json={"session_id": SESSION, "limit": 1}
    ).json()["data"]["results"][0]
    for field in (
        "restaurant_id", "name", "latitude", "longitude", "distance_m",
        "price_range", "rating", "user_ratings_total", "rank_position",
        "predicted_score", "match_source", "suggested_dish",
    ):
        assert field in item, f"thiếu field {field} theo đặc tả API"


def test_search_nests_suggested_dish(client):
    item = client.post(
        f"{API}/search", json={"session_id": SESSION, "limit": 1}
    ).json()["data"]["results"][0]
    assert item["suggested_dish"]["name"] == "Phở bò"
    assert item["suggested_dish"]["confidence"] in (
        "specific", "generic_fallback", "unknown", "ml"
    )


def test_search_price_range_is_string(client):
    """price là chuỗi khoảng giá ("100-200 N ₫"), ép về float sẽ làm hỏng response."""
    item = client.post(
        f"{API}/search", json={"session_id": SESSION, "limit": 1}
    ).json()["data"]["results"][0]
    assert item["price_range"] == "100-200 N ₫"


def test_search_accepts_free_text(client):
    resp = client.post(
        f"{API}/search",
        json={"session_id": SESSION, "query_text": "phở bò", "limit": 3},
    )
    assert resp.status_code == 200


def test_search_returns_query_id_for_interaction_logging(client):
    data = client.post(f"{API}/search", json={"session_id": SESSION}).json()["data"]
    assert data["search_query_id"]


def test_search_missing_session_id_is_400_not_422(client):
    """Đặc tả dùng INVALID_REQUEST/400 cho thiếu trường bắt buộc."""
    assert client.post(f"{API}/search", json={"limit": 1}).status_code == 400


def test_search_returns_503_when_data_missing():
    c = make_client(restaurants=[], restaurants_ready=False)
    resp = c.post(f"{API}/search", json={"session_id": SESSION})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "DATA_NOT_READY"
    assert "data_pipeline" in resp.json()["error"]["message"]


# --- POST /interactions ------------------------------------------------------


def test_log_interaction_returns_201(client):
    resp = client.post(
        f"{API}/interactions",
        json={"session_id": SESSION, "restaurant_id": "id-Quan Pho", "action_type": "save"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["is_positive_signal"] is True


def test_log_interaction_unknown_restaurant_is_404(client):
    resp = client.post(
        f"{API}/interactions",
        json={"session_id": SESSION, "restaurant_id": "khong-co", "action_type": "save"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESTAURANT_NOT_FOUND"


def test_log_interaction_view_detail_without_dwell_is_400(client):
    resp = client.post(
        f"{API}/interactions",
        json={
            "session_id": SESSION,
            "restaurant_id": "id-Quan Pho",
            "action_type": "view_detail",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_REQUEST"


def test_log_interaction_rejects_unknown_action(client):
    resp = client.post(
        f"{API}/interactions",
        json={"session_id": SESSION, "restaurant_id": "id-Quan Pho", "action_type": "fly"},
    )
    assert resp.status_code == 400


# --- GET /restaurants/{id} ---------------------------------------------------


def test_restaurant_detail_missing_is_200_not_404(client):
    """Quán CÓ TỒN TẠI nhưng chưa cào được chi tiết -> 200 kèm has_details=false.

    Bản cũ của test này dùng id `unknown-id` (không hề tồn tại) rồi khẳng định phải trả
    200. Nhưng bảng mã lỗi ở CLAUDE.md mục 5 nói rõ: "Không tìm thấy quán -> 404", còn
    quy tắc 200 chỉ áp dụng cho quán "vẫn tồn tại". Test cũ vì thế đang khoá SAI hành vi.
    Nay dùng đúng id có trong kho quán nhưng không có bản ghi chi tiết.
    """
    resp = client.get(f"{API}/restaurants/id-Quan Pho")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["has_details"] is False
    assert data["restaurant_id"] == "id-Quan Pho"


def test_restaurant_detail_unknown_id_is_404(client):
    """Quán KHÔNG tồn tại -> 404 RESTAURANT_NOT_FOUND (CLAUDE.md mục 5)."""
    resp = client.get(f"{API}/restaurants/khong-he-ton-tai")

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESTAURANT_NOT_FOUND"


# --- meta --------------------------------------------------------------------


def test_health_reports_each_source_and_version(client):
    data = client.get(f"{API}/health").json()["data"]
    assert data["status"] == "ok"
    assert data["api_version"] == "v1"
    for source in ("restaurants", "restaurant_details", "dish_knowledge", "interactions"):
        assert source in data["services"]


def test_root_health_available_for_infrastructure_probe(client):
    assert client.get("/health").status_code == 200


def test_moods_endpoint_lists_supported_moods(client):
    data = client.get(f"{API}/moods").json()["data"]
    assert set(data["supported_moods"]) == {"happy", "sad", "excited", "relaxed"}

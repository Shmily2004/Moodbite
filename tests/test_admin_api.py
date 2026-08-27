"""Test luồng QUẢN TRỊ: xác thực + CRUD + soft-delete.

Dựng CSDL SQLite tạm trong tmp_path nên không đụng dữ liệu thật.

Trọng tâm là BẢO MẬT. Trang quản trị sửa được dữ liệu người dùng nhìn thấy, nên các test
"đường đi sai" ở đây quan trọng hơn test đường đi đúng:
  - không token / token hỏng / token hết hạn / token bị sửa ruột  -> 401
  - chưa cấu hình admin                                            -> 503, KHÔNG cho qua
  - kho lưu trữ không ghi được (CSV)                               -> 503
"""
from __future__ import annotations

import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

from src.application.errors import (
    AdminNotConfiguredError,
    InvalidCredentialsError,
)
from src.application.use_cases.get_restaurant_details import GetRestaurantDetailsUseCase
from pathlib import Path

from src.application.use_cases.get_admin_overview import GetAdminOverviewUseCase
from src.application.use_cases.list_dishes_admin import ListDishesForAdminUseCase
from src.application.use_cases.manage_audit_log import DocNhatKyUseCase, GhiNhatKyUseCase
from src.infrastructure.repositories.sqlite_audit_log_repository import (
    SqliteAuditLogRepository,
)
from src.application.use_cases.log_interaction import LogInteractionUseCase
from src.application.use_cases.manage_restaurants import (
    CreateRestaurantUseCase,
    ListRestaurantsForAdminUseCase,
    SetRestaurantVisibilityUseCase,
    UpdateRestaurantUseCase,
)
from src.application.use_cases.search_restaurants import SearchRestaurantsUseCase
from src.infrastructure.auth.admin_auth import AdminAuthService, hash_password
from src.infrastructure.repositories.sqlite_restaurant_repository import (
    SqliteRestaurantRepository,
)
from src.presentation.api.dependencies import Container
from src.presentation.api.main import create_app
from tests.fakes import (
    FakeDetailsRepo,
    FakeDishKnowledge,
    FakeInteractionRepo,
    FixedContextProvider,
    GENERIC_RULE,
    PHO_RULE,
    UnavailablePredictor,
    attach_closure_tally,
    attach_user_activity,
    attach_disabled_auth,
    attach_dish_catalog,
)
from tests.test_sqlite_repository import make_db

API = "/api/v1"
USER = "admin"
PASSWORD = "mat-khau-du-dai-123"
SECRET = "secret-dung-cho-test-khong-dung-that"

# Băm MỘT LẦN cho cả file. `hash_password` chạy 600k vòng PBKDF2 (~0.4s) — cố ý chậm để
# chống dò mật khẩu. Băm lại ở mỗi test làm bộ test chậm gấp đôi mà không kiểm thêm được
# gì: độ chậm là thuộc tính của thuật toán, không phải hành vi cần test ở đây.
# Riêng `test_bam_mat_khau_moi_lan_moi_khac...` vẫn gọi trực tiếp để kiểm salt ngẫu nhiên.
PASSWORD_HASH = hash_password(PASSWORD)


class NullSemanticSearch:
    is_ready = False

    def similarity(self, query_text):
        return {}

    def status(self):
        return {"ready": False, "reason": "tat trong test"}


@pytest.fixture
def db(tmp_path):
    return make_db(
        tmp_path,
        {"place_id": "pho-1", "name": "Phở Bò Hàng Đồng", "category": "Nhà hàng phở",
         "address": "12 Hàng Đồng", "is_active": 1},
        {"place_id": "bun-2", "name": "Bún Chả Hương Liên", "category": "Nhà hàng",
         "address": "24 Lê Văn Hưu", "is_active": 1},
    )


def build_client(db_path, *, configured=True, writable=True):
    repo = SqliteRestaurantRepository(db_path)
    knowledge = FakeDishKnowledge([PHO_RULE, GENERIC_RULE])
    details_repo = FakeDetailsRepo({})
    interactions = FakeInteractionRepo()
    predictor = UnavailablePredictor()
    context = FixedContextProvider()

    auth = (
        AdminAuthService(USER, PASSWORD_HASH, SECRET, token_ttl_seconds=60)
        if configured
        # Chưa cấu hình = cả 3 giá trị rỗng, đúng như khi chưa đặt biến môi trường.
        else AdminAuthService("", "", "")
    )
    admin_repo = repo if writable else None

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
    c.admin_auth = auth
    c.admin_restaurants = admin_repo
    c.create_restaurant = (
        CreateRestaurantUseCase(admin_repo) if admin_repo else None
    )
    c.list_restaurants_for_admin = (
        ListRestaurantsForAdminUseCase(admin_repo) if admin_repo else None
    )
    c.update_restaurant = UpdateRestaurantUseCase(admin_repo) if admin_repo else None
    c.set_restaurant_visibility = (
        SetRestaurantVisibilityUseCase(admin_repo) if admin_repo else None
    )
    # Tài khoản người dùng cuối TẮT: file này chỉ test luồng quản trị.
    attach_disabled_auth(c)
    attach_dish_catalog(c)
    # Nhật ký hoạt động: kho THẬT trong thư mục tạm, để test đi qua đúng đường ghi/đọc.
    c.audit_log = SqliteAuditLogRepository(Path(db_path).parent / "audit.db")
    c.ghi_nhat_ky = GhiNhatKyUseCase(c.audit_log)
    c.doc_nhat_ky = DocNhatKyUseCase(c.audit_log)
    c.list_dishes_for_admin = ListDishesForAdminUseCase(c.dish_catalog_repository)
    # Màn "Tổng quan". Lắp SAU `attach_dish_catalog` vì nó cần kho món đã có.
    c.admin_overview = GetAdminOverviewUseCase(
        restaurant_repository=repo,
        dish_catalog_repository=c.dish_catalog_repository,
        interaction_repository=interactions,
    )

    # Tiêm container thẳng vào: nếu để create_app() tự lắp, mỗi test sẽ nạp lại toàn
    # bộ dataset thật rồi bị ghi đè ngay - tốn ~1.5s mỗi test cho việc bị vứt đi.
    app = create_app(container=c)
    return TestClient(app, raise_server_exceptions=False), repo


@pytest.fixture
def client(db):
    c, _ = build_client(db)
    return c


def token_of(client) -> str:
    res = client.post(f"{API}/admin/login", json={"username": USER, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return res.json()["data"]["token"]


def auth_header(client) -> dict:
    return {"Authorization": f"Bearer {token_of(client)}"}


# ==========================================================================
# XÁC THỰC — phần quan trọng nhất
# ==========================================================================


def test_dang_nhap_dung_thi_tra_token(client):
    body = client.post(
        f"{API}/admin/login", json={"username": USER, "password": PASSWORD}
    ).json()["data"]

    assert body["token"] and body["token_type"] == "bearer"
    assert body["expires_in"] == 60


@pytest.mark.parametrize(
    "payload",
    [
        {"username": USER, "password": "sai-mat-khau"},
        {"username": "khong-ton-tai", "password": PASSWORD},
        {"username": USER, "password": PASSWORD.upper()},
    ],
)
def test_dang_nhap_sai_tra_401(client, payload):
    res = client.post(f"{API}/admin/login", json=payload)

    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"
    # Không được nói "sai mật khẩu" hay "không có tài khoản này" - lộ thông tin cho
    # người dò tài khoản.
    assert "Sai tài khoản hoặc mật khẩu" in res.json()["error"]["message"]


def test_khong_co_token_thi_401(client):
    res = client.get(f"{API}/admin/restaurants")

    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize(
    "header",
    [
        {"Authorization": "Bearer khong-phai-token"},
        {"Authorization": "Bearer a.b"},
        {"Authorization": "Basic abcdef"},   # sai scheme
        {"Authorization": "Bearer"},          # thiếu token
        {"Authorization": ""},
    ],
)
def test_token_hong_thi_401(client, header):
    assert client.get(f"{API}/admin/restaurants", headers=header).status_code == 401


def test_token_bi_sua_RUOT_van_bi_tu_choi(client):
    """Đổi payload nhưng giữ chữ ký cũ -> phải hỏng, vì chữ ký kiểm TRƯỚC khi đọc ruột."""
    token = token_of(client)
    body, _, signature = token.partition(".")
    # Đổi 1 ký tự trong phần payload.
    gia_mao = f"{body[:-1]}{'A' if body[-1] != 'A' else 'B'}.{signature}"

    res = client.get(
        f"{API}/admin/restaurants", headers={"Authorization": f"Bearer {gia_mao}"}
    )

    assert res.status_code == 401


def test_token_het_han_thi_401(db):
    client, _ = build_client(db)
    # TTL âm -> token sinh ra đã hết hạn ngay lập tức.
    client.app.state.container.admin_auth.token_ttl_seconds = -10
    token = token_of(client)

    res = client.get(
        f"{API}/admin/restaurants", headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == 401
    assert "hết hạn" in res.json()["error"]["message"]


def test_chua_cau_hinh_admin_thi_503_KHONG_cho_qua(db):
    """Fail-closed. Đây là bug nguy hiểm nhất có thể có: mặc định thành công khai."""
    client, _ = build_client(db, configured=False)

    login = client.post(
        f"{API}/admin/login", json={"username": USER, "password": PASSWORD}
    )
    listing = client.get(f"{API}/admin/restaurants")

    assert login.status_code == 503
    assert listing.status_code == 503
    assert "MOODBITE_ADMIN_PASSWORD_HASH" in login.json()["error"]["message"]


def test_kho_khong_ghi_duoc_thi_503_kem_cach_khac_phuc(db):
    client, _ = build_client(db, writable=False)

    res = client.get(f"{API}/admin/restaurants", headers=auth_header(client))

    assert res.status_code == 503
    assert "build_sqlite.py" in res.json()["error"]["message"]


# ==========================================================================
# ĐỌC
# ==========================================================================


def test_liet_ke_quan_cho_admin(client):
    data = client.get(f"{API}/admin/restaurants", headers=auth_header(client)).json()["data"]

    assert data["total"] == 2
    assert {r["name"] for r in data["results"]} == {
        "Phở Bò Hàng Đồng",
        "Bún Chả Hương Liên",
    }
    assert all(r["is_active"] for r in data["results"])


def test_loc_theo_tu_khoa(client):
    data = client.get(
        f"{API}/admin/restaurants", params={"q": "Bún"}, headers=auth_header(client)
    ).json()["data"]

    assert data["total"] == 1
    assert data["results"][0]["restaurant_id"] == "bun-2"


# ==========================================================================
# SỬA
# ==========================================================================


def test_sua_truong_mo_ta(client):
    headers = auth_header(client)

    res = client.patch(
        f"{API}/admin/restaurants/pho-1",
        json={"phone": "024 1234 5678", "price": "50-100 N ₫"},
        headers=headers,
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["phone"] == "024 1234 5678"
    assert data["price"] == "50-100 N ₫"
    assert data["name"] == "Phở Bò Hàng Đồng", "trường không gửi lên phải giữ nguyên"


def test_gui_null_la_XOA_gia_tri(client):
    headers = auth_header(client)
    client.patch(f"{API}/admin/restaurants/pho-1", json={"phone": "024 111"}, headers=headers)

    res = client.patch(
        f"{API}/admin/restaurants/pho-1", json={"phone": None}, headers=headers
    )

    assert res.json()["data"]["phone"] is None


@pytest.mark.parametrize("field", ["rating", "reviews_count", "experience_cluster_id", "place_id"])
def test_sua_truong_bi_cam_tra_400(client, field):
    """Rating/cụm đến từ pipeline. Sửa tay sẽ bị ghi đè ở lần chạy pipeline sau, và
    tệ hơn là làm sai lệch số liệu đánh giá."""
    res = client.patch(
        f"{API}/admin/restaurants/pho-1", json={field: 5}, headers=auth_header(client)
    )

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_REQUEST"


def test_sua_quan_khong_ton_tai_tra_404(client):
    res = client.patch(
        f"{API}/admin/restaurants/khong-co", json={"phone": "024"}, headers=auth_header(client)
    )

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESTAURANT_NOT_FOUND"


def test_yeu_cau_sai_duoc_kiem_TRUOC_khi_tra_404(client):
    """Trường cấm + quán không tồn tại -> phải là 400, vì lỗi của client nằm ở yêu cầu."""
    res = client.patch(
        f"{API}/admin/restaurants/khong-co", json={"rating": 5}, headers=auth_header(client)
    )

    assert res.status_code == 400


# ==========================================================================
# SOFT-DELETE — điểm giao nhau giữa admin và người dùng cuối
# ==========================================================================


def test_an_quan_thi_nguoi_dung_cuoi_khong_thay_nua(db):
    client, repo = build_client(db)
    headers = auth_header(client)
    assert repo.get_by_place_id("pho-1") is not None

    res = client.post(f"{API}/admin/restaurants/pho-1/hide", headers=headers)

    assert res.status_code == 200
    assert res.json()["data"]["is_active"] is False
    # Điểm mấu chốt: bộ nhớ đệm của repository phải được làm mới NGAY, nếu không người
    # dùng vẫn tìm thấy quán đã ẩn cho tới lần khởi động lại sau.
    assert repo.get_by_place_id("pho-1") is None
    assert "pho-1" not in {r.place_id for r in repo.list_all()}


def test_an_quan_thi_GET_chi_tiet_tra_404(db):
    """Bug thật, chỉ test end-to-end mới bắt được (2026-08-17).

    `GET /restaurants/{id}` đọc kho CHI TIẾT, mà kho đó không có khái niệm `is_active`.
    Kết quả: ẩn quán xong nó biến mất khỏi /search NHƯNG ai biết link vẫn xem được.
    Test ở tầng repository không thấy vì chúng không đi qua HTTP.
    """
    client, _ = build_client(db)
    headers = auth_header(client)
    assert client.get(f"{API}/restaurants/pho-1").status_code == 200

    client.post(f"{API}/admin/restaurants/pho-1/hide", headers=headers)

    res = client.get(f"{API}/restaurants/pho-1")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESTAURANT_NOT_FOUND"

    # Bỏ ẩn thì phải xem lại được.
    client.post(f"{API}/admin/restaurants/pho-1/restore", headers=headers)
    assert client.get(f"{API}/restaurants/pho-1").status_code == 200


def test_quan_da_an_van_hien_trong_danh_sach_admin(client):
    headers = auth_header(client)
    client.post(f"{API}/admin/restaurants/pho-1/hide", headers=headers)

    data = client.get(f"{API}/admin/restaurants", headers=headers).json()["data"]

    an = [r for r in data["results"] if r["restaurant_id"] == "pho-1"]
    assert an and an[0]["is_active"] is False, "ẩn xong phải còn thấy để bỏ ẩn lại được"


def test_include_hidden_false_thi_bo_quan_da_an(client):
    headers = auth_header(client)
    client.post(f"{API}/admin/restaurants/pho-1/hide", headers=headers)

    data = client.get(
        f"{API}/admin/restaurants",
        params={"include_hidden": "false"},
        headers=headers,
    ).json()["data"]

    assert {r["restaurant_id"] for r in data["results"]} == {"bun-2"}


def test_bo_an_thi_quan_quay_lai(db):
    client, repo = build_client(db)
    headers = auth_header(client)
    client.post(f"{API}/admin/restaurants/pho-1/hide", headers=headers)

    res = client.post(f"{API}/admin/restaurants/pho-1/restore", headers=headers)

    assert res.json()["data"]["is_active"] is True
    assert repo.get_by_place_id("pho-1") is not None


def test_an_ghi_thang_xuong_CSDL_chu_khong_chi_trong_RAM(db):
    client, _ = build_client(db)
    client.post(f"{API}/admin/restaurants/pho-1/hide", headers=auth_header(client))

    with sqlite3.connect(db) as conn:
        value = conn.execute(
            "SELECT is_active FROM restaurants WHERE place_id = 'pho-1'"
        ).fetchone()[0]

    assert value == 0


def test_an_quan_khong_ton_tai_tra_404(client):
    res = client.post(f"{API}/admin/restaurants/khong-co/hide", headers=auth_header(client))

    assert res.status_code == 404


# ==========================================================================
# Chống trôi giữa domain và adapter
# ==========================================================================


def test_danh_sach_truong_sua_duoc_khop_giua_domain_va_CSDL():
    """`EDITABLE_FIELDS` (domain) và `_WRITABLE_COLUMNS` (SQL) phải luôn giống nhau.

    Hai nơi lệch nhau sinh ra bug lặng lẽ: domain cho phép sửa nhưng SQL bỏ qua, người
    dùng bấm Lưu, API trả 200, mà dữ liệu không đổi.
    """
    from src.domain.value_objects.restaurant_edit import EDITABLE_FIELDS
    from src.infrastructure.repositories.sqlite_restaurant_repository import (
        _WRITABLE_COLUMNS,
    )

    assert set(EDITABLE_FIELDS) == set(_WRITABLE_COLUMNS)


def test_sql_injection_qua_ten_truong_khong_an_thua(client):
    """Tên cột không tham số hoá được trong SQL, nên phải lọc bằng danh sách trắng."""
    res = client.patch(
        f"{API}/admin/restaurants/pho-1",
        json={"name = 'hacked'; --": "x"},
        headers=auth_header(client),
    )

    assert res.status_code == 400


# ==========================================================================
# Đơn vị: dịch vụ xác thực
# ==========================================================================


def test_bam_mat_khau_moi_lan_moi_khac_nhung_van_kiem_dung():
    """Salt ngẫu nhiên: hai lần băm cùng mật khẩu phải ra chuỗi khác nhau."""
    from src.infrastructure.auth.admin_auth import verify_password

    a, b = hash_password(PASSWORD), hash_password(PASSWORD)

    assert a != b
    assert verify_password(PASSWORD, a) and verify_password(PASSWORD, b)
    assert not verify_password("sai", a)


def test_bam_sai_dinh_dang_tra_False_khong_nem_loi():
    from src.infrastructure.auth.admin_auth import verify_password

    for hong in ["", "khong-phai-hash", "pbkdf2_sha256$abc", "md5$1$aa$bb"]:
        assert verify_password(PASSWORD, hong) is False


def test_token_cua_secret_khac_thi_khong_dung_duoc():
    """Đổi MOODBITE_ADMIN_SECRET phải làm mọi token đang lưu hết hiệu lực."""
    a = AdminAuthService(USER, PASSWORD_HASH, "secret-A")
    b = AdminAuthService(USER, PASSWORD_HASH, "secret-B")
    token = a.login(USER, PASSWORD)

    assert a.verify(token) == USER
    with pytest.raises(InvalidCredentialsError):
        b.verify(token)


def test_chua_cau_hinh_thi_nem_AdminNotConfigured():
    auth = AdminAuthService("", "", "")

    assert auth.is_configured is False
    with pytest.raises(AdminNotConfiguredError):
        auth.login(USER, PASSWORD)
    with pytest.raises(AdminNotConfiguredError):
        auth.verify("bat-ky")


def test_token_het_han_theo_dong_ho_that():
    auth = AdminAuthService(USER, PASSWORD_HASH, SECRET, token_ttl_seconds=1)
    token = auth.login(USER, PASSWORD)
    assert auth.verify(token) == USER

    time.sleep(1.1)

    with pytest.raises(InvalidCredentialsError):
        auth.verify(token)


# ==========================================================================
# THÊM QUÁN MỚI — `POST /admin/restaurants` (2026-08-23)
#
# Đây là con đường bổ sung dữ liệu MIỄN PHÍ còn lại: người thật tới tận nơi xác minh.
# Chỗ dễ sai nhất là để lọt dữ liệu rác vào dataset, nên test tập trung vào ĐƯỜNG SAI.
# ==========================================================================


def _them_quan(client, **truong):
    body = {"name": "Bún chả Thử Nghiệm", "lat": 21.0285, "lng": 105.8542}
    body.update(truong)
    return client.post(
        f"{API}/admin/restaurants", json=body, headers=auth_header(client)
    )


def test_them_quan_moi_tra_201_va_tim_lai_duoc(client):
    res = _them_quan(client, address="1 Phố Thử Nghiệm", price="30-60.000 ₫")

    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["name"] == "Bún chả Thử Nghiệm"
    # place_id do SERVER sinh, có tiền tố nói rõ nguồn gốc.
    assert data["restaurant_id"].startswith("manual:")

    ds = client.get(
        f"{API}/admin/restaurants?q=Thử Nghiệm", headers=auth_header(client)
    ).json()["data"]
    assert any(r["name"] == "Bún chả Thử Nghiệm" for r in ds["results"])


def test_quan_moi_hien_ra_o_luong_NGUOI_DUNG_CUOI(client):
    """Thêm xong mà người dùng không tìm thấy thì việc nhập liệu vô nghĩa.

    Đây là test khoá phần LÀM MỚI BỘ NHỚ ĐỆM: repository nạp sẵn vào RAM, quên gọi
    `reload()` sau khi ghi thì quán mới chỉ xuất hiện sau lần khởi động lại kế tiếp.
    """
    ma = _them_quan(client, name="Phở Kiểm Thử Bộ Nhớ").json()["data"]["restaurant_id"]

    res = client.get(f"{API}/restaurants/{ma}")
    assert res.status_code == 200, res.text


def test_thieu_ten_thi_400(client):
    res = client.post(
        f"{API}/admin/restaurants",
        json={"lat": 21.0285, "lng": 105.8542},
        headers=auth_header(client),
    )
    assert res.status_code == 400


def test_toa_do_NGOAI_HA_NOI_bi_tu_choi(client):
    """Phạm vi dự án chốt CHỈ HÀ NỘI (CLAUDE.md mục 4b). Toạ độ TP.HCM phải bị chặn."""
    res = _them_quan(client, lat=10.7769, lng=106.7009)

    assert res.status_code == 400
    assert "Hà Nội" in res.json()["error"]["message"]


def test_KHONG_nhan_rating_tu_form(client):
    """Rating gõ tay là làm sai lệch chính con số dùng để xếp hạng."""
    res = _them_quan(client, rating=5.0, reviews_count=999)

    assert res.status_code == 201
    # Trường lạ bị Pydantic bỏ qua; quán mới KHÔNG có đánh giá.
    ma = res.json()["data"]["restaurant_id"]
    chi_tiet = client.get(f"{API}/restaurants/{ma}").json()["data"]
    assert chi_tiet.get("rating") is None


def test_de_trong_loai_hinh_thi_mac_dinh_Nha_hang(client):
    res = _them_quan(client, name="Quán Không Ghi Loại")

    assert res.json()["data"]["category"] == "Nhà hàng"


def test_chua_dang_nhap_thi_KHONG_them_duoc(client):
    res = client.post(
        f"{API}/admin/restaurants",
        json={"name": "Quán Lậu", "lat": 21.03, "lng": 105.85},
    )
    assert res.status_code == 401


def test_kho_CHI_DOC_thi_tra_503_kem_cach_khac_phuc(tmp_path):
    """CSV không ghi được — phải nói rõ phải làm gì, không phải 500."""
    client_ro, _ = build_client(tmp_path / "ro.db", writable=False)

    res = client_ro.post(
        f"{API}/admin/restaurants",
        json={"name": "Quán X", "lat": 21.03, "lng": 105.85},
        headers=auth_header(client_ro),
    )
    assert res.status_code == 503
    assert "build_sqlite" in res.json()["error"]["message"]

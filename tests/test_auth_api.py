"""Test HTTP của `/api/v1/auth/*`.

`test_user_auth.py` đã test domain và use case. File này test thứ chỉ hỏng ở tầng HTTP:
mã trạng thái, envelope, header, và các chốt chặn gắn ở router.

Trọng tâm vẫn là ĐƯỜNG ĐI SAI — đây là endpoint công khai, ai cũng gọi được:
  - tự đăng ký thành admin qua body JSON  -> phải KHÔNG được
  - lộ `password_hash` ra response        -> phải KHÔNG bao giờ
  - dò xem tên nào tồn tại                -> phải KHÔNG đoán được
  - chưa cấu hình secret                  -> 503, KHÔNG phải cho qua
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.application.use_cases.get_restaurant_details import GetRestaurantDetailsUseCase
from src.application.use_cases.log_interaction import LogInteractionUseCase
from src.application.use_cases.manage_account import LoginUseCase, RegisterUserUseCase
from src.application.use_cases.search_restaurants import SearchRestaurantsUseCase
from src.domain.entities.user import User, UserRole
from src.infrastructure.auth.admin_auth import AdminAuthService
from src.infrastructure.auth.crypto import hash_password, verify_password
from src.infrastructure.auth.rate_limit import SlidingWindowRateLimiter
from src.infrastructure.auth.user_auth import UserTokenService
from src.infrastructure.repositories.sqlite_user_repository import SqliteUserRepository
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

API = "/api/v1"
SECRET = "secret-nguoi-dung-dung-cho-test"
PASSWORD = "mat-khau-du-dai-123"


class NullSemanticSearch:
    is_ready = False

    def similarity(self, query_text):
        return {}

    def status(self):
        return {"ready": False, "reason": "tat trong test"}


def build_client(tmp_path, *, secret=SECRET, login_limit=50, register_limit=50):
    """Dựng app với kho tài khoản thật (SQLite trong tmp_path) nhưng dataset giả.

    Kho tài khoản dùng bản THẬT chứ không giả: ràng buộc UNIQUE và cách chuẩn hoá tên là
    một phần của hành vi đang test, bản giả sẽ không tái hiện được.

    Hạn mức mặc định để RỘNG (50) vì hầu hết test ở đây không nói về giới hạn tần suất;
    để 5 như lúc chạy thật thì test thứ sáu trong cùng một client sẽ hỏng vì lý do không
    liên quan. Test về giới hạn tự truyền hạn mức nhỏ.
    """
    repo = FakeRestaurantRepo([make_restaurant("Quan Pho", category="Nhà hàng phở")])
    knowledge = FakeDishKnowledge([PHO_RULE, GENERIC_RULE])
    details_repo = FakeDetailsRepo({})
    interactions = FakeInteractionRepo()
    predictor = UnavailablePredictor()
    context = FixedContextProvider()

    users = SqliteUserRepository(tmp_path / "users.db")
    tokens = UserTokenService(secret, token_ttl_seconds=60)

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
    c.admin_auth = AdminAuthService("", "", "")
    c.admin_restaurants = None
    c.list_restaurants_for_admin = None
    c.update_restaurant = None
    c.set_restaurant_visibility = None
    c.users = users
    c.user_tokens = tokens
    c.register_user = RegisterUserUseCase(users, hash_password, tokens.issue)
    c.login_user = LoginUseCase(users, verify_password, tokens.issue)
    c.login_rate_limiter = SlidingWindowRateLimiter(login_limit, 300)
    c.register_rate_limiter = SlidingWindowRateLimiter(register_limit, 3600)

    app = create_app(container=c)
    return TestClient(app, raise_server_exceptions=False), users


@pytest.fixture
def client(tmp_path):
    c, _ = build_client(tmp_path)
    return c


def register(client, username="nguoidung", password=PASSWORD, **extra):
    return client.post(
        f"{API}/auth/register",
        json={"username": username, "password": password, **extra},
    )


def login(client, username="nguoidung", password=PASSWORD):
    return client.post(
        f"{API}/auth/login", json={"username": username, "password": password}
    )


# ==========================================================================
# PHÂN QUYỀN — chỗ sai thì nguy hiểm nhất
# ==========================================================================


def test_gui_role_admin_trong_body_KHONG_lam_minh_thanh_admin(client):
    """Trường lạ trong JSON phải bị BỎ QUA, không được chảy vào entity."""
    res = client.post(
        f"{API}/auth/register",
        json={"username": "kesau", "password": PASSWORD, "role": "admin"},
    )

    assert res.status_code == 201, res.text
    assert res.json()["data"]["user"]["role"] == "user"


def test_response_KHONG_BAO_GIO_chua_password_hash(client):
    """Kiểm trên CHUỖI JSON thô, không kiểm theo khoá: hash lọt ra ở bất kỳ chỗ lồng nhau
    nào cũng phải bị bắt."""
    for res in (register(client), login(client)):
        assert "password_hash" not in res.text
        assert "pbkdf2" not in res.text


def test_me_tra_ve_vai_doc_tu_CSDL_chu_khong_tu_token(tmp_path):
    """Nâng vai trong CSDL phải có hiệu lực NGAY, không đợi token hết hạn.

    Đây là lý do token cố tình chỉ chứa `sub`. Nếu vai nằm trong token thì test này đỏ.
    """
    import sqlite3

    client, users = build_client(tmp_path)
    token = register(client).json()["data"]["token"]
    assert client.get(f"{API}/auth/me", headers=bearer(token)).json()["data"]["role"] == "user"

    with sqlite3.connect(users.db_path) as conn:
        conn.execute("UPDATE users SET role = 'admin' WHERE username = 'nguoidung'")
        conn.commit()

    # CÙNG token cũ, không đăng nhập lại.
    assert client.get(f"{API}/auth/me", headers=bearer(token)).json()["data"]["role"] == "admin"


def test_token_cua_admin_KHONG_dung_duoc_cho_nguoi_dung(tmp_path):
    """Hai secret riêng biệt: chữ ký bên này không bao giờ hợp lệ ở bên kia."""
    client, _ = build_client(tmp_path, secret=SECRET)
    token_admin = AdminAuthService(
        "admin", hash_password("x"), "secret-KHAC-hoan-toan"
    )._issue_token("admin")

    res = client.get(f"{API}/auth/me", headers=bearer(token_admin))

    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ==========================================================================
# CHỐNG DÒ TÀI KHOẢN
# ==========================================================================


def test_sai_ten_va_sai_mat_khau_tra_response_Y_HET_NHAU(client):
    register(client, username="cothat")

    sai_mat_khau = login(client, username="cothat", password="sai-mat-khau-roi")
    khong_ton_tai = login(client, username="khongcothat")

    assert sai_mat_khau.status_code == khong_ton_tai.status_code == 401
    # Giống nhau tới từng ký tự, kể cả `details`.
    assert sai_mat_khau.json() == khong_ton_tai.json()


def test_dang_nhap_sai_KHONG_tra_ve_goi_y_do_dai_mat_khau(client):
    """Mật khẩu 3 ký tự lúc ĐĂNG NHẬP phải ra 401 chung chung, KHÔNG phải 400 kèm
    'mật khẩu phải >= 8 ký tự' — câu đó nói cho kẻ tấn công biết luật đặt mật khẩu và
    phân biệt được hai tình huống."""
    res = login(client, password="abc")

    assert res.status_code == 401
    assert "8" not in res.json()["error"]["message"]


# ==========================================================================
# GIỚI HẠN TẦN SUẤT
# ==========================================================================


def test_dang_nhap_sai_qua_nhieu_lan_bi_chan_429(tmp_path):
    client, _ = build_client(tmp_path, login_limit=3)

    for _ in range(3):
        assert login(client).status_code == 401
    res = login(client)

    assert res.status_code == 429
    assert res.json()["error"]["code"] == "RATE_LIMITED"
    # Header chuẩn HTTP, không chỉ nằm trong body.
    assert int(res.headers["Retry-After"]) > 0


def test_dang_nhap_dung_thi_xoa_lich_su_dem(tmp_path):
    """Gõ nhầm 2 lần rồi vào được thì không bị chặn oan ở lần sau."""
    client, _ = build_client(tmp_path, login_limit=3)
    register(client)
    login(client, password="sai-mat-khau-1")
    login(client, password="sai-mat-khau-2")

    assert login(client).status_code == 200

    # Nếu không reset thì lần này đã là lần thứ 4 -> 429.
    assert login(client).status_code == 200


def test_dang_ky_qua_nhieu_bi_chan_429(tmp_path):
    client, _ = build_client(tmp_path, register_limit=2)
    assert register(client, username="mot").status_code == 201
    assert register(client, username="hai").status_code == 201

    assert register(client, username="ba").status_code == 429


def test_dem_TRUOC_khi_bam_mat_khau(tmp_path):
    """Bị chặn rồi thì server KHÔNG được tốn 0.4s CPU băm mật khẩu nữa.

    Ngược lại thì chính cơ chế bảo vệ trở thành cách làm nghẽn server.
    """
    client, users = build_client(tmp_path, register_limit=1)
    register(client, username="mot")
    truoc = users.count()

    assert register(client, username="hai").status_code == 429
    assert users.count() == truoc, "không được ghi gì khi đã bị chặn"


# ==========================================================================
# HỢP ĐỒNG HTTP
# ==========================================================================


def test_dang_ky_thanh_cong_tra_201_va_dung_envelope(client):
    res = register(client, display_name="Nguyễn Văn A")

    assert res.status_code == 201
    data = res.json()["data"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 60
    # Tên hiển thị ĐƯỢC dùng tiếng Việt có dấu, khác tên đăng nhập.
    assert data["user"]["display_name"] == "Nguyễn Văn A"
    assert data["user"]["username"] == "nguoidung"


def test_dang_ky_tra_luon_token_dung_duoc_ngay(client):
    """Không bắt người dùng đăng nhập lại ngay sau khi đăng ký."""
    token = register(client).json()["data"]["token"]

    assert client.get(f"{API}/auth/me", headers=bearer(token)).status_code == 200


def test_ten_da_co_nguoi_dung_tra_409(client):
    register(client, username="trungten")

    res = register(client, username="trungten")

    assert res.status_code == 409
    assert res.json()["error"]["code"] == "USERNAME_TAKEN"


def test_ten_hoa_thuong_khac_nhau_van_la_MOT_tai_khoan(client):
    register(client, username="NguoiDung")

    assert register(client, username="nguoidung").status_code == 409
    # Và đăng nhập được bằng cách viết nào cũng xong.
    assert login(client, username="NGUOIDUNG").status_code == 200


@pytest.mark.parametrize(
    "username", ["ab", "co khoang trang", "dấu-tiếng-việt", "a" * 33]
)
def test_ten_sai_dinh_dang_tra_400(client, username):
    res = register(client, username=username)

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_REQUEST"


def test_mat_khau_ngan_tra_400_khi_DANG_KY(client):
    """Lúc đăng ký thì nói rõ luật được — người dùng cần biết để đặt lại."""
    res = register(client, password="1234567")

    assert res.status_code == 400
    assert "8" in res.json()["error"]["message"]


def test_mat_khau_dai_bat_thuong_bi_tu_choi_400(client):
    """Chặn tài nguyên: không để ai ép server băm PBKDF2 một chuỗi khổng lồ."""
    assert register(client, password="a" * 5000).status_code == 400


# ==========================================================================
# CHỐT CHẶN /me
# ==========================================================================


@pytest.mark.parametrize(
    "header",
    [
        {},
        {"Authorization": ""},
        {"Authorization": "Bearer"},
        {"Authorization": "Basic abc"},
        {"Authorization": "Bearer khong-phai-token"},
        {"Authorization": "Bearer a.b"},
    ],
)
def test_me_khong_co_token_hop_le_tra_401(client, header):
    res = client.get(f"{API}/auth/me", headers=header)

    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_token_bi_sua_ruot_tra_401(client):
    """Đổi payload mà không ký lại thì chữ ký hỏng -> từ chối."""
    token = register(client).json()["data"]["token"]
    body, _, chu_ky = token.partition(".")

    res = client.get(f"{API}/auth/me", headers=bearer(f"{body}x.{chu_ky}"))

    assert res.status_code == 401


def test_tai_khoan_bi_xoa_thi_token_cu_het_gia_tri(tmp_path):
    """Token còn hạn nhưng tài khoản không còn -> 401, không phải 500."""
    import sqlite3

    client, users = build_client(tmp_path)
    token = register(client).json()["data"]["token"]

    with sqlite3.connect(users.db_path) as conn:
        conn.execute("DELETE FROM users WHERE username = 'nguoidung'")
        conn.commit()

    assert client.get(f"{API}/auth/me", headers=bearer(token)).status_code == 401


# ==========================================================================
# FAIL-CLOSED
# ==========================================================================


@pytest.mark.parametrize("path,method", [("register", "post"), ("login", "post")])
def test_chua_dat_secret_thi_tra_503_kem_huong_dan(tmp_path, path, method):
    """Chưa cấu hình = TẮT, tuyệt đối không phải "cho qua"."""
    client, _ = build_client(tmp_path, secret="")

    res = getattr(client, method)(
        f"{API}/auth/{path}", json={"username": "ai", "password": PASSWORD}
    )

    assert res.status_code == 503
    assert res.json()["error"]["code"] == "DATA_NOT_READY"
    # Phải nói CÁCH KHẮC PHỤC, không chỉ báo hỏng.
    assert "MOODBITE_AUTH_SECRET" in res.json()["error"]["message"]


def test_chua_dat_secret_thi_khong_tai_khoan_nao_duoc_tao(tmp_path):
    """503 phải chặn TRƯỚC khi ghi, không phải báo lỗi sau khi đã tạo tài khoản."""
    client, users = build_client(tmp_path, secret="")

    register(client)

    assert users.count() == 0


def test_health_bao_cao_trang_thai_tai_khoan(client):
    services = client.get("/health").json()["data"]["services"]

    assert services["users"]["ready"] is True
    assert services["user_auth"]["ready"] is True


def test_health_noi_RO_khi_chua_bat_tinh_nang_tai_khoan(tmp_path):
    """Hai vấn đề khác nhau phải hiện thành hai dòng khác nhau: kho tài khoản mở được,
    nhưng chưa có secret nên tính năng vẫn tắt."""
    client, _ = build_client(tmp_path, secret="")

    services = client.get("/health").json()["data"]["services"]

    assert services["users"]["ready"] is True
    assert services["user_auth"]["ready"] is False
    assert "MOODBITE_AUTH_SECRET" in services["user_auth"]["error"]

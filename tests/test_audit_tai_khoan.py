"""Khoá các lỗ hổng tìm ra ở đợt rà soát bảo mật tài khoản 2026-10-06.

Mỗi test ở đây ĐỎ trên code trước bản sửa (đã chạy thật để xác nhận), xanh sau bản sửa.
Đánh số theo danh sách phát hiện:

  1. Lách giới hạn đăng nhập: đăng nhập ĐÚNG vào tài khoản của chính mình xoá sạch bộ đếm
     theo IP -> đoán mật khẩu người khác không giới hạn. Admin đăng nhập qua `/auth/login`
     lách được bộ đếm chặt của `/admin/login`. Admin đổi mật khẩu 8 ký tự.
  2. Nhầm loại token: token đặt lại mật khẩu / xác minh email dùng được làm token ĐĂNG
     NHẬP khi các secret trùng nhau (mặc định lui về cùng một secret).
  3. Token có ký tự ngoài ASCII -> 500 hoặc 400 lộ thông điệp nội bộ.
  4. `ValueError` trần -> 400, che bug lập trình.
  5. CSDL tài khoản hỏng -> 401 "sai mật khẩu" thay vì 503.
  6. `require_admin` phải gắn ở CẤP ROUTER.
  8. Token xác minh email mang địa chỉ email đọc được.
  9. Thư xác minh nói sai "xác minh xong mới lấy lại được mật khẩu".
 10. `make_admin_user.py` hỏi mật khẩu trước khi kiểm tên; `--tu-env` tên sai -> traceback.
 11. Giới hạn số bộ sưu tập / mục / địa chỉ bị vượt khi gửi song song; `item_id` không chặn độ dài.
"""
from __future__ import annotations

import base64
import importlib.util
import json
import sqlite3
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.domain.entities.user import User, UserRole
from src.infrastructure.auth.crypto import TokenInvalid, hash_password, sign_token, verify_token
from src.infrastructure.auth.email_verification import EmailVerificationTokenService
from src.infrastructure.auth.password_reset import PasswordResetTokenService
from src.infrastructure.auth.rate_limit import SlidingWindowRateLimiter
from tests.test_auth_api import (
    API,
    PASSWORD,
    SECRET,
    bearer,
    build_client,
    login,
    register,
)

MAT_KHAU_ADMIN = "mat-khau-quan-tri-rat-dai-123"


def _tao_admin(users, username="quantri", password=MAT_KHAU_ADMIN) -> User:
    return users.create(
        User(user_id="", username=username, password_hash=hash_password(password),
             role=UserRole.ADMIN, email="qt@vidu.com")
    )


# ==========================================================================
# 1. GIỚI HẠN ĐĂNG NHẬP
# ==========================================================================


def test_1_dang_nhap_tai_khoan_CUA_MINH_khong_xoa_bo_dem_doan_mat_khau_NGUOI_KHAC(tmp_path):
    """Tái hiện đúng kịch bản tấn công: đoán 1 lần mật khẩu nạn nhân, rồi đăng nhập ĐÚNG
    vào tài khoản của mình (cùng IP) để xoá bộ đếm, lặp lại. Bản cũ: 20 lần đoán, 0 lần 429."""
    client, _ = build_client(tmp_path, login_limit=5)
    register(client, username="nannhan", email="nn@vidu.com")
    register(client, username="kedoan", email="kd@vidu.com")

    ma = []
    for i in range(20):
        ma.append(login(client, "nannhan", f"doan-sai-{i:04d}").status_code)
        assert login(client, "kedoan", PASSWORD).status_code == 200

    assert 429 in ma, f"Không chặn lần nào: {ma}"
    assert ma.index(429) == 5


def test_1_dem_theo_TEN_DANG_NHAP_chan_ca_khi_doi_IP(tmp_path):
    """Đổi IP liên tục (mỗi IP vài lần) vẫn bị chặn ở bộ đếm theo tài khoản."""
    client, _ = build_client(tmp_path, login_limit=50)
    register(client, username="nannhan", email="nn@vidu.com")
    container = client.app.state.container
    container.login_account_rate_limiter = SlidingWindowRateLimiter(4, 900)

    ma = []
    for i in range(6):
        # Mỗi lần thử từ MỘT IP khác: bộ đếm theo IP không bao giờ chạm ngưỡng.
        may = TestClient(client.app, raise_server_exceptions=False, client=(f"10.0.0.{i}", 1))
        ma.append(login(may, "nannhan", f"sai-{i:04d}").status_code)

    assert ma[:4] == [401] * 4
    assert ma[4:] == [429, 429]


def test_1_chu_tai_khoan_dang_nhap_dung_thi_xoa_bo_dem_theo_ten_cua_CHINH_HO(tmp_path):
    client, _ = build_client(tmp_path, login_limit=50)
    register(client, username="hayquen", email="hq@vidu.com")
    container = client.app.state.container
    container.login_account_rate_limiter = SlidingWindowRateLimiter(3, 900)

    login(client, "hayquen", "sai-lan-mot-1")
    login(client, "hayquen", "sai-lan-hai-2")
    assert login(client, "hayquen", PASSWORD).status_code == 200
    # Đã xoá -> còn nguyên 3 lần.
    assert [login(client, "hayquen", f"sai-{i}-xxxx").status_code for i in range(3)] == [401] * 3


def test_1_doan_mat_khau_ADMIN_qua_auth_login_bi_ap_bo_dem_QUAN_TRI(tmp_path):
    """Admin là tài khoản trong bảng `users` nên `/auth/login` cũng đăng nhập được. Bản cũ
    chỉ áp bộ đếm người dùng (5 lần/5 phút) -> lách được bộ đếm 5 lần/15 phút của
    `/admin/login`. Nay tài khoản đích là admin thì dùng CHUNG bộ đếm quản trị."""
    client, users = build_client(tmp_path, login_limit=50)
    _tao_admin(users)
    container = client.app.state.container
    container.admin_login_rate_limiter = SlidingWindowRateLimiter(5, 900)

    ma = [login(client, "quantri", f"doan-{i:04d}").status_code for i in range(7)]

    assert ma[:5] == [401] * 5
    assert ma[5] == 429
    res = login(client, "quantri", f"doan-cuoi")
    assert int(res.headers["Retry-After"]) > 300, "phải là cửa sổ 15 phút của quản trị"


def test_1_admin_doi_mat_khau_KHONG_duoc_ngan_hon_muc_quan_tri(tmp_path):
    """`make_admin_user.py` đòi 12 ký tự nhưng `/auth/change-password` chỉ đòi 8 -> admin tự
    hạ mật khẩu xuống 8 ký tự. Luật nay nằm ở domain, mọi đường đổi mật khẩu cùng kiểm."""
    client, users = build_client(tmp_path)
    _tao_admin(users)
    token = login(client, "quantri", MAT_KHAU_ADMIN).json()["data"]["token"]

    res = client.post(
        f"{API}/auth/change-password",
        json={"current_password": MAT_KHAU_ADMIN, "new_password": "ngan-9ky"},
        headers=bearer(token),
    )
    assert res.status_code == 400, res.text
    assert "12" in res.json()["error"]["message"]

    res = client.post(
        f"{API}/auth/change-password",
        json={"current_password": MAT_KHAU_ADMIN, "new_password": "du-dai-muoi-hai-ky-tu"},
        headers=bearer(token),
    )
    assert res.status_code == 200, res.text


def test_1_nguoi_dung_thuong_van_doi_duoc_mat_khau_8_ky_tu(tmp_path):
    client, _ = build_client(tmp_path)
    token = register(client, username="thuong").json()["data"]["token"]
    res = client.post(
        f"{API}/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "tam-ky-1"},
        headers=bearer(token),
    )
    assert res.status_code == 200, res.text


def test_1_admin_dat_lai_mat_khau_qua_thu_cung_bi_kiem_muc_quan_tri(tmp_path):
    client, users = build_client(tmp_path)
    admin = _tao_admin(users)
    token = client.app.state.container.reset_tokens.issue(admin)

    res = client.post(
        f"{API}/auth/reset-password", json={"token": token, "new_password": "ngan-9ky"}
    )
    assert res.status_code == 400, res.text


# ==========================================================================
# 2. NHẦM LOẠI TOKEN
# ==========================================================================


def test_2_token_DAT_LAI_MAT_KHAU_khong_dung_duoc_de_dang_nhap_du_secret_trung(tmp_path):
    client, users = build_client(tmp_path, reset_secret=SECRET)
    register(client, username="nan", email="n@vidu.com")
    token = PasswordResetTokenService(SECRET).issue(users.get_by_username("nan"))

    res = client.get(f"{API}/auth/me", headers=bearer(token))

    assert res.status_code == 401, res.text


def test_2_token_XAC_MINH_EMAIL_khong_dung_duoc_de_dang_nhap_du_secret_trung(tmp_path):
    client, users = build_client(tmp_path)
    register(client, username="nan", email="n@vidu.com")
    token = EmailVerificationTokenService(SECRET).issue(users.get_by_username("nan"))

    assert client.get(f"{API}/auth/me", headers=bearer(token)).status_code == 401


def test_2_token_DANG_NHAP_khong_mo_duoc_cua_quan_tri_du_secret_trung():
    """Admin đăng nhập qua `/auth/login` nhận token người dùng. Nếu MOODBITE_ADMIN_SECRET
    trùng MOODBITE_AUTH_SECRET thì bản cũ chấp nhận token đó ở `/admin/*` — nó chỉ kiểm
    `sub` là admin và `tv` khớp."""
    from src.application.errors import InvalidCredentialsError
    from src.infrastructure.auth.admin_auth import AdminAuthService
    from src.infrastructure.auth.user_auth import UserTokenService
    from tests.fakes import InMemoryUserRepo

    admin = User(user_id="u-a", username="admin", password_hash="x", role=UserRole.ADMIN)
    token_nguoi_dung = UserTokenService("CUNG-MOT-SECRET").issue(admin)

    with pytest.raises(InvalidCredentialsError):
        AdminAuthService(InMemoryUserRepo([admin]), "CUNG-MOT-SECRET").verify(token_nguoi_dung)


def test_2_token_dang_nhap_CU_khong_co_typ_van_dung_duoc_nhung_token_cu_loai_khac_thi_khong():
    """Token phát TRƯỚC khi có `typ` vẫn được nhận đúng mục đích của nó (suy ra từ các
    trường đặc trưng), nhờ vậy nâng cấp không đăng xuất ai và không giết thư đã gửi."""
    secret = b"s"
    dang_nhap_cu = sign_token({"sub": "u1", "tv": 0}, secret, 60, purpose=None)
    dat_lai_cu = sign_token({"sub": "u1", "pw": "abcd"}, secret, 60, purpose=None)

    assert verify_token(dang_nhap_cu, secret, purpose="login")["sub"] == "u1"
    assert verify_token(dat_lai_cu, secret, purpose="reset")["sub"] == "u1"
    with pytest.raises(TokenInvalid):
        verify_token(dat_lai_cu, secret, purpose="login")
    with pytest.raises(TokenInvalid):
        verify_token(dang_nhap_cu, secret, purpose="admin")


def test_2_canh_bao_khi_cac_secret_trung_nhau():
    from src.infrastructure.auth.crypto import shared_secret_groups

    nhom = shared_secret_groups(
        {"MOODBITE_AUTH_SECRET": "a", "MOODBITE_RESET_SECRET": "a",
         "MOODBITE_ADMIN_SECRET": "b", "MOODBITE_EMAIL_VERIFY_SECRET": ""}
    )
    assert nhom == [["MOODBITE_AUTH_SECRET", "MOODBITE_RESET_SECRET"]]


# ==========================================================================
# 3. TOKEN NGOÀI ASCII
# ==========================================================================


@pytest.mark.parametrize("token", ["ábc.def", "abc.dèf", "日本.語"])
def test_3_verify_token_tu_choi_ky_tu_ngoai_ascii(token):
    with pytest.raises(TokenInvalid):
        verify_token(token, b"secret", purpose="login")


@pytest.mark.parametrize("token", ["ábc.def", "abc.dèf"])
@pytest.mark.parametrize(
    "path,body_key",
    [("/auth/reset-password", "token"), ("/auth/verify-email/confirm", "token")],
)
def test_3_token_ngoai_ascii_tra_401_khong_phai_500_hay_400_lo_noi_bo(
    tmp_path, token, path, body_key
):
    client, _ = build_client(tmp_path)
    body = {body_key: token, "new_password": "mat-khau-moi-123"}

    res = client.post(f"{API}{path}", json=body)

    assert res.status_code == 401, res.text
    assert res.json()["error"]["code"] == "UNAUTHORIZED"
    assert "codec" not in res.text and "ascii" not in res.text


# ==========================================================================
# 4. ValueError trần KHÔNG được thành 400
# ==========================================================================


def test_4_ValueError_tran_la_BUG_tra_500_con_loi_domain_tra_400(tmp_path):
    from src.domain.entities.collection import InvalidCollection

    client, _ = build_client(tmp_path)

    def _bug():
        int("khong-phai-so")

    def _loi_nghiep_vu():
        raise InvalidCollection("Tên bộ sưu tập không được để trống.")

    client.app.add_api_route("/__bug", _bug)
    client.app.add_api_route("/__nghiep_vu", _loi_nghiep_vu)

    bug = client.get("/__bug")
    assert bug.status_code == 500
    assert bug.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "khong-phai-so" not in bug.text, "không được lộ thông điệp nội bộ"

    nv = client.get("/__nghiep_vu")
    assert nv.status_code == 400
    assert nv.json()["error"]["code"] == "INVALID_REQUEST"


def test_4_moi_loi_kiem_du_lieu_cua_domain_deu_ke_thua_DomainValidationError():
    from src.application.use_cases.manage_restaurants import InvalidBulkRequest
    from src.domain.entities.audit_log import InvalidAuditEntry
    from src.domain.entities.collection import InvalidCollection
    from src.domain.entities.saved_item import InvalidSavedItem
    from src.domain.entities.user import InvalidCredentialsFormat, InvalidEmailFormat
    from src.domain.entities.user_address import InvalidUserAddress
    from src.domain.errors import DomainValidationError
    from src.domain.value_objects.location import InvalidCoordinates
    from src.domain.value_objects.mood import UnsupportedMoodError
    from src.domain.value_objects.restaurant_edit import InvalidEditError
    from src.domain.value_objects.restaurant_new import InvalidNewRestaurant

    for lop in (InvalidBulkRequest, InvalidAuditEntry, InvalidCollection, InvalidSavedItem,
                InvalidCredentialsFormat, InvalidEmailFormat, InvalidUserAddress,
                InvalidCoordinates, UnsupportedMoodError, InvalidEditError,
                InvalidNewRestaurant):
        assert issubclass(lop, DomainValidationError), lop


# ==========================================================================
# 5. CSDL tài khoản hỏng -> 503, KHÔNG phải 401
# ==========================================================================


def _pha_bang_users(users) -> None:
    """Giả lập CSDL hỏng giữa chừng (bị khoá / mất bảng): mọi câu SQL sau đó đều lỗi."""
    with sqlite3.connect(users.db_path) as conn:
        conn.execute("ALTER TABLE users RENAME TO users_hong")


def test_5_CSDL_hong_thi_auth_me_tra_503_khong_phai_401(tmp_path):
    client, users = build_client(tmp_path)
    token = register(client).json()["data"]["token"]
    _pha_bang_users(users)

    res = client.get(f"{API}/auth/me", headers=bearer(token))

    assert res.status_code == 503, res.text
    assert res.json()["error"]["code"] == "DATA_NOT_READY"


def test_5_CSDL_hong_thi_dang_nhap_tra_503_khong_phai_sai_mat_khau(tmp_path):
    client, users = build_client(tmp_path)
    register(client)
    _pha_bang_users(users)

    assert login(client).status_code == 503


def test_5_CSDL_hong_khi_ghi_thi_repo_nem_loi_chu_khong_tra_False(tmp_path):
    from src.application.errors import StorageUnavailableError
    from src.infrastructure.repositories.sqlite_user_repository import SqliteUserRepository

    users = SqliteUserRepository(tmp_path / "u.db")
    u = users.create(User(user_id="", username="abc", password_hash="x"))
    _pha_bang_users(users)

    with pytest.raises(StorageUnavailableError):
        users.revoke_tokens(u.user_id)
    with pytest.raises(StorageUnavailableError):
        users.update_password(u.user_id, "y")
    with pytest.raises(StorageUnavailableError):
        users.get_by_id(u.user_id)


def test_5_khong_tim_thay_van_la_None(tmp_path):
    from src.infrastructure.repositories.sqlite_user_repository import SqliteUserRepository

    users = SqliteUserRepository(tmp_path / "u.db")
    assert users.get_by_id("khong-co") is None
    assert users.revoke_tokens("khong-co") is False


# ==========================================================================
# 6. require_admin ở CẤP ROUTER
# ==========================================================================


def test_6_require_admin_gan_o_cap_router():
    from src.presentation.api.dependencies import require_admin
    from src.presentation.api.routers import admin

    assert any(d.dependency is require_admin for d in admin.router.dependencies)
    assert not any(d.dependency is require_admin for d in admin.public_router.dependencies)


def test_6_MOI_endpoint_admin_tru_login_deu_401_khi_khong_co_token(tmp_path):
    from tests.test_admin_api import build_client as build_admin_client
    from tests.test_sqlite_repository import make_db

    db = make_db(tmp_path, {"place_id": "p1", "name": "Phở", "category": "Nhà hàng",
                            "address": "1 Phố", "is_active": 1})
    client, _ = build_admin_client(db)

    # Duyệt theo OpenAPI: FastAPI bản mới gom route của `include_router` thành nhóm lồng
    # nhau nên `app.routes` không còn liệt kê phẳng từng đường dẫn.
    da_thu = 0
    for path, cac_method in client.app.openapi()["paths"].items():
        if not path.startswith(f"{API}/admin") or path == f"{API}/admin/login":
            continue
        url = path.replace("{", "").replace("}", "")
        for method in cac_method:
            res = client.request(method.upper(), url, json={})
            assert res.status_code == 401, f"{method} {path} -> {res.status_code}"
            da_thu += 1
    assert da_thu >= 15, "phải thực sự duyệt qua các endpoint quản trị"


# ==========================================================================
# 8 + 9. Thư xác minh email
# ==========================================================================


def _ruot_token(token: str) -> dict:
    body = token.split(".")[0]
    return json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))


def test_8_token_xac_minh_KHONG_mang_dia_chi_email_doc_duoc():
    user = User(user_id="u1", username="a", password_hash="x", email="bimat@vidu.com")
    token = EmailVerificationTokenService("s").issue(user)

    ruot = _ruot_token(token)
    assert "bimat" not in json.dumps(ruot)
    assert "em" not in ruot


def test_8_xac_minh_van_chay_tron_luong_va_doi_email_thi_link_cu_chet(tmp_path):
    from tests.fakes import FakeEmailSender

    thu = FakeEmailSender()
    client, users = build_client(tmp_path, emails=thu)
    token_dn = register(client, username="xacminh", email="a@vidu.com").json()["data"]["token"]
    link = thu.da_gui[-1]["body"]
    token = link.split("token=")[1].split()[0]

    res = client.post(f"{API}/auth/verify-email/confirm", json={"token": token})
    assert res.status_code == 200, res.text
    assert res.json()["data"]["email_verified"] is True
    # Bấm lại link cũ -> chết.
    assert client.post(f"{API}/auth/verify-email/confirm", json={"token": token}).status_code == 401
    assert client.get(f"{API}/auth/me", headers=bearer(token_dn)).status_code == 200


def test_9_thu_xac_minh_KHONG_noi_sai_ve_dieu_kien_lay_lai_mat_khau(tmp_path):
    from tests.fakes import FakeEmailSender

    thu = FakeEmailSender()
    client, _ = build_client(tmp_path, emails=thu)
    register(client, username="docthu", email="d@vidu.com")

    noi_dung = thu.da_gui[-1]["body"]
    assert "mới lấy lại được mật khẩu" not in noi_dung


# ==========================================================================
# 10. make_admin_user.py
# ==========================================================================


def _nap_script():
    spec = importlib.util.spec_from_file_location(
        "make_admin_user_audit",
        Path(__file__).resolve().parent.parent / "scripts" / "make_admin_user.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_10_tu_env_ten_sai_dinh_dang_KHONG_traceback(tmp_path):
    from src.infrastructure.repositories.sqlite_user_repository import SqliteUserRepository

    script = _nap_script()
    repo = SqliteUserRepository(tmp_path / "u.db")

    ket_qua = script.nhap_tu_env(
        repo,
        {"MOODBITE_ADMIN_USER": "Quản trị!", "MOODBITE_ADMIN_PASSWORD_HASH": hash_password("x")},
    )

    assert ket_qua == script.TEN_KHONG_HOP_LE
    assert repo.count() == 0


def test_10_hoi_dap_kiem_TEN_truoc_khi_hoi_mat_khau(tmp_path, monkeypatch, capsys):
    from src.infrastructure.repositories.sqlite_user_repository import SqliteUserRepository

    script = _nap_script()
    repo = SqliteUserRepository(tmp_path / "u.db")
    monkeypatch.setattr("builtins.input", lambda *_: "ten sai!")

    def _khong_duoc_hoi(*_a, **_k):
        raise AssertionError("không được hỏi mật khẩu khi tên đã sai")

    monkeypatch.setattr(script.getpass, "getpass", _khong_duoc_hoi)

    assert script._che_do_hoi_dap(repo) == 1
    assert "[LOI]" in capsys.readouterr().out


# ==========================================================================
# 11. Giới hạn số lượng: kiểm trong CÙNG giao dịch với lệnh ghi
# ==========================================================================


def test_11_kho_bo_suu_tap_TU_chan_khi_da_du_so_bo(tmp_path, monkeypatch):
    """Use case đếm rồi mới ghi -> hai request song song cùng thấy "còn chỗ". Kho phải tự
    kiểm lại trong giao dịch ghi. Test gọi thẳng kho (bỏ qua bước đếm của use case)."""
    from src.domain.entities import collection as mod
    from src.domain.entities.collection import Collection, InvalidCollection
    from src.infrastructure.repositories.sqlite_collection_repository import (
        SqliteCollectionRepository,
    )

    monkeypatch.setattr(mod, "MAX_COLLECTIONS_PER_USER", 3)
    repo = SqliteCollectionRepository(tmp_path / "c.db")
    for i in range(3):
        repo.create(Collection(collection_id=f"c{i}", user_id="u1", name=f"Bộ {i}"))

    with pytest.raises(InvalidCollection):
        repo.create(Collection(collection_id="c-thua", user_id="u1", name="Thừa"))
    assert repo.count_for_user("u1") == 3


def test_11_tao_bo_suu_tap_SONG_SONG_khong_vuot_gioi_han(tmp_path, monkeypatch):
    from src.application.use_cases.manage_collections import CreateCollectionUseCase
    from src.domain.entities import collection as mod
    from src.infrastructure.repositories.sqlite_collection_repository import (
        SqliteCollectionRepository,
    )

    monkeypatch.setattr(mod, "MAX_COLLECTIONS_PER_USER", 5)
    repo = SqliteCollectionRepository(tmp_path / "c.db")
    tao = CreateCollectionUseCase(repo)
    rao = threading.Barrier(12)

    def _chay(i):
        rao.wait()
        try:
            tao.execute("u1", f"Bộ {i}")
        except ValueError:
            pass

    luong = [threading.Thread(target=_chay, args=(i,)) for i in range(12)]
    for t in luong:
        t.start()
    for t in luong:
        t.join()

    assert repo.count_for_user("u1") <= 5


def test_11_kho_bo_suu_tap_TU_chan_khi_bo_da_day_muc(tmp_path, monkeypatch):
    from src.domain.entities import collection as mod
    from src.domain.entities.collection import Collection, CollectionItem, InvalidCollection
    from src.domain.entities.saved_item import SavedItemType
    from src.infrastructure.repositories.sqlite_collection_repository import (
        SqliteCollectionRepository,
    )

    monkeypatch.setattr(mod, "MAX_ITEMS_PER_COLLECTION", 2)
    repo = SqliteCollectionRepository(tmp_path / "c.db")
    repo.create(Collection(collection_id="c1", user_id="u1", name="Bộ"))
    for i in range(2):
        repo.add_item("u1", "c1", CollectionItem(SavedItemType.RESTAURANT, f"r{i}", "Quán"))

    with pytest.raises(InvalidCollection):
        repo.add_item("u1", "c1", CollectionItem(SavedItemType.RESTAURANT, "r-thua", "Quán"))
    # Thêm lại mục ĐÃ CÓ vẫn được (idempotent, không làm bộ to thêm).
    assert repo.add_item("u1", "c1", CollectionItem(SavedItemType.RESTAURANT, "r0", "Tên mới"))


def test_11_kho_dia_chi_TU_chan_khi_da_du(tmp_path, monkeypatch):
    from src.domain.entities import user_address as mod
    from src.domain.entities.user_address import InvalidUserAddress, UserAddress
    from src.infrastructure.repositories.sqlite_user_address_repository import (
        SqliteUserAddressRepository,
    )

    monkeypatch.setattr(mod, "MAX_ADDRESSES_PER_USER", 2)
    repo = SqliteUserAddressRepository(tmp_path / "a.db")
    for i in range(2):
        repo.create(UserAddress(f"a{i}", "u1", f"Nhà {i}", None, 21.03, 105.85))

    with pytest.raises(InvalidUserAddress):
        repo.create(UserAddress("a-thua", "u1", "Thừa", None, 21.03, 105.85))
    assert repo.count_for_user("u1") == 2


def test_11_item_id_qua_dai_bi_tu_choi_khong_cat_lang_le():
    from src.domain.entities.saved_item import (
        MAX_SAVED_ITEM_ID_LENGTH,
        InvalidSavedItem,
        validate_saved_item,
    )

    assert validate_saved_item("restaurant", "x" * MAX_SAVED_ITEM_ID_LENGTH, "Quán")[1]
    with pytest.raises(InvalidSavedItem):
        validate_saved_item("restaurant", "x" * (MAX_SAVED_ITEM_ID_LENGTH + 1), "Quán")

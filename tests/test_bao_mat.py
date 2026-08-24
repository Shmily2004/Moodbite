"""Khoá các chốt chặn BẢO MẬT dễ bị nới lỏng lại mà không ai nhận ra.

Hai lỗ hổng dưới đây là thật, tìm được trong lượt rà soát ngày 2026-08-24, và cả hai đều
thuộc loại "không ai thấy gì khác lạ khi nó hỏng":

  1. CORS mặc định là `*` kèm `allow_credentials=True`.
  2. `/admin/login` KHÔNG có giới hạn tần suất, trong khi `/auth/login` thì có.

Cái đáng sợ của cả hai là nới lỏng lại RẤT dễ — sửa một dòng mặc định, xoá một lời gọi —
và không test nào đỏ, không log nào kêu. Nên phải có test đứng canh.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.auth.rate_limit import (
    ADMIN_LOGIN_MAX_ATTEMPTS,
    SlidingWindowRateLimiter,
)
from src.presentation.api.main import create_app
from tests.test_admin_api import PASSWORD as MAT_KHAU_ADMIN, build_client
from tests.test_sqlite_repository import make_db

API = "/api/v1"


# --- 1. CORS ----------------------------------------------------------------


@pytest.fixture
def app_mac_dinh(monkeypatch):
    """App với CORS đúng như mặc định — KHÔNG đặt biến môi trường nào."""
    monkeypatch.delenv("MOODBITE_CORS_ORIGINS", raising=False)
    return TestClient(create_app())


def test_cors_mac_dinh_khong_mo_cho_moi_trang_web(app_mac_dinh):
    """Origin lạ KHÔNG được nhận `Access-Control-Allow-Origin`.

    Bản trước mặc định `"*"` nên mọi trang web đều gọi được API bằng JS. Rủi ro khai thác
    ngay lúc đó là thấp (token nằm trong `localStorage`, trang khác không đọc được),
    nhưng "mở hết rồi trông chờ lớp bảo vệ khác" không phải thứ nên để trong đồ án.
    """
    res = app_mac_dinh.get(
        f"{API}/health", headers={"Origin": "https://trang-web-la.example"}
    )

    assert res.headers.get("access-control-allow-origin") is None


def test_cors_mac_dinh_van_cho_frontend_cua_du_an(app_mac_dinh):
    """Siết CORS KHÔNG được làm chết môi trường phát triển của chính dự án.

    5173 = app người dùng, 5174 = app quản trị (xem `frontend/apps/*/vite.config.ts`).
    """
    for cong in (5173, 5174):
        res = app_mac_dinh.get(
            f"{API}/health", headers={"Origin": f"http://localhost:{cong}"}
        )
        assert res.headers.get("access-control-allow-origin") == f"http://localhost:{cong}"


def test_cors_van_dat_duoc_bang_bien_moi_truong(monkeypatch):
    """Deploy thật phải khai được tên miền của mình — siết KHÔNG được thành cứng nhắc."""
    monkeypatch.setenv("MOODBITE_CORS_ORIGINS", "https://moodbite.vn")
    client = TestClient(create_app())

    res = client.get(f"{API}/health", headers={"Origin": "https://moodbite.vn"})

    assert res.headers.get("access-control-allow-origin") == "https://moodbite.vn"


# --- 2. Giới hạn tần suất đăng nhập quản trị --------------------------------


MAT_KHAU = MAT_KHAU_ADMIN


@pytest.fixture
def client_admin(tmp_path):
    """App quản trị với bộ đếm ĐÚNG ngưỡng thật, thay cho bộ đếm rộng của test khác."""
    db = make_db(
        tmp_path,
        {"place_id": "pho-1", "name": "Phở Bò", "category": "Nhà hàng phở",
         "address": "12 Hàng Đồng", "is_active": 1},
    )
    client, _ = build_client(db)
    client.app.state.container.admin_login_rate_limiter = SlidingWindowRateLimiter(
        ADMIN_LOGIN_MAX_ATTEMPTS, 900
    )
    return client


def _dang_nhap(client, mat_khau):
    from tests.test_admin_api import USER

    return client.post(
        f"{API}/admin/login", json={"username": USER, "password": mat_khau}
    )


def test_doan_mat_khau_admin_bi_chan_sau_vai_lan(client_admin):
    """Chỉ có MỘT tài khoản quản trị và nó sửa/ẩn được mọi quán — đây là cửa duy nhất."""
    ma = [_dang_nhap(client_admin, "doan-bua").status_code
          for _ in range(ADMIN_LOGIN_MAX_ATTEMPTS + 2)]

    assert 429 in ma, f"KHÔNG chặn lần nào: {ma}"
    assert ma.index(429) == ADMIN_LOGIN_MAX_ATTEMPTS


def test_chan_truoc_ca_khi_mat_khau_dung(client_admin):
    """Đã quá ngưỡng thì mật khẩu đúng cũng phải đợi.

    Nếu mật khẩu đúng vẫn lọt qua sau khi bị chặn, bộ đếm chỉ là hình thức: kẻ tấn công
    cứ thử tới khi trúng, lần trúng đó vẫn vào được.
    """
    for _ in range(ADMIN_LOGIN_MAX_ATTEMPTS):
        _dang_nhap(client_admin, "doan-bua")

    assert _dang_nhap(client_admin, MAT_KHAU).status_code == 429


def test_dang_nhap_dung_thi_xoa_lich_su_dem(client_admin):
    """Người quản trị gõ nhầm vài lần rồi vào được KHÔNG đáng bị chặn oan lần sau."""
    for _ in range(ADMIN_LOGIN_MAX_ATTEMPTS - 1):
        _dang_nhap(client_admin, "doan-bua")
    assert _dang_nhap(client_admin, MAT_KHAU).status_code == 200

    # Bộ đếm đã được xoá -> vẫn còn nguyên hạn mức cho lần sau.
    ma = [_dang_nhap(client_admin, "doan-bua").status_code
          for _ in range(ADMIN_LOGIN_MAX_ATTEMPTS)]
    assert 429 not in ma


# --- 3. Không bao giờ lộ chuỗi băm mật khẩu ---------------------------------


def test_khong_endpoint_nao_tra_ve_password_hash(tmp_path):
    """Khoá lại điều đã hứa trong docstring của `User.to_public` / `to_self`.

    Đặc biệt đáng khoá SAU ngày 2026-08-24, vì hôm đó `/auth/login` và `/auth/register`
    được đổi từ `to_public()` sang `to_self()` — trả nhiều trường hơn trước.
    """
    from tests.test_auth_api import build_client as build_auth_client, register

    client, _ = build_auth_client(tmp_path)

    dang_ky = register(client, email="ai.do@vi.du.com")
    token = dang_ky.json()["data"]["token"]
    ho_so = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})

    for res in (dang_ky, ho_so):
        assert "password_hash" not in res.text
        assert "pbkdf2" not in res.text.lower()

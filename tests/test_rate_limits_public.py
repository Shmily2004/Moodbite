"""Giới hạn tần suất cho hai endpoint CÔNG KHAI tốn tài nguyên: `POST /search` và
`POST /interactions`.

VÌ SAO (rà soát 2026-10-06):
  - Mỗi lượt `/search` có câu chữ tốn ~0,8-2 giây CPU (đo 2026-10-02). Không chặn thì một
    người gửi liên tục là đủ chiếm hết CPU — endpoint không cần đăng nhập.
  - `/interactions` không cần đăng nhập; `report_closed` ẩn được quán với MỌI người nên
    phải chặt hơn hẳn các loại tương tác khác.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.auth.rate_limit import SlidingWindowRateLimiter
from src.infrastructure.config.settings import (
    DEFAULT_CLOSURE_REPORT_RATE_LIMIT,
    DEFAULT_INTERACTION_RATE_LIMIT,
    DEFAULT_SEARCH_RATE_LIMIT,
    Settings,
    parse_rate_limit,
)
from src.presentation.api.main import create_app
from tests.test_api import SESSION, _container

API = "/api/v1"


def _client(**limiters):
    c = _container()
    for ten, gioi_han in limiters.items():
        setattr(c, ten, gioi_han)
    return TestClient(create_app(container=c), raise_server_exceptions=False), c


def test_search_qua_gioi_han_tra_429_kem_Retry_After():
    client, _ = _client(search_rate_limiter=SlidingWindowRateLimiter(2, 60))
    body = {"session_id": SESSION, "limit": 1}
    assert client.post(f"{API}/search", json=body).status_code == 200
    assert client.post(f"{API}/search", json=body).status_code == 200

    res = client.post(f"{API}/search", json=body)

    assert res.status_code == 429
    assert res.json()["error"]["code"] == "RATE_LIMITED"
    assert int(res.headers["Retry-After"]) > 0


def test_khong_lap_bo_dem_thi_search_khong_bi_chan():
    """Container test cũ (Container.__new__) không có bộ đếm -> hành vi y như trước."""
    client, _ = _client()
    for _ in range(5):
        assert client.post(f"{API}/search", json={"session_id": SESSION}).status_code == 200


def _tuong_tac(client, action="view_detail", **extra):
    body = {
        "session_id": SESSION,
        "restaurant_id": "id-Quan Pho",
        "action_type": action,
        "dwell_time_ms": 5000,
        **extra,
    }
    return client.post(f"{API}/interactions", json=body)


def test_interactions_qua_gioi_han_chung_tra_429():
    client, _ = _client(interaction_rate_limiter=SlidingWindowRateLimiter(3, 60))
    for _ in range(3):
        assert _tuong_tac(client).status_code == 201
    assert _tuong_tac(client).status_code == 429


def test_bao_dong_cua_co_gioi_han_RIENG_chat_hon():
    client, _ = _client(
        interaction_rate_limiter=SlidingWindowRateLimiter(100, 60),
        closure_report_rate_limiter=SlidingWindowRateLimiter(2, 3600),
    )
    assert _tuong_tac(client, "report_closed").status_code == 201
    assert _tuong_tac(client, "report_closed").status_code == 201

    res = _tuong_tac(client, "report_closed")
    assert res.status_code == 429
    assert "Retry-After" in res.headers
    # Hành động khác KHÔNG bị vạ lây: người dùng vẫn xem quán bình thường.
    assert _tuong_tac(client, "view_detail").status_code == 201


# --- Cấu hình -----------------------------------------------------------------------


def test_gia_tri_mac_dinh_hop_ly():
    # Tìm kiếm rộng tay (người thật hiếm khi quá 30 lượt/phút), báo đóng cửa rất chặt.
    assert DEFAULT_SEARCH_RATE_LIMIT == (30, 60)
    assert DEFAULT_INTERACTION_RATE_LIMIT == (120, 60)
    assert DEFAULT_CLOSURE_REPORT_RATE_LIMIT == (5, 3600)


@pytest.mark.parametrize(
    "raw, ky_vong",
    [
        (None, (30, 60)),
        ("", (30, 60)),
        ("10/30", (10, 30)),
        (" 10 / 30 ", (10, 30)),
        ("0/60", (0, 60)),       # 0 = TẮT giới hạn, phải là lựa chọn có ý thức
        ("abc", (30, 60)),       # rác -> giữ mặc định, KHÔNG làm sập app lúc khởi động
        ("10", (30, 60)),
        ("-1/60", (30, 60)),
        ("5/0", (30, 60)),
    ],
)
def test_doc_gioi_han_tu_bien_moi_truong(raw, ky_vong):
    assert parse_rate_limit(raw, (30, 60)) == ky_vong


def test_settings_doc_bien_moi_truong(monkeypatch):
    monkeypatch.setenv("MOODBITE_SEARCH_RATE_LIMIT", "7/11")
    monkeypatch.delenv("MOODBITE_INTERACTION_RATE_LIMIT", raising=False)
    s = Settings.from_env()
    assert s.search_rate_limit == (7, 11)
    assert s.interaction_rate_limit == DEFAULT_INTERACTION_RATE_LIMIT


def test_build_container_lap_dung_bo_dem_theo_settings(tmp_path):
    import dataclasses

    from src.presentation.api.dependencies import build_container
    from tests.test_dish_index_freshness import _settings
    from tests.test_sqlite_repository import make_db

    db = make_db(tmp_path, {"place_id": "p1", "name": "Quán A"})
    s = dataclasses.replace(
        _settings(tmp_path, db),
        search_rate_limit=(4, 9),
        interaction_rate_limit=(0, 60),
        closure_report_rate_limit=(2, 99),
    )
    c = build_container(s)
    assert (c.search_rate_limiter.max_attempts, c.search_rate_limiter.window_seconds) == (4, 9)
    # 0 lượt = tắt giới hạn.
    assert c.interaction_rate_limiter is None
    assert c.closure_report_rate_limiter.max_attempts == 2

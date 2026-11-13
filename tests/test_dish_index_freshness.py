"""Chỉ mục MÓN -> QUÁN phải theo kịp thao tác quản trị, và luồng món phải trả 503 khi
thiếu dữ liệu quán.

BUG THẬT (rà soát 2026-10-06), tái hiện được trên đúng `build_container`:
  - Chỉ mục món-quán dựng MỘT LẦN lúc khởi động từ `restaurant_repository.list_all()`.
  - Admin ẩn/sửa/thêm quán -> `SqliteRestaurantRepository._write()` -> `reload()`, nhưng
    chỉ mục vẫn giữ các đối tượng `Restaurant` CŨ (is_active=True).
  - Hậu quả: `repo.set_active("p1", False)` xong thì `repo.list_all() == []` mà
    `/dishes/{id}/restaurants` VẪN trả p1; quán admin vừa thêm không bao giờ hiện cho tới
    lần khởi động lại; tên/giá vừa sửa vẫn hiện bản cũ.

Test đi qua `build_container` THẬT (không lắp tay) vì lỗi nằm đúng ở chỗ lắp dây.

BUG THẬT thứ hai: thiếu dataset quán thì `/dishes/{id}/restaurants` trả 200 kèm câu
"Chưa có quán nào… khớp món" và `/dishes/suggest` trả 200 kèm "285 món chưa tìm được
quán" — đổ lỗi cho dữ liệu món trong khi thực ra CHƯA NẠP được quán nào.
"""
from __future__ import annotations

import dataclasses
import json

import pytest
from fastapi.testclient import TestClient

from tests.fakes import attach_test_user
from src.infrastructure.config.settings import Settings
from src.infrastructure.repositories.sqlite_restaurant_repository import (
    SqliteRestaurantRepository,
)
from src.domain.entities.restaurant import Restaurant
from src.domain.value_objects.location import Location
from src.presentation.api.dependencies import build_container
from src.presentation.api.main import create_app
from tests.test_sqlite_repository import make_db

API = "/api/v1"
SESSION = "phien-test-chi-muc"

CATALOG = {
    "dishes": [
        {
            "dish_id": "pho-bo",
            "name": "Phở bò",
            "cuisine": "Việt Nam",
            "match_keywords": ["phở bò"],
            "source": "test",
            "is_active": True,
        }
    ]
}


def _settings(tmp_path, db_path, *, catalog=True) -> Settings:
    """Settings THẬT trỏ toàn bộ vào thư mục tạm.

    `dataclasses.replace` trên `from_env()` thay vì gọi constructor: Settings còn được
    thêm trường mới thường xuyên, dựng tay ở đây sẽ vỡ mỗi lần như vậy.
    """
    catalog_path = tmp_path / "dish_catalog.json"
    if catalog:
        catalog_path.write_text(json.dumps(CATALOG, ensure_ascii=False), encoding="utf-8")
    thieu = tmp_path / "khong-ton-tai"
    return dataclasses.replace(
        Settings.from_env(),
        restaurants_db=db_path,
        restaurants_csv=thieu / "x.csv",
        storage_backend="sqlite",
        restaurant_details_json=thieu / "details.json",
        dish_knowledge_json=thieu / "kb.json",
        dish_catalog_json=catalog_path,
        review_summaries_json=thieu / "summaries.json",
        dish_model_path=thieu / "model.joblib",
        interactions_path=tmp_path / "interactions.jsonl",
        users_db=tmp_path / "users.db",
        enable_weather=False,
        dish_adapter_mode="kb",
    )


@pytest.fixture
def app_and_repo(tmp_path):
    db = make_db(
        tmp_path,
        {"place_id": "p1", "name": "Phở Bò Hàng Đồng", "category": "Nhà hàng",
         "price": "1-100.000 ₫"},
    )
    container = build_container(_settings(tmp_path, db))
    headers = attach_test_user(container)
    client = TestClient(create_app(container=container), raise_server_exceptions=False, headers=headers)
    return client, container.restaurant_repository, container


def _ids(client) -> list:
    res = client.get(
        f"{API}/dishes/pho-bo/restaurants", params={"session_id": SESSION}
    )
    assert res.status_code == 200, res.text
    return [r["restaurant_id"] for r in res.json()["data"]["results"]]


def _names(client) -> list:
    res = client.get(
        f"{API}/dishes/pho-bo/restaurants", params={"session_id": SESSION}
    )
    return [r["name"] for r in res.json()["data"]["results"]]


def test_an_quan_thi_trang_mon_KHONG_con_hien_quan_do(app_and_repo):
    client, repo, _ = app_and_repo
    assert isinstance(repo, SqliteRestaurantRepository)
    assert _ids(client) == ["p1"]

    repo.set_active("p1", False)

    assert repo.list_all() == []
    assert _ids(client) == []


def test_an_quan_thi_so_quan_cua_mon_o_trang_chu_cung_giam(app_and_repo):
    client, repo, _ = app_and_repo
    body = {"session_id": SESSION}
    truoc = client.post(f"{API}/dishes/suggest", json=body).json()["data"]["results"]
    assert [d["restaurant_count"] for d in truoc if d["dish_id"] == "pho-bo"] == [1]

    repo.set_active("p1", False)

    chi_tiet = client.get(f"{API}/dishes/pho-bo").json()["data"]
    assert chi_tiet["restaurant_count"] == 0


def test_quan_admin_vua_them_hien_ngay_khong_can_khoi_dong_lai(app_and_repo):
    client, repo, _ = app_and_repo
    repo.create(
        Restaurant(
            place_id="moi-1", name="Phở Bò Mới Mở", category="Nhà hàng",
            location=Location(lat=21.031, lng=105.851), source="manual",
        )
    )
    assert "moi-1" in _ids(client)


def test_sua_ten_quan_thi_trang_mon_hien_ten_moi(app_and_repo):
    client, repo, _ = app_and_repo
    repo.update_fields("p1", {"name": "Phở Bò Hàng Đồng (cơ sở 2)"})
    assert _names(client) == ["Phở Bò Hàng Đồng (cơ sở 2)"]


def test_bang_mon_quan_tri_dem_lai_sau_khi_an(app_and_repo):
    _, repo, container = app_and_repo
    hang = container.list_dishes_for_admin.execute().rows
    assert [r.restaurant_count for r in hang if r.dish_id == "pho-bo"] == [1]

    repo.set_active("p1", False)

    hang = container.list_dishes_for_admin.execute().rows
    assert [r.restaurant_count for r in hang if r.dish_id == "pho-bo"] == [0]


def test_chi_muc_KHONG_dung_lai_moi_request_khi_du_lieu_khong_doi(app_and_repo, monkeypatch):
    """Dựng chỉ mục mất ~3,9 giây trên 52.871 quán (đo 2026-10-06) -> chỉ được dựng lại
    khi dữ liệu ĐỔI, không phải ở mỗi request."""
    client, _, _ = app_and_repo
    from src.infrastructure.adapters import live_dish_restaurant_index as mod

    so_lan = {"n": 0}
    goc = mod.build_dish_restaurant_index

    def dem(*a, **k):
        so_lan["n"] += 1
        return goc(*a, **k)

    monkeypatch.setattr(mod, "build_dish_restaurant_index", dem)
    for _ in range(5):
        _ids(client)
    assert so_lan["n"] == 0


# --- Thiếu dataset quán -> 503, không phải 200 kèm cảnh báo sai -----------------------


@pytest.fixture
def client_khong_co_quan(tmp_path):
    db_khong_ton_tai = tmp_path / "chua-dung.db"
    container = build_container(_settings(tmp_path, db_khong_ton_tai))
    assert container.restaurant_repository.is_ready is False
    headers = attach_test_user(container)
    return TestClient(create_app(container=container), raise_server_exceptions=False, headers=headers)


def test_thieu_du_lieu_quan_thi_trang_quan_cua_mon_tra_503(client_khong_co_quan):
    res = client_khong_co_quan.get(
        f"{API}/dishes/pho-bo/restaurants", params={"session_id": SESSION}
    )
    assert res.status_code == 503, res.text
    err = res.json()["error"]
    assert err["code"] == "DATA_NOT_READY"
    # Phải kèm LỆNH cần chạy (CLAUDE.md mục 5).
    assert "python scripts/build_sqlite.py" in err["message"]


def test_thieu_du_lieu_quan_thi_goi_y_mon_tra_503(client_khong_co_quan):
    res = client_khong_co_quan.post(f"{API}/dishes/suggest", json={"session_id": SESSION})
    assert res.status_code == 503, res.text
    assert res.json()["error"]["code"] == "DATA_NOT_READY"


def test_thieu_du_lieu_quan_thi_chi_tiet_mon_tra_503(client_khong_co_quan):
    res = client_khong_co_quan.get(f"{API}/dishes/pho-bo")
    assert res.status_code == 503, res.text

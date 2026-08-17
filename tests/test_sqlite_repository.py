"""Test `SqliteRestaurantRepository`.

Toàn bộ test ở đây dựng CSDL TẠM trong thư mục tmp - không đụng tới dataset thật, nên
chạy được kể cả khi chưa chạy data_pipeline.

Trọng tâm là các quy ước dữ liệu ở CLAUDE.md mục 4, vì đây đúng là chỗ dễ làm sai khi
đổi kho lưu trữ:
  - NULL phải thành `None`, KHÔNG thành 0
  - `price` phải giữ nguyên CHUỖI
  - thiếu file CSDL KHÔNG được làm sập app
"""
from __future__ import annotations

import json
import sqlite3

import pytest

from src.infrastructure.repositories.sqlite_restaurant_repository import (
    SCHEMA,
    SqliteRestaurantRepository,
)

_INSERT = """
INSERT INTO restaurants (
    place_id, name, category, lat, lng, address, cuisine, price, rating,
    reviews_count, mood_scores, atmosphere_tags, review_text, opening_hours,
    is_active, district, dietary, amenities, phone, website, source,
    data_confidence, experience_cluster_id, experience_cluster_label
) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""

_DEFAULTS = {
    "place_id": "id-1", "name": "Quán A", "category": "Nhà hàng",
    "lat": 21.03, "lng": 105.85, "address": None, "cuisine": None,
    "price": None, "rating": None, "reviews_count": None,
    "mood_scores": None, "atmosphere_tags": None, "review_text": None,
    "opening_hours": None, "is_active": 1, "district": None, "dietary": None,
    "amenities": None, "phone": None, "website": None, "source": None,
    "data_confidence": None, "experience_cluster_id": None,
    "experience_cluster_label": None,
}
_ORDER = list(_DEFAULTS)


def make_db(tmp_path, *rows: dict):
    """Dựng CSDL tạm với các dòng cho trước. Trường không khai lấy theo `_DEFAULTS`."""
    db_path = tmp_path / "test.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.executemany(
            _INSERT,
            [tuple({**_DEFAULTS, **row}[c] for c in _ORDER) for row in rows],
        )
        conn.commit()
    return db_path


# --------------------------------------------------------------------------
# Quy ước dữ liệu - CLAUDE.md mục 4
# --------------------------------------------------------------------------


def test_NULL_giu_nguyen_None_khong_bien_thanh_0(tmp_path):
    """3793/4938 quán chưa có rating. Biến None thành 0 là nói dối người dùng "0 sao"."""
    db = make_db(tmp_path, {"rating": None, "reviews_count": None})

    quan = SqliteRestaurantRepository(db).list_all()[0]

    assert quan.rating is None
    assert quan.rating != 0
    assert quan.reviews_count is None


def test_price_giu_nguyen_CHUOI(tmp_path):
    """Giá thật là chuỗi khoảng giá. Ép về float từng là bug có thật."""
    db = make_db(tmp_path, {"price": "1-100.000 ₫"})

    quan = SqliteRestaurantRepository(db).list_all()[0]

    assert quan.price == "1-100.000 ₫"
    assert isinstance(quan.price, str)


def test_cum_chua_phan_la_None_khong_phai_0(tmp_path):
    """Cold Start: quán chưa phân cụm ≠ quán dở (rules/rules.md mục 3.3)."""
    db = make_db(tmp_path, {"experience_cluster_id": None})

    quan = SqliteRestaurantRepository(db).list_all()[0]

    assert quan.experience_cluster_id is None


# --------------------------------------------------------------------------
# Soft-delete - thứ mà bản CSV không lưu được
# --------------------------------------------------------------------------


def test_quan_bi_an_khong_bao_gio_tra_ve(tmp_path):
    db = make_db(
        tmp_path,
        {"place_id": "hien", "name": "Hiện", "is_active": 1},
        {"place_id": "an", "name": "Ẩn", "is_active": 0},
    )
    repo = SqliteRestaurantRepository(db)

    ten = [r.name for r in repo.list_all()]

    assert ten == ["Hiện"]
    assert repo.get_by_place_id("an") is None
    assert repo.get_by_place_id("hien") is not None


def test_reload_thay_duoc_thay_doi_moi(tmp_path):
    """Admin ghi xong PHẢI gọi reload(), nếu không người dùng vẫn thấy dữ liệu cũ."""
    db = make_db(tmp_path, {"place_id": "x", "name": "Trước"})
    repo = SqliteRestaurantRepository(db)
    assert repo.list_all()[0].name == "Trước"

    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE restaurants SET name = 'Sau' WHERE place_id = 'x'")
        conn.commit()

    assert repo.list_all()[0].name == "Trước", "bộ nhớ đệm phải giữ nguyên tới khi reload"
    repo.reload()
    assert repo.list_all()[0].name == "Sau"


# --------------------------------------------------------------------------
# Suy biến an toàn - thiếu/hỏng dữ liệu KHÔNG được làm sập app
# --------------------------------------------------------------------------


def test_thieu_file_khong_lam_sap_app(tmp_path):
    """CLAUDE.md mục 4 quy tắc 3: báo lỗi kèm CÁCH KHẮC PHỤC, không ném exception."""
    repo = SqliteRestaurantRepository(tmp_path / "chua-co.db")

    assert repo.is_ready is False
    assert repo.list_all() == []
    assert repo.get_by_place_id("bat-ky") is None
    assert "build_sqlite.py" in repo.load_error, "phải nói rõ lệnh cần chạy"


def test_thieu_file_thi_KHONG_tao_file_rong(tmp_path):
    """`sqlite3.connect` mặc định TẠO file mới nếu chưa có - sẽ biến "sai đường dẫn"
    thành "0 quán" mà không báo gì. Repo phải mở ở chế độ chỉ đọc."""
    missing = tmp_path / "chua-co.db"
    SqliteRestaurantRepository(missing)

    assert not missing.exists()


def test_json_hong_tra_rong_khong_lam_hong_ca_luot_nap(tmp_path):
    db = make_db(tmp_path, {"dietary": "{khong-phai-json", "amenities": "[]"})

    quan = SqliteRestaurantRepository(db).list_all()[0]

    assert quan.dietary == []
    assert quan.amenities == []


def test_thieu_toa_do_thi_bo_qua_quan_do(tmp_path):
    """Quán thiếu toạ độ không xếp hạng/hiển thị được -> bỏ qua, giống bản CSV."""
    db = make_db(tmp_path, {"place_id": "tot", "name": "Tốt"})
    # lat NOT NULL trong lược đồ, nên phải chèn thẳng bằng SQL để mô phỏng dữ liệu hỏng.
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO restaurants (place_id, name, lat, lng, is_active) "
            "VALUES ('hong', 'Hỏng', 999, 105.85, 1)"  # lat ngoài [-90, 90]
        )
        conn.commit()

    ten = [r.name for r in SqliteRestaurantRepository(db).list_all()]

    assert ten == ["Tốt"]


def test_quan_khong_co_place_id_van_nam_trong_list_all(tmp_path):
    """Quán từ OpenStreetMap không có placeId của Google. Dùng place_id làm khoá chính
    sẽ lặng lẽ đánh rơi nhóm này - đó là lý do lược đồ để UNIQUE chứ không PRIMARY KEY."""
    db = make_db(
        tmp_path,
        {"place_id": None, "name": "Quán OSM"},
        {"place_id": "co-id", "name": "Quán Google"},
    )

    quan = SqliteRestaurantRepository(db).list_all()

    assert {r.name for r in quan} == {"Quán OSM", "Quán Google"}


# --------------------------------------------------------------------------
# Tương thích port - đổi adapter không được làm /health đổi hình dạng
# --------------------------------------------------------------------------


def test_status_cung_hinh_dang_voi_ban_CSV(tmp_path):
    db = make_db(tmp_path, {})

    status = SqliteRestaurantRepository(db).status()

    assert set(status) == {"ready", "source", "count", "error"}
    assert status["ready"] is True
    assert status["count"] == 1
    assert status["error"] is None


def test_thoa_man_port_RestaurantRepository(tmp_path):
    from src.application.ports.restaurant_repository import RestaurantRepository

    repo = SqliteRestaurantRepository(make_db(tmp_path, {}))

    assert isinstance(repo, RestaurantRepository)


def test_mood_scores_du_cot_va_thieu_thi_bang_0(tmp_path):
    from src.domain.value_objects.mood import MOOD_SCORE_COLUMNS

    cot_dau = MOOD_SCORE_COLUMNS[0]
    db = make_db(tmp_path, {"mood_scores": json.dumps({cot_dau: 0.75})})

    quan = SqliteRestaurantRepository(db).list_all()[0]

    assert quan.mood_score(cot_dau) == pytest.approx(0.75)
    for col in MOOD_SCORE_COLUMNS[1:]:
        assert quan.mood_score(col) == 0.0, "thiếu cột phải là 0.0 trung lập"


# ==========================================================================
# CHỐT CHẶN: `build_sqlite.py` KHÔNG được ghi đè lên kho tài khoản
# ==========================================================================
#
# VÌ SAO CÓ NHÓM TEST NÀY: hai file .db nằm CÙNG thư mục và chỉ khác tên. Kho quán dựng
# lại được từ CSV; kho tài khoản thì mất là mất hẳn. Script dựng CSDL chạy
# `DELETE FROM restaurants` rồi ghi lại — gõ nhầm `--out` một lần là xong đời tài khoản.


def _refuse(path):
    from scripts.build_sqlite import _refuse_if_user_database

    return _refuse_if_user_database(path)


def test_tu_choi_ghi_de_len_file_co_bang_users(tmp_path):
    """Nhận diện theo NỘI DUNG file, nên đổi tên file vẫn được bảo vệ."""
    from src.infrastructure.repositories.sqlite_user_repository import (
        SqliteUserRepository,
    )

    db = tmp_path / "ten-gi-do-khong-goi-nho.db"
    SqliteUserRepository(db)   # tạo bảng `users`

    assert _refuse(db) is not None


def test_tu_choi_ghi_de_len_duong_dan_MOODBITE_USERS_DB(tmp_path, monkeypatch):
    """Chặn cả khi file CHƯA tồn tại — lần chạy đầu tiên cũng phải được bảo vệ."""
    chua_ton_tai = tmp_path / "users.db"
    monkeypatch.setenv("MOODBITE_USERS_DB", str(chua_ton_tai))

    assert _refuse(chua_ton_tai) is not None


def test_cho_qua_kho_quan_binh_thuong(tmp_path):
    """Chốt chặn không được chặn nhầm việc dựng lại kho quán - đó là việc hằng ngày."""
    assert _refuse(make_db(tmp_path, {})) is None
    assert _refuse(tmp_path / "chua-co-file-nao.db") is None

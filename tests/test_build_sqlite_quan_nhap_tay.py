"""Quán admin NHẬP TAY không được mất khi dựng lại CSDL (rà soát 2026-11-08).

Lỗi thật: endpoint `POST /admin/restaurants` đã chạy, nhưng `build_sqlite.py` vẫn
`DELETE FROM restaurants` rồi chỉ ghi lại CSV. Quán vừa nhập biến mất ở lần dựng lại kế tiếp.
"""
import sqlite3

from scripts.build_sqlite import (
    _doc_quan_thu_cong,
    _ghi_lai_quan_thu_cong,
)
from src.infrastructure.repositories.sqlite_restaurant_repository import SCHEMA


def _dung_csdl(path, *rows):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    for place_id, name, is_active in rows:
        conn.execute(
            "INSERT INTO restaurants (place_id, name, lat, lng, is_active, source) "
            "VALUES (?, ?, 21.03, 105.85, ?, ?)",
            (place_id, name, is_active, "manual" if place_id.startswith("manual:") else "osm"),
        )
    conn.commit()
    conn.close()


def test_doc_quan_thu_cong_chi_lay_quan_co_tien_to_manual(tmp_path):
    db = tmp_path / "quan.db"
    _dung_csdl(db,
               ("manual:quan-moi-abc12345", "Quán Tôi Nhập", 1),
               ("osm-123", "Quán Từ CSV", 1))

    rows = _doc_quan_thu_cong(db)

    assert [r["place_id"] for r in rows] == ["manual:quan-moi-abc12345"]
    assert rows[0]["name"] == "Quán Tôi Nhập"


def test_dung_lai_csdl_giu_quan_nhap_tay_va_trang_thai_an(tmp_path):
    db = tmp_path / "quan.db"
    _dung_csdl(db, ("manual:quan-an-deadbeef", "Quán Đã Ẩn", 0))
    quan_cu = _doc_quan_thu_cong(db)

    # Mô phỏng đúng bước dựng lại: xoá sạch rồi ghi lại (CSV không có quán này).
    conn = sqlite3.connect(db)
    conn.execute("DELETE FROM restaurants")
    assert _ghi_lai_quan_thu_cong(conn, quan_cu) == 1
    conn.commit()
    row = conn.execute(
        "SELECT name, is_active, source FROM restaurants WHERE place_id = ?",
        ("manual:quan-an-deadbeef",),
    ).fetchone()
    conn.close()

    assert row == ("Quán Đã Ẩn", 0, "manual"), "quán nhập tay phải còn, và vẫn đang ẩn"


def test_lược_đồ_cũ_thiếu_cột_van_giu_duoc_quan_nhap_tay(tmp_path):
    """Bản CSDL cũ thiếu cột mới: build_sqlite DROP bảng rồi dựng lại. Quán nhập tay phải
    sống sót qua đường này, không chỉ qua đường DELETE."""
    db = tmp_path / "cu.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE restaurants (place_id TEXT, name TEXT, lat REAL, lng REAL, is_active INTEGER)"
    )
    conn.execute(
        "INSERT INTO restaurants VALUES ('manual:quan-cu-11112222', 'Quán Cũ Lược Đồ', 21.0, 105.8, 1)"
    )
    conn.commit()
    conn.close()

    quan_cu = _doc_quan_thu_cong(db)
    conn = sqlite3.connect(db)
    conn.execute("DROP TABLE restaurants")
    conn.executescript(SCHEMA)
    _ghi_lai_quan_thu_cong(conn, quan_cu)
    conn.commit()
    row = conn.execute(
        "SELECT name, is_active FROM restaurants WHERE place_id = ?",
        ("manual:quan-cu-11112222",),
    ).fetchone()
    conn.close()

    assert row == ("Quán Cũ Lược Đồ", 1)


def test_chua_co_csdl_thi_khong_co_gi_de_giu(tmp_path):
    assert _doc_quan_thu_cong(tmp_path / "khong_co.db") == []

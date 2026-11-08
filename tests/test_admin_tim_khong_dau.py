"""Ô tìm quán của QUẢN TRỊ phải khớp không phân biệt dấu và HOA/THƯỜNG.

BUG THẬT 2026-11-08 (đo trên CSDL thật, 52.871 quán): "Phở Thìn" ra 21 quán, nhưng
"PHỞ THÌN" chỉ ra 2 và "pho thin" ra 5. Nguyên nhân: SQLite `LIKE` chỉ bỏ hoa/thường với chữ
ASCII, nên chữ có dấu viết hoa không khớp chữ thường. Admin không thể kiểm "quán này đã có
trong CSDL chưa" nếu gõ khác dấu với dữ liệu.

Sửa bằng hàm `normalize` của domain đăng ký lên kết nối đọc; test này khoá đúng hành vi đó.
"""
from __future__ import annotations

from src.application.ports.admin_restaurant_repository import AdminRestaurantFilter
from src.infrastructure.repositories.sqlite_restaurant_repository import (
    SqliteRestaurantRepository,
)
from tests.test_sqlite_repository import make_db


def _ten(db_path, q):
    """Tên các quán khớp `q`, sắp xếp để so sánh tất định."""
    repo = SqliteRestaurantRepository(db_path)
    kq, _tong = repo.page_for_admin(AdminRestaurantFilter(query=q), offset=0, limit=50)
    return (sorted(r.name for r in kq),)


def test_tim_khong_phan_biet_hoa_thuong_va_dau(tmp_path):
    db = make_db(
        tmp_path,
        {"place_id": "a", "name": "Phở Thìn Lò Đúc"},
        {"place_id": "b", "name": "Quán Bún Chả"},
        {"place_id": "c", "name": "Phố Cổ Cafe"},
    )
    ket_qua = {q: _ten(db, q)[0] for q in ["Phở Thìn", "PHỞ THÌN", "pho thin", "phở thìn"]}
    for q, names in ket_qua.items():
        assert names == ["Phở Thìn Lò Đúc"], f"gõ {q!r} phải ra đúng 1 quán, ra {names}"


def test_tim_khong_dau_khop_quan_co_dau(tmp_path):
    db = make_db(tmp_path, {"place_id": "a", "name": "Bún Chả Đắc Kim"})
    assert _ten(db, "bun cha dac kim")[0] == ["Bún Chả Đắc Kim"]
    assert _ten(db, "dac kim")[0] == ["Bún Chả Đắc Kim"]


def test_tim_theo_dia_chi_cung_bo_dau(tmp_path):
    db = make_db(
        tmp_path,
        {"place_id": "a", "name": "Quán X", "address": "Phố Hàng Bông, Hoàn Kiếm"},
    )
    assert _ten(db, "hang bong")[0] == ["Quán X"]

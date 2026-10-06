"""`SqliteRestaurantRepository.reload()` phải ĐỔI DỮ LIỆU TRONG MỘT NHÁT.

BUG THẬT (rà soát 2026-10-06): `reload()` gán `_restaurants = None`, `_by_place_id = {}`
rồi mới nạp lại; cuối cùng gán `_restaurants` và `_by_place_id` bằng HAI câu lệnh riêng.
Request đồng thời rơi vào khe giữa hai câu đó nhận `get_by_place_id() -> None` -> 404 cho
một quán đang tồn tại. Rơi vào khe đầu thì request đó tự nạp lại TOÀN BỘ CSDL lần nữa
(~2 giây trên 52.871 quán) — admin bấm "ẩn" một lần mà máy chủ nạp dữ liệu hai lần.

Cách sửa: dựng ảnh chụp mới ở biến cục bộ rồi gán MỘT thuộc tính duy nhất.
"""
from __future__ import annotations

import threading

from src.infrastructure.repositories.sqlite_restaurant_repository import (
    SqliteRestaurantRepository,
)
from tests.test_sqlite_repository import make_db


def test_trong_luc_reload_nguoi_doc_van_thay_du_lieu_cu_va_KHONG_nap_lai(tmp_path, monkeypatch):
    db = make_db(tmp_path, {"place_id": "p1", "name": "Quán A"})
    repo = SqliteRestaurantRepository(db)

    dang_nap = threading.Event()
    cho_phep_xong = threading.Event()
    luong_reload: dict = {}
    nap_tu_luong_doc = {"n": 0}
    goc = SqliteRestaurantRepository._to_entity

    def cham(row):
        if threading.get_ident() == luong_reload.get("id"):
            dang_nap.set()
            cho_phep_xong.wait(5)
        else:
            nap_tu_luong_doc["n"] += 1
        return goc(row)

    monkeypatch.setattr(SqliteRestaurantRepository, "_to_entity", staticmethod(cham))

    def chay_reload():
        luong_reload["id"] = threading.get_ident()
        repo.reload()

    t = threading.Thread(target=chay_reload)
    t.start()
    try:
        assert dang_nap.wait(5), "reload không chạy tới bước dựng dữ liệu"
        # Reload đang dở dang: người đọc phải thấy ẢNH CHỤP CŨ, trọn vẹn.
        assert repo.get_by_place_id("p1") is not None
        assert [r.place_id for r in repo.list_all()] == ["p1"]
        assert repo.is_ready is True
        # ...và KHÔNG tự đi nạp lại CSDL lần thứ hai.
        assert nap_tu_luong_doc["n"] == 0
    finally:
        cho_phep_xong.set()
        t.join(5)


def test_moi_lan_ghi_thanh_cong_tang_phien_ban_du_lieu(tmp_path):
    """Phiên bản dữ liệu là thứ chỉ mục món-quán dùng để biết khi nào phải dựng lại."""
    db = make_db(tmp_path, {"place_id": "p1", "name": "Quán A"})
    repo = SqliteRestaurantRepository(db)
    v0 = repo.data_version

    assert repo.set_active("p1", False) is True
    v1 = repo.data_version
    assert v1 > v0

    # Ghi không đổi dòng nào -> không nạp lại -> phiên bản giữ nguyên.
    assert repo.set_active("khong-co", False) is False
    assert repo.data_version == v1


def test_reload_bao_cho_nguoi_dang_ky(tmp_path):
    db = make_db(tmp_path, {"place_id": "p1", "name": "Quán A"})
    repo = SqliteRestaurantRepository(db)
    da_bao: list = []
    repo.add_reload_listener(lambda: da_bao.append(repo.data_version))

    repo.update_fields("p1", {"name": "Quán B"})

    assert da_bao == [repo.data_version]
    assert repo.get_by_place_id("p1").name == "Quán B"

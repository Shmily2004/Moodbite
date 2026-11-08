"""Quản trị viên sửa mô tả món: bản sửa nằm riêng, đọc chồng lên danh mục gốc.

Bốn tầng được khoá, mỗi tầng một nhóm test:
  1. domain  : quy tắc độ dài + "chuỗi rỗng = gỡ bản sửa"
  2. adapter : bảng `dish_overrides` ghi/đọc/gỡ đúng
  3. overlay : danh mục gốc KHÔNG bị đổi; bản sửa chỉ hiện khi có
  4. API     : PATCH cần đăng nhập, sai trả 400/404, sửa xong GET thấy ngay, có nhật ký

Lý do cần: `dish_catalog.json` do `build_dish_catalog.py` sinh ra và ghi đè mỗi lần chạy, nên
sửa thẳng vào file đó thì chữ người quản trị nhập sẽ mất sau lần dựng lại kế tiếp.
"""
from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

from src.domain.entities.dish import Dish
from src.domain.errors import DomainValidationError
from src.domain.value_objects.dish_description import DESCRIPTION_MAX_LENGTH, chuan_hoa_mo_ta
from src.infrastructure.repositories.overlay_dish_catalog_repository import (
    OverlayDishCatalogRepository,
)
from src.infrastructure.repositories.sqlite_dish_override_repository import (
    SqliteDishOverrideRepository,
)
from tests.fakes import FakeDishCatalog
from tests.test_admin_api import API, build_client, token_of
from tests.test_sqlite_repository import make_db

GOC = "Phở bò là món nước truyền thống."


def _mon(ten="Phở bò", mo_ta=GOC, dish_id="pho-bo"):
    return Dish(name=ten, dish_id=dish_id, description=mo_ta, is_active=True)


# ---------------------------------------------------------------------------
# 1. DOMAIN
# ---------------------------------------------------------------------------


def test_chuan_hoa_cat_khoang_trang_va_giu_chu():
    assert chuan_hoa_mo_ta("  Phở bò nước dùng trong  ") == "Phở bò nước dùng trong"


@pytest.mark.parametrize("rong", [None, "", "   \n\t  "])
def test_rong_hoac_none_nghia_la_go_ban_sua(rong):
    assert chuan_hoa_mo_ta(rong) is None


def test_qua_dai_bi_tu_choi_truoc_khi_ghi():
    with pytest.raises(DomainValidationError):
        chuan_hoa_mo_ta("a" * (DESCRIPTION_MAX_LENGTH + 1))


def test_dung_dung_gioi_han_van_nhan():
    assert chuan_hoa_mo_ta("a" * DESCRIPTION_MAX_LENGTH) == "a" * DESCRIPTION_MAX_LENGTH


# ---------------------------------------------------------------------------
# 2. ADAPTER
# ---------------------------------------------------------------------------


def test_ghi_doc_go_trong_csdl_that(tmp_path):
    kho = SqliteDishOverrideRepository(tmp_path / "users.db")
    assert kho.get_description("pho-bo") is None

    kho.set_description("pho-bo", "Bản sửa 1", actor="admin")
    kho.set_description("pho-bo", "Bản sửa 2", actor="admin")  # ghi đè, không nhân đôi
    assert kho.get_description("pho-bo") == "Bản sửa 2"
    assert kho.all_descriptions() == {"pho-bo": "Bản sửa 2"}

    kho.clear_description("pho-bo")
    assert kho.get_description("pho-bo") is None
    kho.clear_description("khong-co")  # gỡ món chưa sửa: không lỗi


# ---------------------------------------------------------------------------
# 3. OVERLAY — danh mục gốc không bị đổi
# ---------------------------------------------------------------------------


def test_overlay_doc_chong_ban_sua_nhung_goc_van_nguyen(tmp_path):
    goc = FakeDishCatalog([_mon(), _mon("Bún chả", "Bún chả Hà Nội.", "bun-cha")])
    kho = SqliteDishOverrideRepository(tmp_path / "users.db")
    kho.set_description("pho-bo", "Bản sửa tay.", actor="admin")
    lop = OverlayDishCatalogRepository(goc, kho)

    mo_ta = {d.identifier: d.description for d in lop.list_all_dishes()}
    assert mo_ta == {"pho-bo": "Bản sửa tay.", "bun-cha": "Bún chả Hà Nội."}
    assert lop.get_dish("pho-bo").description == "Bản sửa tay."
    assert lop.get_dish("bun-cha").description == "Bún chả Hà Nội."

    # Danh mục gốc KHÔNG bị đụng tới: đây là điều làm cho việc dựng lại file an toàn.
    assert goc.get_dish("pho-bo").description == GOC


def test_overlay_go_ban_sua_thi_tra_ve_mo_ta_goc(tmp_path):
    goc = FakeDishCatalog([_mon()])
    kho = SqliteDishOverrideRepository(tmp_path / "users.db")
    lop = OverlayDishCatalogRepository(goc, kho)
    kho.set_description("pho-bo", "Tạm thời", actor="admin")
    assert lop.get_dish("pho-bo").description == "Tạm thời"
    kho.clear_description("pho-bo")
    assert lop.get_dish("pho-bo").description == GOC


def test_overlay_giu_nguyen_cac_truong_khac(tmp_path):
    mon = _mon()
    goc = FakeDishCatalog([replace(mon, cuisine="Việt Nam", is_active=False)])
    kho = SqliteDishOverrideRepository(tmp_path / "users.db")
    kho.set_description("pho-bo", "Sửa", actor="admin")
    sua = OverlayDishCatalogRepository(goc, kho).get_dish("pho-bo")
    assert sua.cuisine == "Việt Nam" and sua.is_active is False  # chỉ đổi mô tả


# ---------------------------------------------------------------------------
# 4. API
# ---------------------------------------------------------------------------


@pytest.fixture
def api(tmp_path):
    db = make_db(tmp_path, {"place_id": "pho-1", "name": "Phở Bò Hàng Đồng", "is_active": 1})
    client, _ = build_client(db, dishes=[_mon()])
    return client


def _sua(client, dish_id, payload):
    headers = {"Authorization": f"Bearer {token_of(client)}"}
    return client.patch(f"{API}/admin/dishes/{dish_id}", json=payload, headers=headers)


def test_patch_khong_dang_nhap_bi_tu_choi(api):
    res = api.patch(f"{API}/admin/dishes/pho-bo", json={"description": "x"})
    assert res.status_code == 401


def test_sua_xong_chi_tiet_hien_ban_moi_va_danh_dau_da_sua(api):
    res = _sua(api, "pho-bo", {"description": "  Mô tả mới của quản trị viên.  "})
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["description"] == "Mô tả mới của quản trị viên."
    assert data["mo_ta_da_sua"] is True

    lai = api.get(
        f"{API}/admin/dishes/pho-bo",
        headers={"Authorization": f"Bearer {token_of(api)}"},
    )
    assert lai.json()["data"]["description"] == "Mô tả mới của quản trị viên."


def test_gui_null_thi_go_ban_sua_ve_mo_ta_goc(api):
    _sua(api, "pho-bo", {"description": "Tạm"})
    data = _sua(api, "pho-bo", {"description": None}).json()["data"]
    assert data["description"] == GOC
    assert data["mo_ta_da_sua"] is False


def test_chuoi_rong_cung_la_go(api):
    _sua(api, "pho-bo", {"description": "Tạm"})
    assert _sua(api, "pho-bo", {"description": "   "}).json()["data"]["description"] == GOC


def test_mon_khong_ton_tai_tra_404(api):
    res = _sua(api, "khong-co-mon", {"description": "x"})
    assert res.status_code == 404


def test_qua_dai_tra_400_va_KHONG_ghi_gi(api):
    res = _sua(api, "pho-bo", {"description": "a" * (DESCRIPTION_MAX_LENGTH + 1)})
    assert res.status_code == 400
    # Lỗi nhập không được để lại bản sửa dở dang.
    assert _sua(api, "pho-bo", {"description": None}).json()["data"]["mo_ta_da_sua"] is False


def test_moi_lan_sua_deu_vao_nhat_ky(api, tmp_path):
    _sua(api, "pho-bo", {"description": "Lần 1"})
    _sua(api, "pho-bo", {"description": None})
    with sqlite3.connect(tmp_path / "audit.db") as conn:
        rows = conn.execute(
            "SELECT action, target_type, target_id, summary FROM audit_log "
            "WHERE action = 'update_dish' ORDER BY id"
        ).fetchall()
    assert [r[0:3] for r in rows] == [("update_dish", "dish", "pho-bo")] * 2
    assert "sửa mô tả" in rows[0][3]
    assert "gỡ bản sửa" in rows[1][3]

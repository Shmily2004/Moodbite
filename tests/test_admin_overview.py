"""Màn "Tổng quan" của trang quản trị — `GET /admin/overview`.

Dựng theo `frontend/design/Dashboard admin.png` (chủ dự án gửi 2026-08-26).

Thứ đáng khoá ở đây KHÔNG phải "gọi được ra JSON", mà là:

  1. **KHÔNG BỊA SỐ.** Bản thiết kế vẽ sẵn "+1.248 so với tuần trước", "CTR 8.7%",
     "Lượt gợi ý hôm nay 1.306". Dự án không lưu ảnh chụp theo ngày và không ghi nhật ký
     tìm kiếm → những trường đó KHÔNG được phép xuất hiện trong response.
  2. Đếm món phải là TOÀN BỘ danh mục, kể cả món chưa có quán — nếu không, người quản trị
     nhìn thấy 298 và tưởng mất 557 món.
  3. Cần token admin. Đây là dữ liệu vận hành, không phải trang công khai.
  4. Độ phủ 0 mẫu phải ra 0%, KHÔNG phải 100%.
"""
from __future__ import annotations

import pytest

from src.domain.services.data_quality import (
    DoPhuTruong,
    do_phu_quan,
    thong_ke_nguon,
    viec_can_xu_ly,
)
from tests.test_admin_api import API, auth_header, build_client, db  # noqa: F401


# ==========================================================================
# Tầng domain — quy tắc đếm
# ==========================================================================


class _Quan:
    """Quán tối giản, chỉ có đúng những trường phép đếm cần."""

    def __init__(self, **kw):
        self.address = kw.get("address")
        self.district = kw.get("district")
        self.category = kw.get("category")
        self.phone = kw.get("phone")
        self.website = kw.get("website")
        self.source = kw.get("source")
        self.is_active = kw.get("is_active", True)
        self.temporarily_closed = kw.get("temporarily_closed")


class _Mon:
    def __init__(self, **kw):
        self.description = kw.get("description")
        self.image_url = kw.get("image_url")
        self.is_active = kw.get("is_active", True)


def test_do_phu_khong_mau_thi_la_0_phan_tram_chu_khong_phai_100():
    """"Không thiếu gì" và "không có gì" là hai chuyện khác hẳn nhau."""
    assert DoPhuTruong(khoa="x", nhan="x", mo_ta="", so_co=0, tong=0).phan_tram == 0.0


def test_chuoi_rong_tinh_la_CHUA_CO():
    """Nguồn dữ liệu hay trả `""` thay vì bỏ trống — coi là "có" sẽ thổi phồng độ phủ."""
    quan = [
        _Quan(address="12 Lê Duẩn", district="Hoàn Kiếm", category="Quán ăn", phone="0123"),
        _Quan(address="   ", district="Ba Đình", category="Cà phê", phone=""),
    ]

    do_phu = {x.khoa: x for x in do_phu_quan(quan)}

    assert do_phu["co_ban"].so_co == 1, "Địa chỉ toàn khoảng trắng vẫn bị tính là có"
    assert do_phu["phone"].so_co == 1


def test_du_thong_tin_co_ban_la_DU_CA_BA_khong_phai_trung_binh_cong():
    """Một quán thiếu địa chỉ thì không dùng được, dù có đủ hai trường kia."""
    quan = [_Quan(address=None, district="Ba Đình", category="Quán ăn")]

    do_phu = {x.khoa: x for x in do_phu_quan(quan)}

    assert do_phu["co_ban"].so_co == 0


def test_muc_do_phu_chia_dung_ba_nhom():
    def muc(so_co, tong):
        return DoPhuTruong(khoa="x", nhan="x", mo_ta="", so_co=so_co, tong=tong).muc

    assert muc(90, 100) == "tot"           # >= 80
    assert muc(80, 100) == "tot"           # đúng ngưỡng
    assert muc(60, 100) == "trung_binh"    # >= 50
    assert muc(20, 100) == "kem"


def test_thong_ke_nguon_sap_theo_so_luong_giam_dan():
    quan = [_Quan(source="overture") for _ in range(3)]
    quan += [_Quan(source="openstreetmap")]
    quan += [_Quan(source=None)]

    nguon = thong_ke_nguon(quan)

    assert [x.nguon for x in nguon] == ["overture", "(không rõ nguồn)", "openstreetmap"]
    assert nguon[0].so_luong == 3 and nguon[0].phan_tram == 60.0


def test_can_xu_ly_giu_lai_ca_dong_bang_0():
    """"0 quán có khả năng đóng cửa" là câu trả lời có ích, khác với dòng biến mất."""
    viec = viec_can_xu_ly([_Quan(phone="0123")], [_Mon(description="x", image_url="x")])

    assert all(v.so_luong == 0 for v in viec)
    assert len(viec) == 5, "Không được lọc bỏ dòng có số 0"


def test_thieu_lien_he_la_thieu_CA_HAI():
    """Có website mà không có điện thoại thì vẫn liên hệ được — không tính là thiếu."""
    quan = [
        _Quan(website="https://a.vn"),      # còn liên hệ được
        _Quan(),                            # không có gì
    ]

    viec = {v.khoa: v for v in viec_can_xu_ly(quan, [])}

    assert viec["thieu_lien_he"].so_luong == 1


def test_mon_chua_co_quan_la_THONG_TIN_khong_phai_canh_bao():
    """Phần lớn là món quốc tế chưa quán nào ở Hà Nội bán — sự thật thị trường, không
    phải lỗi dữ liệu phải đi sửa. Xếp vào cảnh báo sẽ tạo ra 557 "việc" không làm được."""
    viec = {v.khoa: v for v in viec_can_xu_ly([], [_Mon(is_active=False)])}

    assert viec["mon_khong_quan"].muc_do == "thong_tin"
    assert viec["mon_khong_quan"].so_luong == 1


# ==========================================================================
# Tầng HTTP
# ==========================================================================


@pytest.fixture
def client(db):  # `db` là fixture của `test_admin_api` — dùng lại bộ dữ liệu 2 quán.
    c, _ = build_client(db)
    return c


def test_chua_dang_nhap_thi_401(client):
    """Đây là dữ liệu vận hành, không phải trang công khai."""
    assert client.get(f"{API}/admin/overview").status_code == 401


def test_tra_ve_du_cac_khoi_cua_ban_thiet_ke(client):
    res = client.get(f"{API}/admin/overview", headers=auth_header(client))

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    for khoa in (
        "restaurants_total",
        "dishes_total",
        "dishes_with_restaurants",
        "dishes_without_restaurants",
        "data_quality",
        "by_source",
        "needs_attention",
        "needs_attention_total",
        "generated_at",
    ):
        assert khoa in data, f"Thiếu khối '{khoa}' của bản thiết kế"


def test_KHONG_tra_ve_nhung_con_so_KHONG_CO_NGUON(client):
    """Chốt chặn quan trọng nhất của file này.

    `Dashboard admin.png` vẽ sẵn "+1.248 so với tuần trước", "CTR 8.7%", "Lượt gợi ý hôm
    nay", sparkline theo ngày. Dự án KHÔNG lưu ảnh chụp dữ liệu theo ngày và KHÔNG ghi
    nhật ký lượt tìm kiếm — không có cách nào tính được. Thà thiếu còn hơn bịa
    (CLAUDE.md mục 0 và mục 4).

    Test này đỏ nghĩa là ai đó vừa thêm một con số không có thật để cho khớp bản vẽ.
    """
    data = client.get(f"{API}/admin/overview", headers=auth_header(client)).json()["data"]

    cam = [
        "ctr", "click_rate", "trend", "change", "delta",
        "vs_last_week", "vs_yesterday", "sparkline", "history",
        "suggestions_today", "revenue",
    ]
    khoa_co = {k.lower() for k in data}
    dinh = [c for c in cam if any(c in k for k in khoa_co)]
    assert not dinh, f"Đang trả về số KHÔNG CÓ NGUỒN: {dinh}"


def test_dem_mon_la_TOAN_BO_danh_muc_ke_ca_mon_chua_co_quan(client):
    """Chỉ đếm món đang bật thì người quản trị tưởng danh mục bị mất gần 2/3."""
    data = client.get(f"{API}/admin/overview", headers=auth_header(client)).json()["data"]

    assert (
        data["dishes_total"]
        == data["dishes_with_restaurants"] + data["dishes_without_restaurants"]
    )


def test_moi_do_phu_deu_co_muc_de_giao_dien_to_mau(client):
    data = client.get(f"{API}/admin/overview", headers=auth_header(client)).json()["data"]

    assert data["data_quality"], "Không có dòng độ phủ nào"
    for x in data["data_quality"]:
        assert x["level"] in {"tot", "trung_binh", "kem"}
        assert 0 <= x["percent"] <= 100

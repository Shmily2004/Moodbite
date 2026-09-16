"""Test màn "CHẤT LƯỢNG DỮ LIỆU" và màn "CẦN XỬ LÝ" của trang quản trị.

Bản thiết kế: `frontend/design/quality data admin.png` · `needs to be handled admin.png`.

TRỌNG TÂM KHÔNG PHẢI "ĐƯỜNG ĐI ĐÚNG". Hai màn này toàn số, và cái sai nguy hiểm nhất
không phải là hỏng mà là **hiện một con số nghe hợp lý nhưng không có thật**. Vì vậy phần
lớn test dưới đây canh đúng chỗ đó:

  - chưa có mốc lịch sử  -> `delta` phải là `None`, KHÔNG phải 0
  - quán thiếu toạ độ    -> KHÔNG bị chấm là "ngoài Hà Nội"
  - hai chi nhánh cùng tên khác vị trí -> KHÔNG bị chấm là trùng lặp
  - đổi tab lọc          -> năm thẻ số ở đầu trang phải GIỮ NGUYÊN
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import List, Optional

import pytest

from src.domain.entities.issue_resolution import DanhDauXong
from src.domain.services.data_issues import (
    CAN_KIEM_TRA,
    NGHIEM_TRONG,
    QUAN_TRONG,
    ban_ghi_dinh_loi,
    dem_trung_lap,
    quan_ngoai_ha_noi,
    viec_can_xu_ly,
)
from src.domain.services.data_quality_history import (
    AnhChupChatLuong,
    chuoi_xu_huong,
    dem_theo_uu_tien,
    moc_gan_nhat_truoc,
    so_sanh,
)
from src.domain.value_objects.location import Location
from src.infrastructure.repositories.sqlite_issue_resolution_repository import (
    SqliteIssueResolutionRepository,
)
from src.infrastructure.repositories.sqlite_quality_snapshot_repository import (
    SqliteQualitySnapshotRepository,
)
from tests.test_admin_api import API, auth_header, build_client


# ==========================================================================
# DOMAIN — quy tắc thuần, không cần HTTP
# ==========================================================================


@dataclass
class _Quan:
    """Quán tối giản. Chỉ có đúng những trường các quy tắc dưới đây đọc tới."""

    name: str = "Phở Bò"
    location: Optional[Location] = None
    place_id: str = "q1"
    phone: Optional[str] = None
    website: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    thumbnail_url: Optional[str] = None
    source_updated_at: Optional[str] = None
    temporarily_closed: Optional[bool] = None


@dataclass
class _Mon:
    name: str = "Phở"
    dish_id: str = "pho"
    cuisine: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True


HOAN_KIEM = Location(lat=21.0285, lng=105.8542)


def test_quan_thieu_toa_do_KHONG_bi_cham_la_ngoai_ha_noi():
    """"Không biết ở đâu" khác "biết chắc ở tỉnh khác".

    Gộp hai thứ này lại sẽ đẩy người quản trị đi xoá nhầm hàng loạt quán chỉ vì nguồn
    dữ liệu chưa có toạ độ.
    """
    quan = [_Quan(location=None), _Quan(location=HOAN_KIEM)]

    assert quan_ngoai_ha_noi(quan) == []


def test_quan_o_tinh_khac_bi_cham_la_ngoai_ha_noi():
    # Đà Nẵng — nằm ngoài khung bao Hà Nội một cách rõ ràng.
    da_nang = _Quan(name="Mì Quảng", location=Location(lat=16.0544, lng=108.2022))

    ra_ngoai = quan_ngoai_ha_noi([da_nang, _Quan(location=HOAN_KIEM)])

    assert [q.name for q in ra_ngoai] == ["Mì Quảng"]


def test_hai_chi_nhanh_cung_ten_khac_vi_tri_KHONG_phai_trung_lap():
    """Chuỗi cà phê có hàng chục chi nhánh cùng tên — chấm trùng là xoá nhầm cả chuỗi."""
    quan = [
        _Quan(name="Highlands Coffee", location=Location(lat=21.0285, lng=105.8542)),
        # Cách ~1km, thừa xa so với ô lưới ~11m.
        _Quan(name="Highlands Coffee", location=Location(lat=21.0375, lng=105.8542)),
    ]

    assert dem_trung_lap(quan) == 0


def test_cung_ten_cung_vi_tri_thi_dem_BAN_THUA_chu_khong_dem_ca_nhom():
    """3 bản ghi của một quán = 1 quán thật + 2 bản cần gỡ. Con số đúng là 2."""
    quan = [_Quan(name="Phở Thìn", location=HOAN_KIEM, place_id=f"p{i}") for i in range(3)]

    assert dem_trung_lap(quan) == 2


def test_ten_co_dau_va_khong_dau_duoc_coi_la_MOT():
    """"Phở Bò" và "Pho Bo" là cùng một quán — đây là bug thật đã xảy ra của dự án."""
    quan = [
        _Quan(name="Phở Bò", location=HOAN_KIEM, place_id="a"),
        _Quan(name="Pho Bo", location=HOAN_KIEM, place_id="b"),
    ]

    assert dem_trung_lap(quan) == 1


def test_nhom_so_luong_0_van_duoc_giu_lai():
    """"0 quán đã đóng cửa" là câu trả lời có ích; dòng biến mất thì không.

    Người quản trị phải phân biệt được "đã kiểm, không có gì" với "chưa kiểm bao giờ".
    """
    khoa = {v.khoa for v in viec_can_xu_ly([], [])}

    assert khoa == {
        "dong_tam",
        "thieu_lien_he",
        "trung_lap",
        "mon_thieu_anh",
        "mon_thieu_mo_ta",
        "ngoai_ha_noi",
        "mon_khong_quan",
    }


def test_muc_uu_tien_dung_theo_ban_thiet_ke():
    viec = {v.khoa: v for v in viec_can_xu_ly([], [])}

    assert viec["dong_tam"].uu_tien == NGHIEM_TRONG
    assert viec["thieu_lien_he"].uu_tien == QUAN_TRONG
    assert viec["trung_lap"].uu_tien == QUAN_TRONG
    assert viec["mon_thieu_anh"].uu_tien == CAN_KIEM_TRA


def test_mon_chua_tim_duoc_quan_la_THONG_TIN_chu_khong_phai_loi():
    """Phần lớn là món quốc tế chưa quán nào ở Hà Nội bán — sự thật thị trường, không phải lỗi."""
    viec = {v.khoa: v for v in viec_can_xu_ly([], [_Mon(is_active=False)])}

    assert viec["mon_khong_quan"].muc_do == "thong_tin"
    assert viec["mon_khong_quan"].so_luong == 1


def test_vi_du_dinh_loi_tra_ve_ban_ghi_co_ten_that():
    quan = [_Quan(name="Bún Chả Hàng Mành", district="Hoàn Kiếm", temporarily_closed=True)]

    ban_ghi = ban_ghi_dinh_loi(quan, [], "dong_tam")

    assert len(ban_ghi) == 1
    assert ban_ghi[0].ten == "Bún Chả Hàng Mành"
    assert ban_ghi[0].mo_ta == "Hoàn Kiếm"


def test_khoa_la_tra_ve_rong_chu_khong_nem_loi():
    """Một khoá gõ sai không đáng làm trắng cả trang quản trị."""
    assert ban_ghi_dinh_loi([_Quan()], [_Mon()], "khoa-khong-ton-tai") == []


# ==========================================================================
# DOMAIN — lịch sử. Đây là chỗ dễ bịa số nhất.
# ==========================================================================


def test_chua_co_moc_thi_delta_la_None_KHONG_phai_0():
    """Ngày đầu bật tính năng chỉ có MỘT ảnh chụp — không có gì để so.

    "+0" nghe như đã so và không đổi; "None" nói đúng là chưa so được.
    """
    thay_doi = so_sanh(52_871, None, "tong_quan")

    assert thay_doi.chenh_lech is None
    assert thay_doi.co_so_sanh is False


def test_co_moc_du_cu_thi_tinh_duoc_chenh_lech():
    lich_su = [AnhChupChatLuong("2026-08-01", 52_800, 850, 88.0, 1, 2, 3)]

    moc = moc_gan_nhat_truoc(lich_su, date(2026, 9, 8), so_ngay=30)

    assert moc is not None
    assert so_sanh(52_871, moc, "tong_quan").chenh_lech == 71


def test_moc_chua_du_cu_thi_KHONG_duoc_dung_lam_mocaso():
    """Ảnh chụp hôm qua không phải "tháng trước". Dùng bừa sẽ ra một con số sai hẳn."""
    lich_su = [AnhChupChatLuong("2026-09-07", 52_800, 850, 88.0, 1, 2, 3)]

    assert moc_gan_nhat_truoc(lich_su, date(2026, 9, 8), so_ngay=30) is None


def test_xu_huong_KHONG_bu_ngay_trong_bang_so_0():
    """Bù 0 sẽ vẽ ra một cú sụt không có thật trong dữ liệu."""
    lich_su = [
        AnhChupChatLuong("2026-09-02", 10, 5, 90.0, 1, 1, 1),
        AnhChupChatLuong("2026-09-08", 12, 6, 91.0, 0, 1, 1),
    ]

    diem = chuoi_xu_huong(lich_su, date(2026, 9, 8), so_ngay=7)

    assert [d.ngay for d in diem] == ["2026-09-02", "2026-09-08"]


def test_xu_huong_bo_ngay_qua_cu():
    lich_su = [
        AnhChupChatLuong("2026-01-01", 1, 1, 1.0, 0, 0, 0),
        AnhChupChatLuong("2026-09-08", 2, 2, 2.0, 0, 0, 0),
    ]

    assert [d.ngay for d in chuoi_xu_huong(lich_su, date(2026, 9, 8), 7)] == ["2026-09-08"]


def test_dem_theo_uu_tien_luon_du_ba_khoa():
    """Thẻ số biến mất vì hôm nay không có lỗi loại đó sẽ làm bố cục nhảy."""
    dem = dem_theo_uu_tien([])

    assert set(dem) == {NGHIEM_TRONG, QUAN_TRONG, CAN_KIEM_TRA}
    assert all(v == 0 for v in dem.values())


# ==========================================================================
# INFRASTRUCTURE — hai kho SQLite
# ==========================================================================


def test_ghi_hai_lan_trong_cung_ngay_chi_con_MOT_dong(tmp_path):
    """Mở trang 50 lần trong ngày mà đẻ 50 điểm thì biểu đồ vẽ ra xu hướng không có thật."""
    kho = SqliteQualitySnapshotRepository(tmp_path / "q.db")

    kho.ghi(AnhChupChatLuong("2026-09-08", 10, 5, 90.0, 1, 1, 1))
    kho.ghi(AnhChupChatLuong("2026-09-08", 20, 6, 91.0, 0, 1, 1))

    dong = kho.doc_gan_day()
    assert len(dong) == 1
    assert dong[0].tong_quan == 20, "lần ghi sau phải ĐÈ lên lần trước"


def test_danh_dau_xong_go_ra_duoc(tmp_path):
    """Người ta bấm nhầm được — khác nhật ký hoạt động vốn chỉ ghi thêm."""
    kho = SqliteIssueResolutionRepository(tmp_path / "i.db")

    kho.danh_dau(DanhDauXong(khoa="dong_tam", target_id="q1", actor="admin"))
    assert kho.dem() == 1

    assert kho.bo_danh_dau("dong_tam", "q1") is True
    assert kho.dem() == 0


def test_cung_mot_quan_hai_loai_van_de_la_HAI_viec(tmp_path):
    """Xử lý xong "thiếu liên hệ" không có nghĩa đã xử lý "nghi đã đóng cửa"."""
    kho = SqliteIssueResolutionRepository(tmp_path / "i.db")

    kho.danh_dau(DanhDauXong(khoa="dong_tam", target_id="q1", actor="admin"))
    kho.danh_dau(DanhDauXong(khoa="thieu_lien_he", target_id="q1", actor="admin"))

    assert kho.dem() == 2


def test_dem_trong_ngay_chi_dem_dung_ngay_do(tmp_path):
    kho = SqliteIssueResolutionRepository(tmp_path / "i.db")
    hom_qua = datetime(2026, 9, 7, 10, 0, tzinfo=timezone.utc)

    kho.danh_dau(DanhDauXong("dong_tam", "q1", "admin", resolved_at=hom_qua))
    kho.danh_dau(DanhDauXong("dong_tam", "q2", "admin"))  # hôm nay

    assert kho.dem_trong_ngay("2026-09-07") == 1


# ==========================================================================
# API — gọi thật qua HTTP
# ==========================================================================


@pytest.fixture
def client(tmp_path):
    from tests.test_sqlite_repository import make_db

    db = make_db(
        tmp_path,
        {"place_id": "pho-1", "name": "Phở Bò Hàng Đồng", "category": "Nhà hàng phở",
         "address": "12 Hàng Đồng", "is_active": 1},
        {"place_id": "bun-2", "name": "Bún Chả Hương Liên", "category": "Nhà hàng",
         "address": "24 Lê Văn Hưu", "is_active": 1},
    )
    c, _ = build_client(db)
    return c


def test_chat_luong_khong_token_thi_401(client):
    assert client.get(f"{API}/admin/quality").status_code == 401


def test_chat_luong_tra_du_khoi_cua_ban_thiet_ke(client):
    res = client.get(f"{API}/admin/quality", headers=auth_header(client))

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    for truong in (
        "restaurants_total",
        "dishes_total",
        "restaurants_in_hanoi",
        "completeness_percent",
        "critical",
        "important",
        "to_review",
        "data_quality",
        "by_source",
        "needs_attention",
        "needs_attention_now",
        "trend",
        "resolved_today",
        "history_available",
    ):
        assert truong in data, f"thiếu trường {truong}"


def test_lan_dau_mo_trang_thi_delta_la_null(client):
    """Chưa có ảnh chụp nào đủ cũ — giao diện phải nói "chưa đủ dữ liệu", không vẽ mũi tên."""
    data = client.get(f"{API}/admin/quality", headers=auth_header(client)).json()["data"]

    assert data["restaurants_total"]["delta"] is None
    assert data["restaurants_total"]["baseline"] is None
    assert data["restaurants_total"]["current"] == 2


def test_mo_trang_hai_lan_van_chi_co_MOT_diem_xu_huong(client):
    """Ảnh chụp phải bất biến theo ngày, nếu không biểu đồ sẽ dày đặc ở hôm nay."""
    h = auth_header(client)
    client.get(f"{API}/admin/quality", headers=h)
    data = client.get(f"{API}/admin/quality?refresh=true", headers=h).json()["data"]

    assert len(data["trend"]) == 1


def test_danh_sach_van_de_co_du_ba_the_so(client):
    data = client.get(f"{API}/admin/issues", headers=auth_header(client)).json()["data"]

    assert data["critical"] >= 0
    assert data["important"] >= 0
    assert data["to_review"] >= 0
    assert data["total"] == data["critical"] + data["important"] + data["to_review"]
    assert data["can_resolve"] is True


def test_doi_tab_loc_thi_nam_the_so_GIU_NGUYEN(client):
    """Bấm tab "Nghiêm trọng" mà ba thẻ kia tụt về 0 là hiểu sai con số."""
    h = auth_header(client)
    tat_ca = client.get(f"{API}/admin/issues", headers=h).json()["data"]
    loc = client.get(f"{API}/admin/issues?priority=nghiem_trong", headers=h).json()["data"]

    assert loc["total"] == tat_ca["total"]
    assert loc["important"] == tat_ca["important"]
    assert all(v["priority"] == "nghiem_trong" for v in loc["groups"])


def test_priority_go_sai_thi_KHONG_loc(client):
    """Bảng trống trơn sẽ khiến người quản trị tưởng hệ thống sạch lỗi."""
    h = auth_header(client)
    tat_ca = client.get(f"{API}/admin/issues", headers=h).json()["data"]
    la = client.get(f"{API}/admin/issues?priority=khong-ton-tai", headers=h).json()["data"]

    assert len(la["groups"]) == len(tat_ca["groups"])


def test_chi_tiet_mot_nhom_tra_ve_ban_ghi_cu_the(client):
    res = client.get(f"{API}/admin/issues/thieu_lien_he", headers=auth_header(client))

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["key"] == "thieu_lien_he"
    # Hai quán trong fixture đều không có phone/website.
    assert data["total"] == 2
    assert {b["name"] for b in data["results"]} == {
        "Phở Bò Hàng Đồng",
        "Bún Chả Hương Liên",
    }


def test_chi_tiet_khoa_la_tra_200_rong_chu_KHONG_404(client):
    res = client.get(f"{API}/admin/issues/khoa-bia-ra", headers=auth_header(client))

    assert res.status_code == 200
    assert res.json()["data"]["results"] == []
    assert res.json()["data"]["total"] == 0


def test_danh_dau_xong_roi_go_ra(client):
    h = auth_header(client)

    dat = client.post(
        f"{API}/admin/issues/resolve",
        json={"key": "thieu_lien_he", "target_id": "pho-1", "note": "đã gọi điện"},
        headers=h,
    )
    assert dat.status_code == 200, dat.text
    assert dat.json()["data"]["resolved"] is True
    assert dat.json()["data"]["resolved_by"] == "admin"

    # Dòng đã đánh dấu vẫn HIỆN trong danh sách, chỉ kèm dấu — giấu đi thì người bấm
    # nhầm không còn cách nào tìm lại để gỡ.
    chi_tiet = client.get(f"{API}/admin/issues/thieu_lien_he", headers=h).json()["data"]
    da_danh_dau = {b["id"]: b for b in chi_tiet["results"]}
    assert da_danh_dau["pho-1"]["resolved_at"] is not None
    assert da_danh_dau["bun-2"]["resolved_at"] is None

    go = client.delete(
        f"{API}/admin/issues/resolve?key=thieu_lien_he&target_id=pho-1", headers=h
    )
    assert go.status_code == 200
    assert go.json()["data"]["resolved"] is False


def test_go_danh_dau_chua_tung_dat_van_tra_200(client):
    """Kết quả mong muốn ("dòng này hiện không bị đánh dấu") đã đạt được rồi."""
    res = client.delete(
        f"{API}/admin/issues/resolve?key=dong_tam&target_id=khong-ton-tai",
        headers=auth_header(client),
    )

    assert res.status_code == 200


def test_danh_dau_xong_KHONG_sua_du_lieu_quan(client):
    """Đánh dấu chỉ nói "tôi đã xem", tuyệt đối không được ẩn hay đổi quán."""
    h = auth_header(client)
    truoc = client.get(f"{API}/admin/restaurants", headers=h).json()["data"]

    client.post(
        f"{API}/admin/issues/resolve",
        json={"key": "thieu_lien_he", "target_id": "pho-1"},
        headers=h,
    )

    sau = client.get(f"{API}/admin/restaurants", headers=h).json()["data"]
    assert sau == truoc

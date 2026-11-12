"""Khoá lại tính năng NGƯỜI DÙNG BÁO QUÁN ĐÃ ĐÓNG CỬA — theo biểu đồ UC06 / UC21.

Biểu đồ: lượt báo đưa quán vào HÀNG CHỜ quản trị; lượt báo KHÔNG tự ẩn quán. Quản trị là
người quyết định ẩn. Các test ở đây khoá đúng điều đó, và khoá luôn chống phá hoại (một
người không được đếm hai lần).

Vì sao có tính năng này: dữ liệu quán lấy từ OSM/Overture/Apify, mà đo ngày 2026-08-19
cho thấy 65% bản ghi OSM chưa ai sửa trong hơn một năm (có bản ghi từ 2010). Người đang
đứng trước cửa quán là tín hiệu tươi DUY NHẤT còn lại.
"""
import pytest

from src.domain.services.closure_reports import ClosureReportTally
from src.domain.services.search_ranking import rank_restaurants
from src.domain.value_objects.location import Location
from tests.fakes import make_restaurant

HANOI = Location(lat=21.03, lng=105.85)


@pytest.fixture
def tally():
    return ClosureReportTally()


# --- Đếm theo NGƯỜI BÁO, không theo lượt bấm --------------------------------


def test_MOT_nguoi_bam_nhieu_lan_chi_tinh_la_1(tally):
    """Chống phá hoại: người bực mình bấm 50 lần vẫn chỉ tính là 1 người báo."""
    for _ in range(50):
        tally.record("quan-x", "cung-mot-nguoi")

    assert tally.report_count("quan-x") == 1


def test_nhieu_nguoi_bao_thi_dem_dung_so_nguoi(tally):
    for i in range(3):
        tally.record("quan-x", f"nguoi-{i}")

    assert tally.report_count("quan-x") == 3


def test_quan_chua_ai_bao_thi_khong_bi_anh_huong(tally):
    tally.record("quan-x", "p1")
    assert tally.report_count("quan-khac") == 0


def test_thieu_du_lieu_thi_bo_qua_chu_khong_no(tally):
    """Client gửi thiếu trường không được làm hỏng lượt ghi."""
    assert tally.record("", "nguoi") == 0
    assert tally.record("quan-x", "") == 0


# --- Lượt báo KHÔNG tự ẩn quán (UC06) ----------------------------------------


def test_bao_nhieu_nguoi_cung_KHONG_lam_quan_bien_mat_khoi_ket_qua(tally):
    """Theo biểu đồ: báo chỉ vào hàng chờ quản trị. Quán đông người báo vẫn hiện."""
    quan = make_restaurant("Quán bị báo", place_id="q1")
    con_mo = make_restaurant("Quán còn mở", place_id="q2")
    for i in range(10):
        tally.record("q1", f"nguoi-{i}")

    ranked = rank_restaurants(restaurants=[quan, con_mo], origin=HANOI, limit=10)

    assert {r.restaurant.name for r in ranked} == {"Quán bị báo", "Quán còn mở"}


def test_hang_cho_liet_ke_quan_bi_bao_theo_so_nguoi_bao(tally):
    """Admin (UC21) cần danh sách để quyết định; quán bị báo nhiều đứng trước."""
    tally.record("q1", "a")
    for i in range(3):
        tally.record("q2", f"b-{i}")

    assert tally.reported_counts() == {"q1": 1, "q2": 3}
    assert tally.status() == {"ready": True, "quan_bi_bao": 2}


def test_xoa_luot_bao_dua_quan_ra_khoi_hang_cho(tally):
    """UC21 nhánh 'không thật sự đóng cửa': gỡ lượt báo -> quán không còn trong hàng chờ."""
    for i in range(3):
        tally.record("q1", f"nguoi-{i}")

    assert tally.clear("q1") == 3
    assert tally.reported_counts() == {}


def test_khong_truyen_bo_dem_thi_hanh_vi_y_HET_nhu_truoc():
    """Xếp hạng không cần biết gì về báo đóng cửa: không truyền gì vẫn chạy."""
    quan = make_restaurant("Quán bất kỳ", place_id="q1")

    ranked = rank_restaurants(restaurants=[quan], origin=HANOI, limit=10)

    assert [r.restaurant.name for r in ranked] == ["Quán bất kỳ"]

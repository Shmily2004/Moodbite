"""Khoá lại tính năng NGƯỜI DÙNG BÁO QUÁN ĐÃ ĐÓNG CỬA.

Vì sao có tính năng này: dữ liệu quán lấy từ OSM/Overture/Apify, mà đo ngày 2026-08-19
cho thấy 65% bản ghi OSM chưa ai sửa trong hơn một năm (có bản ghi từ 2010). Mọi nguồn
biết trạng thái theo thời gian thực đều cần thẻ thanh toán hoặc vi phạm ToS. Người đang
đứng trước cửa quán là tín hiệu tươi DUY NHẤT còn lại.
"""
import pytest

from src.domain.services.closure_reports import (
    MIN_REPORTS_TO_HIDE,
    ClosureReportTally,
)
from src.domain.services.search_ranking import rank_restaurants
from src.domain.value_objects.location import Location
from tests.fakes import make_restaurant

HANOI = Location(lat=21.03, lng=105.85)


@pytest.fixture
def tally():
    return ClosureReportTally()


# --- Đếm theo PHIÊN, không theo lượt bấm ------------------------------------


def test_chua_du_nguong_thi_CHUA_an(tally):
    for i in range(MIN_REPORTS_TO_HIDE - 1):
        tally.record("quan-x", f"phien-{i}")
    assert tally.is_reported_closed("quan-x") is False


def test_du_nguong_thi_an(tally):
    for i in range(MIN_REPORTS_TO_HIDE):
        tally.record("quan-x", f"phien-{i}")
    assert tally.is_reported_closed("quan-x") is True


def test_MOT_nguoi_bam_nhieu_lan_KHONG_du_de_dim_quan(tally):
    """Chống phá hoại: người bực mình bấm 50 lần vẫn chỉ tính là 1 phiếu.
    Không có luật này thì bất kỳ ai cũng xoá được quán đối thủ trong 10 giây."""
    for _ in range(50):
        tally.record("quan-x", "cung-mot-phien")

    assert tally.report_count("quan-x") == 1
    assert tally.is_reported_closed("quan-x") is False


def test_quan_chua_ai_bao_thi_khong_bi_anh_huong(tally):
    tally.record("quan-x", "p1")
    assert tally.report_count("quan-khac") == 0
    assert tally.is_reported_closed("quan-khac") is False


def test_thieu_du_lieu_thi_bo_qua_chu_khong_no(tally):
    """Client gửi thiếu trường không được làm hỏng lượt ghi."""
    assert tally.record("", "phien") == 0
    assert tally.record("quan-x", "") == 0


# --- Nối vào xếp hạng --------------------------------------------------------


def test_quan_bi_bao_du_nguong_bien_mat_khoi_ket_qua(tally):
    quan = make_restaurant("Quán đã đóng", place_id="q1")
    con_mo = make_restaurant("Quán còn mở", place_id="q2")
    for i in range(MIN_REPORTS_TO_HIDE):
        tally.record("q1", f"phien-{i}")

    ranked = rank_restaurants(
        restaurants=[quan, con_mo], origin=HANOI, limit=10,
        is_reported_closed=tally.is_reported_closed,
    )

    assert [r.restaurant.name for r in ranked] == ["Quán còn mở"]


def test_khong_truyen_bo_dem_thi_hanh_vi_y_HET_nhu_truoc():
    """Tham số mới phải KHÔNG bắt buộc: mọi chỗ gọi cũ chạy nguyên như cũ."""
    quan = make_restaurant("Quán bất kỳ", place_id="q1")

    ranked = rank_restaurants(restaurants=[quan], origin=HANOI, limit=10)

    assert [r.restaurant.name for r in ranked] == ["Quán bất kỳ"]


def test_admin_biet_quan_nao_dang_bi_an(tally):
    """Ẩn tự động mà không ai tra lại được là ẩn mù. Admin phải lấy ra được danh sách."""
    for i in range(MIN_REPORTS_TO_HIDE):
        tally.record("q1", f"phien-{i}")
    tally.record("q2", "phien-le")

    assert tally.hidden_place_ids() == {"q1"}
    assert tally.status()["quan_bi_bao"] == 2
    assert tally.status()["quan_da_an"] == 1

"""Tách CỤM ĐỊA ĐIỂM ("gần hồ gươm", "ở hoàn kiếm") khỏi câu tìm kiếm.

Bug thật 2026-09-16 (gọi API thật): "bún chả gần hồ gươm" trả top-3 là "Ho Guom Bar",
"GóC HỒ GƯƠM", "Hồ Gươm - Hồ Hoàn Kiếm" - không quán nào bán bún chả. Cụm địa điểm bị
đem đi khớp TÊN QUÁN như thể nó là món ăn.
"""
from src.domain.services.query_location import (
    build_ward_centroids,
    find_ward,
    split_location_phrase,
)
from tests.fakes import make_restaurant


def test_cum_gan_X_bi_tach_khoi_phan_khop_ten():
    parsed = split_location_phrase("bún chả gần hồ gươm")
    assert parsed.text == "bún chả"
    assert parsed.place == "hồ gươm"


def test_cac_gioi_tu_dia_diem_co_dau():
    assert split_location_phrase("phở ở hoàn kiếm").place == "hoàn kiếm"
    assert split_location_phrase("lẩu quanh cầu giấy").place == "cầu giấy"
    assert split_location_phrase("cà phê tại ba đình").place == "ba đình"
    assert split_location_phrase("bún chả khu vực đống đa").place == "đống đa"
    assert split_location_phrase("bún chả khu vực đống đa").text == "bún chả"


def test_cum_dia_diem_dung_dau_cau_van_tach_duoc():
    parsed = split_location_phrase("gần hồ gươm có quán bún chả nào")
    assert parsed.place == "hồ gươm"
    assert "bún chả" in parsed.text
    assert "gươm" not in parsed.text


def test_gan_day_la_vi_tri_hien_tai_khong_phai_dia_danh():
    parsed = split_location_phrase("lẩu gần đây")
    assert parsed.text == "lẩu"
    assert parsed.place is None
    assert parsed.near_current_location


def test_khong_co_cum_dia_diem_thi_giu_nguyen_cau():
    parsed = split_location_phrase("bún chả")
    assert parsed.text == "bún chả"
    assert parsed.place is None


def test_gan_KHONG_DAU_mo_ho_voi_mon_gan_nen_chi_tach_khi_la_dia_danh_da_biet():
    """'gan' không dấu vừa là 'gần' vừa là 'gan' (lá gan): "pate gan ngỗng" là MÓN.
    Chỉ dám hiểu là giới từ khi phần phía sau đúng là một địa danh ta biết."""
    parsed = split_location_phrase("pate gan ngỗng")
    assert parsed.place is None
    assert parsed.text == "pate gan ngỗng"

    biet = split_location_phrase(
        "bun cha gan hoan kiem", is_known_place=lambda p: p == "hoan kiem"
    )
    assert biet.place == "hoan kiem"
    assert biet.text == "bun cha"


def test_tai_co_dau_khong_nuot_mon_tai_heo():
    """'tại' có dấu là giới từ; 'tai' trong 'tai heo' là món - dấu phân biệt được."""
    parsed = split_location_phrase("tai heo luộc")
    assert parsed.place is None
    assert parsed.text == "tai heo luộc"


def test_o_co_dau_khong_nuot_banh_mi_o():
    parsed = split_location_phrase("bánh mì ổ")
    assert parsed.place is None


# --- Tâm phường suy từ dữ liệu -----------------------------------------------


def test_tam_phuong_la_trung_binh_toa_do_quan_trong_phuong():
    wards = build_ward_centroids([
        make_restaurant("A", lat=21.00, lng=105.80, district="Phường Hoàn Kiếm"),
        make_restaurant("B", lat=21.02, lng=105.82, district="Phường Hoàn Kiếm"),
        make_restaurant("C", lat=21.10, lng=105.90, district="Phường Cầu Giấy"),
    ])
    hk = find_ward("hoàn kiếm", wards)
    assert hk is not None
    assert hk.name == "Phường Hoàn Kiếm"
    assert abs(hk.location.lat - 21.01) < 1e-9
    assert abs(hk.location.lng - 105.81) < 1e-9
    assert hk.restaurant_count == 2


def test_tim_phuong_khop_ca_ten_khong_dau_va_co_tien_to():
    wards = build_ward_centroids([
        make_restaurant("A", district="Phường Cầu Giấy"),
    ])
    assert find_ward("cau giay", wards) is not None
    assert find_ward("phường cầu giấy", wards) is not None


def test_dia_danh_khong_phai_phuong_thi_khong_doan_toa_do():
    """Không có bảng toạ độ địa danh -> KHÔNG bịa toạ độ Hồ Gươm."""
    wards = build_ward_centroids([
        make_restaurant("A", district="Phường Hoàn Kiếm"),
    ])
    assert find_ward("hồ gươm", wards) is None
    # Khớp NGUYÊN tên phường, không khớp một phần: "kiếm" không phải "Hoàn Kiếm".
    assert find_ward("kiếm", wards) is None

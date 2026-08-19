"""Khoá lại CHỈ MỤC MÓN <-> QUÁN: quán nào bán món này, và tin được tới đâu."""
from src.domain.entities.dish import Dish
from src.domain.services.dish_matching import (
    MATCHED_BY_DISH_NAME,
    MATCHED_BY_NAME,
    MATCHED_BY_REVIEW,
    build_dish_restaurant_index,
)
from tests.fakes import make_restaurant

PHO_GA = Dish(name="Phở gà", match_keywords=["phở"])
PHO_BO = Dish(name="Phở bò", match_keywords=["phở"])


def _chi_muc(restaurants, dishes=(PHO_GA, PHO_BO)):
    return build_dish_restaurant_index(list(dishes), restaurants)


def _cach_khop(index, dish_id, ten_quan):
    for m in index[dish_id]:
        if m.restaurant.name == ten_quan:
            return m.matched_by
    return None


# --- Ba tầng tin cậy ---------------------------------------------------------


def test_ten_quan_ghi_DUNG_TEN_MON_la_tang_manh_nhat():
    quan = make_restaurant("Phở Gà Nguyệt")
    index = _chi_muc([quan])
    assert _cach_khop(index, PHO_GA.identifier, "Phở Gà Nguyệt") == MATCHED_BY_DISH_NAME


def test_chi_khop_TU_KHOA_CHUNG_thi_o_tang_giua():
    """Quán "Phở Thìn" vẫn xuất hiện ở trang Phở gà - ta không đọc được thực đơn nên
    không dám loại - nhưng phải đứng SAU quán ghi rõ "phở gà"."""
    quan = make_restaurant("Phở Thìn")
    index = _chi_muc([quan])
    assert _cach_khop(index, PHO_GA.identifier, "Phở Thìn") == MATCHED_BY_NAME


def test_chi_duoc_REVIEW_nhac_toi_la_tang_yeu_nhat():
    quan = make_restaurant("Nhà Hàng Hoàng", review_text="ở đây có phở gà ngon lắm")
    index = _chi_muc([quan])
    assert _cach_khop(index, PHO_GA.identifier, "Nhà Hàng Hoàng") == MATCHED_BY_REVIEW


def test_tang_manh_hon_thi_strength_lon_hon():
    quan_manh = make_restaurant("Phở Gà Nguyệt")
    quan_yeu = make_restaurant("Phở Thìn")
    index = _chi_muc([quan_manh, quan_yeu])
    diem = {m.restaurant.name: m.strength for m in index[PHO_GA.identifier]}
    assert diem["Phở Gà Nguyệt"] > diem["Phở Thìn"]


def test_hai_mon_chung_TU_KHOA_van_phan_biet_duoc_nhau():
    """Đây là lý do tầng "đúng tên món" ra đời: Phở bò và Phở gà cùng từ khoá "phở",
    trước đó hai trang món trả về danh sách y hệt nhau."""
    ga = make_restaurant("Phở Gà Nguyệt")
    bo = make_restaurant("Phở Bò Gia Truyền")
    index = _chi_muc([ga, bo])

    assert _cach_khop(index, PHO_GA.identifier, "Phở Gà Nguyệt") == MATCHED_BY_DISH_NAME
    assert _cach_khop(index, PHO_GA.identifier, "Phở Bò Gia Truyền") == MATCHED_BY_NAME
    assert _cach_khop(index, PHO_BO.identifier, "Phở Bò Gia Truyền") == MATCHED_BY_DISH_NAME
    assert _cach_khop(index, PHO_BO.identifier, "Phở Gà Nguyệt") == MATCHED_BY_NAME


# --- Đụng độ dấu (lỗi 39,2% ngày 2026-08-19) ---------------------------------


def test_quan_TAO_PHO_khong_lot_vao_trang_mon_pho():
    for ten in ["Tào Phớ Gánh", "Nhà Hàng Hải Sản Phố", "Phố Nhậu"]:
        index = _chi_muc([make_restaurant(ten)])
        assert index[PHO_GA.identifier] == [], f"khop nham: {ten}"


def test_quan_ghi_bien_KHONG_DAU_van_duoc_giu():
    index = _chi_muc([make_restaurant("Pho Bo Gia Truyen")])
    assert len(index[PHO_BO.identifier]) == 1

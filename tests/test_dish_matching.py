"""Khoá lại CHỈ MỤC MÓN <-> QUÁN: quán nào bán món này, và tin được tới đâu."""
from src.domain.entities.dish import Dish
from src.domain.services.dish_matching import (
    MATCHED_BY_DISH_NAME,
    MATCHED_BY_NAME,
    MATCHED_BY_REVIEW,
    MATCHED_BY_UNACCENTED_AT_DRINK_VENUE,
    MATCH_STRENGTH,
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


def test_chi_khop_LOAI_HINH_thi_xep_duoi_quan_khop_TEN():
    """CLAUDE.md mục 4 quy tắc 6: ưu tiên TÊN QUÁN hơn `categoryName`. Trước 2026-09-29
    hai loại cùng bậc - đo thật: 10/298 trang món có quán chỉ khớp loại hình chen lên trên
    quán khớp tên còn đang bị ẩn."""
    theo_ten = make_restaurant("Phở Thìn")
    theo_loai_hinh = make_restaurant("Quán Cô Hoa", category="Quán phở")
    index = _chi_muc([theo_ten, theo_loai_hinh])

    ten = _match(index, PHO_GA.identifier, "Phở Thìn")
    loai_hinh = _match(index, PHO_GA.identifier, "Quán Cô Hoa")
    assert loai_hinh.match_source == "category"
    assert loai_hinh.strength < ten.strength
    # Vẫn là khớp trên dữ liệu có cấu trúc -> đứng trên quán chỉ được review nhắc tới.
    assert loai_hinh.strength > MATCH_STRENGTH[MATCHED_BY_REVIEW]
    # Hạ bậc KHÔNG đổi `matched_by` - trường đó là hợp đồng API của trang quản trị.
    assert loai_hinh.matched_by == MATCHED_BY_NAME


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


# --- Nguồn khớp để hiện cho người dùng (bug thật 2026-09-16) ----------------------
#
# GET /dishes/pho/restaurants trả `match_source="mood"` cho MỌI quán dù không gửi mood:
# chỉ mục biết rõ quán khớp bằng tên / loại hình / review nhưng thông tin đó bị vứt đi.


def _match(index, dish_id, ten_quan):
    return next(m for m in index[dish_id] if m.restaurant.name == ten_quan)


def test_match_source_noi_dung_truong_da_khop():
    index = _chi_muc([
        make_restaurant("Phở Thìn"),
        make_restaurant("Quán Hương", category="Nhà hàng phở"),
        make_restaurant("Nhà Hàng Hoàng", review_text="phở gà ở đây ngon"),
    ])
    assert _match(index, PHO_GA.identifier, "Phở Thìn").match_source == "name"
    assert _match(index, PHO_GA.identifier, "Quán Hương").match_source == "category"
    assert _match(index, PHO_GA.identifier, "Nhà Hàng Hoàng").match_source == "review"


# --- Quán đồ uống khớp tên KHÔNG DẤU (đo 2026-09-16) -------------------------------
#
# Trang món Phở: 1491 quán, 39 quán có loại hình đồ uống (Quán cà phê/bar/trà), trong đó
# 19 quán khớp CHỈ nhờ chữ "pho" không dấu - "Pho Co Coffee", "Ca phe pho", "Cafe Goc
# pho" (gần như chắc là "phố"). Hai quán như thế đứng hạng 2 và 5.
#
# KHÔNG đổi quy tắc "dấu là bằng chứng" (chủ dự án chưa chốt): quán vẫn CÓ MẶT, chỉ bị
# xếp xuống tầng dưới quán khớp tên có bằng chứng.


def test_quan_ca_phe_khop_ten_khong_dau_bi_ha_tang_nhung_van_co_mat():
    index = _chi_muc([
        make_restaurant("Pho Co Coffee", category="Quán cà phê"),
        make_restaurant("Phở Thìn"),
    ])
    ca_phe = _match(index, PHO_GA.identifier, "Pho Co Coffee")
    assert ca_phe.matched_by == MATCHED_BY_UNACCENTED_AT_DRINK_VENUE
    assert ca_phe.strength < _match(index, PHO_GA.identifier, "Phở Thìn").strength
    assert ca_phe.strength > MATCH_STRENGTH[MATCHED_BY_REVIEW]


def test_quan_ca_phe_ghi_CO_DAU_khong_bi_ha_tang():
    """Có dấu là có bằng chứng: loại hình Google gắn sai không phải lý do để hạ."""
    index = _chi_muc([make_restaurant("Phở Cuốn Hoa Lan", category="Quán cà phê")])
    assert _match(index, PHO_GA.identifier, "Phở Cuốn Hoa Lan").matched_by == MATCHED_BY_NAME


def test_quan_KHONG_phai_do_uong_khop_khong_dau_giu_nguyen_tang():
    """Quy tắc bao dung với biển không dấu vẫn nguyên - chỉ quán đồ uống mới bị hạ."""
    index = _chi_muc([make_restaurant("Pho Bo Gia Truyen", category="Nhà hàng")])
    assert _match(index, PHO_BO.identifier, "Pho Bo Gia Truyen").matched_by in (
        MATCHED_BY_NAME, MATCHED_BY_DISH_NAME,
    )


def test_mon_DO_UONG_khong_ha_tang_quan_ca_phe():
    ca_phe_sua = Dish(name="Cà phê sữa đá", match_keywords=["cà phê", "coffee"])
    index = _chi_muc(
        [make_restaurant("Ca phe Nang", category="Quán cà phê")], dishes=(ca_phe_sua,)
    )
    assert _match(index, ca_phe_sua.identifier, "Ca phe Nang").matched_by == MATCHED_BY_NAME

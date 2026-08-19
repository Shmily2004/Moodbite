"""Khoá lại phép SO KHỚP CHỮ TIẾNG VIỆT - nơi dự án đã trả giá nhiều lần nhất.

Ba lỗi có thật, mỗi lỗi một nhóm test dưới đây:

  1. Khớp CHUỖI CON: "oc" khớp "Ngọc", "bo" khớp "bột".
  2. Không bỏ dấu: quán tự đặt tên "Pho Bo" không bao giờ khớp món "Phở bò".
  3. ĐỤNG ĐỘ SAU KHI BỎ DẤU: "phở" / "phố" / "phớ" đều thành "pho". Đo trên dữ liệu
     thật ngày 2026-08-19: 763/1948 (39,2%) quán trả về cho món Phở là quán "Tào Phớ"
     (món tráng miệng) hoặc có chữ "Phố" trong tên - hoàn toàn không bán phở.

Lỗi 1 và 2 đã sửa từ trước. Lỗi 3 là lỗi bộ test này được viết ra để bắt.
"""
import pytest

from src.domain.value_objects.text import (
    contains_phrase,
    normalize,
    tokenize,
    tokenize_pairs,
)


# --- Lỗi 1: chuỗi con (đã sửa từ trước, giữ để không tái phát) ----------------


def test_khong_khop_chuoi_con():
    assert not contains_phrase("Ngọc Sương quán", "ốc")
    assert not contains_phrase("Bột chiên Sài Gòn", "bò")


def test_khop_cum_tu_nguyen_ven():
    assert contains_phrase("Quán bún chả ngon nhất phố", "bún chả")


# --- Lỗi 2: bỏ dấu (đã sửa từ trước) -----------------------------------------


def test_ten_quan_KHONG_DAU_van_khop_mon_co_dau():
    """Rất nhiều quán tự ghi biển không dấu. Đây là lý do `normalize` tồn tại."""
    assert contains_phrase("Pho Bo Gia Truyen", "phở")
    assert contains_phrase("O Bun Cha", "bún chả")


def test_nguoi_dung_go_KHONG_DAU_van_tim_duoc_quan_co_dau():
    assert contains_phrase("Phở Thìn Bờ Hồ", "pho")


# --- Lỗi 3: ĐỤNG ĐỘ DẤU - phần chính của file này ----------------------------


@pytest.mark.parametrize(
    "ten_quan",
    [
        "Tào Phớ Gánh",              # món tráng miệng, không phải phở
        "Ăn tào phớ ngon 10k",
        "Nhà Hàng Hải Sản Phố",      # "phố" = đường phố
        "Phố Nhậu",
        "Bún dọc mùng phố cổ",
    ],
)
def test_pho_KHONG_duoc_khop_phot_hay_phod(ten_quan):
    """"Phở" != "phớ" != "phố". Bỏ dấu xong cả ba đều là "pho" - nhưng khi CẢ HAI vế
    đều có dấu thì dấu là bằng chứng chắc chắn rằng đây là hai từ khác nhau."""
    assert not contains_phrase(ten_quan, "phở"), f"khop nham: {ten_quan}"


def test_pho_VAN_khop_quan_pho_that():
    for ten in ["Phở Thìn", "Phở Sân Vườn", "Bún phở Thanh Định", "PHỞ 10 LÝ QUỐC SƯ"]:
        assert contains_phrase(ten, "phở"), f"bo sot quan pho that: {ten}"


@pytest.mark.parametrize(
    "ten_quan, tu_khoa",
    [
        ("Cửa hàng Cốm Vòng", "cơm"),        # cốm != cơm
        ("Quán Cháo Lòng", "chao"),          # cháo != chao (khớp không dấu thì được)
        ("Bánh Mì Chảo", "cháo"),            # chảo != cháo
        ("Chè Bưởi", "chê"),
    ],
)
def test_cac_cap_dung_do_khac(ten_quan, tu_khoa):
    if normalize(tu_khoa) == tu_khoa:
        # Từ khoá KHÔNG dấu -> không có bằng chứng để loại, phải khớp (bao dung).
        assert contains_phrase(ten_quan, tu_khoa)
    else:
        assert not contains_phrase(ten_quan, tu_khoa)


def test_mot_ve_khong_dau_thi_VAN_KHOP():
    """Chỉ loại khi CẢ HAI vế đều có dấu. Một vế không dấu = không đủ bằng chứng,
    và bao dung ở đây chính là thứ giữ cho lỗi 2 không quay lại."""
    assert contains_phrase("Tao Pho Ganh", "phở")      # tên quán mất dấu -> vẫn khớp
    assert contains_phrase("Tào Phớ Gánh", "pho")      # từ khoá mất dấu -> vẫn khớp


# --- Bất biến của `tokenize_pairs` -------------------------------------------


def test_tokenize_pairs_giu_dung_thu_tu_va_so_luong_voi_tokenize():
    """`tokenize` phải là hình chiếu của `tokenize_pairs`. Lệch nhau là chỉ mục món
    tra sai ô (bucket) và mất quán một cách âm thầm."""
    for text in [
        "Phở Thìn Bờ Hồ",
        "Bún chả - Nem cua bể 34",
        "Pho Bo Gia Truyen",
        "Cà phê 1988 & Trà đá",
        "",
    ]:
        pairs = tokenize_pairs(text, min_length=1)
        assert [p for p, _ in pairs] == tokenize(text, min_length=1)


def test_tokenize_pairs_ve_trai_la_ban_bo_dau_cua_ve_phai():
    pairs = tokenize_pairs("Phở Bò Tái", min_length=1)
    assert pairs == [("pho", "phở"), ("bo", "bò"), ("tai", "tái")]

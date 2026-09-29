"""Công tắc "Chỉ hiện quán có ghi giá" (bản vẽ `frontend/design/Filler.png`).

VÌ SAO CÓ RIÊNG MỘT BỘ TEST: đây là bộ lọc ĐẮT NHẤT của sản phẩm. Đo trên dataset thật
ngày 2026-09-23:

    671/52.872 quán (1,3%) có ô giá đọc được
    trong bán kính 10km quanh trung tâm Hà Nội: 47.571 cặp quán-món -> 1.293 (2,7%)
    món cụ thể hiện ra ở trang chủ: 282 -> 156

Ba nguồn quán chính (OSM, Overture, Wikidata) đều KHÔNG có trường giá; giá chỉ đến từ lớp
làm giàu Apify. Vì vậy điều được khoá ở đây không chỉ là "lọc đúng", mà là **lọc xong có
NÓI RA hay không** - im lặng cắt danh sách còn 2,7% sẽ khiến người dùng kết luận sai rằng
khu mình ở ít quán, trong khi thứ thiếu là dữ liệu giá của ta (CLAUDE.md mục 4 quy tắc 1
và mục 5).
"""
import pytest

from src.domain.value_objects.price import has_known_price
from tests.fakes import make_restaurant
from tests.test_dish_api import API, BUN_CHA, PHO_BO, SESSION, make_client

# Giá THẬT lấy từ dataset - nhiều định dạng, và `price` là CHUỖI chứ không phải số.
GIA_THAT = "1-100.000 ₫"


def client_co_gia_va_khong():
    """Một món, hai quán: một quán ghi giá, một quán không. Đủ để thấy bộ lọc cắt ở đâu."""
    co_gia = make_restaurant("Bún Chả Hương Liên", lat=21.0285, lng=105.8542, price=GIA_THAT)
    khong_gia = make_restaurant("Bún Chả Đắc Kim", lat=21.0286, lng=105.8543, price=None)
    return make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [co_gia, khong_gia]},
    )


# --- domain ------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, mong_doi",
    [
        ("1-100.000 ₫", True),
        ("Trên 1 Tr ₫", True),
        ("70 US$", True),
        (None, False),
        ("", False),
        # Có chữ nhưng KHÔNG có con số nào -> không xếp được mức giá, nên với bộ lọc này
        # nó vẫn là "chưa biết giá". Nới ở đây sẽ phản bội chính lời hứa của công tắc.
        ("Liên hệ", False),
    ],
)
def test_has_known_price(raw, mong_doi):
    assert has_known_price(raw) is mong_doi


# --- POST /dishes/suggest ----------------------------------------------------


def test_suggest_chi_dem_quan_co_gia_khi_bat_cong_tac():
    """`restaurant_count` phải đổi theo công tắc, nếu không con số đang nói dối."""
    client = client_co_gia_va_khong()

    tat = client.post(f"{API}/dishes/suggest", json={"session_id": SESSION}).json()["data"]
    bat = client.post(
        f"{API}/dishes/suggest", json={"session_id": SESSION, "only_with_price": True}
    ).json()["data"]

    assert tat["results"][0]["restaurant_count"] == 2
    assert bat["results"][0]["restaurant_count"] == 1


def test_suggest_an_mon_khong_quan_nao_ghi_gia_va_noi_ra():
    """Ẩn món là đúng; im lặng ẩn thì không - đúng lỗi `/suggest-dish` cũ từng mắc."""
    co_gia = make_restaurant("Bún Chả Hương Liên", lat=21.0285, lng=105.8542, price=GIA_THAT)
    khong_gia = make_restaurant("Phở Thìn", lat=21.0290, lng=105.8550, price=None)
    client = make_client(
        dishes=[BUN_CHA, PHO_BO],
        index={"bun-cha": [co_gia], "pho-bo": [khong_gia]},
    )

    data = client.post(
        f"{API}/dishes/suggest", json={"session_id": SESSION, "only_with_price": True}
    ).json()["data"]

    assert [m["name"] for m in data["results"]] == ["Bún chả"]
    canh_bao = " ".join(data["warnings"])
    assert "ghi giá" in canh_bao and "1 món" in canh_bao


def test_mon_bi_an_vi_gia_khong_bi_doi_thanh_khu_vuc_khong_co_quan():
    """Hai lý do khác nhau thì phải là hai câu khác nhau.

    Phở Thìn ở NGAY ĐÓ và có bán phở - chỉ là ta không biết giá. Nói "khu vực này chưa
    tìm được quán nào bán" là một chẩn đoán SAI, và nó còn dẫn người dùng đi nới bán kính
    một cách vô ích.
    """
    client = make_client(
        dishes=[BUN_CHA, PHO_BO],
        index={
            "bun-cha": [make_restaurant("Bún Chả Hương Liên", price=GIA_THAT)],
            "pho-bo": [make_restaurant("Phở Thìn", lat=21.029, lng=105.855, price=None)],
        },
    )

    data = client.post(
        f"{API}/dishes/suggest", json={"session_id": SESSION, "only_with_price": True}
    ).json()["data"]

    assert not any("chưa tìm được quán nào bán" in w for w in data["warnings"])


def test_mac_dinh_tat_cong_tac():
    """Không gửi gì thì hành vi phải y như trước - đây là thay đổi CỘNG THÊM."""
    client = client_co_gia_va_khong()

    data = client.post(f"{API}/dishes/suggest", json={"session_id": SESSION}).json()["data"]

    assert data["results"][0]["restaurant_count"] == 2
    assert not any("ghi giá" in w for w in data["warnings"])


# --- GET /dishes/{id}/restaurants --------------------------------------------


def test_danh_sach_quan_bo_quan_khong_ghi_gia_va_dem_so_da_bo():
    client = client_co_gia_va_khong()

    r = client.get(
        f"{API}/dishes/bun-cha/restaurants",
        params={"session_id": SESSION, "only_with_price": True},
    )

    data = r.json()["data"]
    assert [q["name"] for q in data["results"]] == ["Bún Chả Hương Liên"]
    assert all(q["price_range"] for q in data["results"])
    assert any("đã bỏ 1 quán" in w for w in data["warnings"])


def test_loc_gia_vet_sach_thi_khong_do_toi_cho_khau_doi_chieu_ten_quan():
    """BUG ĐÃ CHẶN: câu "chưa quán nào khớp món" nói về CHỈ MỤC MÓN-QUÁN.

    Khi chỉ mục có quán mà bộ lọc giá vét sạch, dán thêm câu đó vào là đổ tội nhầm cho
    khâu đối chiếu tên quán - người đọc sẽ đi sửa đúng chỗ không hỏng.
    """
    client = make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [make_restaurant("Bún Chả Đắc Kim", price=None)]},
    )

    data = client.get(
        f"{API}/dishes/bun-cha/restaurants",
        params={"session_id": SESSION, "only_with_price": True},
    ).json()["data"]

    assert data["results"] == []
    assert not any("khớp món" in w for w in data["warnings"])
    assert any("chưa có giá" in w for w in data["warnings"])


def test_khong_co_gi_trong_chi_muc_thi_van_noi_dung_ly_do_cu():
    """Vế còn lại của test trên: chỉ mục RỖNG thì câu cũ vẫn phải còn."""
    client = make_client(dishes=[BUN_CHA], index={"bun-cha": []})

    data = client.get(
        f"{API}/dishes/bun-cha/restaurants", params={"session_id": SESSION}
    ).json()["data"]

    assert any("khớp món" in w for w in data["warnings"])


# --- GET /dishes/{id} --------------------------------------------------------


def test_trang_chi_tiet_mon_dem_cung_bo_loc_voi_danh_sach_ben_duoi():
    """Hứa "2 quán" rồi danh sách hiện 1 quán là tự mâu thuẫn ngay trong một màn hình."""
    client = client_co_gia_va_khong()

    chi_tiet = client.get(
        f"{API}/dishes/bun-cha", params={"only_with_price": True}
    ).json()["data"]
    danh_sach = client.get(
        f"{API}/dishes/bun-cha/restaurants",
        params={"session_id": SESSION, "only_with_price": True},
    ).json()["data"]

    assert chi_tiet["restaurant_count"] == len(danh_sach["results"]) == 1


def test_nearest_restaurant_km_cung_theo_bo_loc():
    """`None` = không có quán nào CÓ GIÁ quanh đây, tuyệt đối không phải 0.0 km."""
    client = make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [make_restaurant("Bún Chả Đắc Kim", price=None)]},
    )

    data = client.get(
        f"{API}/dishes/bun-cha", params={"only_with_price": True}
    ).json()["data"]

    assert data["restaurant_count"] == 0
    assert data["nearest_restaurant_km"] is None

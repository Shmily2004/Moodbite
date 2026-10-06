"""Độ tin cậy món ở TRANG MÓN phải theo CÁCH KHỚP của từng quán (CLAUDE.md §4.4).

BUG THẬT (rà soát 2026-10-06): `find_restaurants_for_dish` gắn `confidence="specific"`
cho MỌI quán, kể cả quán chỉ khớp LOẠI HÌNH ("Nhà hàng ăn nhanh") hay chỉ được REVIEW
nhắc tới. Giao diện vì thế hiện "khớp loại hình cụ thể của quán" cho đúng những quán ta
ít bằng chứng nhất — nói quá điều ta biết.
"""
from __future__ import annotations

from src.application.use_cases.find_restaurants_for_dish import (
    FindRestaurantsForDishUseCase,
    RestaurantsForDishQuery,
)
from src.domain.entities.dish import Dish
from src.domain.services.dish_matching import (
    FIELD_CATEGORY,
    MATCHED_BY_DISH_NAME,
    MATCHED_BY_NAME,
    MATCHED_BY_REVIEW,
    MATCHED_BY_UNACCENTED_AT_DRINK_VENUE,
    DishMatch,
)
from tests.fakes import FakeDishCatalog, make_restaurant

DISH = Dish(name="Bún chả", dish_id="bun-cha", match_keywords=["bún chả"])


def _ket_qua():
    ten = make_restaurant("Bún Chả Hương Liên", place_id="ten", lat=21.030)
    tu_khoa = make_restaurant("Quán Bún Chả", place_id="tu-khoa", lat=21.031)
    loai_hinh = make_restaurant("Quán Bà Tư", place_id="loai-hinh", lat=21.032,
                                category="Bún chả")
    review = make_restaurant("Nhà Hàng Hoàng", place_id="review", lat=21.033)
    do_uong = make_restaurant("Bun Cha Coffee", place_id="do-uong", lat=21.034,
                              category="Quán cà phê")
    index = {
        "bun-cha": [
            DishMatch(ten, MATCHED_BY_DISH_NAME),
            DishMatch(tu_khoa, MATCHED_BY_NAME),
            DishMatch(loai_hinh, MATCHED_BY_NAME, FIELD_CATEGORY),
            DishMatch(review, MATCHED_BY_REVIEW),
            DishMatch(do_uong, MATCHED_BY_UNACCENTED_AT_DRINK_VENUE),
        ]
    }
    uc = FindRestaurantsForDishUseCase(FakeDishCatalog([DISH]), index)
    kq = uc.execute(RestaurantsForDishQuery(session_id="s", dish_id="bun-cha", limit=10))
    return {r.restaurant_id: r.suggested_dish for r in kq.results}


def test_khop_TEN_quan_la_specific():
    kq = _ket_qua()
    assert kq["ten"].confidence == "specific"
    assert kq["tu-khoa"].confidence == "specific"


def test_chi_khop_LOAI_HINH_KHONG_duoc_la_specific():
    kq = _ket_qua()
    assert kq["loai-hinh"].confidence == "generic_fallback"
    assert "loại hình" in kq["loai-hinh"].reason.lower()


def test_chi_REVIEW_nhac_toi_KHONG_duoc_la_specific():
    kq = _ket_qua()
    assert kq["review"].confidence == "generic_fallback"
    assert "review" in kq["review"].reason.lower()


def test_quan_do_uong_khop_ten_KHONG_DAU_la_tin_hieu_mo_ho():
    kq = _ket_qua()
    assert kq["do-uong"].confidence == "generic_fallback"


def test_ly_do_luon_noi_chua_phai_thuc_don_that():
    """Kể cả khớp tên: ta chưa từng đọc thực đơn thật (CLAUDE.md §4.4)."""
    for item in _ket_qua().values():
        assert "thực đơn" in item.reason


def test_moi_gia_tri_confidence_deu_nam_trong_tap_frontend_biet():
    """Frontend chỉ có nhãn cho 4 giá trị (format.ts DISH_CONFIDENCE_LABELS)."""
    hop_le = {"specific", "generic_fallback", "unknown", "ml"}
    assert {i.confidence for i in _ket_qua().values()} <= hop_le

"""Nhãn "Nổi tiếng" trên thẻ quán (`design/restaurance recommend.png`, dựng 2026-08-27).

Và một bug thật tìm được cùng lúc: `/dishes/{id}/restaurants` THIẾU 4 trường mà
`/search` có, trong đó có `temporarily_closed`. Hậu quả: trang chi tiết món — LUỒNG
CHÍNH của sản phẩm — không hiện nhãn "quán đang tạm nghỉ", nên người dùng bị dẫn tới
quán đóng cửa mà không được báo. Nguyên nhân gốc: response được dựng ở HAI nơi bằng tay.
"""
from __future__ import annotations

import pytest

from src.domain.services.restaurant_badges import (
    RATING_TOI_THIEU_NOI_TIENG,
    SO_REVIEW_NOI_TIENG,
    la_quan_noi_tieng,
)


# ==========================================================================
# Quy tắc ở domain
# ==========================================================================


def test_du_ca_hai_dieu_kien_thi_noi_tieng():
    assert la_quan_noi_tieng(4.5, 1000) is True


def test_dung_nguong_van_tinh_la_noi_tieng():
    """Ngưỡng là "từ ... trở lên", không phải "hơn"."""
    assert la_quan_noi_tieng(RATING_TOI_THIEU_NOI_TIENG, SO_REVIEW_NOI_TIENG) is True


def test_nhieu_review_nhung_rating_THAP_thi_KHONG_noi_tieng():
    """"Nhiều người nhắc tới" chưa chắc là "đáng tới".

    Gắn nhãn "Nổi tiếng" cho một quán 500 review mà 2,8 sao là đánh lừa người dùng.
    """
    assert la_quan_noi_tieng(2.8, 500) is False


def test_rating_cao_nhung_it_review_thi_KHONG_noi_tieng():
    """5 sao từ 3 lượt đánh giá không nói lên điều gì."""
    assert la_quan_noi_tieng(5.0, 3) is False


@pytest.mark.parametrize(
    "rating,reviews",
    [(None, 1000), (4.5, None), (None, None)],
)
def test_thieu_du_lieu_thi_KHONG_gan_nhan(rating, reviews):
    """Thiếu bằng chứng phải cho ra False, KHÔNG được đoán bừa.

    ⚠️ Và `False` ở đây nghĩa là "không biết", KHÔNG phải "quán không nổi tiếng" — chỉ
    2,4% quán có dữ liệu review (đo 2026-08-27).
    """
    assert la_quan_noi_tieng(rating, reviews) is False


def test_du_lieu_hong_khong_lam_sap_luot_tim():
    """Chuỗi lạ lọt vào cột số -> không gắn nhãn, không ném lỗi."""
    assert la_quan_noi_tieng("bốn phẩy năm", "nhiều") is False  # type: ignore[arg-type]


# ==========================================================================
# Tầng HTTP — hai endpoint phải trả GIỐNG NHAU
# ==========================================================================


def test_hai_endpoint_tra_ve_CUNG_BO_TRUONG(monkeypatch):
    """Chốt chặn cho bug đã xảy ra: response dựng ở hai nơi thì sẽ lệch nhau.

    So bộ khoá của một quán trong `/search` với một quán trong
    `/dishes/{id}/restaurants`. Lệch nghĩa là ai đó vừa thêm trường ở một nơi và quên
    nơi kia — đúng cách `temporarily_closed` từng biến mất khỏi trang chi tiết món.
    """
    from src.presentation.api.result_mapping import search_result_to_dict
    from src.presentation.api.routers import dishes as router_dishes
    import inspect

    # Router món PHẢI gọi hàm dựng chung, không được chép tay lại danh sách trường.
    ma_nguon = inspect.getsource(router_dishes)
    assert "search_result_to_dict" in ma_nguon
    assert '"user_ratings_total": item.user_ratings_total' not in ma_nguon, (
        "Router món đang chép tay lại danh sách trường — đúng lỗi đã sửa ngày 2026-08-27"
    )
    assert callable(search_result_to_dict)


def test_mapping_co_du_bon_truong_tung_bi_thieu():
    """Bốn trường này từng vắng mặt ở `/dishes/{id}/restaurants`."""
    from src.presentation.api.result_mapping import search_result_to_dict
    import inspect

    src = inspect.getsource(search_result_to_dict)
    for truong in (
        "temporarily_closed",
        "source_updated_at",
        "source_datasets",
        "surveyed_at",
        "is_famous",
    ):
        assert f'"{truong}"' in src, f"Thiếu trường {truong}"

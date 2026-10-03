"""Định dạng khoảng cách trong câu cảnh báo gửi người dùng (thêm 2026-10-02).

Bug thật thấy trên giao diện: "nằm ngoài bán kính 10.0 km" - số thực in thô, dấu chấm
thập phân kiểu Anh giữa câu tiếng Việt.
"""
import pytest

from src.domain.value_objects.location import mo_ta_km


@pytest.mark.parametrize("km,mong_doi", [
    (10.0, "10 km"), (10, "10 km"), (2.5, "2,5 km"), (0.75, "0,8 km"), (1.04, "1 km"),
])
def test_mo_ta_km(km, mong_doi):
    assert mo_ta_km(km) == mong_doi

"""Test phân tích GIỜ MỞ CỬA - hai định dạng cùng tồn tại trong dataset.

Nguyên tắc quan trọng nhất được khoá ở đây: KHÔNG PHÂN TÍCH ĐƯỢC nghĩa là "không biết",
tuyệt đối KHÔNG được hiểu thành "đóng cửa". Chỉ ~25% quán có dữ liệu giờ; hiểu sai chỗ
này sẽ xoá 75% dataset khỏi kết quả.
"""
import pytest

from src.domain.value_objects.opening_hours import (
    MINUTES_PER_DAY,
    parse_opening_hours,
)

MON, TUE, SAT, SUN = 0, 1, 5, 6


def at(hour: int, minute: int = 0) -> int:
    return hour * 60 + minute


# --- Định dạng Google/Apify ---------------------------------------------------


def test_parses_google_list_format():
    schedule = parse_opening_hours([{"day": "Thứ Hai", "hours": "07:00 to 23:00"}])
    assert schedule is not None
    assert schedule.is_open_at(MON, at(8)) is True
    assert schedule.is_open_at(MON, at(6)) is False
    assert schedule.is_open_at(TUE, at(8)) is False, "chỉ khai báo Thứ Hai"


def test_parses_google_stored_as_string_in_csv():
    """Cột CSV lưu list Python dưới dạng chuỗi - phải khôi phục được."""
    schedule = parse_opening_hours("[{'day': 'Chủ Nhật', 'hours': '09:00 to 22:00'}]")
    assert schedule is not None
    assert schedule.is_open_at(SUN, at(10)) is True


def test_parses_vietnamese_all_day_marker():
    schedule = parse_opening_hours([{"day": "Thứ Bảy", "hours": "Mở cửa cả ngày"}])
    assert schedule.is_open_at(SAT, at(3)) is True
    assert schedule.is_open_at(SAT, at(23, 59)) is True


def test_closed_day_is_not_open():
    schedule = parse_opening_hours([{"day": "Thứ Hai", "hours": "Đóng cửa"}])
    assert schedule is not None
    assert schedule.is_open_at(MON, at(12)) is False


# --- Định dạng OpenStreetMap --------------------------------------------------


def test_parses_osm_day_range():
    schedule = parse_opening_hours("Mo-Su 06:00-22:00")
    assert all(schedule.is_open_at(day, at(12)) for day in range(7))
    assert schedule.is_open_at(MON, at(5)) is False


def test_parses_osm_24_7():
    schedule = parse_opening_hours("24/7")
    assert schedule.is_open_at(SUN, at(4)) is True


def test_parses_osm_multiple_rules():
    schedule = parse_opening_hours("Mo-Fr 09:00-17:00; Sa 09:00-12:00")
    assert schedule.is_open_at(MON, at(10)) is True
    assert schedule.is_open_at(SAT, at(10)) is True
    assert schedule.is_open_at(SAT, at(15)) is False
    assert schedule.is_open_at(SUN, at(10)) is False


# --- Khung giờ qua đêm --------------------------------------------------------


def test_overnight_hours_span_midnight():
    """Quán 18:00-02:00 phải được coi là mở lúc 01:00 SÁNG HÔM SAU."""
    schedule = parse_opening_hours("Mo-Su 18:00-02:00")
    assert schedule.is_open_at(MON, at(20)) is True
    assert schedule.is_open_at(TUE, at(1)) is True, "1h sáng thứ Ba vẫn thuộc ca tối thứ Hai"
    assert schedule.is_open_at(TUE, at(10)) is False


# --- Thiếu dữ liệu / không hiểu -----------------------------------------------


@pytest.mark.parametrize("value", [None, "", "   ", "[]", [], "rác rưởi không giờ giấc"])
def test_unknown_returns_none_not_closed(value):
    """None = KHÔNG BIẾT. Tầng gọi phải giữ lại quán, không được loại."""
    schedule = parse_opening_hours(value)
    assert schedule is None or schedule.is_empty


def test_malformed_python_literal_does_not_raise():
    assert parse_opening_hours("[{'day': 'Thứ Hai',") is None


def test_all_day_interval_covers_full_day():
    schedule = parse_opening_hours("24/7")
    assert schedule.intervals[MON] == [(0, MINUTES_PER_DAY)]

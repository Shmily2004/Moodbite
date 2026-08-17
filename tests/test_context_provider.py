"""Test ADAPTER thời tiết `OpenMeteoContextProvider`.

VÌ SAO CÓ FILE NÀY: `test_use_cases.py` đã chứng minh use case sống sót khi ContextProvider
NÉM LỖI (`test_search_survives_broken_context_provider`). Nhưng chưa có test nào chứng minh
chính ADAPTER thật suy biến an toàn — tức là nó NUỐT lỗi mạng và trả ngữ cảnh trung lập
thay vì để lỗi thoát ra ngoài. Đó là hai chuyện khác nhau:

  - use case sống sót  = "nếu adapter ném lỗi thì use case vẫn chạy"
  - adapter suy biến   = "adapter KHÔNG BAO GIỜ ném lỗi ra ngoài ngay từ đầu"

CLAUDE.md mục 4 quy tắc 7: "Tín hiệu ngữ cảnh (thời tiết/giờ) hỏng KHÔNG được làm hỏng
lượt tìm kiếm. Trả ngữ cảnh trung lập là đủ."

Toàn bộ test ở đây KHÔNG gọi mạng thật — `requests.get` luôn bị monkeypatch. Test phải
chạy được cả khi máy không có Internet.
"""
from __future__ import annotations

import pytest

from src.domain.value_objects.context_signal import WeatherCondition
from src.domain.value_objects.location import Location
from src.infrastructure.adapters.open_meteo_context_provider import (
    ClockOnlyContextProvider,
    OpenMeteoContextProvider,
)

HANOI = Location(lat=21.0325, lng=105.8509)


class _FakeResponse:
    """Bản giả của `requests.Response`, chỉ đủ phần adapter thật sự dùng."""

    def __init__(self, payload, raise_for_status_exc: Exception | None = None):
        self._payload = payload
        self._exc = raise_for_status_exc

    def raise_for_status(self):
        if self._exc is not None:
            raise self._exc

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _patch_requests(monkeypatch, handler):
    """Thay `requests.get` bằng `handler`.

    Adapter gọi `import requests` BÊN TRONG hàm, nên phải vá thuộc tính của module
    trong sys.modules chứ không vá tên đã import sẵn ở đầu file.
    """
    import requests

    monkeypatch.setattr(requests, "get", handler)


# --------------------------------------------------------------------------
# Đường đi ĐÚNG: API trả dữ liệu hợp lệ
# --------------------------------------------------------------------------


def test_doc_duoc_thoi_tiet_khi_api_tra_dung(monkeypatch):
    _patch_requests(
        monkeypatch,
        lambda *a, **kw: _FakeResponse(
            {"current": {"weather_code": 0, "temperature_2m": 27.2}}
        ),
    )
    provider = OpenMeteoContextProvider(enable_weather=True)

    ctx = provider.get_context(HANOI)

    assert ctx.weather is WeatherCondition.CLEAR
    assert ctx.temperature_c == 27.2
    assert provider.last_error is None


# --------------------------------------------------------------------------
# SUY BIẾN AN TOÀN: mọi kiểu hỏng đều phải cho ra ngữ cảnh trung lập
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "hong,mo_ta",
    [
        (ConnectionError("mất mạng"), "mất kết nối"),
        (TimeoutError("quá hạn"), "API chậm quá timeout"),
        (ValueError("json hỏng"), "phản hồi không phải JSON"),
    ],
)
def test_loi_mang_thi_tra_ngu_canh_trung_lap(monkeypatch, hong, mo_ta):
    """Adapter phải NUỐT lỗi, không được để thoát ra ngoài. Xem CLAUDE.md mục 4 quy tắc 7."""

    def _no(*args, **kwargs):
        raise hong

    _patch_requests(monkeypatch, _no)
    provider = OpenMeteoContextProvider(enable_weather=True)

    ctx = provider.get_context(HANOI)  # KHÔNG được ném lỗi

    assert ctx.weather is WeatherCondition.UNKNOWN, mo_ta
    assert ctx.temperature_c is None, mo_ta
    assert provider.last_error is not None, "phải ghi lại lý do cho /health"


def test_http_500_cung_suy_bien(monkeypatch):
    _patch_requests(
        monkeypatch,
        lambda *a, **kw: _FakeResponse({}, raise_for_status_exc=OSError("HTTP 500")),
    )
    provider = OpenMeteoContextProvider(enable_weather=True)

    ctx = provider.get_context(HANOI)

    assert ctx.weather is WeatherCondition.UNKNOWN
    assert ctx.temperature_c is None


def test_payload_thieu_truong_khong_lam_no(monkeypatch):
    """API đổi định dạng / trả rỗng -> vẫn phải chạy, chỉ là không biết thời tiết."""
    _patch_requests(monkeypatch, lambda *a, **kw: _FakeResponse({}))
    provider = OpenMeteoContextProvider(enable_weather=True)

    ctx = provider.get_context(HANOI)

    assert ctx.weather is WeatherCondition.UNKNOWN
    assert ctx.temperature_c is None


def test_tin_hieu_GIO_van_dung_khi_thoi_tiet_hong(monkeypatch):
    """Điểm mấu chốt: giờ ăn và cuối tuần KHÔNG phụ thuộc mạng.

    Thời tiết hỏng chỉ được làm mất tín hiệu thời tiết, không được kéo theo tín hiệu giờ -
    vì giờ ăn mới là tín hiệu ngữ cảnh luôn bật (PROJECT_CHECKLIST: "giờ ăn luôn bật").
    """

    def _no(*args, **kwargs):
        raise ConnectionError("mất mạng")

    _patch_requests(monkeypatch, _no)

    hong = OpenMeteoContextProvider(enable_weather=True).get_context(HANOI)
    chi_dung_gio = ClockOnlyContextProvider().get_context(HANOI)

    assert hong.meal_time == chi_dung_gio.meal_time
    assert hong.is_weekend == chi_dung_gio.is_weekend
    assert hong.weekday == chi_dung_gio.weekday


def test_tat_thoi_tiet_thi_KHONG_goi_mang(monkeypatch):
    """`enable_weather=False` là mặc định khi chạy dev - phải không đụng tới mạng.

    ⚠️ ĐẾM số lần gọi, KHÔNG dùng `raise AssertionError` trong hàm giả. Bản đầu của test
    này làm thế và hoá ra VÔ DỤNG: adapter bắt `except Exception`, mà `AssertionError`
    cũng là `Exception`, nên nó nuốt luôn lời tố cáo của chính test. Mutation test
    (đổi `if self.enable_weather:` thành `if True:`) vẫn xanh -> phát hiện ra lỗ hổng này.
    """
    so_lan_goi = []

    _patch_requests(monkeypatch, lambda *a, **kw: so_lan_goi.append(1))
    provider = OpenMeteoContextProvider(enable_weather=False)

    ctx = provider.get_context(HANOI)

    assert so_lan_goi == [], "enable_weather=False mà vẫn gọi mạng"
    assert ctx.weather is WeatherCondition.UNKNOWN
    assert provider.status()["weather_enabled"] is False


def test_status_bao_loi_cho_health(monkeypatch):
    """/health phải nói được LÝ DO thời tiết hỏng, không im lặng."""

    def _no(*args, **kwargs):
        raise ConnectionError("DNS không phân giải được")

    _patch_requests(monkeypatch, _no)
    provider = OpenMeteoContextProvider(enable_weather=True)
    provider.get_context(HANOI)

    status = provider.status()
    assert status["weather_enabled"] is True
    assert "DNS" in status["error"]


# --------------------------------------------------------------------------
# Ánh xạ mã WMO -> nhóm thời tiết dùng cho xếp hạng
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code,mong_doi",
    [
        (0, WeatherCondition.CLEAR),     # trời quang
        (1, WeatherCondition.CLEAR),     # ít mây
        (2, WeatherCondition.CLOUDY),    # nhiều mây
        (3, WeatherCondition.CLOUDY),    # u ám
        (45, WeatherCondition.CLOUDY),   # sương mù
        (61, WeatherCondition.RAIN),     # mưa nhẹ
        (95, WeatherCondition.RAIN),     # dông
        (None, WeatherCondition.UNKNOWN),
    ],
)
def test_anh_xa_ma_wmo(code, mong_doi):
    assert OpenMeteoContextProvider._to_condition(code) is mong_doi

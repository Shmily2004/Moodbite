"""Bộ mẫu frontend phải được gom ở GIỜ CỐ ĐỊNH (2026-10-02).

Xếp hạng có thiên hướng theo bữa ăn đọc từ đồng hồ thật, nên trước đây tỉ lệ "thật" mà
`verify.py` mục 9 so với bộ mẫu đổi theo giờ chạy (rating 35,6% buổi chiều, 30,6% lúc 10h
sáng) -> phép kiểm đỏ/xanh tuỳ lúc chạy.
"""
import importlib.util
from pathlib import Path

import src.infrastructure.adapters.open_meteo_context_provider as mod
from src.infrastructure.adapters.open_meteo_context_provider import ClockOnlyContextProvider
from src.domain.value_objects.location import HANOI_CENTER_LAT, HANOI_CENTER_LNG, Location

_SPEC = importlib.util.spec_from_file_location(
    "make_fixture", Path(__file__).resolve().parent.parent / "scripts" / "make_fixture.py"
)
make_fixture = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(make_fixture)

TAM = Location(lat=HANOI_CENTER_LAT, lng=HANOI_CENTER_LNG)


def test_ngu_canh_khong_doi_theo_gio_chay_khi_gom_mau():
    with make_fixture.co_dinh_gio((12, 0)):
        trua = ClockOnlyContextProvider().get_context(TAM)
    with make_fixture.co_dinh_gio((12, 0)):
        lan_hai = ClockOnlyContextProvider().get_context(TAM)
    with make_fixture.co_dinh_gio((21, 0)):
        toi = ClockOnlyContextProvider().get_context(TAM)

    assert trua == lan_hai
    # Chứng minh việc cố định có tác dụng thật: giờ khác thì ngữ cảnh khác.
    assert trua != toi


def test_tra_lai_dong_ho_that_sau_khi_gom():
    goc = mod.datetime
    with make_fixture.co_dinh_gio():
        assert mod.datetime is not goc
    assert mod.datetime is goc


def test_ngu_canh_khong_doi_theo_NGAY_chay(monkeypatch):
    """BUG THẬT (2026-10-13): `co_dinh_gio` chỉ ghim GIỜ, giữ nguyên NGÀY. Xếp hạng có tín
    hiệu cuối tuần, nên bộ mẫu gom thứ Bảy (10/10, rating 35,6%) đo lại thứ Ba (13/10)
    thành 30,6% -> verify.py mục 9 đỏ chỉ vì hôm nay không phải thứ Bảy."""
    from datetime import datetime as that

    def gia_ngay(y, m, d):
        class _Ngay(that):
            @classmethod
            def now(cls, tz=None):
                return that(y, m, d, 15, 30, tzinfo=tz)
        return _Ngay

    monkeypatch.setattr(mod, "datetime", gia_ngay(2026, 10, 10))   # thứ Bảy
    with make_fixture.co_dinh_gio():
        thu_bay = ClockOnlyContextProvider().get_context(TAM)
    monkeypatch.setattr(mod, "datetime", gia_ngay(2026, 10, 13))   # thứ Ba
    with make_fixture.co_dinh_gio():
        thu_ba = ClockOnlyContextProvider().get_context(TAM)

    assert thu_bay == thu_ba

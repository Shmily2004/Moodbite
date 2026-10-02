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

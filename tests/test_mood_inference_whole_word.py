"""`infer_mood_weights` phải khớp TỪ NGUYÊN VẸN + "dấu là bằng chứng" (CLAUDE.md §4.5).

BUG THẬT (rà soát 2026-10-06): hàm so `normalize(kw) in normalized` — CHUỖI CON trên bản
ĐÃ BỎ DẤU. Tái hiện được:

    "quán phở ngon nhé"   -> mood "happy"   (vì "nhé" bỏ dấu = "nhe" = "nhẹ")
    "chỗ ngồi lâu"        -> có "excited"   (vì "lâu" bỏ dấu = "lau" = "lẩu")
    "Buôn Ma Thuột"       -> mood "sad"     (vì "buôn" bỏ dấu = "buon" = "buồn")
    "quán metro"          -> mood "sad"     (vì "metro" chứa chuỗi con "met" = "mệt")
"""
from __future__ import annotations

import pytest

from src.domain.services.text_relevance import infer_mood_weights
from src.domain.value_objects.mood import MOOD_PROFILES


def _mood_khop(cau):
    """Mood nào có MẶT trong trọng số trả về (so với bảng profile của từng mood)."""
    weights = infer_mood_weights(cau)
    if weights is None:
        return set()
    return {
        mood for mood, profile in MOOD_PROFILES.items()
        if mood in ("sad", "happy", "excited", "relaxed")
        and weights == pytest.approx(dict(profile))
    } or {"tron"}


@pytest.mark.parametrize(
    "cau",
    ["quán phở ngon nhé", "Buôn Ma Thuột", "quán metro", "món này ngon"],
)
def test_dong_am_sau_khi_bo_dau_KHONG_duoc_doan_mood(cau):
    assert infer_mood_weights(cau) is None


def test_ngoi_lau_la_relaxed_KHONG_phai_lau_cay():
    """"chỗ ngồi lâu" khớp "ngồi lâu" (relaxed) — KHÔNG được kéo theo "lẩu" (excited)."""
    assert _mood_khop("chỗ ngồi lâu") == {"relaxed"}


def test_tu_khoa_that_van_khop():
    assert _mood_khop("muốn ăn món nhẹ") == {"happy"}
    assert _mood_khop("đang buồn quá") == {"sad"}
    assert _mood_khop("đi ăn lẩu") == {"excited"}
    assert _mood_khop("hôm nay mệt") == {"sad"}


def test_nguoi_dung_go_KHONG_DAU_van_khop():
    """Quy tắc 'một vế không dấu thì bao dung' — người gõ 'lau' vẫn được hiểu."""
    assert _mood_khop("an lau cay") == {"excited"}

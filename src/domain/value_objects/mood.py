"""Mood và cách quy đổi mood -> điểm số. Đây là TRÁI TIM nghiệp vụ của MoodBite.

Thuần Python - KHÔNG import pandas/FastAPI. Muốn đổi cách chấm điểm mood thì sửa
DUY NHẤT ở file này.
"""
from __future__ import annotations

from typing import Dict, List

# Tên 5 cột mood-score do data_pipeline/feature_engineering.py sinh ra.
MOOD_SCORE_COLUMNS: tuple[str, ...] = (
    "comfort_cozy_score",
    "spicy_hot_score",
    "fresh_healthy_score",
    "cheap_budget_score",
    "quick_fast_score",
)

# Ánh xạ mood (cảm xúc người dùng) sang mood-score (đặc điểm món ăn).
#
# Đây là 2 bộ từ vựng khác nhau, nên ánh xạ là QUYẾT ĐỊNH SẢN PHẨM, không có đáp án
# "đúng tuyệt đối". Mỗi mood là TỔ HỢP CÓ TRỌNG SỐ của nhiều cột, không chỉ 1 cột.
#
# Lý do dùng tổ hợp (2 bug thật, đã đo trên dataset 4170 quán):
#   1. Trước đây "sad" và "relaxed" cùng trỏ vào comfort_cozy_score nên trả về DANH SÁCH
#      QUÁN GIỐNG HỆT NHAU - người dùng đổi mood mà kết quả không đổi.
#   2. cheap_budget_score và quick_fast_score được tính ra nhưng KHÔNG mood nào dùng tới
#      - 2/5 feature chết, phí công tính.
#
# Trọng số âm nghĩa là "trừ điểm". sad và relaxed cùng lấy comfort_cozy làm cột chính,
# nên phải có cột phụ đủ mạnh để tách ra. Chọn cheap_budget vì số liệu thật cho thấy:
#   - Trong nhóm comfort_cozy cao, quick_fast gần như bằng 0 (164/1774 quán) -> không tách được.
#   - cheap_budget trải rộng (0.0-0.73) và dày nhất (3977/4170 quán) -> tách được thật.
MOOD_PROFILES: Dict[str, Dict[str, float]] = {
    "happy":   {"fresh_healthy_score": 1.0, "quick_fast_score": 0.3},
    "sad":     {"comfort_cozy_score": 1.0, "cheap_budget_score": 0.5},
    "excited": {"spicy_hot_score": 1.0, "fresh_healthy_score": 0.2},
    "relaxed": {"comfort_cozy_score": 1.0, "cheap_budget_score": -0.5,
                "quick_fast_score": -0.5},
}

# Cột CHÍNH của mỗi mood (trọng số lớn nhất). Use-case gợi ý MÓN cần đúng 1 tên cột
# để xếp hạng quán trong từng nhóm món.
MOOD_TO_SCORE_COLUMN: Dict[str, str] = {
    mood: max(weights, key=weights.get) for mood, weights in MOOD_PROFILES.items()
}

# Tag mood_keywords cấp MÓN trong dish_knowledge_base.json - dùng để chọn món nào
# đáng đề xuất cho mood này. Giữ nhất quán Ý NGHĨA với MOOD_PROFILES ở trên.
MOOD_TO_DISH_KEYWORDS: Dict[str, List[str]] = {
    "happy": ["fresh", "sweet"],
    "sad": ["comfort", "cozy"],
    "excited": ["spicy"],
    "relaxed": ["comfort", "cozy"],
}

SUPPORTED_MOODS: tuple[str, ...] = tuple(MOOD_PROFILES.keys())


class UnsupportedMoodError(ValueError):
    """Mood client gửi lên không nằm trong SUPPORTED_MOODS."""

    def __init__(self, mood: str) -> None:
        super().__init__(
            f"Mood '{mood}' không được hỗ trợ. "
            f"Các mood hợp lệ: {list(SUPPORTED_MOODS)}"
        )
        self.mood = mood


def normalize_mood(mood: str) -> str:
    """Chuẩn hoá và kiểm tra mood. Raise UnsupportedMoodError nếu không hợp lệ."""
    key = (mood or "").strip().lower()
    if key not in MOOD_PROFILES:
        raise UnsupportedMoodError(mood)
    return key


def weights_for(mood: str) -> Dict[str, float]:
    """Trọng số các cột mood-score cho 1 mood đã chuẩn hoá."""
    return MOOD_PROFILES[normalize_mood(mood)]


def score_column_for(mood: str) -> str:
    """Cột mood-score CHÍNH của 1 mood."""
    return MOOD_TO_SCORE_COLUMN[normalize_mood(mood)]


def dish_keywords_for(mood: str) -> List[str]:
    """Các tag mood_keywords cấp món ứng với 1 mood."""
    return MOOD_TO_DISH_KEYWORDS[normalize_mood(mood)]

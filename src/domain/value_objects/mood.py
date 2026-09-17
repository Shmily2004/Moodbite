"""Mood và cách quy đổi mood -> điểm số. Đây là TRÁI TIM nghiệp vụ của MoodBite.

Thuần Python - KHÔNG import pandas/FastAPI. Muốn đổi cách chấm điểm mood thì sửa
DUY NHẤT ở file này.
"""
from __future__ import annotations

from typing import Dict

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

# Tag mood_keywords cấp MÓN có trong dữ liệu thật (dish_catalog.json, đo 2026-09-16).
DISH_MOOD_KEYWORDS = frozenset(
    {"comfort", "cozy", "quick", "cheap", "fresh", "sweet", "spicy"}
)

# ÁNH XẠ MOOD -> THUỘC TÍNH MÓN, có TRỌNG SỐ. Dùng ở `dish_ranking._score_mood`.
#
# THAY CHO `MOOD_TO_DISH_KEYWORDS` (mood -> danh sách tag, chấm NHỊ PHÂN). Bug thật
# 2026-09-16 khi gọi POST /dishes/suggest trên dữ liệu thật:
#   - "sad" và "relaxed" cùng trỏ vào ["comfort","cozy"] -> top-10 trùng 10/10 món.
#   - Món tag ['cozy','spicy'] (Đồ nhắm, Lẩu Thái) ăn TRỌN điểm cho cả sad lẫn excited,
#     nên "Đồ nhắm" đứng #1 cho CẢ BA mood sad/excited/relaxed; điểm top-5 chỉ lệch ở chữ
#     số thứ 4 (0.674 - 0.675) vì mọi món "khớp" đều được đúng 1.0.
#
# CÁCH MỚI: cộng trọng số của từng thuộc tính món CÓ THẬT trong danh mục (tag, nóng/lạnh,
# cách chế biến, độ cay, khẩu phần, bữa). KHÔNG bịa gì về món - chỉ quyết định thuộc tính
# nào hợp mood nào, cùng ý nghĩa với `MOOD_PROFILES` và `MOOD_KEYWORDS` (text_relevance):
#   sad     = ấm bụng, an ủi, rẻ   -> món nước nóng, comfort; cay xé lưỡi thì không an ủi.
#   excited = cay, lẩu, nướng      -> độ cay cao, đồ nướng; món không cay thì bị trừ.
#   happy   = tươi, nhẹ, healthy   -> fresh, gỏi/trộn, khẩu phần nhẹ; đồ chiên thì trừ.
#   relaxed = chill, ngồi lâu, cà phê -> đồ ngọt/đồ uống nhâm nhi, cozy; KHÔNG phải "rẻ,
#             nhanh" (đúng dấu âm của cheap/quick trong MOOD_PROFILES["relaxed"]).
#
# ⚠️ GIỚI HẠN ĐO ĐƯỢC: thuộc tính có cấu trúc chỉ có ở ĐÚNG 79/855 món (70/285 món đang
# bật) - và đó CHÍNH LÀ 79 món có mood_keywords (cả hai cùng đến từ dish_seed_manual.json).
# Nên ánh xạ này làm mood PHÂN BIỆT ĐƯỢC NHAU, nhưng KHÔNG nâng được độ phủ. Món không có
# thuộc tính nào vẫn nhận điểm trung tính. Muốn phủ rộng hơn phải nhập thêm thuộc tính món.
#
# Khoá thuộc tính: "kw:<tag>" · "temp:<hot|cold|room>" · "method:<Dish.cooking_method>" ·
# "meal:<Dish.meal_times>" · "portion:<light|small|regular|heavy>" ·
# "spice:none" (spice_level = 0) · "spice:hot" (spice_level >= 2).
# Có test khoá mọi giá trị phải thuộc bộ giá trị thật của entity Dish.
#
# Số trọng số chọn theo SỐ ĐO (POST /dishes/suggest, dữ liệu thật, bán kính 10km quanh
# trung tâm, ngữ cảnh cố định "bữa tối, 27°C"), mục tiêu: bốn mood ra top-5 khác nhau và
# món đầu bảng đúng tinh thần mood.
#   TRƯỚC: sad/relaxed trùng top-5 5/5; sad/excited 2/5; top-5 mọi mood điểm 0.724-0.725.
#     sad: Đồ nhắm · Gà rán · Lẩu Thái · Lẩu gà lá é · Nem nướng
#   SAU  : trùng top-5 lớn nhất 2/5 (excited/relaxed), sad/relaxed 0/5.
#     sad    : Phở bò · Phở gà · Ramen · Lẩu gà lá é · Lẩu nướng
#     excited: Chân gà nướng · Lẩu Thái · Thịt nướng vỉ · Hải sản nướng · Tom Yum
#     happy  : Sushi · Phở cuốn · Nem nướng · Phở gà · Ốc luộc
#     relaxed: Thịt nướng vỉ · Lẩu hải sản · Pizza hải sản · Đồ nhắm · Lẩu Thái
# Đã thử relaxed = {sweet .4, cozy .4, comfort .1, an_vat .2, quick -.1, cheap -.2}: bữa
# tối vẫn trùng sad 4/5 vì điểm giờ ăn (+0.2) lấn át -> thêm "portion:heavy" (lẩu/nướng
# ngồi lâu) và trừ "spice:hot" để không trùng excited.
MOOD_DISH_AFFINITY: Dict[str, Dict[str, float]] = {
    "sad": {
        "kw:comfort": 0.5, "kw:cozy": 0.2, "kw:cheap": 0.2,
        "temp:hot": 0.2, "method:nuoc": 0.3,
        "spice:hot": -0.3, "temp:cold": -0.2,
    },
    "excited": {
        "kw:spicy": 0.5, "spice:hot": 0.3, "method:nuong": 0.3,
        "kw:cozy": 0.1, "portion:heavy": 0.1,
        "spice:none": -0.2,
    },
    "happy": {
        "kw:fresh": 0.5, "kw:sweet": 0.3, "kw:quick": 0.1,
        "method:song": 0.3, "method:tron": 0.3,
        "portion:light": 0.2, "portion:small": 0.2, "temp:cold": 0.1,
        "portion:heavy": -0.2, "method:chien": -0.2,
    },
    "relaxed": {
        "kw:sweet": 0.4, "kw:cozy": 0.4, "meal:an_vat": 0.2, "portion:heavy": 0.2,
        "kw:quick": -0.2, "kw:cheap": -0.2, "spice:hot": -0.2,
    },
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


# ⚠️ ĐÃ XOÁ `score_column_for()` và `dish_keywords_for()` ngày 2026-08-25.
# Cả hai là wrapper một dòng quanh hai dict ngay phía trên và KHÔNG chỗ nào gọi. Nơi cần
# thì đọc thẳng dict, nên giữ lại chỉ tạo hai đường làm cùng một việc.
# ⚠️ ĐÃ THAY `MOOD_TO_DISH_KEYWORDS` bằng `MOOD_DISH_AFFINITY` ngày 2026-09-16 (xem trên).

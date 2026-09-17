"""Chân dung người dùng giả lập + ĐỘ HỢP (utility) — "sự thật mặt đất" cho đánh giá.

⚠️ VÌ SAO UTILITY PHẢI ĐỘC LẬP VỚI CÔNG THỨC XẾP HẠNG CỦA MOODBITE
Nếu người dùng giả "thích" quán theo đúng công thức `search_ranking.py` thì đánh giá sẽ
luôn nói MoodBite xếp hạng tuyệt vời — ta chỉ đang đo công thức với chính nó (vòng tròn).
Vì vậy file này:
  * KHÔNG import bất cứ gì trong `src/domain/services/` hay `src/application/`
    (có test khoá: `tests/test_gia_lap_nguoi_dung.py`);
  * KHÔNG đọc `predicted_score`, `rank_position`, `match_source`, `experience_cluster_*`,
    `is_famous` — những trường là ĐẦU RA của mô hình MoodBite;
  * chỉ dùng thuộc tính "vật lý" của quán mà một người thật cũng nhìn thấy: khoảng cách,
    tên/loại quán, rating (CHỈ khi có), chuỗi giá (CHỈ khi có).

Chỉ import `text.py` (tiện ích bỏ dấu/khớp từ) vì CLAUDE.md mục 4.5 bắt buộc so khớp tiếng
Việt phải đi qua đó — tự viết lại là lặp lại đúng ba bug phở/phố/phớ đã xảy ra.

GIỚI HẠN PHẢI NÓI RÕ: người thật cũng quan tâm khoảng cách và rating, MoodBite cũng vậy,
nên hai bên VẪN tương quan một phần. Đó là tương quan có thật ngoài đời, không phải vòng
tròn — nhưng cũng có nghĩa baseline "chỉ khoảng cách" sẽ là đối thủ khó.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import asdict, dataclass
from typing import Optional, Sequence

from src.domain.value_objects.text import contains_phrase

# Khẩu vị -> từ khoá tìm trong tên/loại quán/tên món. Có dấu để phân biệt phở/phố.
TASTE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "pho": ("phở",),
    "bun": ("bún", "bún chả", "bún bò"),
    "com": ("cơm", "cơm tấm", "cơm rang"),
    "banh_mi": ("bánh mì",),
    "lau": ("lẩu",),
    "nuong": ("nướng", "bbq"),
    "hai_san": ("hải sản", "ốc", "cua"),
    "ca_phe": ("cà phê", "cafe", "coffee"),
    "tra_sua": ("trà sữa",),
    "chay": ("chay", "vegetarian"),
    "an_nhanh": ("gà rán", "pizza", "burger"),
    "nhat_han": ("sushi", "ramen", "kimbap", "hàn quốc", "nhật bản"),
}

# Câu tìm kiếm tự nhiên theo khẩu vị. Viết như người Hà Nội gõ, có cả câu không dấu.
QUERY_TEMPLATES: dict[str, tuple[str, ...]] = {
    "pho": ("phở bò gần đây", "pho ngon buoi sang", "quán phở gà"),
    "bun": ("bún chả ngon", "bún bò huế", "bun rieu cua"),
    "com": ("cơm văn phòng rẻ", "cơm tấm sườn", "com rang dua bo"),
    "banh_mi": ("bánh mì pate", "banh mi nhanh gon"),
    "lau": ("quán lẩu ấm cúng cho nhóm bạn", "lẩu thái chua cay"),
    "nuong": ("đồ nướng tối nay", "quán nướng bbq"),
    "hai_san": ("hải sản tươi", "ốc luộc vỉa hè"),
    "ca_phe": ("cà phê yên tĩnh làm việc", "cafe view dep"),
    "tra_sua": ("trà sữa trân châu", "tra sua ngon"),
    "chay": ("quán chay thanh đạm", "đồ chay healthy"),
    "an_nhanh": ("gà rán giòn", "pizza giao nhanh"),
    "nhat_han": ("sushi ngon", "mì ramen nóng", "đồ hàn quốc"),
}

# Bán kính sẵn sàng đi (km) và tỷ lệ người chọn. GIẢ ĐỊNH, không đo: đa số người đi ăn
# trong 2-3km, số ít chịu đi xa. Đổi phân bố này sẽ đổi mức "khó" của baseline khoảng cách.
TRAVEL_KM_CHOICES = (1.5, 2.0, 3.0, 5.0, 8.0)
TRAVEL_KM_WEIGHTS = (0.15, 0.25, 0.30, 0.20, 0.10)
# Số phiên kỳ vọng / ngày theo mức hoạt động (ít / vừa / nhiều). Giả định.
ACTIVITY_LEVELS = (0.15, 0.4, 0.9)
ACTIVITY_WEIGHTS = (0.5, 0.35, 0.15)
# Độ lệch nhà quanh tâm phường: ~0.006 độ ≈ 650m — đủ để hai người cùng phường không
# đứng trùng một điểm, nhưng vẫn ở trong phường.
HOME_JITTER_DEG = 0.006

# Trọng số của utility, tổng = 1. Thiếu rating thì phần chất lượng lấy TRUNG LẬP 0.5
# (người dùng không BIẾT quán dở hay hay — không phải "quán 0 sao", CLAUDE.md mục 4.1).
# Bản đầu chia lại trọng số cho phần còn lại: 90% quán không có rating nên khẩu vị bị
# phóng lên 56% và gần như mọi ứng viên đạt nhãn >= 2 — đánh giá mất khả năng phân biệt.
W_DISTANCE, W_TASTE, W_QUALITY = 0.35, 0.45, 0.20
NEUTRAL_QUALITY = 0.5
PRICE_EFFECT = 0.10   # ± tối đa do giá, nhân với độ nhạy giá
NOISE_EFFECT = 0.10   # ± sở thích cá nhân khó giải thích, cố định theo (người, quán)


@dataclass(frozen=True)
class Persona:
    username: str
    home_ward: str
    home_lat: float
    home_lng: float
    preferred_moods: tuple[str, ...]
    taste_tags: tuple[str, ...]
    budget_sensitivity: float
    max_travel_km: float
    activity_per_day: float

    def to_dict(self) -> dict:
        return asdict(self)


def sample_persona(
    rng: random.Random, index: int, ward_centers: Sequence[dict], moods: Sequence[str]
) -> Persona:
    """Rút ngẫu nhiên (có seed) một chân dung. `ward_centers` lấy từ DATASET, không hardcode."""
    ward = rng.choices(ward_centers, weights=[w["count"] for w in ward_centers])[0]
    return Persona(
        username=f"demo_{index:04d}",
        home_ward=ward["ward"],
        home_lat=round(ward["lat"] + rng.gauss(0, HOME_JITTER_DEG), 6),
        home_lng=round(ward["lng"] + rng.gauss(0, HOME_JITTER_DEG), 6),
        preferred_moods=tuple(rng.sample(list(moods), k=min(2, len(moods)))),
        taste_tags=tuple(rng.sample(sorted(TASTE_KEYWORDS), k=rng.choice((2, 3, 4)))),
        budget_sensitivity=round(rng.random(), 3),
        max_travel_km=rng.choices(TRAVEL_KM_CHOICES, weights=TRAVEL_KM_WEIGHTS)[0],
        activity_per_day=rng.choices(ACTIVITY_LEVELS, weights=ACTIVITY_WEIGHTS)[0],
    )


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _personal_noise(username: str, item_id: str) -> float:
    """Số trong [-1, 1] cố định cho mỗi cặp (người, quán). Băm thay vì random để chạy lại
    ra cùng kết quả và để cùng một người gặp lại quán cũ thì vẫn thích y như lần trước."""
    digest = hashlib.sha256(f"{username}|{item_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF * 2 - 1


def taste_match(persona: Persona, *texts: Optional[str]) -> bool:
    haystack = " | ".join(t for t in texts if t)
    return any(
        contains_phrase(haystack, kw)
        for tag in persona.taste_tags
        for kw in TASTE_KEYWORDS[tag]
    )


def price_affordability(price: Optional[str]) -> Optional[float]:
    """Chuỗi giá -> mức dễ chi trả [0,1]. `None` = không có dữ liệu giá (không đoán).

    Giá là CHUỖI (CLAUDE.md mục 4.2): "1-100.000 ₫", "100-200 N ₫", "Trên 1 Tr ₫", "70 US$".
    """
    if not price:
        return None
    p = price.lower()
    if "tr" in p or "us$" in p:
        return 0.0
    if p.startswith("1-100") or p.startswith("1–100"):
        return 1.0
    return 0.5


def restaurant_utility(persona: Persona, item: dict) -> float:
    """Độ hợp [0,1] của một quán (dict đúng `SearchResultItemSchema`) với chân dung."""
    distance_km = (item.get("distance_m") or 0) / 1000
    # BÌNH PHƯƠNG phần còn lại của quãng đường: bản tuyến tính cho quán cách 500m và quán
    # cách 100m gần như cùng điểm với người chịu đi 8km -> nhãn bão hoà, mọi cách xếp đều
    # "tốt". Đo ở lần chạy thử 5 người: 80% ứng viên đạt nhãn >= 2, không phân biệt được gì.
    parts = [(W_DISTANCE, _clamp(1 - distance_km / persona.max_travel_km) ** 2)]
    dish = item.get("suggested_dish") or {}
    taste = taste_match(persona, item.get("name"), item.get("category"), dish.get("name"))
    parts.append((W_TASTE, 1.0 if taste else 0.0))
    rating = item.get("rating")
    quality = NEUTRAL_QUALITY if rating is None else _clamp((float(rating) - 3.0) / 2.0)
    parts.append((W_QUALITY, quality))
    score = sum(w * v for w, v in parts)

    affordability = price_affordability(item.get("price_range"))
    if affordability is not None:
        score += PRICE_EFFECT * persona.budget_sensitivity * (affordability - 0.5) * 2
    score += NOISE_EFFECT * _personal_noise(persona.username, str(item.get("restaurant_id")))
    return round(_clamp(score), 4)


def dish_utility(persona: Persona, dish: dict) -> float:
    """Độ hợp [0,1] của một MÓN: đúng khẩu vị + có quán trong tầm đi."""
    taste = 1.0 if taste_match(persona, dish.get("name"), dish.get("cuisine")) else 0.0
    nearest = dish.get("nearest_restaurant_km")
    reach = 0.5 if nearest is None else _clamp(1 - nearest / persona.max_travel_km)
    score = 0.65 * taste + 0.35 * reach
    score += NOISE_EFFECT * _personal_noise(persona.username, f"dish:{dish.get('dish_id')}")
    return round(_clamp(score), 4)


# Ngưỡng chia utility thành nhãn phân cấp 0-3 cho NDCG. Quán "liên quan" (P@K, MRR) là
# nhãn >= RELEVANT_GRADE. Chọn sao cho quán vừa đúng khẩu vị vừa trong tầm đi mới đạt 2.
GRADE_THRESHOLDS = (0.50, 0.70, 0.85)
RELEVANT_GRADE = 2


def relevance_grade(utility: float) -> int:
    return sum(1 for t in GRADE_THRESHOLDS if utility >= t)


def natural_query(rng: random.Random, persona: Persona) -> str:
    return rng.choice(QUERY_TEMPLATES[rng.choice(persona.taste_tags)])

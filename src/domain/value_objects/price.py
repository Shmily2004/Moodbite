"""Khoảng giá - phân tích chuỗi giá của Google Maps thành mức giá so sánh được.

Thuần Python - KHÔNG import pandas/sklearn/fastapi.

VÌ SAO CẦN: Google Maps trả giá dưới dạng CHUỖI người đọc, nhiều định dạng khác nhau:
    "1-100.000 ₫"   "100-200 N ₫"   "Trên 1 Tr ₫"   "70 US$"
Không so sánh hay phân cụm được nếu để nguyên chuỗi. Nhưng cũng KHÔNG được ép về một
con số giả vờ chính xác - đây là KHOẢNG giá, không phải giá cụ thể.

Giải pháp: quy về 4 MỨC (price level 1-4) giống quy ước của Google Places, kèm giá trị
đại diện bằng VND để phân cụm.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Tỷ giá quy đổi thô, chỉ để XẾP MỨC chứ không phải để tính tiền.
# Vài quán ghi giá bằng USD; không quy đổi thì chúng rơi nhầm vào mức rẻ nhất.
USD_TO_VND = 25_000

# Ngưỡng chia mức (VND, cho một người). Chọn theo mặt bằng giá Hà Nội.
LEVEL_THRESHOLDS = (
    (100_000, 1),    # ≤100k  - bình dân
    (300_000, 2),    # ≤300k  - trung bình
    (700_000, 3),    # ≤700k  - khá cao
)
MAX_LEVEL = 4        # trên 700k - cao cấp

_NUMBER = re.compile(r"(\d+(?:[.,]\d+)*)")


@dataclass(frozen=True)
class PriceRange:
    """Khoảng giá đã chuẩn hoá.

    `level` 1-4 dùng để lọc và phân cụm; `raw` giữ nguyên chuỗi gốc để hiển thị -
    KHÔNG bao giờ hiện `level` cho người dùng, vì nó là suy luận của hệ thống.
    """

    raw: str
    level: int
    approx_vnd: Optional[int] = None

    @property
    def label(self) -> str:
        return {1: "Bình dân", 2: "Trung bình", 3: "Khá cao", 4: "Cao cấp"}[self.level]


def _to_vnd(number_text: str, unit_hint: str) -> Optional[float]:
    """Một con số + đơn vị đi kèm -> VND."""
    cleaned = number_text.replace(".", "").replace(",", "")
    if not cleaned.isdigit():
        return None
    value = float(cleaned)

    if "us$" in unit_hint or "usd" in unit_hint or "$" in unit_hint:
        return value * USD_TO_VND
    # "N" = nghìn, "Tr" = triệu (cách Google viết tắt trong giao diện tiếng Việt).
    if re.search(r"\btr\b|triệu", unit_hint):
        return value * 1_000_000
    if re.search(r"\bn\b|nghìn|k\b", unit_hint):
        return value * 1_000
    return value


def parse_price(raw: Optional[str]) -> Optional[PriceRange]:
    """Chuỗi giá bất kỳ -> PriceRange. Không hiểu được thì trả None.

    None nghĩa là KHÔNG BIẾT, không phải "miễn phí" - tầng gọi phải giữ nguyên quy ước
    này (xem `domain/entities/restaurant.py`).
    """
    if not raw or not isinstance(raw, str):
        return None

    text = raw.replace("\xa0", " ").strip()
    lowered = text.lower()
    numbers = _NUMBER.findall(text)
    if not numbers:
        return None

    values = [v for v in (_to_vnd(n, lowered) for n in numbers) if v is not None]
    if not values:
        return None

    # "100-200 N ₫" -> lấy trung điểm; "Trên 1 Tr ₫" -> lấy chính con số đó.
    midpoint = sum(values) / len(values)

    level = MAX_LEVEL
    for threshold, candidate in LEVEL_THRESHOLDS:
        if midpoint <= threshold:
            level = candidate
            break

    return PriceRange(raw=text, level=level, approx_vnd=int(midpoint))


def has_known_price(raw: Optional[str]) -> bool:
    """Quán này có GHI GIÁ đọc được không?

    Dùng cho bộ lọc "chỉ hiện quán có ghi giá". Định nghĩa CỐ Ý khắt khe: phải
    `parse_price` ra được một mức, không chỉ là "ô giá khác rỗng". Lý do: ô giá có thể
    chứa chữ không mang con số nào, và hiện một quán như thế cho người đang lọc theo giá
    là không giữ lời hứa của chính bộ lọc.

    `None`/rỗng -> False, đúng quy ước "None là CHƯA CÓ DỮ LIỆU" (CLAUDE.md mục 4 quy tắc
    1). Chú ý: False ở đây nghĩa là "ta KHÔNG BIẾT giá", KHÔNG phải "quán này không có
    giá" - nên bộ lọc phải nói rõ là nó đang lọc theo thứ ta biết, không phải theo thực tế.
    """
    return parse_price(raw) is not None

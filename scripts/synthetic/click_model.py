"""Mô hình BẤM của người dùng giả lập: thiên lệch vị trí x độ hợp.

Dạng "examination hypothesis" (Richardson 2007, Joachims 2017): người dùng chỉ bấm vào
thứ họ ĐÃ NHÌN, và xác suất nhìn giảm dần theo thứ hạng — kể cả khi quán ở dưới hay hơn.

    P(bấm ở hạng r) = P(nhìn | r) x P(hấp dẫn | utility)

VÌ SAO QUAN TRỌNG: nếu người giả lập bấm theo đúng utility mà không có thiên lệch vị trí,
dữ liệu tương tác sinh ra sẽ "đẹp" hơn thật và mọi mô hình học từ nó đều bị thổi phồng.
Mọi hằng số dưới đây là GIẢ ĐỊNH hợp lý, KHÔNG đo từ người dùng thật (chưa có dữ liệu đó).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional, Sequence

# P(nhìn | r) = 1 / r^EXAMINATION_DECAY. Hạng 1 chắc chắn được nhìn, hạng 10 còn ~16%.
EXAMINATION_DECAY = 0.8
# Chỉ 10 quán đầu hiện trên màn hình (một lần cuộn điện thoại).
SHOWN_TOP_K = 10
# Bấm tối đa 3 quán / phiên — người thật hiếm khi mở hơn thế trước khi quyết.
MAX_CLICKS_PER_SESSION = 3
# Ngay cả quán không hợp cũng có ~3% bị bấm nhầm/tò mò: nhiễu này có thật.
BASE_ATTRACTION = 0.03


def examination_probability(rank: int) -> float:
    return 1.0 / (rank ** EXAMINATION_DECAY)


def attraction_probability(utility: float) -> float:
    # Bình phương: quán "tàm tạm" (0.5) chỉ hấp dẫn ~25%, quán rất hợp (0.9) ~80%.
    return BASE_ATTRACTION + (1 - BASE_ATTRACTION) * utility ** 2


def simulate_clicks(rng: random.Random, utilities: Sequence[float]) -> list[int]:
    """Trả CHỈ SỐ (0-based) các mục được bấm trong danh sách đã hiển thị."""
    clicked = []
    for index, utility in enumerate(utilities[:SHOWN_TOP_K]):
        p = examination_probability(index + 1) * attraction_probability(utility)
        if rng.random() < p:
            clicked.append(index)
            if len(clicked) >= MAX_CLICKS_PER_SESSION:
                break
    return clicked


@dataclass(frozen=True)
class Reaction:
    action_type: str
    dwell_time_ms: Optional[int] = None


def reactions_after_click(rng: random.Random, utility: float) -> list[Reaction]:
    """Chuỗi hành động sau khi mở chi tiết một quán.

    Thời gian xem theo log-normal (đuôi dài như dữ liệu dwell thật): quán hợp xem lâu,
    quán không hợp thoát nhanh — nhiều lần dưới ngưỡng 3 giây của server, tức nhãn âm.
    """
    # Trung vị 0.5s (không hợp) -> 2s (u=0.5) -> 9s (u=0.9) -> 12.5s (rất hợp); độ lệch 1.0
    # để quán "tàm tạm" vẫn hay bị thoát trước 3 giây. Bản đầu (tuyến tính, lệch 0.6) cho
    # 96-100% tín hiệu dương ở lần chạy thử — không giống log hành vi thật nào.
    median_ms = 500 + 12000 * utility ** 3
    dwell = int(rng.lognormvariate(math.log(median_ms), 1.0))
    out = [Reaction("view_detail", dwell)]
    if utility >= 0.6 and rng.random() < utility * 0.6:
        out.append(Reaction("get_directions"))
    if utility >= 0.7 and rng.random() < 0.25:
        out.append(Reaction("save"))
    if utility >= 0.75 and rng.random() < 0.15:
        out.append(Reaction("explicit_positive"))
    if utility < 0.3 and rng.random() < 0.2:
        out.append(Reaction("explicit_negative"))
    return out


def choose_one(rng: random.Random, utilities: Sequence[float]) -> Optional[int]:
    """Chọn MỘT mục (VD một món ở trang chủ) theo cùng mô hình; không chọn gì = bỏ về."""
    clicks = simulate_clicks(rng, utilities)
    return clicks[0] if clicks else None

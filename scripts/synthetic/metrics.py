"""Độ đo xếp hạng — thuần Python, test được bằng ví dụ tính tay.

Quy ước: đầu vào là danh sách NHÃN theo đúng thứ tự đã xếp (phần tử 0 = hạng 1).
"""
from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence


def dcg_at_k(gains: Sequence[float], k: int) -> float:
    """DCG dạng mũ (2^g - 1) / log2(i + 2): thưởng mạnh cho nhãn cao ở hạng đầu."""
    return sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(gains[:k]))


def ndcg_at_k(ranked_gains: Sequence[float], k: int) -> Optional[float]:
    """NDCG@k. Trả `None` khi cả danh sách không có mục nào liên quan.

    VÌ SAO None CHỨ KHÔNG 0 hay 1: phiên không có quán nào hợp thì MỌI cách xếp đều như
    nhau. Tính là 0 sẽ phạt oan mô hình, tính là 1 sẽ thưởng oan — nên loại khỏi trung bình
    và báo số phiên bị loại.
    """
    ideal = dcg_at_k(sorted(ranked_gains, reverse=True), k)
    if ideal == 0:
        return None
    return dcg_at_k(ranked_gains, k) / ideal


def precision_at_k(ranked_relevant: Sequence[bool], k: int) -> float:
    """Tỷ lệ mục liên quan trong k hạng đầu. Mẫu số LUÔN là k (danh sách ngắn hơn k bị
    tính thiếu) — đúng định nghĩa chuẩn, để hai hệ trả số kết quả khác nhau vẫn so được."""
    return sum(1 for r in ranked_relevant[:k] if r) / k


def reciprocal_rank(ranked_relevant: Sequence[bool]) -> float:
    for i, r in enumerate(ranked_relevant):
        if r:
            return 1.0 / (i + 1)
    return 0.0


def catalog_coverage(top_lists: Iterable[Sequence[str]], universe: Iterable[str]) -> float:
    """Tỷ lệ quán (trong tập ứng viên) từng xuất hiện ở top — đo độ ĐA DẠNG.

    Mô hình luôn đẩy cùng vài quán nổi tiếng lên đầu sẽ có coverage thấp dù NDCG cao.
    """
    universe_set = set(universe)
    if not universe_set:
        return 0.0
    shown = {rid for lst in top_lists for rid in lst} & universe_set
    return len(shown) / len(universe_set)


def mean(values: Iterable[Optional[float]]) -> Optional[float]:
    kept = [v for v in values if v is not None]
    return sum(kept) / len(kept) if kept else None

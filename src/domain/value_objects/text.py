"""Tiện ích XỬ LÝ VĂN BẢN tiếng Việt, dùng chung cho mọi chỗ cần so khớp chữ.

Thuần Python, không phụ thuộc gì khác trong dự án - đây là tầng thấp nhất, để cả entity
(dish.py) lẫn service (text_relevance.py) đều import được mà không tạo vòng phụ thuộc.

HAI QUY TẮC ĐÃ TRẢ GIÁ ĐỂ HỌC:

1. BỎ DẤU khi so khớp. Người dùng gõ "pho bo", tên quán ghi "Phở Bò" - không bỏ dấu thì
   không bao giờ khớp. Đo trên dataset: rất nhiều quán tự đặt tên không dấu ("Pho Bo",
   "O Bun Cha", "Banh mi long hoi").

2. So khớp theo TỪ NGUYÊN VẸN, không phải chuỗi con. Sau khi bỏ dấu, "ốc" thành "oc" -
   nếu dùng `"oc" in text` thì khớp luôn "Ngọc", "Học", "Cốc"... Bug này vừa có thật ở
   tìm kiếm ("bo" khớp "bột"), đừng lặp lại ở chỗ khác.
"""
from __future__ import annotations

import re
import unicodedata
from typing import List, Optional


def normalize(text: Optional[str]) -> str:
    """Bỏ dấu + hạ chữ thường. 'Phở Bò' -> 'pho bo'."""
    if not text:
        return ""
    lowered = str(text).lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    # đ/Đ không tách được bằng NFD nên phải xử lý riêng.
    return stripped.replace("đ", "d")


def tokenize(text: Optional[str], min_length: int = 2) -> List[str]:
    """Tách thành các từ đã bỏ dấu.

    `min_length=2` (mặc định) dùng cho CÂU TÌM KIẾM của người dùng: bỏ từ 1 ký tự để
    tránh nhiễu.

    `min_length=1` BẮT BUỘC dùng khi so khớp từ khoá rule. Tiếng Việt có từ 1 ký tự mang
    nghĩa đầy đủ ("ý" = nước Ý, "gà", "mì"). Bug thật đã xảy ra: bộ lọc mặc định nuốt mất
    "ý" khiến rule "nhà hàng ý" (đồ Ý) rút gọn thành "nhà hàng" và khớp MỌI quán -> nhà
    hàng Nhật/Quảng Đông đều bị gợi ý "Mì Ý sốt bò bằm".
    """
    return [
        w for w in re.findall(r"[a-z0-9]+", normalize(text)) if len(w) >= min_length
    ]


def contains_phrase(haystack: Optional[str], needle: Optional[str]) -> bool:
    """`needle` có xuất hiện trong `haystack` dưới dạng CỤM TỪ NGUYÊN VẸN không.

    Khớp theo ranh giới từ, nên "oc" KHÔNG khớp "ngoc", nhưng "bun cha" vẫn khớp
    "quan bun cha ngon".

    Giữ nguyên từ 1 ký tự ở CẢ HAI phía - xem giải thích ở `tokenize`.
    """
    haystack_tokens = tokenize(haystack, min_length=1)
    needle_tokens = tokenize(needle, min_length=1)
    if not haystack_tokens or not needle_tokens:
        return False

    span = len(needle_tokens)
    return any(
        haystack_tokens[i : i + span] == needle_tokens
        for i in range(len(haystack_tokens) - span + 1)
    )

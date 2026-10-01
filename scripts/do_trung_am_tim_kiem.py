"""Đo: tìm bằng câu tự do (`POST /search`) có trả quán TRÙNG ÂM SAU KHI BỎ DẤU không.

VÍ DỤ LỖI: tìm "phở" ra "Nhà Hàng Phố Cổ", "Gà Phố". Hai từ "phở" và "phố" đều CÓ DẤU mà
dấu khác nhau -> theo CLAUDE.md §4.5 ("dấu là bằng chứng") thì KHÔNG được khớp.

Một kết quả bị tính là "trùng âm" khi: tên quán có một từ CÓ DẤU, bỏ dấu thì trùng một từ
CÓ DẤU trong câu tìm kiếm nhưng dấu khác, và tên quán KHÔNG chứa đúng từ đó. Chỉ xét
TÊN quán vì đó là thứ người dùng nhìn thấy trên thẻ.

Chạy:
    python scripts/do_trung_am_tim_kiem.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.application.use_cases.search_restaurants import SearchQuery  # noqa: E402
from src.domain.value_objects.text import tokenize_pairs, tokens_match  # noqa: E402
from src.presentation.api.dependencies import build_container  # noqa: E402

# Các cặp đụng độ đã biết, ghi trong CLAUDE.md §4.5.
TRUY_VAN = ["phở", "phở bò", "phở gà", "cơm", "cơm tấm", "cháo", "cháo sườn", "chè"]
SO_KET_QUA = 20


def la_trung_am(ten_quan: str, cau: str) -> bool:
    tu_cau = [t for t in tokenize_pairs(cau) if t[0] != t[1]]
    tu_ten = tokenize_pairs(ten_quan)
    co_dung = any(tokens_match(h, n) for h in tu_ten for n in tu_cau)
    co_sai = any(
        h[0] == n[0] and h[0] != h[1] and not tokens_match(h, n)
        for h in tu_ten for n in tu_cau
    )
    return co_sai and not co_dung


def main() -> None:
    logging.disable(logging.CRITICAL)
    container = build_container()
    uc = container.search_restaurants
    tong = 0
    print(f"{'truy vấn':<12} {'trùng âm/top':>13}   ví dụ")
    for cau in TRUY_VAN:
        kq = uc.execute(SearchQuery(session_id="do", query_text=cau, limit=SO_KET_QUA))
        sai = [r.name for r in kq.results if la_trung_am(r.name, cau)]
        tong += len(sai)
        print(f"{cau:<12} {len(sai):>6}/{len(kq.results):<6}   {', '.join(sai[:3])}")
    print(f"TỔNG: {tong} kết quả trùng âm trong top-{SO_KET_QUA} của {len(TRUY_VAN)} truy vấn")


if __name__ == "__main__":
    main()

"""Mở kết nối SQLite cho MỘT lần dùng: một giao dịch rồi ĐÓNG. Dùng chung cho mọi repository.

⚠️ `with sqlite3.connect(...) as conn:` KHÔNG đóng kết nối - context manager của
`sqlite3.Connection` chỉ commit (thành công) hoặc rollback (có lỗi). Đây là hiểu lầm rất
phổ biến. Đo ngày 2026-10-02: cả bộ test in ~30.000 `ResourceWarning: unclosed database`,
và trên Windows file `.db` bị giữ handle tới lúc bộ gom rác chạy - chặn xoá/thay file CSDL
(`scripts/build_sqlite.py` dựng lại kho quán), làm hỏng ngẫu nhiên việc dọn thư mục tạm.

Hàm này giữ NGUYÊN ngữ nghĩa giao dịch cũ (thành công -> commit, lỗi -> rollback) và
thêm bước đóng. Thay `with sqlite3.connect(X) as conn:` bằng `with mo_ket_noi(X) as conn:`
là đủ, không phải sửa thân khối lệnh. Có test khoá: `tests/test_dong_ket_noi_sqlite.py`.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator


@contextmanager
def mo_ket_noi(*args: Any, **kwargs: Any) -> Iterator[sqlite3.Connection]:
    """Nhận đúng tham số của `sqlite3.connect` (đường dẫn, `uri=True`, `timeout`...)."""
    conn = sqlite3.connect(*args, **kwargs)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


__all__ = ["mo_ket_noi"]

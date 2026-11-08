"""ADAPTER: lưu bản SỬA TAY mô tả món vào SQLite.

DÙNG CHUNG FILE với `moodbite_users.db` (cùng lý do với nhật ký quản trị): đây là dữ liệu do
người quản trị nhập, không sinh lại được. `build_sqlite.py` dựng lại `moodbite.db` mà không
được làm mất chữ đã sửa.

Đọc ở chế độ `mode=ro` và chỉ khi file tồn tại, để gõ nhầm đường dẫn không tạo file rỗng.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from src.infrastructure.config.settings import describe_path
from src.infrastructure.repositories.sqlite_ket_noi import mo_ket_noi

logger = logging.getLogger("moodbite.repository")

SCHEMA = """
CREATE TABLE IF NOT EXISTS dish_overrides (
    dish_id     TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    updated_by  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""


class SqliteDishOverrideRepository:
    """Triển khai `DishOverrideRepository`."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with mo_ket_noi(self.db_path) as conn:
                conn.executescript(SCHEMA)
        except (sqlite3.Error, OSError) as exc:
            # Không mở được thì đọc trả rỗng (món hiện mô tả gốc) và ghi báo lỗi 503 ở router.
            logger.error("Không mở được bảng sửa món %s: %s", describe_path(self.db_path), exc)

    def all_descriptions(self) -> Dict[str, str]:
        if not self.db_path.exists():
            return {}
        try:
            with mo_ket_noi(f"file:{self.db_path.as_posix()}?mode=ro", uri=True) as conn:
                rows = conn.execute("SELECT dish_id, description FROM dish_overrides").fetchall()
        except sqlite3.Error as exc:
            logger.error("Không đọc được bản sửa món: %s", exc)
            return {}
        return {dish_id: text for dish_id, text in rows}

    def get_description(self, dish_id: str) -> Optional[str]:
        return self.all_descriptions().get(dish_id)

    def set_description(self, dish_id: str, text: str, actor: str) -> None:
        with mo_ket_noi(self.db_path) as conn:
            conn.execute(
                "INSERT INTO dish_overrides (dish_id, description, updated_by, updated_at) "
                "VALUES (?, ?, ?, ?) ON CONFLICT(dish_id) DO UPDATE SET "
                "description=excluded.description, updated_by=excluded.updated_by, "
                "updated_at=excluded.updated_at",
                (dish_id, text, actor, datetime.now(timezone.utc).isoformat()),
            )

    def clear_description(self, dish_id: str) -> None:
        with mo_ket_noi(self.db_path) as conn:
            conn.execute("DELETE FROM dish_overrides WHERE dish_id = ?", (dish_id,))

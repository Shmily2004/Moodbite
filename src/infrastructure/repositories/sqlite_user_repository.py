"""ADAPTER: lưu tài khoản người dùng vào SQLite.

⚠️ DÙNG FILE CSDL RIÊNG, KHÔNG chung với CSDL quán. Lý do:

  `moodbite.db` (quán)        = DỮ LIỆU DẪN XUẤT — dựng lại được bất cứ lúc nào từ CSV
                                bằng `scripts/build_sqlite.py`, và đang bị .gitignore.
  `moodbite_users.db` (người) = DỮ LIỆU GỐC — mất là mất hẳn, không có nguồn nào dựng lại.

Để chung một file thì chỉ cần ai đó xoá `.db` đi để dựng lại dữ liệu quán (việc hoàn toàn
bình thường, tài liệu còn khuyến khích) là **bay sạch tài khoản**. Tách hai file khiến sai
lầm đó không thể xảy ra.

`sqlite3` nằm trong thư viện chuẩn — không thêm phụ thuộc nào.
"""
from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.application.ports.user_repository import UsernameAlreadyExists
from src.domain.entities.user import User, UserRole
from src.infrastructure.config.settings import describe_path

logger = logging.getLogger("moodbite.users")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id       TEXT PRIMARY KEY,
    -- UNIQUE ở tầng CSDL, KHÔNG kiểm bằng SELECT trước rồi mới INSERT: hai người đăng ký
    -- cùng lúc sẽ cùng vượt qua phép kiểm đó rồi tạo hai tài khoản trùng tên.
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user',
    display_name  TEXT,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
"""

_COLUMNS = "user_id, username, password_hash, role, display_name, created_at"


class SqliteUserRepository:
    """Triển khai `UserRepository`.

    KHÔNG nạp sẵn vào bộ nhớ như kho quán: số tài khoản nhỏ, truy vấn theo tên đăng nhập
    có index nên rất nhanh, và quan trọng hơn là **luôn đọc dữ liệu mới nhất** — đổi mật
    khẩu hay đổi vai phải có hiệu lực ngay, không đợi khởi động lại.
    """

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._error: Optional[str] = None
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Tạo bảng nếu chưa có. Khác kho quán, ở đây app ĐƯỢC PHÉP tạo file mới —
        lần chạy đầu tiên thì đúng là chưa có tài khoản nào."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(SCHEMA)
        except (sqlite3.Error, OSError) as exc:
            self._error = f"Không mở được kho tài khoản {describe_path(self.db_path)}: {exc}"
            logger.error(self._error)

    # -- Port UserRepository --------------------------------------------------

    @property
    def is_ready(self) -> bool:
        return self._error is None

    def get_by_username(self, username: str) -> Optional[User]:
        return self._one("WHERE username = ?", [(username or "").strip().lower()])

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self._one("WHERE user_id = ?", [str(user_id)])

    def create(self, user: User) -> User:
        record = User(
            user_id=user.user_id or f"u-{uuid.uuid4()}",
            username=user.username,
            password_hash=user.password_hash,
            role=user.role,
            display_name=user.display_name,
            created_at=user.created_at or datetime.now(timezone.utc),
        )
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    f"INSERT INTO users ({_COLUMNS}) VALUES (?,?,?,?,?,?)",
                    (
                        record.user_id,
                        record.username,
                        record.password_hash,
                        record.role.value,
                        record.display_name,
                        record.created_at.isoformat(),
                    ),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            # Ràng buộc UNIQUE bị vi phạm = tên đã có người dùng.
            raise UsernameAlreadyExists(user.username)
        return record

    def count(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        except sqlite3.Error:
            return 0

    # -- Nội bộ ---------------------------------------------------------------

    def _one(self, where: str, params: list) -> Optional[User]:
        if self._error is not None:
            return None
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    f"SELECT {_COLUMNS} FROM users {where}", params
                ).fetchone()
        except sqlite3.Error as exc:
            logger.error("Lỗi đọc kho tài khoản: %s", exc)
            return None
        if row is None:
            return None
        created = row["created_at"]
        return User(
            user_id=row["user_id"],
            username=row["username"],
            password_hash=row["password_hash"],
            # Vai lạ trong CSDL -> hạ về `user`, KHÔNG nâng lên admin. Dữ liệu hỏng thì
            # phải chọn phía AN TOÀN.
            role=UserRole(row["role"]) if row["role"] in
                 (r.value for r in UserRole) else UserRole.USER,
            display_name=row["display_name"],
            created_at=datetime.fromisoformat(created) if created else None,
        )

    def status(self) -> dict:
        return {
            "ready": self.is_ready,
            "source": describe_path(self.db_path),
            "count": self.count(),
            "error": self._error,
        }


__all__ = ["SqliteUserRepository", "SCHEMA"]

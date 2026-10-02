"""ADAPTER: lưu "Địa chỉ của tôi" vào SQLite (file `moodbite_users.db`).

Cùng file với tài khoản — dữ liệu gốc do người dùng tạo, không dựng lại được.

BẤT BIẾN "KHÔNG QUÁ MỘT ĐỊA CHỈ MẶC ĐỊNH" ĐƯỢC GIỮ Ở HAI LỚP:
  1. Code: đặt mặc định = bỏ cờ mọi địa chỉ khác rồi bật cờ địa chỉ này, trong MỘT giao
     dịch (`with conn:`).
  2. CSDL: chỉ mục UNIQUE CÓ ĐIỀU KIỆN `WHERE is_default = 1`. Lỡ có đường ghi nào quên
     bước 1 thì SQLite từ chối ngay, thay vì để lại hai địa chỉ mặc định rồi điểm dự
     phòng vị trí thành ngẫu nhiên.
"""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List, Optional

from src.domain.entities.user_address import UserAddress
from src.infrastructure.config.settings import describe_path
from src.infrastructure.repositories.sqlite_ket_noi import mo_ket_noi

logger = logging.getLogger("moodbite.addresses")

SCHEMA = """
CREATE TABLE IF NOT EXISTS user_addresses (
    address_id   TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL,
    label        TEXT NOT NULL,
    -- NULL = người dùng không gõ mô tả. KHÔNG sinh chữ thay họ (không có geocoding).
    address_text TEXT,
    lat          REAL NOT NULL,
    lng          REAL NOT NULL,
    is_default   INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_user_addresses_user ON user_addresses(user_id);
-- Lớp bảo vệ thứ hai cho bất biến "tối đa MỘT mặc định mỗi người" — xem ghi chú đầu file.
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_addresses_default
    ON user_addresses(user_id) WHERE is_default = 1;
"""

_COLUMNS = "address_id, user_id, label, address_text, lat, lng, is_default, created_at"


class SqliteUserAddressRepository:
    """Triển khai `UserAddressRepository`."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._error: Optional[str] = None
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            try:
                conn.executescript(SCHEMA)
            finally:
                conn.close()
        except (sqlite3.Error, OSError) as exc:
            self._error = f"Không mở được kho địa chỉ {describe_path(self.db_path)}: {exc}"
            logger.error(self._error)

    @property
    def is_ready(self) -> bool:
        return self._error is None

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        """Một giao dịch rồi đóng kết nối — xem `SqliteCollectionRepository._tx`."""
        if self._error is not None:
            raise RuntimeError(self._error)
        with mo_ket_noi(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            yield conn

    # --- Đọc -----------------------------------------------------------------

    def list_for_user(self, user_id: str) -> List[UserAddress]:
        if self._error is not None:
            return []
        with self._tx() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM user_addresses WHERE user_id = ? "
                # Mặc định lên đầu: đó là thứ người dùng tìm khi mở tab này.
                "ORDER BY is_default DESC, created_at ASC",
                (str(user_id),),
            ).fetchall()
        return [_to_address(r) for r in rows]

    def get(self, user_id: str, address_id: str) -> Optional[UserAddress]:
        if self._error is not None:
            return None
        with self._tx() as conn:
            row = _get(conn, user_id, address_id)
        return _to_address(row) if row is not None else None

    def count_for_user(self, user_id: str) -> int:
        if self._error is not None:
            return 0
        with self._tx() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM user_addresses WHERE user_id = ?", (str(user_id),)
            ).fetchone()[0]

    # --- Ghi -----------------------------------------------------------------

    def create(self, address: UserAddress) -> UserAddress:
        record = UserAddress(
            address_id=address.address_id,
            user_id=address.user_id,
            label=address.label,
            address_text=address.address_text,
            lat=address.lat,
            lng=address.lng,
            is_default=address.is_default,
            created_at=address.created_at or datetime.now(timezone.utc),
        )
        with self._tx() as conn:
            if record.is_default:
                _clear_default(conn, record.user_id)
            conn.execute(
                f"INSERT INTO user_addresses ({_COLUMNS}) VALUES (?,?,?,?,?,?,?,?)",
                (
                    record.address_id,
                    record.user_id,
                    record.label,
                    record.address_text,
                    record.lat,
                    record.lng,
                    1 if record.is_default else 0,
                    record.created_at.isoformat(),
                ),
            )
        return record

    def update(
        self,
        user_id: str,
        address_id: str,
        *,
        label: Optional[str] = None,
        address_text: Optional[str] = None,
        clear_address_text: bool = False,
        is_default: Optional[bool] = None,
    ) -> Optional[UserAddress]:
        with self._tx() as conn:
            if _get(conn, user_id, address_id) is None:
                return None
            if label is not None:
                conn.execute(
                    "UPDATE user_addresses SET label = ? WHERE user_id = ? AND address_id = ?",
                    (label, str(user_id), str(address_id)),
                )
            if clear_address_text or address_text is not None:
                conn.execute(
                    "UPDATE user_addresses SET address_text = ? "
                    "WHERE user_id = ? AND address_id = ?",
                    (None if clear_address_text else address_text, str(user_id), str(address_id)),
                )
            if is_default is True:
                # Bỏ cờ của MỌI địa chỉ khác trước, rồi mới bật — cùng giao dịch, nên
                # không có khoảnh khắc nào người dùng có hai (hay chỉ mục UNIQUE báo lỗi).
                _clear_default(conn, user_id)
                conn.execute(
                    "UPDATE user_addresses SET is_default = 1 "
                    "WHERE user_id = ? AND address_id = ?",
                    (str(user_id), str(address_id)),
                )
            elif is_default is False:
                conn.execute(
                    "UPDATE user_addresses SET is_default = 0 "
                    "WHERE user_id = ? AND address_id = ?",
                    (str(user_id), str(address_id)),
                )
            row = _get(conn, user_id, address_id)
        return _to_address(row) if row is not None else None

    def delete(self, user_id: str, address_id: str) -> bool:
        with self._tx() as conn:
            cur = conn.execute(
                "DELETE FROM user_addresses WHERE user_id = ? AND address_id = ?",
                (str(user_id), str(address_id)),
            )
            return cur.rowcount > 0

    def status(self) -> dict:
        dem = 0
        if self._error is None:
            try:
                with self._tx() as conn:
                    dem = conn.execute("SELECT COUNT(*) FROM user_addresses").fetchone()[0]
            except sqlite3.Error:
                dem = 0
        return {
            "ready": self.is_ready,
            "source": describe_path(self.db_path),
            "count": dem,
            "error": self._error,
        }


def _get(conn: sqlite3.Connection, user_id: str, address_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        f"SELECT {_COLUMNS} FROM user_addresses WHERE user_id = ? AND address_id = ?",
        (str(user_id), str(address_id)),
    ).fetchone()


def _clear_default(conn: sqlite3.Connection, user_id: str) -> None:
    conn.execute(
        "UPDATE user_addresses SET is_default = 0 WHERE user_id = ? AND is_default = 1",
        (str(user_id),),
    )


def _to_address(row: sqlite3.Row) -> UserAddress:
    created = row["created_at"]
    return UserAddress(
        address_id=row["address_id"],
        user_id=row["user_id"],
        label=row["label"],
        address_text=row["address_text"],
        lat=float(row["lat"]),
        lng=float(row["lng"]),
        is_default=bool(row["is_default"]),
        created_at=datetime.fromisoformat(created) if created else None,
    )


__all__ = ["SqliteUserAddressRepository", "SCHEMA"]

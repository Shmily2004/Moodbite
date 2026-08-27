"""ADAPTER: ghi nhật ký hoạt động quản trị vào SQLite.

DÙNG CHUNG FILE với `moodbite_users.db`, không dùng `moodbite.db`:
nhật ký là DỮ LIỆU GỐC, mất là mất hẳn. `moodbite.db` là dữ liệu dẫn xuất và
`scripts/build_sqlite.py` dựng lại được bất cứ lúc nào — để chung thì một lần dựng lại
dữ liệu quán là bay sạch nhật ký.

`sqlite3` nằm trong thư viện chuẩn — không thêm phụ thuộc nào.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from src.domain.entities.audit_log import AuditAction, AuditEntry
from src.infrastructure.config.settings import describe_path

logger = logging.getLogger("moodbite.audit")

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    actor       TEXT NOT NULL,
    action      TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id   TEXT NOT NULL,
    summary     TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
-- Truy vấn duy nhất trong thực tế: "N dòng mới nhất", có khi lọc theo hành động.
CREATE INDEX IF NOT EXISTS idx_audit_moi_nhat ON audit_log(created_at DESC);
"""

_COLUMNS = "actor, action, target_type, target_id, summary, created_at"

# Chặn trên số dòng trả về một lần. Nhật ký chỉ để ĐỌC LẠI GẦN ĐÂY; muốn phân tích cả
# lịch sử thì mở thẳng file CSDL bằng công cụ SQL.
MAX_TRA_VE = 200


class SqliteAuditLogRepository:
    """Triển khai `AuditLogRepository`. Chỉ ghi thêm, không sửa."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._error: Optional[str] = None
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(SCHEMA)
        except (sqlite3.Error, OSError) as exc:
            self._error = f"Không mở được nhật ký {describe_path(self.db_path)}: {exc}"
            logger.error(self._error)

    @property
    def is_ready(self) -> bool:
        return self._error is None

    def add(self, entry: AuditEntry) -> AuditEntry:
        ban_ghi = AuditEntry(
            actor=entry.actor,
            action=entry.action,
            target_type=entry.target_type,
            target_id=entry.target_id,
            summary=entry.summary,
            created_at=entry.created_at or datetime.now(timezone.utc),
        )
        if self._error is not None:
            raise RuntimeError(self._error)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"INSERT INTO audit_log ({_COLUMNS}) VALUES (?,?,?,?,?,?)",
                (
                    ban_ghi.actor,
                    ban_ghi.action.value,
                    ban_ghi.target_type,
                    ban_ghi.target_id,
                    ban_ghi.summary,
                    ban_ghi.created_at.isoformat(),
                ),
            )
            conn.commit()
        return ban_ghi

    def list_recent(
        self, limit: int = 50, action: Optional[str] = None
    ) -> List[AuditEntry]:
        if self._error is not None:
            return []
        so = max(1, min(int(limit), MAX_TRA_VE))
        where = ""
        params: list = []
        if action:
            where = "WHERE action = ?"
            params.append(action)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    f"SELECT {_COLUMNS} FROM audit_log {where} "
                    "ORDER BY created_at DESC, id DESC LIMIT ?",
                    [*params, so],
                ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Lỗi đọc nhật ký: %s", exc)
            return []

        ket_qua: List[AuditEntry] = []
        for row in rows:
            try:
                hanh_dong = AuditAction(row["action"])
            except ValueError:
                # Hành động lạ (bản ghi từ phiên bản cũ) -> BỎ QUA dòng đó, không làm
                # sập cả trang nhật ký.
                continue
            ket_qua.append(
                AuditEntry(
                    actor=row["actor"],
                    action=hanh_dong,
                    target_type=row["target_type"],
                    target_id=row["target_id"],
                    summary=row["summary"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )
        return ket_qua

    def count(self) -> int:
        if self._error is not None:
            return 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                return conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        except sqlite3.Error:
            return 0

    def xoa_cu_hon(self, so_ngay: int) -> int:
        if self._error is not None:
            return 0
        moc = (datetime.now(timezone.utc) - timedelta(days=max(1, int(so_ngay)))).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("DELETE FROM audit_log WHERE created_at < ?", (moc,))
                conn.commit()
                return cur.rowcount
        except sqlite3.Error as exc:
            logger.error("Lỗi dọn nhật ký: %s", exc)
            return 0

    def status(self) -> dict:
        return {
            "ready": self.is_ready,
            "source": describe_path(self.db_path),
            "count": self.count(),
            "error": self._error,
        }


__all__ = ["SqliteAuditLogRepository", "SCHEMA", "MAX_TRA_VE"]

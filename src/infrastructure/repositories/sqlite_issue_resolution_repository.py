"""ADAPTER: lưu trạng thái "vấn đề đã xử lý" vào SQLite.

Chung file CSDL với tài khoản và nhật ký (`moodbite_users.db`) vì cùng lý do: đây là dữ
liệu GỐC do người quản trị tạo ra, không dựng lại được từ dataset.

`sqlite3` nằm trong thư viện chuẩn — không thêm phụ thuộc nào.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from src.domain.entities.issue_resolution import DanhDauXong
from src.infrastructure.config.settings import describe_path

logger = logging.getLogger("moodbite.issues")

# Khoá chính là CẶP (khoa, target_id): cùng một quán vừa nghi đóng cửa vừa thiếu liên hệ
# là HAI việc khác nhau. Xem `domain/entities/issue_resolution.py`.
SCHEMA = """
CREATE TABLE IF NOT EXISTS issue_resolution (
    khoa        TEXT NOT NULL,
    target_id   TEXT NOT NULL,
    actor       TEXT NOT NULL,
    ghi_chu     TEXT,
    resolved_at TEXT NOT NULL,
    PRIMARY KEY (khoa, target_id)
);
-- Hai truy vấn thật: "đã xử lý gần đây" và "đã xử lý trong ngày N".
CREATE INDEX IF NOT EXISTS idx_issue_moi_nhat ON issue_resolution(resolved_at DESC);
"""

_COLUMNS = "khoa, target_id, actor, ghi_chu, resolved_at"

# Chặn trên số dòng trả về một lần — cùng lý do với nhật ký hoạt động.
MAX_TRA_VE = 200


def _tu_row(r) -> DanhDauXong:
    try:
        luc = datetime.fromisoformat(r[4])
    except (TypeError, ValueError):
        luc = None
    return DanhDauXong(
        khoa=r[0], target_id=r[1], actor=r[2], ghi_chu=r[3], resolved_at=luc
    )


class SqliteIssueResolutionRepository:
    """Triển khai `IssueResolutionRepository`."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._error: Optional[str] = None
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(SCHEMA)
        except (sqlite3.Error, OSError) as exc:
            self._error = (
                f"Không mở được kho xử lý vấn đề {describe_path(self.db_path)}: {exc}"
            )
            logger.error(self._error)

    @property
    def is_ready(self) -> bool:
        return self._error is None

    def danh_dau(self, ban_ghi: DanhDauXong) -> DanhDauXong:
        # Ở ĐÂY thì KHÔNG im lặng bỏ qua như kho ảnh chụp: người dùng vừa bấm một nút và
        # đang chờ kết quả. Nuốt lỗi sẽ khiến nút bấm xong không có gì xảy ra mà cũng
        # không báo gì — kiểu hỏng khó chịu nhất.
        if self._error is not None:
            raise RuntimeError(self._error)
        day_du = DanhDauXong(
            khoa=ban_ghi.khoa,
            target_id=ban_ghi.target_id,
            actor=ban_ghi.actor,
            ghi_chu=ban_ghi.ghi_chu,
            resolved_at=ban_ghi.resolved_at or datetime.now(timezone.utc),
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO issue_resolution ({_COLUMNS}) VALUES (?,?,?,?,?)",
                (
                    day_du.khoa,
                    day_du.target_id,
                    day_du.actor,
                    day_du.ghi_chu,
                    day_du.resolved_at.isoformat(),
                ),
            )
        return day_du

    def bo_danh_dau(self, khoa: str, target_id: str) -> bool:
        if self._error is not None:
            raise RuntimeError(self._error)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "DELETE FROM issue_resolution WHERE khoa = ? AND target_id = ?",
                (khoa, target_id),
            )
            return cur.rowcount > 0

    def da_xong(self, khoa: str, target_ids: List[str]) -> Dict[str, DanhDauXong]:
        if self._error is not None or not target_ids:
            return {}
        # Dựng đúng số dấu `?` theo số phần tử: nối chuỗi giá trị vào SQL là đường thẳng
        # tới SQL injection, dù ở đây id do server sinh ra.
        cho_trong = ",".join("?" for _ in target_ids)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM issue_resolution "
                f"WHERE khoa = ? AND target_id IN ({cho_trong})",
                (khoa, *target_ids),
            ).fetchall()
        return {r[1]: _tu_row(r) for r in rows}

    def dem(self, khoa: Optional[str] = None) -> int:
        if self._error is not None:
            return 0
        with sqlite3.connect(self.db_path) as conn:
            if khoa is None:
                row = conn.execute("SELECT COUNT(*) FROM issue_resolution").fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) FROM issue_resolution WHERE khoa = ?", (khoa,)
                ).fetchone()
        return int(row[0]) if row else 0

    def dem_trong_ngay(self, ngay: str) -> int:
        if self._error is not None:
            return 0
        # `resolved_at` lưu dạng ISO đầy đủ, nên so bằng tiền tố ngày. Dùng `LIKE 'ngay%'`
        # thay vì hàm `date()` của SQLite để không phụ thuộc vào cách SQLite hiểu múi giờ.
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM issue_resolution WHERE resolved_at LIKE ?",
                (f"{ngay}%",),
            ).fetchone()
        return int(row[0]) if row else 0

    def liet_ke(self, limit: int = 50) -> List[DanhDauXong]:
        if self._error is not None:
            return []
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM issue_resolution "
                "ORDER BY resolved_at DESC LIMIT ?",
                (min(max(limit, 1), MAX_TRA_VE),),
            ).fetchall()
        return [_tu_row(r) for r in rows]


__all__ = ["SqliteIssueResolutionRepository", "SCHEMA", "MAX_TRA_VE"]

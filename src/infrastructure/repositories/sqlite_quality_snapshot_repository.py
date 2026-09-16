"""ADAPTER: lưu ảnh chụp chất lượng dữ liệu theo ngày vào SQLite.

DÙNG CHUNG FILE với `moodbite_users.db`, không dùng `moodbite.db`: lịch sử là DỮ LIỆU
GỐC, mất là mất hẳn và KHÔNG dựng lại được — dataset hôm nay không nói được hôm qua nó
trông thế nào. `moodbite.db` thì `scripts/build_sqlite.py` dựng lại bất cứ lúc nào, để
chung là một lần dựng lại dữ liệu quán sẽ bay sạch lịch sử.

`sqlite3` nằm trong thư viện chuẩn — không thêm phụ thuộc nào.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

from src.domain.services.data_quality_history import AnhChupChatLuong
from src.infrastructure.config.settings import describe_path

logger = logging.getLogger("moodbite.quality_history")

# `ngay` là KHOÁ CHÍNH: mỗi ngày đúng một dòng. Ghi lại trong cùng ngày thì `INSERT OR
# REPLACE` đè lên, không đẻ dòng mới — xem docstring `QualitySnapshotRepository`.
SCHEMA = """
CREATE TABLE IF NOT EXISTS quality_snapshot (
    ngay                 TEXT PRIMARY KEY,
    tong_quan            INTEGER NOT NULL,
    tong_mon             INTEGER NOT NULL,
    hoan_thien_phan_tram REAL    NOT NULL,
    nghiem_trong         INTEGER NOT NULL,
    quan_trong           INTEGER NOT NULL,
    can_kiem_tra         INTEGER NOT NULL
);
"""

_COLUMNS = (
    "ngay, tong_quan, tong_mon, hoan_thien_phan_tram, "
    "nghiem_trong, quan_trong, can_kiem_tra"
)


class SqliteQualitySnapshotRepository:
    """Triển khai `QualitySnapshotRepository`."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._error: Optional[str] = None
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(SCHEMA)
        except (sqlite3.Error, OSError) as exc:
            self._error = (
                f"Không mở được lịch sử chất lượng {describe_path(self.db_path)}: {exc}"
            )
            logger.error(self._error)

    @property
    def is_ready(self) -> bool:
        return self._error is None

    def ghi(self, anh_chup: AnhChupChatLuong) -> None:
        if self._error is not None:
            # Im lặng bỏ qua CÓ CHỦ Ý, và đây là chỗ duy nhất trong dự án được phép:
            # lịch sử là khối phụ của màn hình chất lượng. Ném lỗi ra sẽ làm hỏng cả
            # màn hình vì một biểu đồ. Đã ghi log ở `__init__` nên không mất dấu vết.
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO quality_snapshot ({_COLUMNS}) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    anh_chup.ngay,
                    int(anh_chup.tong_quan),
                    int(anh_chup.tong_mon),
                    float(anh_chup.hoan_thien_phan_tram),
                    int(anh_chup.nghiem_trong),
                    int(anh_chup.quan_trong),
                    int(anh_chup.can_kiem_tra),
                ),
            )

    def doc_gan_day(self, so_ngay: int = 60) -> List[AnhChupChatLuong]:
        if self._error is not None:
            return []
        han = (date.today() - timedelta(days=max(so_ngay, 1))).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM quality_snapshot "
                "WHERE ngay >= ? ORDER BY ngay ASC",
                (han,),
            ).fetchall()
        return [
            AnhChupChatLuong(
                ngay=r[0],
                tong_quan=r[1],
                tong_mon=r[2],
                hoan_thien_phan_tram=r[3],
                nghiem_trong=r[4],
                quan_trong=r[5],
                can_kiem_tra=r[6],
            )
            for r in rows
        ]


__all__ = ["SqliteQualitySnapshotRepository", "SCHEMA"]

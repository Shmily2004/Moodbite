"""ADAPTER: lưu "quán/món yêu thích" vào SQLite.

DÙNG CHUNG FILE với `moodbite_users.db`, không dùng `moodbite.db`:
mục yêu thích là DỮ LIỆU GỐC do người dùng tạo ra, mất là mất hẳn. `moodbite.db` là dữ
liệu dẫn xuất và `scripts/build_sqlite.py` dựng lại được bất cứ lúc nào — để chung thì
một lần dựng lại dữ liệu quán là bay sạch danh sách yêu thích của mọi người.

`sqlite3` nằm trong thư viện chuẩn — không thêm phụ thuộc nào.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from src.domain.entities.saved_item import SavedItem, SavedItemType, SavedListType
from src.infrastructure.config.settings import describe_path

logger = logging.getLogger("moodbite.saved_items")

SCHEMA = """
CREATE TABLE IF NOT EXISTS saved_items (
    user_id    TEXT NOT NULL,
    -- 'favorite' (trái tim) hoặc 'bookmark' (dấu trang). Giá trị do domain quyết
    -- (SavedListType), không phải ở đây. Xem `domain/entities/saved_item.py`.
    list_type  TEXT NOT NULL DEFAULT 'favorite',
    -- 'restaurant' hoặc 'dish'. Giá trị do domain quyết (SavedItemType), không phải ở đây.
    item_type  TEXT NOT NULL,
    item_id    TEXT NOT NULL,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL,
    -- Khoá chính GỘP BỐN CỘT: cùng một người không thể lưu hai lần cùng một thứ VÀO CÙNG
    -- MỘT DANH SÁCH, nhưng VẪN ĐƯỢC vừa thích vừa đánh dấu cùng một món. Ràng buộc này ở
    -- tầng CSDL chứ không kiểm bằng SELECT trước khi INSERT — hai tab bấm cùng lúc sẽ
    -- cùng vượt qua phép kiểm đó.
    PRIMARY KEY (user_id, list_type, item_type, item_id)
);
-- Truy vấn thường gặp là "mọi mục của một người, mới nhất trước".
CREATE INDEX IF NOT EXISTS idx_saved_user ON saved_items(user_id, created_at DESC);
"""


def _nang_cap_bang(conn: sqlite3.Connection) -> bool:
    """Chuyển bảng CŨ (chưa có `list_type`) sang bảng mới. Trả True nếu ĐÃ chuyển.

    VÌ SAO PHẢI DỰNG LẠI BẢNG chứ không chỉ `ALTER TABLE ADD COLUMN`: khoá chính đổi từ
    ba cột sang bốn cột, mà SQLite không sửa được khoá chính tại chỗ. Chỉ thêm cột thì
    khoá chính vẫn là (user_id, item_type, item_id) và người dùng KHÔNG thể vừa thích vừa
    đánh dấu cùng một món — đúng cái tính năng ta đang thêm.

    DỮ LIỆU CŨ VỀ ĐÂU: tất cả thành 'favorite'. Hồi đó nút duy nhất là trái tim và giao
    diện gọi nó là "yêu thích", nên đó mới đúng là điều người dùng đã làm. Đổ hết vào
    'bookmark' sẽ là suy diễn một ý định họ chưa từng bày tỏ.

    ⚠️ Chạy TRONG MỘT GIAO DỊCH: đứt điện giữa chừng mà bảng cũ đã xoá còn bảng mới chưa
    đầy là mất sạch dữ liệu gốc của người dùng — thứ không dựng lại được.
    """
    cot = {r[1] for r in conn.execute("PRAGMA table_info(saved_items)")}
    if not cot or "list_type" in cot:
        return False                      # bảng chưa có, hoặc đã là bản mới

    logger.info("Nâng cấp bảng saved_items: thêm list_type, dữ liệu cũ -> 'favorite'")
    conn.executescript(
        """
        BEGIN;
        CREATE TABLE saved_items_moi (
            user_id    TEXT NOT NULL,
            list_type  TEXT NOT NULL DEFAULT 'favorite',
            item_type  TEXT NOT NULL,
            item_id    TEXT NOT NULL,
            name       TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_id, list_type, item_type, item_id)
        );
        INSERT INTO saved_items_moi (user_id, list_type, item_type, item_id, name, created_at)
            SELECT user_id, 'favorite', item_type, item_id, name, created_at FROM saved_items;
        DROP TABLE saved_items;
        ALTER TABLE saved_items_moi RENAME TO saved_items;
        CREATE INDEX IF NOT EXISTS idx_saved_user ON saved_items(user_id, created_at DESC);
        COMMIT;
        """
    )
    return True


_COLUMNS = "user_id, list_type, item_type, item_id, name, created_at"


class SqliteSavedItemRepository:
    """Triển khai `SavedItemRepository`.

    Không nạp sẵn vào RAM: danh sách yêu thích phải luôn là bản mới nhất (người dùng có
    thể mở hai tab), và số lượng nhỏ nên truy vấn có index là đủ nhanh.
    """

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._error: Optional[str] = None
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                # Nâng cấp TRƯỚC: `CREATE TABLE IF NOT EXISTS` trong SCHEMA sẽ im lặng bỏ
                # qua khi bảng cũ đang tồn tại, nên nếu chạy sau thì bảng vĩnh viễn kẹt ở
                # bản ba cột.
                _nang_cap_bang(conn)
                conn.executescript(SCHEMA)
        except (sqlite3.Error, OSError) as exc:
            self._error = f"Không mở được kho yêu thích {describe_path(self.db_path)}: {exc}"
            logger.error(self._error)

    @property
    def is_ready(self) -> bool:
        return self._error is None

    def add(self, item: SavedItem) -> SavedItem:
        record = SavedItem(
            user_id=item.user_id,
            item_type=item.item_type,
            item_id=item.item_id,
            name=item.name,
            created_at=item.created_at or datetime.now(timezone.utc),
            list_type=item.list_type,
        )
        if self._error is not None:
            raise RuntimeError(self._error)
        with sqlite3.connect(self.db_path) as conn:
            # ON CONFLICT ... DO UPDATE: lưu lại thứ đã lưu thì cập nhật tên chứ không
            # lỗi, và KHÔNG đổi `created_at` — thứ tự trong danh sách phải giữ nguyên
            # theo lần lưu ĐẦU TIÊN, nếu không thì mỗi lần đồng bộ lại là xáo trộn hết.
            conn.execute(
                f"INSERT INTO saved_items ({_COLUMNS}) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(user_id, list_type, item_type, item_id) "
                "DO UPDATE SET name = excluded.name",
                (
                    record.user_id,
                    record.list_type.value,
                    record.item_type.value,
                    record.item_id,
                    record.name,
                    record.created_at.isoformat(),
                ),
            )
            conn.commit()
        return record

    def remove(
        self,
        user_id: str,
        item_type: SavedItemType,
        item_id: str,
        list_type: SavedListType = SavedListType.FAVORITE,
    ) -> bool:
        if self._error is not None:
            return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute(
                    # `list_type` NẰM TRONG điều kiện: bỏ tim một món không được xoá
                    # luôn dấu trang của chính món đó — hai ý định khác nhau.
                    "DELETE FROM saved_items "
                    "WHERE user_id=? AND list_type=? AND item_type=? AND item_id=?",
                    (str(user_id), list_type.value, item_type.value, str(item_id)),
                )
                conn.commit()
                return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error("Lỗi bỏ lưu: %s", exc)
            return False

    def list_for_user(
        self,
        user_id: str,
        item_type: Optional[SavedItemType] = None,
        list_type: Optional[SavedListType] = None,
    ) -> List[SavedItem]:
        if self._error is not None:
            return []
        where = "WHERE user_id = ?"
        params: list = [str(user_id)]
        if item_type is not None:
            where += " AND item_type = ?"
            params.append(item_type.value)
        # `None` = KHÔNG lọc, tức lấy CẢ HAI danh sách. Xem port: giao diện cần cả
        # hai trong một lần gọi để biết tim nào bật, dấu trang nào bật.
        if list_type is not None:
            where += " AND list_type = ?"
            params.append(list_type.value)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    f"SELECT {_COLUMNS} FROM saved_items {where} ORDER BY created_at DESC",
                    params,
                ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Lỗi đọc kho yêu thích: %s", exc)
            return []

        out: List[SavedItem] = []
        for row in rows:
            try:
                loai = SavedItemType(row["item_type"])
                danh_sach = SavedListType(row["list_type"])
            except ValueError:
                # Dữ liệu hỏng (loại lạ) thì BỎ QUA dòng đó, không làm sập cả danh sách.
                continue
            created = row["created_at"]
            out.append(
                SavedItem(
                    user_id=row["user_id"],
                    item_type=loai,
                    item_id=row["item_id"],
                    name=row["name"],
                    created_at=datetime.fromisoformat(created) if created else None,
                    list_type=danh_sach,
                )
            )
        return out

    def count_for_user(
        self,
        user_id: str,
        item_type: Optional[SavedItemType] = None,
        list_type: Optional[SavedListType] = None,
    ) -> int:
        if self._error is not None:
            return 0
        where = "WHERE user_id = ?"
        params: list = [str(user_id)]
        if item_type is not None:
            where += " AND item_type = ?"
            params.append(item_type.value)
        # `None` = KHÔNG lọc, tức lấy CẢ HAI danh sách. Xem port: giao diện cần cả
        # hai trong một lần gọi để biết tim nào bật, dấu trang nào bật.
        if list_type is not None:
            where += " AND list_type = ?"
            params.append(list_type.value)
        try:
            with sqlite3.connect(self.db_path) as conn:
                return conn.execute(
                    f"SELECT COUNT(*) FROM saved_items {where}", params
                ).fetchone()[0]
        except sqlite3.Error:
            return 0

    def count_distinct_items(
        self, user_id: str, item_type: Optional[SavedItemType] = None
    ) -> int:
        """Đếm số THỨ khác nhau — xem giải thích ở port. Cố ý KHÔNG nhận `list_type`:
        gộp cả hai danh sách lại rồi mới đếm chính là ý nghĩa của hàm này."""
        if self._error is not None:
            return 0
        where = "WHERE user_id = ?"
        params: list = [str(user_id)]
        if item_type is not None:
            where += " AND item_type = ?"
            params.append(item_type.value)
        try:
            with sqlite3.connect(self.db_path) as conn:
                return conn.execute(
                    "SELECT COUNT(DISTINCT item_type || '|' || item_id) "
                    f"FROM saved_items {where}",
                    params,
                ).fetchone()[0]
        except sqlite3.Error:
            return 0

    def count(self) -> int:
        if self._error is not None:
            return 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                return conn.execute("SELECT COUNT(*) FROM saved_items").fetchone()[0]
        except sqlite3.Error:
            return 0

    def status(self) -> dict:
        return {
            "ready": self.is_ready,
            "source": describe_path(self.db_path),
            "count": self.count(),
            "error": self._error,
        }


__all__ = ["SqliteSavedItemRepository", "SCHEMA"]

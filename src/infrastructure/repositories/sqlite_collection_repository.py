"""ADAPTER: lưu "Bộ sưu tập của tôi" vào SQLite (file `moodbite_users.db`).

CÙNG FILE với tài khoản và `saved_items`, cùng lý do: đây là dữ liệu GỐC do người dùng
tạo, mất là mất hẳn. `moodbite.db` là dữ liệu dẫn xuất, dựng lại bất cứ lúc nào.

GIỚI HẠN PHẠM VI NGƯỜI DÙNG NGAY TRONG SQL: mọi câu lệnh đụng tới `collection_items` đều
kèm điều kiện "bộ này thuộc `user_id`". Không làm kiểu "SELECT kiểm quyền rồi mới DELETE"
ở tầng trên — hai bước rời nhau là một chỗ để quên.

VÌ SAO KHÔNG DÙNG `FOREIGN KEY ... ON DELETE CASCADE`: SQLite TẮT kiểm khoá ngoại theo
mặc định, phải bật `PRAGMA foreign_keys=ON` ở TỪNG kết nối. Quên một chỗ là mục mồ côi
nằm lại mãi mà không ai báo. Xoá tường minh cả hai bảng trong một giao dịch thì không phụ
thuộc vào cờ đó.
"""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from src.domain.entities.collection import Collection, CollectionItem
from src.domain.entities.saved_item import SavedItemType
from src.infrastructure.config.settings import describe_path
from src.infrastructure.repositories.sqlite_ket_noi import mo_ket_noi

logger = logging.getLogger("moodbite.collections")

SCHEMA = """
CREATE TABLE IF NOT EXISTS collections (
    collection_id TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL,
    name          TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
-- Truy vấn duy nhất theo người dùng: "mọi bộ của tôi, mới nhất trước".
CREATE INDEX IF NOT EXISTS idx_collections_user ON collections(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS collection_items (
    collection_id TEXT NOT NULL,
    -- 'restaurant' | 'dish' — giá trị do domain quyết (SavedItemType).
    item_type     TEXT NOT NULL,
    item_id       TEXT NOT NULL,
    name          TEXT NOT NULL,
    added_at      TEXT NOT NULL,
    -- Một thứ chỉ nằm MỘT lần trong một bộ. Khoá ở CSDL chứ không SELECT kiểm trước:
    -- hai tab bấm cùng lúc sẽ cùng vượt qua phép kiểm đó.
    PRIMARY KEY (collection_id, item_type, item_id)
);
"""


class SqliteCollectionRepository:
    """Triển khai `CollectionRepository`. Mở kết nối cho từng lần gọi, không nạp vào RAM
    — cùng lý do với `SqliteSavedItemRepository` (hai tab phải thấy bản mới nhất)."""

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
            self._error = f"Không mở được kho bộ sưu tập {describe_path(self.db_path)}: {exc}"
            logger.error(self._error)

    @property
    def is_ready(self) -> bool:
        return self._error is None

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        """MỘT giao dịch rồi ĐÓNG kết nối - xem `sqlite_ket_noi.mo_ket_noi`."""
        if self._error is not None:
            raise RuntimeError(self._error)
        with mo_ket_noi(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            yield conn

    # --- Đọc -----------------------------------------------------------------

    def _items_of(
        self, conn: sqlite3.Connection, collection_ids: List[str]
    ) -> Dict[str, List[CollectionItem]]:
        if not collection_ids:
            return {}
        cho = ",".join("?" for _ in collection_ids)
        rows = conn.execute(
            "SELECT collection_id, item_type, item_id, name, added_at "
            f"FROM collection_items WHERE collection_id IN ({cho}) "
            "ORDER BY added_at DESC",
            collection_ids,
        ).fetchall()
        out: Dict[str, List[CollectionItem]] = {cid: [] for cid in collection_ids}
        for row in rows:
            try:
                loai = SavedItemType(row["item_type"])
            except ValueError:
                # Dòng hỏng (loại lạ) thì bỏ qua, không làm sập cả danh sách.
                continue
            out[row["collection_id"]].append(
                CollectionItem(
                    item_type=loai,
                    item_id=row["item_id"],
                    name=row["name"],
                    added_at=_parse(row["added_at"]),
                )
            )
        return out

    def list_for_user(self, user_id: str) -> List[Collection]:
        if self._error is not None:
            return []
        with self._tx() as conn:
            rows = conn.execute(
                "SELECT collection_id, user_id, name, created_at FROM collections "
                "WHERE user_id = ? ORDER BY created_at DESC",
                (str(user_id),),
            ).fetchall()
            items = self._items_of(conn, [r["collection_id"] for r in rows])
        return [_to_collection(r, items.get(r["collection_id"], [])) for r in rows]

    def get(self, user_id: str, collection_id: str) -> Optional[Collection]:
        if self._error is not None:
            return None
        with self._tx() as conn:
            row = conn.execute(
                "SELECT collection_id, user_id, name, created_at FROM collections "
                "WHERE user_id = ? AND collection_id = ?",
                (str(user_id), str(collection_id)),
            ).fetchone()
            if row is None:
                return None
            items = self._items_of(conn, [row["collection_id"]])
        return _to_collection(row, items.get(row["collection_id"], []))

    def count_for_user(self, user_id: str) -> int:
        if self._error is not None:
            return 0
        with self._tx() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM collections WHERE user_id = ?", (str(user_id),)
            ).fetchone()[0]

    # --- Ghi -----------------------------------------------------------------

    def create(self, collection: Collection) -> Collection:
        record = Collection(
            collection_id=collection.collection_id,
            user_id=collection.user_id,
            name=collection.name,
            created_at=collection.created_at or datetime.now(timezone.utc),
            items=[],
        )
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO collections (collection_id, user_id, name, created_at) "
                "VALUES (?,?,?,?)",
                (
                    record.collection_id,
                    record.user_id,
                    record.name,
                    record.created_at.isoformat(),
                ),
            )
        return record

    def rename(self, user_id: str, collection_id: str, name: str) -> bool:
        with self._tx() as conn:
            cur = conn.execute(
                "UPDATE collections SET name = ? WHERE user_id = ? AND collection_id = ?",
                (name, str(user_id), str(collection_id)),
            )
            return cur.rowcount > 0

    def delete(self, user_id: str, collection_id: str) -> bool:
        # `with conn:` = MỘT giao dịch: lỗi giữa chừng thì cả hai lệnh cùng huỷ, không
        # bao giờ còn lại mục mồ côi của một bộ đã xoá (hay bộ trống mất hết mục).
        with self._tx() as conn:
            cur = conn.execute(
                "DELETE FROM collections WHERE user_id = ? AND collection_id = ?",
                (str(user_id), str(collection_id)),
            )
            if cur.rowcount == 0:
                return False
            conn.execute(
                "DELETE FROM collection_items WHERE collection_id = ?",
                (str(collection_id),),
            )
            return True

    def add_item(
        self, user_id: str, collection_id: str, item: CollectionItem
    ) -> bool:
        added = (item.added_at or datetime.now(timezone.utc)).isoformat()
        with self._tx() as conn:
            # INSERT ... SELECT có WHERE theo user_id: bộ của người khác thì câu SELECT
            # không trả dòng nào, và không có gì được chèn — kiểm quyền ngay trong câu ghi.
            cur = conn.execute(
                "INSERT INTO collection_items "
                "(collection_id, item_type, item_id, name, added_at) "
                "SELECT collection_id, ?, ?, ?, ? FROM collections "
                "WHERE user_id = ? AND collection_id = ? "
                # Thêm lại thứ đã có: cập nhật tên, GIỮ `added_at` cũ để thứ tự không xáo.
                "ON CONFLICT(collection_id, item_type, item_id) "
                "DO UPDATE SET name = excluded.name",
                (
                    item.item_type.value,
                    item.item_id,
                    item.name,
                    added,
                    str(user_id),
                    str(collection_id),
                ),
            )
            return cur.rowcount > 0

    def remove_item(
        self,
        user_id: str,
        collection_id: str,
        item_type: SavedItemType,
        item_id: str,
    ) -> bool:
        with self._tx() as conn:
            cur = conn.execute(
                "DELETE FROM collection_items "
                "WHERE collection_id = ? AND item_type = ? AND item_id = ? "
                "AND collection_id IN "
                "(SELECT collection_id FROM collections WHERE user_id = ?)",
                (str(collection_id), item_type.value, str(item_id), str(user_id)),
            )
            return cur.rowcount > 0

    def status(self) -> dict:
        dem = 0
        if self._error is None:
            try:
                with self._tx() as conn:
                    dem = conn.execute("SELECT COUNT(*) FROM collections").fetchone()[0]
            except sqlite3.Error:
                dem = 0
        return {
            "ready": self.is_ready,
            "source": describe_path(self.db_path),
            "count": dem,
            "error": self._error,
        }


def _parse(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


def _to_collection(row: sqlite3.Row, items: List[CollectionItem]) -> Collection:
    return Collection(
        collection_id=row["collection_id"],
        user_id=row["user_id"],
        name=row["name"],
        created_at=_parse(row["created_at"]),
        items=items,
    )


__all__ = ["SqliteCollectionRepository", "SCHEMA"]

"""ADAPTER: lưu BÀI VIẾT vào SQLite (file `moodbite_users.db`).

Cùng file với tài khoản, vì đây là nội dung gốc của đội vận hành. Mất là mất hẳn, còn
`moodbite.db` là dữ liệu dẫn xuất có thể dựng lại.

Đường dẫn (`slug`) có ràng buộc UNIQUE ở CSDL, nên hai request cùng lúc không thể cùng ghi
một đường dẫn: request thua sẽ nhận `sqlite3.IntegrityError`, được đổi thành `InvalidPost`
để trả 400 chứ không thành 500.
"""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from src.domain.entities.post import InvalidPost, Post, PostOrigin, PostStatus
from src.infrastructure.config.settings import describe_path
from src.infrastructure.repositories.sqlite_ket_noi import mo_ket_noi

logger = logging.getLogger("moodbite.posts")

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    post_id     TEXT PRIMARY KEY,
    slug        TEXT NOT NULL UNIQUE,
    title       TEXT NOT NULL,
    summary     TEXT NOT NULL,
    body        TEXT NOT NULL,
    -- 'draft' | 'published' — giá trị do domain quyết (PostStatus).
    status      TEXT NOT NULL,
    -- 'admin' | 'web_sample' — giá trị do domain quyết (PostOrigin).
    origin      TEXT NOT NULL,
    source_name TEXT,
    source_url  TEXT,
    last_updated TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    published_at TEXT,
    -- Ảnh minh hoạ (tuỳ chọn). Hai cột này được THÊM SAU; bảng cũ được nâng ở `_nang_cap_bang`.
    image_url    TEXT,
    image_credit TEXT
);
-- Trang công khai chỉ lọc theo trạng thái rồi sắp theo thời gian đăng.
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status, published_at DESC);
"""

_COT = (
    "post_id, slug, title, summary, body, status, origin, source_name, source_url, "
    "last_updated, created_at, updated_at, published_at, image_url, image_credit"
)


class SqlitePostRepository:
    """Triển khai `PostRepository`. Mở kết nối theo từng lần gọi, không giữ trong RAM."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._error: Optional[str] = None
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            try:
                conn.executescript(SCHEMA)
                _nang_cap_bang(conn)
            finally:
                conn.close()
        except (sqlite3.Error, OSError) as exc:
            self._error = f"Không mở được kho bài viết {describe_path(self.db_path)}: {exc}"
            logger.error(self._error)

    @property
    def is_ready(self) -> bool:
        return self._error is None

    def _mo(self):
        if self._error is not None:
            raise RuntimeError(self._error)
        return mo_ket_noi(self.db_path)

    # --- Đọc -----------------------------------------------------------------

    def list(self, status: Optional[PostStatus] = None) -> List[Post]:
        if self._error is not None:
            return []
        sql = f"SELECT {_COT} FROM posts"
        tham_so: tuple = ()
        if status is not None:
            sql += " WHERE status = ?"
            tham_so = (status.value,)
        sql += " ORDER BY COALESCE(published_at, updated_at) DESC"
        with self._mo() as conn:
            conn.row_factory = sqlite3.Row
            return [_to_post(r) for r in conn.execute(sql, tham_so).fetchall()]

    def get(self, post_id: str) -> Optional[Post]:
        return self._mot(f"SELECT {_COT} FROM posts WHERE post_id = ?", (str(post_id),))

    def get_by_slug(self, slug: str) -> Optional[Post]:
        return self._mot(f"SELECT {_COT} FROM posts WHERE slug = ?", (str(slug),))

    def _mot(self, sql: str, tham_so: tuple) -> Optional[Post]:
        if self._error is not None:
            return None
        with self._mo() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(sql, tham_so).fetchone()
        return _to_post(row) if row is not None else None

    def slug_taken(self, slug: str, exclude_post_id: Optional[str] = None) -> bool:
        if self._error is not None:
            return False
        with self._mo() as conn:
            if exclude_post_id is None:
                row = conn.execute("SELECT 1 FROM posts WHERE slug = ?", (slug,)).fetchone()
            else:
                row = conn.execute(
                    "SELECT 1 FROM posts WHERE slug = ? AND post_id != ?",
                    (slug, str(exclude_post_id)),
                ).fetchone()
        return row is not None

    # --- Ghi -----------------------------------------------------------------

    def create(self, post: Post) -> Post:
        bay_gio = datetime.now().astimezone()
        record = replace(
            post,
            created_at=post.created_at or bay_gio,
            updated_at=post.updated_at or bay_gio,
        )
        try:
            with self._mo() as conn:
                conn.execute(
                    f"INSERT INTO posts ({_COT}) VALUES ({','.join('?' * 15)})",
                    _to_row(record),
                )
        except sqlite3.IntegrityError as exc:
            # Trùng đường dẫn do một request khác vừa ghi: báo 400 để người dùng thử lại.
            raise InvalidPost("Đường dẫn bài viết vừa bị trùng, hãy thử lại.") from exc
        return record

    def update(self, post: Post) -> bool:
        try:
            with self._mo() as conn:
                cur = conn.execute(
                    "UPDATE posts SET slug=?, title=?, summary=?, body=?, status=?, origin=?, "
                    "source_name=?, source_url=?, last_updated=?, created_at=?, updated_at=?, "
                    "published_at=?, image_url=?, image_credit=? WHERE post_id=?",
                    (*_to_row(post)[1:], post.post_id),
                )
                return cur.rowcount > 0
        except sqlite3.IntegrityError as exc:
            raise InvalidPost("Đường dẫn bài viết bị trùng.") from exc

    def delete(self, post_id: str) -> bool:
        with self._mo() as conn:
            cur = conn.execute("DELETE FROM posts WHERE post_id = ?", (str(post_id),))
            return cur.rowcount > 0

    def status(self) -> dict:
        dem = 0
        if self._error is None:
            try:
                with self._mo() as conn:
                    dem = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
            except sqlite3.Error:
                dem = 0
        return {
            "ready": self.is_ready,
            "source": describe_path(self.db_path),
            "count": dem,
            "error": self._error,
        }


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


def _to_row(post: Post) -> tuple:
    """Thứ tự khớp `_COT`. Thời gian lưu dạng ISO 8601 có múi giờ."""
    return (
        post.post_id,
        post.slug,
        post.title,
        post.summary,
        post.body,
        post.status.value,
        post.origin.value,
        post.source_name,
        post.source_url,
        post.last_updated.isoformat() if post.last_updated else None,
        post.created_at.isoformat() if post.created_at else None,
        post.updated_at.isoformat() if post.updated_at else None,
        post.published_at.isoformat() if post.published_at else None,
        post.image_url,
        post.image_credit,
    )


def _nang_cap_bang(conn: sqlite3.Connection) -> None:
    """Thêm cột ảnh vào kho CŨ (đã tạo trước khi có ảnh minh hoạ).

    `CREATE TABLE IF NOT EXISTS` KHÔNG thêm cột vào bảng đã có, nên phải kiểm và `ALTER`
    tay. Không làm vậy thì kho cũ sẽ lỗi `no such column` ngay lần đọc đầu tiên.
    """
    cot_hien_co = {r[1] for r in conn.execute("PRAGMA table_info(posts)")}
    for cot in ("image_url", "image_credit"):
        if cot not in cot_hien_co:
            conn.execute(f"ALTER TABLE posts ADD COLUMN {cot} TEXT")
    conn.commit()


def _to_post(row: sqlite3.Row) -> Post:
    return Post(
        post_id=row["post_id"],
        slug=row["slug"],
        title=row["title"],
        summary=row["summary"],
        body=row["body"],
        status=PostStatus(row["status"]),
        origin=PostOrigin(row["origin"]),
        source_name=row["source_name"],
        source_url=row["source_url"],
        last_updated=date.fromisoformat(row["last_updated"]) if row["last_updated"] else None,
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
        published_at=_parse_dt(row["published_at"]),
        image_url=row["image_url"],
        image_credit=row["image_credit"],
    )


__all__ = ["SqlitePostRepository", "SCHEMA"]

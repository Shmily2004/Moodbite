"""ADAPTER: đọc quán từ SQLite. Triển khai CÙNG port `RestaurantRepository` như bản CSV.

VÌ SAO CÓ FILE NÀY: bản CSV chỉ ĐỌC được. Trang Admin cần SỬA/ẨN quán, mà CSV thì không
sửa an toàn được (ghi đè cả file, không có transaction, không khoá được ghi đồng thời).
SQLite cho ta transaction + ghi tại chỗ mà KHÔNG cần cài server database, không cần thẻ
thanh toán - đúng ràng buộc chi phí ở CLAUDE.md mục 1b.

ĐIỂM MẤU CHỐT: file này triển khai đúng port cũ, nên use case và router KHÔNG ĐỔI một dòng
nào. Đổi kho lưu trữ chỉ là đổi một dòng ở `dependencies.py`.

KHÔNG import pandas ở đây: `sqlite3` nằm sẵn trong thư viện chuẩn Python. pandas chỉ xuất
hiện ở `scripts/build_sqlite.py` (lúc dựng CSDL), không phải lúc chạy app.

QUY ƯỚC DỮ LIỆU (CLAUDE.md mục 4):
  - NULL trong CSDL -> `None` trong entity, KHÔNG phải 0. "Chưa có đánh giá" ≠ "0 sao".
  - `price` lưu kiểu TEXT vì giá trị thật là chuỗi khoảng giá ("1-100.000 ₫", "70 US$").
  - Thiếu file CSDL KHÔNG được làm sập app -> ghi nhận lỗi, /health báo ready=false.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from src.domain.entities.restaurant import Restaurant
from src.domain.value_objects.location import Location
from src.domain.value_objects.mood import MOOD_SCORE_COLUMNS

# Lược đồ bảng. `place_id` để UNIQUE chứ KHÔNG làm PRIMARY KEY: một phần quán từ
# OpenStreetMap không có placeId của Google, và bản CSV vẫn giữ chúng trong `list_all()`.
# Dùng place_id làm khoá chính sẽ lặng lẽ đánh rơi nhóm quán đó.
SCHEMA = """
CREATE TABLE IF NOT EXISTS restaurants (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id                 TEXT UNIQUE,
    name                     TEXT NOT NULL,
    category                 TEXT,
    lat                      REAL NOT NULL,
    lng                      REAL NOT NULL,
    address                  TEXT,
    cuisine                  TEXT,
    price                    TEXT,     -- CHUỖI khoảng giá, KHÔNG phải số
    rating                   REAL,     -- NULL = chưa có dữ liệu, không phải 0 sao
    reviews_count            INTEGER,
    mood_scores              TEXT,     -- JSON {tên cột: điểm}
    atmosphere_tags          TEXT,     -- JSON array
    review_text              TEXT,
    opening_hours            TEXT,
    is_active                INTEGER NOT NULL DEFAULT 1,  -- soft-delete
    district                 TEXT,
    dietary                  TEXT,     -- JSON array
    amenities                TEXT,     -- JSON array
    phone                    TEXT,
    website                  TEXT,
    source                   TEXT,
    data_confidence          TEXT,
    experience_cluster_id    INTEGER,  -- NULL = CHƯA phân cụm (Cold Start), không phải cụm kém
    experience_cluster_label TEXT
);
-- Truy vấn theo place_id là đường đi nóng của GET /restaurants/{id}.
CREATE INDEX IF NOT EXISTS idx_restaurants_place_id ON restaurants(place_id);
-- Admin lọc quán đã ẩn; index này để soft-delete không phải quét cả bảng.
CREATE INDEX IF NOT EXISTS idx_restaurants_is_active ON restaurants(is_active);
"""

# Thứ tự cột phải khớp câu SELECT bên dưới.
_COLUMNS = (
    "place_id, name, category, lat, lng, address, cuisine, price, rating, "
    "reviews_count, mood_scores, atmosphere_tags, review_text, opening_hours, "
    "is_active, district, dietary, amenities, phone, website, source, "
    "data_confidence, experience_cluster_id, experience_cluster_label"
)


def _json_list(raw: Optional[str]) -> List[str]:
    """Cột JSON -> list[str]. Dữ liệu hỏng trả rỗng, KHÔNG làm hỏng cả lượt nạp."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return []
    return [str(v) for v in parsed if v] if isinstance(parsed, list) else []


def _json_scores(raw: Optional[str]) -> Dict[str, float]:
    """Điểm mood. Thiếu cột nào coi như 0.0 - trung lập, không phải điểm trừ."""
    scores: Dict[str, float] = {col: 0.0 for col in MOOD_SCORE_COLUMNS}
    if not raw:
        return scores
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return scores
    if isinstance(parsed, dict):
        for col in MOOD_SCORE_COLUMNS:
            value = parsed.get(col)
            if value is not None:
                scores[col] = float(value)
    return scores


class SqliteRestaurantRepository:
    """Triển khai `RestaurantRepository` từ file SQLite.

    Nạp toàn bộ vào bộ nhớ MỘT LẦN giống bản CSV, vì `list_all()` được gọi ở MỖI lượt
    tìm kiếm - truy vấn lại CSDL mỗi lần sẽ chậm hơn hẳn mà không được gì. Sau khi Admin
    ghi dữ liệu thì gọi `reload()` để làm mới bộ nhớ đệm.
    """

    def __init__(self, db_path: Path | str, eager: bool = True) -> None:
        self.db_path = Path(db_path)
        self._restaurants: Optional[List[Restaurant]] = None
        self._by_place_id: Dict[str, Restaurant] = {}
        self._load_error: Optional[str] = None
        if eager:
            self._ensure_loaded()

    # -- Port RestaurantRepository -------------------------------------------

    @property
    def is_ready(self) -> bool:
        self._ensure_loaded()
        return self._restaurants is not None

    def list_all(self) -> List[Restaurant]:
        self._ensure_loaded()
        return list(self._restaurants or [])

    def get_by_place_id(self, place_id: str) -> Optional[Restaurant]:
        self._ensure_loaded()
        return self._by_place_id.get(str(place_id))

    # -- Phần thêm so với port ------------------------------------------------

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def reload(self) -> None:
        """Bỏ bộ nhớ đệm và nạp lại. Admin PHẢI gọi sau khi ghi, nếu không người dùng
        vẫn thấy dữ liệu cũ cho tới lần khởi động lại tiếp theo."""
        self._restaurants = None
        self._by_place_id = {}
        self._load_error = None
        self._ensure_loaded()

    def status(self) -> dict:
        """Tự mô tả cho /health - cùng hình dạng với bản CSV để Container không phải
        biết đang dùng adapter nào."""
        ready = self.is_ready
        return {
            "ready": ready,
            "source": str(self.db_path),
            "count": len(self._restaurants or []),
            "error": self._load_error,
        }

    # -- Nội bộ ---------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """Nạp 1 lần. Thiếu file KHÔNG làm sập app - endpoint liên quan trả 503 kèm
        hướng dẫn khắc phục (CLAUDE.md mục 4 quy tắc 3)."""
        if self._restaurants is not None or self._load_error is not None:
            return
        if not self.db_path.exists():
            self._load_error = (
                f"Không tìm thấy CSDL: {self.db_path}. "
                "Chạy: python scripts/build_sqlite.py"
            )
            return
        try:
            # read-only + uri=True: app chạy chỉ ĐỌC, không vô tình tạo file rỗng khi
            # gõ nhầm đường dẫn (sqlite3.connect mặc định TẠO file mới nếu chưa có -
            # đúng thứ sẽ biến "sai đường dẫn" thành "0 quán" mà không báo lỗi gì).
            uri = f"file:{self.db_path.as_posix()}?mode=ro"
            with sqlite3.connect(uri, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    f"SELECT {_COLUMNS} FROM restaurants WHERE is_active = 1"
                ).fetchall()
        except sqlite3.Error as exc:
            self._load_error = f"Không đọc được {self.db_path}: {exc}"
            return

        restaurants = [r for r in (self._to_entity(row) for row in rows) if r]
        self._restaurants = restaurants
        self._by_place_id = {
            r.place_id: r for r in restaurants if r.place_id is not None
        }

    @staticmethod
    def _to_entity(row: sqlite3.Row) -> Optional[Restaurant]:
        lat, lng = row["lat"], row["lng"]
        name = row["name"]
        # Thiếu toạ độ/tên thì không xếp hạng hay hiển thị được -> bỏ qua, thay vì để nổ
        # giữa vòng lặp tính khoảng cách. Cùng quy tắc với bản CSV.
        if lat is None or lng is None or not name:
            return None
        try:
            location = Location(lat=float(lat), lng=float(lng))
        except ValueError:
            return None

        return Restaurant(
            place_id=row["place_id"],
            name=name,
            category=row["category"],
            location=location,
            address=row["address"],
            cuisine=row["cuisine"],
            price=row["price"],
            rating=row["rating"],
            reviews_count=row["reviews_count"],
            mood_scores=_json_scores(row["mood_scores"]),
            atmosphere_tags=_json_list(row["atmosphere_tags"]),
            review_text=row["review_text"],
            opening_hours=row["opening_hours"],
            is_active=bool(row["is_active"]),
            district=row["district"],
            dietary=_json_list(row["dietary"]),
            amenities=_json_list(row["amenities"]),
            phone=row["phone"],
            website=row["website"],
            source=row["source"],
            data_confidence=row["data_confidence"],
            experience_cluster_id=row["experience_cluster_id"],
            experience_cluster_label=row["experience_cluster_label"],
        )


__all__ = ["SqliteRestaurantRepository", "SCHEMA"]

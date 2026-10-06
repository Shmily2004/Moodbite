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
import logging
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from src.domain.entities.restaurant import Restaurant
from src.domain.value_objects.location import Location
from src.application.ports.admin_restaurant_repository import (
    ADMIN_STATUS_HIDDEN,
    ADMIN_STATUS_VISIBLE,
    MANUAL_SOURCES,
    AdminRestaurantFilter,
    AdminRestaurantStats,
    RestaurantAlreadyExists,
)
from src.domain.value_objects.mood import MOOD_SCORE_COLUMNS
from src.infrastructure.config.settings import describe_path
from src.infrastructure.repositories.sqlite_ket_noi import mo_ket_noi

logger = logging.getLogger("moodbite.repository")

# Cột admin được phép GHI. Danh sách này là chốt chặn cuối chống SQL injection: tên cột
# không tham số hoá được nên phải so với danh sách trắng cố định.
# Phải khớp với EDITABLE_FIELDS ở domain/value_objects/restaurant_edit.py - có test khoá.
_WRITABLE_COLUMNS = frozenset(
    {"name", "category", "cuisine", "address", "price", "phone", "website", "district"}
)

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
    thumbnail_url            TEXT,     -- chi 21.5% quan co anh
    opening_hours            TEXT,
    is_active                INTEGER NOT NULL DEFAULT 1,  -- soft-delete
    -- Trạng thái kinh doanh từ NGUỒN DỮ LIỆU, khác hẳn `is_active` (admin tự tắt).
    -- NULL = không biết (quán OSM/Overture không có trường này). Đừng NOT NULL DEFAULT 0:
    -- như thế là tự nhận đã xác minh 40.000 quán còn mở trong khi chưa kiểm quán nào.
    permanently_closed       INTEGER,
    temporarily_closed       INTEGER,
    -- TUỔI THẬT: ngày NGUỒN cập nhật, khác hẳn `last_updated` (ngày ta cào).
    source_updated_at        TEXT,
    source_datasets          TEXT,     -- JSON: nền tảng nào cùng xác nhận
    surveyed_at              TEXT,     -- ngày có người xác minh tận nơi (OSM check_date)
    socials                  TEXT,     -- JSON: link Facebook/Instagram do nguồn cung cấp
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
    "reviews_count, mood_scores, atmosphere_tags, review_text, thumbnail_url, "
    "opening_hours, "
    "is_active, permanently_closed, temporarily_closed, "
    "source_updated_at, source_datasets, surveyed_at, socials, "
    "district, dietary, amenities, phone, website, source, "
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


def _bool_or_none(value) -> Optional[bool]:
    """NULL trong SQLite -> None, không phải False. Xem comment ở phần khai báo bảng."""
    return None if value is None else bool(value)


@dataclass(frozen=True)
class _Snapshot:
    """MỘT ảnh chụp dữ liệu quán: danh sách + bảng tra + số phiên bản, đi CÙNG nhau.

    VÌ SAO GOM LẠI (bug thật, rà soát 2026-10-06): bản cũ giữ `_restaurants` và
    `_by_place_id` là HAI thuộc tính, `reload()` xoá cả hai rồi gán lại bằng hai câu lệnh
    riêng. Request rơi vào khe giữa hai câu nhận `get_by_place_id() -> None` -> 404 cho
    quán đang tồn tại; rơi vào khe trước đó thì tự nạp lại toàn bộ CSDL lần nữa (~2 giây).
    Gom vào một đối tượng bất biến thì đổi dữ liệu chỉ còn MỘT phép gán thuộc tính — người
    đọc luôn thấy trọn bản cũ hoặc trọn bản mới, không bao giờ thấy nửa này nửa kia.
    """

    restaurants: Tuple[Restaurant, ...]
    by_place_id: Mapping[str, Restaurant]
    version: int


class SqliteRestaurantRepository:
    """Triển khai `RestaurantRepository` từ file SQLite.

    Nạp toàn bộ vào bộ nhớ MỘT LẦN giống bản CSV, vì `list_all()` được gọi ở MỖI lượt
    tìm kiếm - truy vấn lại CSDL mỗi lần sẽ chậm hơn hẳn mà không được gì. Sau khi Admin
    ghi dữ liệu thì gọi `reload()` để làm mới bộ nhớ đệm.

    `data_version` tăng sau MỖI lần nạp lại thành công. Thứ gì dựng từ `list_all()` rồi
    giữ lâu (chỉ mục món-quán) phải so số này để biết khi nào dữ liệu đã cũ — xem
    `infrastructure/adapters/live_dish_restaurant_index.py`.
    """

    def __init__(self, db_path: Path | str, eager: bool = True) -> None:
        self.db_path = Path(db_path)
        self._snapshot: Optional[_Snapshot] = None
        self._load_error: Optional[str] = None
        # Một lượt nạp tại một thời điểm: hai admin bấm cùng lúc thì lượt sau chờ, không
        # đọc CSDL hai lần song song. Người ĐỌC không bao giờ phải chờ khoá này (trừ lần
        # nạp đầu tiên, khi chưa có ảnh chụp nào để trả).
        self._load_lock = threading.Lock()
        self._version = 0
        self._reload_listeners: List[Callable[[], None]] = []
        if eager:
            self._ensure_loaded()

    # -- Port RestaurantRepository -------------------------------------------

    @property
    def is_ready(self) -> bool:
        return self._current() is not None

    def list_all(self) -> List[Restaurant]:
        snapshot = self._current()
        return list(snapshot.restaurants) if snapshot is not None else []

    def get_by_place_id(self, place_id: str) -> Optional[Restaurant]:
        snapshot = self._current()
        return snapshot.by_place_id.get(str(place_id)) if snapshot is not None else None

    # -- Phần thêm so với port ------------------------------------------------

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    @property
    def data_version(self) -> int:
        """Số phiên bản của ảnh chụp đang phục vụ. 0 = chưa nạp được gì."""
        snapshot = self._current()
        return snapshot.version if snapshot is not None else 0

    def add_reload_listener(self, callback: Callable[[], None]) -> None:
        """Đăng ký hàm được gọi SAU mỗi lần nạp lại thành công (sau khi admin ghi).

        Dùng để chỉ mục món-quán bắt đầu dựng lại NGAY trong nền, thay vì để người dùng
        đầu tiên sau đó phải chờ. Hàm được gọi ở luồng của request ghi, nên phải NHANH
        (VD chỉ khởi động một thread) — không được tự làm việc nặng ở đây.
        """
        self._reload_listeners.append(callback)

    def reload(self) -> None:
        """Nạp lại từ CSDL rồi THAY ảnh chụp trong MỘT phép gán. Admin PHẢI gọi sau khi
        ghi, nếu không người dùng vẫn thấy dữ liệu cũ cho tới lần khởi động lại.

        Trong lúc đang nạp (~2 giây trên 52.871 quán, đo 2026-10-06), người đọc vẫn được
        phục vụ bằng ảnh chụp CŨ - không 404, không tự nạp lại lần hai.

        Nạp lỗi (CSDL bị khoá, file hỏng giữa chừng) mà ĐÃ có ảnh chụp cũ thì GIỮ ảnh chụp
        cũ và ghi log: dữ liệu cũ vài giây tốt hơn hẳn việc cả app báo "chưa sẵn sàng".
        """
        with self._load_lock:
            snapshot, error = self._load_snapshot()
            if snapshot is not None:
                self._snapshot = snapshot
                self._load_error = None
            elif self._snapshot is None:
                self._load_error = error
            else:
                logger.error("Nạp lại CSDL quán thất bại, giữ dữ liệu cũ: %s", error)
                return
        if snapshot is not None:
            self._notify_reload()

    def status(self) -> dict:
        """Tự mô tả cho /health - cùng hình dạng với bản CSV để Container không phải
        biết đang dùng adapter nào."""
        snapshot = self._current()
        return {
            "ready": snapshot is not None,
            "source": describe_path(self.db_path),
            "count": len(snapshot.restaurants) if snapshot is not None else 0,
            "error": self._load_error,
        }

    # -- Port AdminRestaurantRepository (GHI) ---------------------------------
    #
    # Phần đọc ở trên phục vụ luồng người dùng cuối và LỌC BỎ quán đã ẩn. Phần dưới
    # phục vụ trang quản trị nên phải nhìn thấy CẢ quán đã ẩn - nếu không, ẩn xong sẽ
    # không còn cách nào bỏ ẩn.

    def list_for_admin(
        self,
        query: Optional[str] = None,
        limit: int = 50,
        include_hidden: bool = True,
        loc: Optional[str] = None,
    ) -> List[Restaurant]:
        """`loc` là bộ lọc VIỆC CẦN XỬ LÝ, để hộp "Cần xử lý" ở trang Tổng quan bấm sang
        được đúng danh sách. Giá trị hợp lệ do `domain/services/data_quality.py` đặt tên;
        giá trị lạ thì BỎ QUA (không lọc) chứ không báo lỗi — một khoá cũ trong đường dẫn
        đã lưu không đáng làm hỏng cả trang.
        """
        rows, _ = self.page_for_admin(
            AdminRestaurantFilter(query=query, include_hidden=include_hidden, loc=loc),
            offset=0,
            limit=limit,
        )
        return rows

    @staticmethod
    def _admin_where(filters: AdminRestaurantFilter) -> Tuple[str, List[object]]:
        """Mệnh đề WHERE dùng CHUNG cho trang dữ liệu và câu COUNT.

        Dùng chung là bắt buộc: hai bản điều kiện viết riêng sẽ có ngày lệch nhau, và
        "Hiển thị 1-20 của 4.933" sẽ nói sai số trang.
        """
        conditions: List[str] = []
        params: List[object] = []
        if filters.loc == "dong_tam":
            conditions.append("COALESCE(temporarily_closed, 0) = 1")
        elif filters.loc == "thieu_lien_he":
            # Thiếu CẢ HAI mới tính. Có website mà không có điện thoại thì vẫn liên hệ
            # được — cùng quy tắc với `viec_can_xu_ly` ở domain, đừng để hai nơi lệch nhau.
            conditions.append(
                "COALESCE(TRIM(phone), '') = '' AND COALESCE(TRIM(website), '') = ''"
            )
        if not filters.include_hidden:
            conditions.append("is_active = 1")
            # Quán đã đóng HẲN không bao giờ trả cho người dùng (xem `Restaurant.is_visible`).
            conditions.append("COALESCE(permanently_closed, 0) = 0")
        if filters.status == ADMIN_STATUS_VISIBLE:
            conditions.append("is_active = 1")
        elif filters.status == ADMIN_STATUS_HIDDEN:
            conditions.append("is_active = 0")
        if filters.district:
            conditions.append("district = ?")
            params.append(filters.district)
        if filters.source:
            if filters.source in MANUAL_SOURCES:
                cho = ", ".join("?" for _ in MANUAL_SOURCES)
                conditions.append(f"source IN ({cho})")
                params.extend(MANUAL_SOURCES)
            else:
                conditions.append("source = ?")
                params.append(filters.source)
        if filters.query:
            # LIKE không phân biệt hoa thường cho ASCII; tiếng Việt có dấu vẫn khớp
            # được vì admin thường gõ đúng tên hiển thị. Tìm kiếm cho NGƯỜI DÙNG mới
            # cần bỏ dấu - đó là việc của domain, không phải của lớp quản trị.
            conditions.append("(name LIKE ? OR place_id LIKE ? OR address LIKE ?)")
            params.extend([f"%{filters.query}%"] * 3)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        return where, params

    def page_for_admin(
        self, filters: AdminRestaurantFilter, offset: int, limit: int
    ) -> Tuple[List[Restaurant], int]:
        where, params = self._admin_where(filters)
        rows = self._read(
            f"SELECT {_COLUMNS} FROM restaurants{where} ORDER BY name LIMIT ? OFFSET ?",
            [*params, int(limit), max(0, int(offset))],
        )
        dem = self._read(f"SELECT COUNT(*) AS n FROM restaurants{where}", params)
        tong = int(dem[0]["n"]) if dem else 0
        return [r for r in (self._to_entity(row) for row in rows) if r], tong

    def stats_for_admin(self) -> AdminRestaurantStats:
        cho = ", ".join("?" for _ in MANUAL_SOURCES)
        tong = self._read(
            "SELECT COUNT(*) AS n, "
            "COALESCE(SUM(is_active = 1), 0) AS hien, "
            "COALESCE(SUM(is_active = 0), 0) AS an, "
            f"COALESCE(SUM(source IN ({cho})), 0) AS tay FROM restaurants",
            list(MANUAL_SOURCES),
        )
        khu_vuc = self._read(
            "SELECT district AS v, COUNT(*) AS n FROM restaurants "
            "WHERE COALESCE(TRIM(district), '') <> '' GROUP BY district ORDER BY n DESC, v",
            [],
        )
        nguon = self._read(
            "SELECT source AS v, COUNT(*) AS n FROM restaurants "
            "WHERE COALESCE(TRIM(source), '') <> '' GROUP BY source ORDER BY n DESC, v",
            [],
        )
        dong = tong[0] if tong else None
        return AdminRestaurantStats(
            total=int(dong["n"]) if dong else 0,
            visible=int(dong["hien"]) if dong else 0,
            hidden=int(dong["an"]) if dong else 0,
            manual=int(dong["tay"]) if dong else 0,
            districts=[(r["v"], int(r["n"])) for r in khu_vuc],
            sources=[(r["v"], int(r["n"])) for r in nguon],
        )

    def set_active_many(self, place_ids: Sequence[str], is_active: bool) -> List[str]:
        ma = list(dict.fromkeys(str(p) for p in place_ids if p))
        if not ma:
            return []
        cho = ", ".join("?" for _ in ma)
        co_that = [
            r["place_id"]
            for r in self._read(
                f"SELECT place_id FROM restaurants WHERE place_id IN ({cho})", ma
            )
        ]
        if co_that:
            cho_that = ", ".join("?" for _ in co_that)
            # MỘT câu UPDATE + MỘT lần nạp lại bộ đệm (trong `_write`), bất kể chọn bao
            # nhiêu quán — xem docstring của port.
            self._write(
                f"UPDATE restaurants SET is_active = ? WHERE place_id IN ({cho_that})",
                [1 if is_active else 0, *co_that],
            )
        return co_that

    def get_for_admin(self, place_id: str) -> Optional[Restaurant]:
        rows = self._read(
            f"SELECT {_COLUMNS} FROM restaurants WHERE place_id = ?", [str(place_id)]
        )
        return self._to_entity(rows[0]) if rows else None

    def create(self, restaurant: Restaurant) -> Restaurant:
        """Thêm quán mới (nhập tay qua trang quản trị).

        ⚠️ CHỈ ghi những cột người nhập thật sự cung cấp. `rating`, `reviews_count`,
        `mood_scores`, cụm trải nghiệm đều để NULL — None nghĩa là CHƯA CÓ DỮ LIỆU
        (CLAUDE.md mục 4 quy tắc 1). Đặt 0 vào đó là nói dối "0 sao".
        """
        cot = {
            "place_id": restaurant.place_id,
            "name": restaurant.name,
            "category": restaurant.category,
            "lat": restaurant.location.lat,
            "lng": restaurant.location.lng,
            "address": restaurant.address,
            "cuisine": restaurant.cuisine,
            "price": restaurant.price,
            "district": restaurant.district,
            "phone": restaurant.phone,
            "website": restaurant.website,
            "is_active": 1 if restaurant.is_active else 0,
            "source": restaurant.source,
            "data_confidence": restaurant.data_confidence,
            "source_updated_at": restaurant.source_updated_at,
        }
        ten_cot = ", ".join(cot)
        cho_trong = ", ".join("?" for _ in cot)
        try:
            with mo_ket_noi(self.db_path) as conn:
                conn.execute(
                    f"INSERT INTO restaurants ({ten_cot}) VALUES ({cho_trong})",
                    list(cot.values()),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            raise RestaurantAlreadyExists(restaurant.place_id or "")
        except sqlite3.Error as exc:
            logger.error("Lỗi thêm quán: %s", exc)
            raise
        # Làm mới bộ nhớ đệm, nếu không quán vừa thêm sẽ không tìm thấy cho tới lần
        # khởi động lại sau — cùng lý do như `_write()`.
        self.reload()
        return restaurant

    def update_fields(self, place_id: str, changes: Mapping[str, object]) -> bool:
        """Ghi các trường ĐÃ được domain kiểm tra.

        Tên cột được lọc qua `_WRITABLE_COLUMNS` chứ không ghép thẳng từ input: tên cột
        không thể tham số hoá trong SQL, nên đây là chốt chặn chống SQL injection.
        """
        columns = [c for c in changes if c in _WRITABLE_COLUMNS]
        if not columns:
            return False
        assignments = ", ".join(f"{c} = ?" for c in columns)
        params = [changes[c] for c in columns] + [str(place_id)]

        changed = self._write(
            f"UPDATE restaurants SET {assignments} WHERE place_id = ?", params
        )
        return changed > 0

    def set_active(self, place_id: str, is_active: bool) -> bool:
        changed = self._write(
            "UPDATE restaurants SET is_active = ? WHERE place_id = ?",
            [1 if is_active else 0, str(place_id)],
        )
        return changed > 0

    # -- Nội bộ: đọc/ghi ------------------------------------------------------

    def _read(self, sql: str, params: List[object]) -> List[sqlite3.Row]:
        """Truy vấn thẳng CSDL, KHÔNG qua bộ nhớ đệm.

        Trang quản trị phải thấy dữ liệu mới nhất ngay sau khi ghi. Bộ nhớ đệm chỉ phục
        vụ `list_all()` của luồng tìm kiếm, nơi tốc độ quan trọng hơn độ tươi.
        """
        self._ensure_loaded()
        if self._load_error is not None:
            return []
        try:
            with mo_ket_noi(
                f"file:{self.db_path.as_posix()}?mode=ro", uri=True
            ) as conn:
                conn.row_factory = sqlite3.Row
                return conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Lỗi đọc CSDL quản trị: %s", exc)
            return []

    def _write(self, sql: str, params: List[object]) -> int:
        """Ghi rồi LÀM MỚI bộ nhớ đệm.

        Quên `reload()` ở đây là bug âm thầm khó chịu nhất của thiết kế có cache: admin
        ẩn một quán, trang quản trị báo thành công, nhưng người dùng vẫn tìm thấy quán
        đó cho tới lần khởi động lại sau.
        """
        try:
            with mo_ket_noi(self.db_path) as conn:
                cursor = conn.execute(sql, params)
                conn.commit()
                changed = cursor.rowcount
        except sqlite3.Error as exc:
            logger.error("Lỗi ghi CSDL quản trị: %s", exc)
            return 0
        if changed:
            self.reload()
        return changed

    # -- Nội bộ ---------------------------------------------------------------

    def _current(self) -> Optional[_Snapshot]:
        """Ảnh chụp đang phục vụ. Đọc thuộc tính MỘT LẦN rồi dùng biến cục bộ, để một
        lượt `reload()` chen giữa không đổi được dữ liệu dưới chân người gọi."""
        snapshot = self._snapshot
        if snapshot is None:
            self._ensure_loaded()
            snapshot = self._snapshot
        return snapshot

    def _notify_reload(self) -> None:
        for callback in list(self._reload_listeners):
            try:
                callback()
            except Exception:  # noqa: BLE001 - việc phụ không được làm hỏng lượt ghi
                logger.exception("Hàm theo dõi nạp lại dữ liệu quán bị lỗi")

    def _ensure_loaded(self) -> None:
        """Nạp 1 lần. Thiếu file KHÔNG làm sập app - endpoint liên quan trả 503 kèm
        hướng dẫn khắc phục (CLAUDE.md mục 4 quy tắc 3)."""
        if self._snapshot is not None or self._load_error is not None:
            return
        with self._load_lock:
            # Kiểm lại SAU khi có khoá: luồng khác có thể vừa nạp xong trong lúc ta chờ.
            if self._snapshot is not None or self._load_error is not None:
                return
            snapshot, error = self._load_snapshot()
            if snapshot is not None:
                self._snapshot = snapshot
            else:
                self._load_error = error

    def _load_snapshot(self) -> Tuple[Optional[_Snapshot], Optional[str]]:
        """Đọc CSDL thành một ảnh chụp MỚI. KHÔNG đụng vào thuộc tính nào của `self`
        ngoài bộ đếm phiên bản — việc thay ảnh chụp là của người gọi, trong một phép gán.

        Chỉ gọi khi đang giữ `_load_lock`.
        """
        if not self.db_path.exists():
            return None, (
                f"Không tìm thấy CSDL: {describe_path(self.db_path)}. "
                "Chạy: python scripts/build_sqlite.py"
            )
        try:
            # read-only + uri=True: app chạy chỉ ĐỌC, không vô tình tạo file rỗng khi
            # gõ nhầm đường dẫn (sqlite3.connect mặc định TẠO file mới nếu chưa có -
            # đúng thứ sẽ biến "sai đường dẫn" thành "0 quán" mà không báo lỗi gì).
            uri = f"file:{self.db_path.as_posix()}?mode=ro"
            with mo_ket_noi(uri, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    f"SELECT {_COLUMNS} FROM restaurants WHERE is_active = 1 "
                    "AND COALESCE(permanently_closed, 0) = 0"
                ).fetchall()
        except sqlite3.Error as exc:
            return None, f"Không đọc được {describe_path(self.db_path)}: {exc}"

        restaurants = tuple(r for r in (self._to_entity(row) for row in rows) if r)
        self._version += 1
        return _Snapshot(
            restaurants=restaurants,
            by_place_id={r.place_id: r for r in restaurants if r.place_id is not None},
            version=self._version,
        ), None

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
            thumbnail_url=row["thumbnail_url"],
            opening_hours=row["opening_hours"],
            is_active=bool(row["is_active"]),
            permanently_closed=_bool_or_none(row["permanently_closed"]),
            temporarily_closed=_bool_or_none(row["temporarily_closed"]),
            source_updated_at=row["source_updated_at"],
            source_datasets=_json_list(row["source_datasets"]),
            surveyed_at=row["surveyed_at"],
            socials=_json_list(row["socials"]),
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

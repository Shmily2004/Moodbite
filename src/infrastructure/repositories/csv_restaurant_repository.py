"""ADAPTER: đọc quán từ CSV do data_pipeline sinh ra, trả về entity thuần Python.

Đây là RANH GIỚI duy nhất giữa pandas và phần còn lại của app. pandas dừng ở file này -
domain và application không bao giờ nhìn thấy DataFrame.

Vì sao đọc hết vào bộ nhớ 1 lần: 4170 dòng ~0.7MB, đọc 1 lần lúc khởi động rẻ hơn nhiều
so với cách cũ (df.copy() toàn bộ DataFrame ở MỖI request).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.domain.entities.restaurant import Restaurant
from src.domain.value_objects.location import Location
from src.domain.value_objects.mood import MOOD_SCORE_COLUMNS
from src.infrastructure.config.settings import describe_path

# Tên cột trong CSV -> ý nghĩa. Đổi tên cột ở data_pipeline thì sửa DUY NHẤT ở đây.
COL_PLACE_ID = "placeId"
COL_NAME = "title"
COL_CATEGORY = "categoryName"
COL_CUISINE = "cuisine"
COL_ADDRESS = "address"
COL_PRICE = "price"
COL_RATING = "totalScore"
COL_REVIEWS_COUNT = "reviewsCount"
COL_LAT = "location/lat"
COL_LNG = "location/lng"
COL_ATMOSPHERE = "additionalInfo/Bầu không khí"
COL_OPENING_HOURS = "openingHours"
COL_DISTRICT = "district"
COL_DIETARY = "dietary"
COL_AMENITIES = "amenities"
COL_PHONE = "phone"
COL_WEBSITE = "website"
COL_SOURCE = "source"
COL_CLUSTER_ID = "experience_cluster_id"
COL_CLUSTER_LABEL = "experience_cluster_label"
# Trạng thái kinh doanh từ nguồn. Chỉ quán Apify/Google mới có -> thiếu là `None`.
COL_PERMANENTLY_CLOSED = "permanentlyClosed"
COL_TEMPORARILY_CLOSED = "temporarilyClosed"
COL_CONFIDENCE = "data_confidence"

REQUIRED_COLUMNS = (COL_NAME, COL_LAT, COL_LNG)


def _clean(value):
    """NaN của pandas không phải JSON hợp lệ và không phải giá trị nghiệp vụ hợp lệ.

    Đổi thành None ngay tại ranh giới để domain chỉ làm việc với None.
    """
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        # Giá trị dạng list/dict -> pd.isna trả mảng, không phải bool.
        pass
    return value


def _as_float(value) -> Optional[float]:
    value = _clean(value)
    return None if value is None else float(value)


def _as_int(value) -> Optional[int]:
    value = _clean(value)
    return None if value is None else int(value)


def _as_str(value) -> Optional[str]:
    value = _clean(value)
    return None if value is None else str(value)


def _as_optional_bool(value) -> Optional[bool]:
    """BA trạng thái: True / False / None. `None` = nguồn không có trường này.

    KHÔNG được rút về hai trạng thái. "Không biết quán còn mở không" khác hẳn "biết chắc
    quán đang mở": 96,5% dataset (OSM + Overture) không có trường này, ép về `False` là
    tự nhận đã xác minh 40.000 quán mà thực ra chưa kiểm quán nào.
    """
    if value is None or (isinstance(value, float) and value != value):   # NaN
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "1", "1.0", "yes"):
        return True
    if text in ("false", "0", "0.0", "no"):
        return False
    return None


def _as_tags(value) -> List[str]:
    """Cột tag của Google Maps lưu dưới dạng chuỗi Python literal, ví dụ:
        "[{'Ấm cúng': True}, {'Thông thường': True}]"
    Trả về ["Ấm cúng", "Thông thường"]. Dữ liệu lạ -> trả rỗng, KHÔNG làm hỏng cả lượt nạp.

    Dùng ast.literal_eval chứ không dùng eval: literal_eval chỉ dựng được kiểu dữ liệu
    cơ bản, không thực thi được mã, nên an toàn với dữ liệu cào từ ngoài về.
    """
    text = _as_str(value)
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return []
    if not isinstance(parsed, list):
        return []
    tags: List[str] = []
    for entry in parsed:
        if isinstance(entry, dict):
            tags.extend(str(k) for k, v in entry.items() if v)
        elif isinstance(entry, str):
            tags.append(entry)
    return tags


def _as_list(value) -> List[str]:
    """Cột lưu danh sách dưới dạng chuỗi (`"['vegetarian', 'vegan']"`) -> list[str].

    Dữ liệu lạ trả rỗng thay vì ném lỗi: một ô hỏng không được làm hỏng cả lượt nạp.
    """
    if isinstance(value, list):
        return [str(v) for v in value if v]
    text = _as_str(value)
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return []
        return [str(v) for v in parsed if v] if isinstance(parsed, list) else []
    # Chuỗi ngăn cách bằng dấu phẩy hoặc chấm phẩy.
    return [part.strip() for part in re.split(r"[;,]", text) if part.strip()]


def _as_price(value) -> Optional[str]:
    """Giá là CHUỖI khoảng giá của Google Maps ("1-100.000 ₫", "70 US$"), không phải số.

    Chuẩn hoá non-breaking space (\\xa0) thành khoảng trắng thường để frontend hiển thị
    và xuống dòng bình thường.
    """
    text = _as_str(value)
    return None if text is None else text.replace("\xa0", " ").strip()


class CsvRestaurantRepository:
    """Triển khai RestaurantRepository từ file CSV."""

    def __init__(
        self,
        csv_path: Path | str,
        eager: bool = True,
        review_texts: Optional[Dict[str, str]] = None,
        thumbnail_urls: Optional[Dict[str, str]] = None,
    ) -> None:
        """`review_texts` ({place_id: nội dung review}) đến từ restaurant_details.json.

        Truyền vào từ ngoài thay vì để repository tự đọc file thứ hai: giữ cho mỗi
        repository chỉ có đúng MỘT nguồn dữ liệu, việc ghép nguồn là của composition root
        (dependencies.py). Nhờ vậy test có thể nạp CSV mà không cần file review.
        """
        self.csv_path = Path(csv_path)
        self._review_texts = review_texts or {}
        self._thumbnail_urls = thumbnail_urls or {}
        self._restaurants: Optional[List[Restaurant]] = None
        self._by_place_id: dict[str, Restaurant] = {}
        self._load_error: Optional[str] = None
        if eager:
            self._ensure_loaded()

    @property
    def is_ready(self) -> bool:
        self._ensure_loaded()
        return self._restaurants is not None

    def list_all(self) -> List[Restaurant]:
        """Quán ĐANG HIỆN cho người dùng - quán đã đóng hẳn bị loại ngay từ đây.

        Phải khớp hành vi của `SqliteRestaurantRepository.list_all` (nó lọc bằng SQL).
        Hai kho trả số lượng khác nhau là loại lỗi tệ nhất: đổi `MOODBITE_STORAGE` xong
        kết quả tìm kiếm đổi theo mà không ai hiểu vì sao.

        Bộ lọc ở tầng xếp hạng (`is_visible`) vẫn giữ nguyên làm lớp chặn thứ hai - lọc
        hai lần thì rẻ, còn lọt một lần là người dùng đi tới quán đã đóng cửa.
        """
        self._ensure_loaded()
        return [r for r in (self._restaurants or []) if r.is_visible]

    def get_by_place_id(self, place_id: str) -> Optional[Restaurant]:
        """Quán ĐANG HIỆN cho người dùng. Quán đã đóng hẳn coi như không tồn tại (404).

        Trả cả quán đã đóng thì trang chi tiết vẫn mở được từ link cũ hoặc bookmark, và
        người dùng đi tới nơi mới biết quán không còn.
        """
        self._ensure_loaded()
        found = self._by_place_id.get(str(place_id))
        return found if found is not None and found.is_visible else None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def status(self) -> dict:
        """Tự mô tả trạng thái cho /health. Mỗi adapter tự báo cáo, để Container không
        phải biết adapter cụ thể có những thuộc tính gì."""
        ready = self.is_ready
        return {
            "ready": ready,
            "source": describe_path(self.csv_path),
            "count": len(self._restaurants or []),
            "error": self._load_error,
        }

    def _ensure_loaded(self) -> None:
        """Nạp 1 lần. Thiếu file KHÔNG làm sập app - app chạy chế độ degraded và
        endpoint liên quan trả 503 kèm hướng dẫn khắc phục."""
        if self._restaurants is not None or self._load_error is not None:
            return
        if not self.csv_path.exists():
            self._load_error = f"Không tìm thấy dataset: {describe_path(self.csv_path)}"
            return
        try:
            # `low_memory=False`: đọc cả cột một lần thay vì theo từng khối, nên pandas
            # không phải đoán kiểu hai lần rồi cảnh báo `DtypeWarning` cho 14 cột trộn
            # kiểu (giá là chuỗi, giờ mở cửa là JSON...). Cảnh báo đó in ra ở MỌI lần khởi
            # động và mọi lần chạy test - tiếng ồn cỡ đó là chỗ tốt nhất để một cảnh báo
            # thật lẩn vào mà không ai thấy.
            df = pd.read_csv(self.csv_path, low_memory=False)
        except Exception as exc:  # file hỏng, thiếu quyền đọc...
            self._load_error = f"Không đọc được {describe_path(self.csv_path)}: {exc}"
            return

        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            self._load_error = (
                f"{describe_path(self.csv_path)} thiếu cột bắt buộc: {missing}. "
                "Chạy lại python -m data_pipeline.feature_engineering"
            )
            return

        restaurants = [r for r in (self._to_entity(row) for _, row in df.iterrows()) if r]
        self._restaurants = restaurants
        self._by_place_id = {
            r.place_id: r for r in restaurants if r.place_id is not None
        }

    def _to_entity(self, row) -> Optional[Restaurant]:
        lat, lng = _as_float(row.get(COL_LAT)), _as_float(row.get(COL_LNG))
        name = _as_str(row.get(COL_NAME))
        # Quán thiếu toạ độ hoặc tên thì không thể xếp hạng/hiển thị -> bỏ qua thay vì
        # để nổ ở giữa vòng lặp tính khoảng cách.
        if lat is None or lng is None or not name:
            return None
        try:
            location = Location(lat=lat, lng=lng)
        except ValueError:
            return None

        place_id = _as_str(row.get(COL_PLACE_ID))
        return Restaurant(
            place_id=place_id,
            name=name,
            category=_as_str(row.get(COL_CATEGORY)),
            location=location,
            address=_as_str(row.get(COL_ADDRESS)),
            cuisine=_as_str(row.get(COL_CUISINE)),
            price=_as_price(row.get(COL_PRICE)),
            rating=_as_float(row.get(COL_RATING)),
            reviews_count=_as_int(row.get(COL_REVIEWS_COUNT)),
            mood_scores={
                col: (_as_float(row.get(col)) or 0.0) for col in MOOD_SCORE_COLUMNS
            },
            atmosphere_tags=_as_tags(row.get(COL_ATMOSPHERE)),
            opening_hours=_as_str(row.get(COL_OPENING_HOURS)),
            review_text=self._review_texts.get(place_id) if place_id else None,
            thumbnail_url=self._thumbnail_urls.get(place_id) if place_id else None,
            district=_as_str(row.get(COL_DISTRICT)),
            dietary=_as_list(row.get(COL_DIETARY)),
            amenities=_as_list(row.get(COL_AMENITIES)),
            phone=_as_str(row.get(COL_PHONE)),
            website=_as_str(row.get(COL_WEBSITE)),
            source=_as_str(row.get(COL_SOURCE)),
            data_confidence=_as_str(row.get(COL_CONFIDENCE)),
            experience_cluster_id=_as_int(row.get(COL_CLUSTER_ID)),
            experience_cluster_label=_as_str(row.get(COL_CLUSTER_LABEL)),
            permanently_closed=_as_optional_bool(row.get(COL_PERMANENTLY_CLOSED)),
            temporarily_closed=_as_optional_bool(row.get(COL_TEMPORARILY_CLOSED)),
        )

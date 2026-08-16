"""HỢP ĐỒNG CHUNG cho mọi nguồn dữ liệu quán ăn.

VÌ SAO CÓ FILE NÀY: trước đây mỗi lần thêm nguồn là viết một script riêng với định dạng
riêng (`scrape_osm_hanoi.py`, `scrapers/foody_parser.py`, `scrapers/toididau_parser.py`),
rồi phải sửa cả pipeline để hiểu định dạng mới. Nay mọi nguồn đều trả về CÙNG một cấu
trúc `RawPlace`, nên thêm nguồn mới = viết 1 adapter, KHÔNG đụng vào pipeline.

Luồng dữ liệu:

    SourceAdapter.fetch()  ->  list[RawPlace]  ->  data_raw/NN_<source>.json
                                                        |
                                merge_and_prepare_raw.py  (gộp + khử trùng lặp)
                                                        |
                                        data_cleaning.py -> feature_engineering.py

Mọi bản ghi BẮT BUỘC có `source`, `source_url`, `last_updated`, `data_confidence` —
để sau này luôn trả lời được "field này ở đâu ra, đáng tin tới mức nào".
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

# Mức độ tin cậy của một bản ghi.
#   verified   = có định danh chính thức + dữ liệu phong phú (VD Google Places)
#   community  = dữ liệu cộng đồng đóng góp, có thể thiếu/cũ (VD OpenStreetMap)
#   derived    = do hệ thống tự suy ra (VD quận suy từ toạ độ)
CONFIDENCE_VERIFIED = "verified"
CONFIDENCE_COMMUNITY = "community"
CONFIDENCE_DERIVED = "derived"


@dataclass
class RawPlace:
    """Một quán ăn ở dạng CHUẨN HOÁ, trước khi vào pipeline.

    Tên field giữ đúng quy ước cũ (`title`, `placeId`, `location`, `categoryName`) để
    `merge_and_prepare_raw.py` và `feature_engineering.py` đọc được mà không phải sửa.
    """

    # --- định danh ---
    placeId: str
    title: str
    source: str
    source_url: Optional[str] = None
    last_updated: Optional[str] = None
    data_confidence: str = CONFIDENCE_COMMUNITY

    # --- phân loại ---
    categoryName: Optional[str] = None
    cuisine: Optional[str] = None
    aliases: List[str] = field(default_factory=list)

    # --- vị trí ---
    location: Dict[str, Any] = field(default_factory=dict)   # {"lat": ..., "lng": ...}
    address: Optional[str] = None
    district: Optional[str] = None
    # Quận có thể do nguồn cung cấp (community) hoặc do hệ thống suy từ toạ độ (derived).
    # Tách riêng khỏi `data_confidence` để không nhập nhằng độ tin cậy của cả bản ghi.
    district_confidence: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    countryCode: str = "VN"

    # --- liên hệ ---
    phone: Optional[str] = None
    website: Optional[str] = None
    openingHours: Optional[Any] = None

    # --- chất lượng / phổ biến ---
    price: Optional[str] = None
    totalScore: Optional[float] = None
    reviewsCount: Optional[int] = None
    imagesCount: Optional[int] = None

    # --- tiện nghi & thuộc tính (dùng cho lọc và xếp hạng theo ngữ cảnh) ---
    amenities: List[str] = field(default_factory=list)       # outdoor_seating, air_conditioning...
    dietary: List[str] = field(default_factory=list)         # vegetarian, vegan, halal
    delivery: Optional[bool] = None
    takeaway: Optional[bool] = None
    delivery_platforms: List[str] = field(default_factory=list)

    # --- món ăn (nếu nguồn có) ---
    dishes: List[str] = field(default_factory=list)
    menu: Optional[str] = None

    def to_record(self) -> Dict[str, Any]:
        """Chuyển sang dict để ghi ra JSON cho pipeline đọc."""
        data = asdict(self)
        if not data.get("last_updated"):
            data["last_updated"] = utc_now_iso()
        return data


def utc_now_iso() -> str:
    """Thời điểm hiện tại dạng ISO-8601 UTC, đúng quy ước ở Data Dictionary mục 2.1."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@runtime_checkable
class SourceAdapter(Protocol):
    """Hợp đồng mà mọi nguồn dữ liệu phải tuân theo.

    Thêm nguồn mới (Google Places, ShopeeFood, website quán...) = tạo 1 class thoả
    protocol này rồi đăng ký ở `sources/__init__.py`. KHÔNG cần sửa pipeline.
    """

    @property
    def name(self) -> str:
        """Tên ngắn, dùng làm tên file output và giá trị field `source`."""
        ...

    def is_available(self) -> tuple[bool, str]:
        """(dùng được không, lý do). Ví dụ thiếu API key -> (False, 'thiếu GOOGLE_API_KEY').

        Cho phép `harvest.py` bỏ qua nguồn chưa cấu hình mà KHÔNG làm hỏng cả lượt chạy.
        """
        ...

    def fetch(self) -> List[RawPlace]:
        """Lấy dữ liệu về. Được phép chậm; nên tự cache để chạy lại không tốn công."""
        ...


def dedupe_places(places: List[RawPlace]) -> tuple[List[RawPlace], int]:
    """Khử trùng lặp TRONG một nguồn theo placeId. Trả (danh sách sạch, số bị loại).

    Khử trùng lặp GIỮA các nguồn do `merge_and_prepare_raw.py` lo (theo placeId hoặc
    cặp title+address), vì lúc đó mới nhìn thấy đủ mọi nguồn.
    """
    seen: set[str] = set()
    unique: List[RawPlace] = []
    for place in places:
        if place.placeId in seen:
            continue
        seen.add(place.placeId)
        unique.append(place)
    return unique, len(places) - len(unique)

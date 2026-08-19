"""Nguồn quán ăn từ OVERTURE MAPS — dữ liệu POI mở, KHÔNG phải OSM, KHÔNG phải Google.

    python -m data_pipeline.harvest --source overture --city ha_noi

VÌ SAO NGUỒN NÀY
----------------
Chủ dự án cần THÊM QUÁN từ nguồn ngoài OSM/Google, nhưng `CLAUDE.md` mục 4b CẤM thu thập
từ ShopeeFood, GrabFood, Foody, TripAdvisor, Facebook (ToS của họ cấm truy cập tự động).

Overture Maps Foundation phát hành dữ liệu POI theo giấy phép **CDLA Permissive 2.0** —
tải về hợp pháp, không cần khoá API, không cần thẻ thanh toán. Dữ liệu Places do Meta và
Microsoft đóng góp, nên KHÁC tập OSM đang có: đo được trong bbox Hà Nội có **307.562 POI**
(2026-07-22.0), trong khi lượt cào OSM trước đó chỉ ra vài nghìn quán ăn.

Cũng đã thử và LOẠI: **Wikidata** chỉ có 5 nhà hàng ở toàn Việt Nam — không đáng làm nguồn.

CÁCH LẤY MÀ KHÔNG LÀM ĐẦY Ổ CỨNG
--------------------------------
Bộ Places toàn cầu nặng hàng chục GB. KHÔNG tải hết. DuckDB đọc parquet trực tiếp trên S3
và đẩy điều kiện lọc xuống tầng đọc file (predicate pushdown) nhờ cột `bbox` có sẵn trong
lược đồ Overture, nên chỉ những row group chạm vào Hà Nội mới được tải về.

Kết quả lọc được ghi ra MỘT file parquet nhỏ trong `.overture_cache/` và dùng lại ở các
lần chạy sau — lần hai gần như không tốn mạng.

HAI ĐIỀU ĐÃ TRẢ GIÁ ĐỂ HỌC (lượt chạy 2026-08-19)
-------------------------------------------------
1. `ST_GeomFromWKB` cần extension `spatial`, không có sẵn -> truy vấn chết giữa chừng.
   Places của Overture là ĐIỂM, nên `bbox.xmin == xmax == kinh độ`: dùng thẳng `bbox` vừa
   khỏi cần extension vừa nhanh hơn vì không phải giải mã WKB.
2. Đường dẫn phải là `.../theme=places/type=place/*.zstd.parquet` (đuôi `.zstd.parquet`,
   không phải `.parquet`), và tên bản phát hành phải tra từ S3 chứ đừng đoán.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from data_pipeline.sources.base import (
    CONFIDENCE_COMMUNITY,
    CONFIDENCE_VERIFIED,
    RawPlace,
    utc_now_iso,
)
from data_pipeline.sources.osm_overpass import CITY_BBOXES, HANOI_BBOX

logger = logging.getLogger(__name__)

# Thư mục S3 công khai của Overture. Không cần khoá, không cần đăng nhập.
S3_BUCKET = "s3://overturemaps-us-west-2/release"
S3_LIST_URL = (
    "https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/"
    "?list-type=2&delimiter=/&prefix=release/"
)
PLACES_GLOB = "theme=places/type=place/*.zstd.parquet"

# Bản phát hành dùng khi không tra được danh sách (VD máy đang offline nhưng đã có cache).
FALLBACK_RELEASE = "2026-07-22.0"

# Danh mục Overture được coi là QUÁN ĂN UỐNG.
#
# Overture dùng taxonomy phẳng, các từ nối bằng gạch dưới ("vietnamese_restaurant",
# "coffee_shop"). KHỚP THEO TỪ, KHÔNG khớp chuỗi con.
#
# BUG THẬT đã mắc ở bản đầu (2026-08-19): khớp chuỗi con với "pub" làm
# "public_and_government_association" (673 POI) bị nhận là quán bia, và "food" làm
# "health_food_store" (874 POI) bị nhận là quán ăn. Đây đúng là lỗi "oc khớp Ngọc" mà
# dự án đã trả giá một lần ở `value_objects/text.py` - đừng lặp lại lần thứ ba.
FOOD_TOKENS = frozenset({
    "restaurant", "restaurants", "cafe", "cafes", "coffee", "bar", "bars", "pub",
    "pubs", "bakery", "bistro", "diner", "deli", "canteen", "steakhouse",
    "pizzeria", "brewery", "brasserie", "eatery", "buffet", "izakaya",
    "teahouse", "creperie", "taqueria", "cafeteria",
})

# Danh mục nhiều từ mà xét từng từ thì không ra: "tea" một mình là lá trà (cửa hàng),
# nhưng "tea_room" là quán. Liệt kê đích danh.
FOOD_EXACT_CATEGORIES = frozenset({
    "eat_and_drink", "food_court", "coffee_shop", "tea_room", "bubble_tea",
    "ice_cream_shop", "juice_bar", "food_stand", "food_truck", "street_vendor",
    "dessert_shop", "donut_shop", "bagel_shop", "sandwich_shop", "noodle_house",
    "hot_pot", "barbecue", "dim_sum", "sushi_bar", "wine_bar", "beer_garden",
    "beer_hall", "cocktail_bar", "night_club", "karaoke",
})

# Từ cho biết đây là CỬA HÀNG/DỊCH VỤ chứ không phải chỗ ngồi ăn. Chặn kể cả khi danh mục
# có chứa từ "food"/"coffee" (VD "health_food_store", "coffee_wholesaler").
NON_FOOD_TOKENS = frozenset({
    "store", "market", "supermarket", "grocery", "wholesaler", "wholesale",
    "distributor", "supply", "supplier", "manufacturer", "manufacturing",
    "association", "school", "equipment", "bank", "factory", "farm",
    "processing", "packaging", "rental", "catering",
})

# Overture -> nhãn tiếng Việt, dùng CHUNG bộ từ vựng với nguồn OSM để
# `dish_knowledge_base.json` và bộ lọc mood khớp được.
CATEGORY_LABELS = (
    ("coffee", "Quán cà phê"),
    ("cafe", "Quán cà phê"),
    ("tea", "Quán trà"),
    ("bakery", "Tiệm bánh"),
    ("dessert", "Tiệm bánh ngọt"),
    ("ice_cream", "Quán kem"),
    ("juice", "Quán nước ép"),
    ("bar", "Quán bar"),
    ("pub", "Quán bia"),
    ("brewery", "Quán bia"),
    ("fast_food", "Nhà hàng ăn nhanh"),
    ("food_court", "Khu ăn uống"),
    ("restaurant", "Nhà hàng"),
)

# Ngưỡng tin cậy của Overture. Bản ghi dưới ngưỡng thường là POI trùng lặp hoặc đã đóng
# cửa. 0.5 chọn theo phân bố thật, KHÔNG phải số bịa - xem báo cáo lúc chạy `fetch()`.
MIN_CONFIDENCE = 0.5


class OverturePlacesSource:
    """Adapter Overture Maps. Thoả `SourceAdapter` ở `sources/base.py`."""

    def __init__(
        self,
        bbox: tuple[float, float, float, float] = HANOI_BBOX,
        city: str = "ha_noi",
        release: Optional[str] = None,
        cache_dir: Path | str = "data_pipeline/data_raw/.overture_cache",
        min_confidence: float = MIN_CONFIDENCE,
    ) -> None:
        self.bbox = bbox
        self.city = city
        self.release = release
        self.cache_dir = Path(cache_dir)
        self.min_confidence = min_confidence

    @property
    def name(self) -> str:
        return "overture"

    def is_available(self) -> tuple[bool, str]:
        """Cần `duckdb`. Thiếu thì báo rõ cách cài, KHÔNG làm hỏng cả lượt harvest."""
        try:
            import duckdb  # noqa: F401
        except ImportError:
            return False, "thieu thu vien duckdb - cai bang: pip install duckdb"
        return True, "san sang"

    # --- lấy dữ liệu ---------------------------------------------------------

    def _cache_file(self) -> Path:
        return self.cache_dir / f"{self.city}_places.parquet"

    def _latest_release(self) -> str:
        """Tra bản phát hành mới nhất trên S3.

        Tra thay vì hardcode: Overture ra bản mới hàng tháng, và đoán tên bản thì sai -
        đã thử 7 cái tên hợp lý, không cái nào tồn tại.
        """
        if self.release:
            return self.release
        try:
            import re

            import requests

            response = requests.get(S3_LIST_URL, timeout=60)
            response.raise_for_status()
            releases = re.findall(r"<Prefix>release/([^<]+)/</Prefix>", response.text)
            if releases:
                return sorted(releases)[-1]
        except Exception as exc:
            logger.warning("Khong tra duoc ban phat hanh moi nhat (%s)", exc)
        return FALLBACK_RELEASE

    def _download_to_cache(self) -> Path:
        """Lọc theo bbox rồi ghi ra parquet nhỏ ở máy. Đã có cache thì dùng lại."""
        import duckdb

        cache_file = self._cache_file()
        if cache_file.exists() and cache_file.stat().st_size > 0:
            logger.info("Dung cache co san: %s", cache_file)
            return cache_file

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        release = self._latest_release()
        south, west, north, east = self.bbox
        source_path = f"{S3_BUCKET}/{release}/{PLACES_GLOB}"

        logger.info("Tai Overture %s cho '%s' (co the mat 5-20 phut)...", release, self.city)
        con = duckdb.connect()
        con.execute("INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2';")
        # `bbox` nằm sẵn trong lược đồ Overture -> DuckDB đẩy điều kiện xuống tầng đọc
        # file, chỉ tải về những row group chạm vào thành phố này.
        con.execute(
            f"""
            COPY (
              SELECT id,
                     names.primary  AS name,
                     categories.primary AS category,
                     confidence,
                     bbox.xmin AS lng,
                     bbox.ymin AS lat,
                     addresses, websites, phones, socials
              FROM read_parquet('{source_path}')
              WHERE bbox.xmin BETWEEN {west} AND {east}
                AND bbox.ymin BETWEEN {south} AND {north}
                AND categories.primary IS NOT NULL
            ) TO '{cache_file.as_posix()}' (FORMAT PARQUET)
            """
        )
        con.close()
        logger.info("Da ghi cache: %s", cache_file)
        return cache_file

    def fetch(self) -> List[RawPlace]:
        import duckdb

        cache_file = self._download_to_cache()
        con = duckdb.connect()
        rows = con.execute(
            f"SELECT * FROM read_parquet('{cache_file.as_posix()}')"
        ).fetchdf().to_dict("records")
        con.close()

        total = len(rows)
        places: List[RawPlace] = []
        dropped_not_food = 0
        dropped_low_confidence = 0

        for row in rows:
            category = (row.get("category") or "").lower()
            if not _is_food(category):
                dropped_not_food += 1
                continue
            confidence = float(row.get("confidence") or 0.0)
            if confidence < self.min_confidence:
                dropped_low_confidence += 1
                continue
            place = self._to_place(row, category, confidence)
            if place is not None:
                places.append(place)

        logger.info(
            "Overture '%s': %d POI -> %d quan an uong "
            "(bo %d khong phai an uong, %d duoi nguong tin cay %.2f)",
            self.city, total, len(places), dropped_not_food,
            dropped_low_confidence, self.min_confidence,
        )
        return places

    def _to_place(
        self, row: Dict[str, Any], category: str, confidence: float
    ) -> Optional[RawPlace]:
        name = (row.get("name") or "").strip()
        if not name:
            # Không tên thì không hiển thị được cho người dùng, cũng không khớp món được.
            return None
        try:
            lat = float(row["lat"])
            lng = float(row["lng"])
        except (KeyError, TypeError, ValueError):
            return None

        return RawPlace(
            # Tiền tố nguồn để không bao giờ đụng id với OSM/Google khi gộp dữ liệu.
            placeId=f"overture:{row.get('id')}",
            title=name,
            source="overture",
            source_url="https://overturemaps.org/",
            last_updated=utc_now_iso(),
            # Overture tự chấm `confidence`; bản ghi điểm cao thường có nguồn chính thức.
            data_confidence=(
                CONFIDENCE_VERIFIED if confidence >= 0.8 else CONFIDENCE_COMMUNITY
            ),
            categoryName=_label_for(category),
            location={"lat": lat, "lng": lng},
            address=_first_address(row.get("addresses")),
            phone=_first_of(row.get("phones")),
            website=_first_of(row.get("websites")),
        )


def _is_food(category: str) -> bool:
    """Danh mục này có phải chỗ ăn uống không.

    Khớp theo TỪ (tách bằng gạch dưới), không khớp chuỗi con - xem giải thích ở
    `FOOD_TOKENS`. Thứ tự xét: danh mục đích danh -> loại cửa hàng -> khớp từ.
    """
    normalized = (category or "").strip().lower()
    if not normalized:
        return False
    if normalized in FOOD_EXACT_CATEGORIES:
        return True

    tokens = set(normalized.split("_"))
    if tokens & NON_FOOD_TOKENS:
        return False
    return bool(tokens & FOOD_TOKENS)


def _label_for(category: str) -> str:
    """Danh mục Overture -> nhãn tiếng Việt.

    Duyệt theo THỨ TỰ trong `CATEGORY_LABELS`: mục cụ thể ("fast_food") phải đứng trước
    mục chung ("restaurant"), nếu không "fast_food_restaurant" bị gán nhầm "Nhà hàng".
    """
    normalized = (category or "").strip().lower()
    for hint, label in CATEGORY_LABELS:
        if hint in normalized:
            return label
    return "Nhà hàng"


def _first_of(value: Any) -> Optional[str]:
    """Overture trả mảng cho phones/websites. Lấy phần tử đầu, rỗng thì None."""
    if value is None:
        return None
    if isinstance(value, str):
        return value or None
    try:
        items = [str(v) for v in value if v]
    except TypeError:
        return None
    return items[0] if items else None


def _first_address(value: Any) -> Optional[str]:
    """Địa chỉ Overture là mảng struct {freeform, locality, region, country}."""
    if value is None:
        return None
    try:
        items = list(value)
    except TypeError:
        return None
    for item in items:
        if isinstance(item, str):
            try:
                item = json.loads(item)
            except (ValueError, TypeError):
                return item or None
        if isinstance(item, dict):
            parts = [item.get("freeform"), item.get("locality"), item.get("region")]
            joined = ", ".join(p for p in parts if p)
            if joined:
                return joined
    return None


def bbox_for_city(city: str) -> tuple[float, float, float, float]:
    """Dùng CHUNG bảng thành phố với nguồn OSM - thêm thành phố một lần, cả hai nguồn dùng được."""
    if city not in CITY_BBOXES:
        raise ValueError(f"Khong co thanh pho '{city}'. Co: {sorted(CITY_BBOXES)}")
    return CITY_BBOXES[city]

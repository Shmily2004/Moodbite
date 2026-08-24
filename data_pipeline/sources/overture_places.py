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
    # --- Bổ sung 2026-08-23 sau khi SOÁT danh mục bị loại -----------------
    # Rà 218.907 POI bị loại "không phải ăn uống", lọc ra những danh mục có chữ liên quan
    # đồ ăn rồi xét từng cái một. Bảy cái dưới đây đúng là CHỖ NGƯỜI TA NGỒI ĂN (+784 POI):
    "food",           # 460 — danh mục chung chung nhưng vẫn là hàng ăn
    "desserts",       # 139 — dạng số nhiều, `dessert_shop` ở trên không phủ
    "delicatessen",   # 123 — quán bán đồ nguội ăn tại chỗ
    "gastropub",      #  38
    "night_market",   #  12 — chợ đêm là nơi ăn uống ở Việt Nam, khác hẳn chợ mua bán
    "donuts",         #   9
    "soul_food",      #   3
    # CỐ Ý KHÔNG LẤY, dù tên có chữ đồ ăn — đây là CỬA HÀNG/DỊCH VỤ, không phải chỗ ăn:
    #   health_food_store (820) · farmers_market (136) · specialty_foods (25)
    #   restaurant_equipment_and_supply (92) · food_delivery_service (91)
    #   food_consultant (28) · restaurant_wholesale (27) · food_tours (27)
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

# Ngưỡng tin cậy của Overture.
#
# HẠ 0.5 -> 0.2 ngày 2026-08-24, SAU KHI ĐO, không phải để lấy cho nhiều.
#
# Giả định cũ ("dưới ngưỡng thường là POI trùng lặp hoặc đã đóng cửa") KHÔNG đứng vững
# khi soi vào 14.386 POI ăn uống bị 0.5 loại ở Hà Nội (bản 2026-08-19.0):
#   - 100% có TÊN, 100% có ĐỊA CHỈ, 83% có SỐ ĐIỆN THOẠI
#   - 100% được nguồn cập nhật trong năm 2026
#   - chỉ 10,8% trùng tên với bản ghi đã nhận -> phần lớn KHÔNG phải bản sao
#   - số nền tảng đóng góp = 1,0 ở MỌI dải điểm, kể cả dải 0.8-1.0. Tức `confidence`
#     KHÔNG phản ánh "được mấy nguồn xác nhận" như từng đoán.
# Tên thật ở dải bị loại đều là quán ăn Hà Nội: "Bún riêu cua Nga Sơn",
# "Bún chả Thanh Tâm CS 2", "Chè Sài Gòn Thập Cẩm", "Tiệm Bánh Bé Bin".
#
# VÌ SAO DỪNG Ở 0.2 CHỨ KHÔNG LẤY HẾT: tỷ lệ có số điện thoại - dấu hiệu đo được duy
# nhất về chất lượng bản ghi - tụt hẳn ở dải dưới 0.2 (74,9% và 81,7%) so với dải
# 0.2-0.35 (89,9% / 89,3% / 86,4%). Cắt ở 0.2 bỏ 949 bản ghi yếu nhất và giữ ~13.400.
#
# AN TOÀN: điểm gốc vẫn được ghi nguyên vào `source_confidence` của mọi bản ghi, nên
# tầng xếp hạng hạ điểm quán ít bằng chứng lúc nào cũng được, không mất thông tin.
MIN_CONFIDENCE = 0.2


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
        """Tên cache PHẢI kèm BẢN PHÁT HÀNH.

        ⚠️ BUG THẬT, sửa 2026-08-23: bản cũ đặt tên `ha_noi_places.parquet` không kèm gì
        cả. Overture ra bản mới hàng tháng và `_latest_release()` tra đúng bản mới, nhưng
        rồi lại thấy file cache cũ và dùng luôn — nghĩa là **cào lại bao nhiêu lần cũng ra
        đúng dữ liệu của tháng đầu tiên**, mà không có lấy một dòng log nào báo. Kèm tên
        bản vào thì bản mới tự sinh file mới, bản cũ vẫn còn đó để đối chiếu.
        """
        # ⚠️ PHẢI KÈM CẢ BBOX, không chỉ bản phát hành. Sửa 2026-08-24 — đây là LẦN THỨ BA
        # cùng một loại lỗi trong dự án (Overture quên bản phát hành 08-23, OSM quên nội
        # dung query 08-24). Ngày 2026-08-24 bbox Hà Nội được sửa từ
        # (20.85,105.70,21.40,106.05) thành (20.55,105.28,21.40,106.03) vì bản cũ cắt mất
        # 1/3 thành phố; nếu tên cache không đổi theo thì lượt cào "vùng mới" sẽ đọc trúng
        # file cũ và trả về ĐÚNG dữ liệu thiếu đó, không một dòng log nào báo.
        vung = "_".join(f"{v:.4f}" for v in self.bbox)
        return self.cache_dir / f"{self.city}_{vung}_places_{self._latest_release()}.parquet"

    def _latest_release(self) -> str:
        """Tra bản phát hành mới nhất trên S3.

        Tra thay vì hardcode: Overture ra bản mới hàng tháng, và đoán tên bản thì sai -
        đã thử 7 cái tên hợp lý, không cái nào tồn tại.
        """
        if self.release:
            return self.release
        # Nhớ lại: `_cache_file()` gọi hàm này nhiều lần, không nhớ thì mỗi lần lại đi
        # hỏi S3 một vòng.
        if getattr(self, "_release_da_tra", None):
            return self._release_da_tra
        try:
            import re

            import requests

            response = requests.get(S3_LIST_URL, timeout=60)
            response.raise_for_status()
            releases = re.findall(r"<Prefix>release/([^<]+)/</Prefix>", response.text)
            if releases:
                self._release_da_tra = sorted(releases)[-1]
                return self._release_da_tra
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
                     addresses, websites, phones, socials,
                     -- TUỔI THẬT + BẰNG CHỨNG. Cột `sources` vốn ĐÃ nằm trong parquet ta
                     -- tải về, chỉ là trước đây không lấy ra. Không tốn thêm một byte
                     -- mạng nào. Đo 2026-08-19: 99,7% bản ghi cập nhật trong năm 2026 -
                     -- tươi hơn hẳn OSM (34,9%), nhưng ta không hề ghi lại nên không
                     -- chứng minh được.
                     list_transform(sources, x -> x.dataset)     AS src_datasets,
                     list_max(list_transform(sources, x -> CAST(x.update_time AS VARCHAR)))
                                                                AS src_updated_at
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
            source_updated_at=_as_text(row.get("src_updated_at")),
            # Bỏ "Overture" khỏi danh sách: bản ghi nào cũng có nên nó không phân biệt
            # được gì. Cái đáng giữ là nền tảng ĐÓNG GÓP (meta, Microsoft, Foursquare...).
            source_datasets=[
                str(d) for d in _danh_sach(row.get("src_datasets"))
                if d is not None and str(d) and str(d).lower() != "overture"
            ],
            source_confidence=confidence,
            socials=[
                str(x) for x in _danh_sach(row.get("socials"))
                if x is not None and str(x)
            ],
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


def _as_text(value: Any) -> Optional[str]:
    """Chuỗi hoặc None. DuckDB trả về NaN/NaT cho ô trống, không phải None."""
    if value is None or (isinstance(value, float) and value != value):
        return None
    text = str(value).strip()
    return text or None


def _danh_sach(value: Any) -> list:
    """Đưa một ô của DuckDB/Arrow về `list` Python, an toàn với mọi kiểu.

    ⚠️ LỖI THẬT, sửa 2026-08-23: bản cũ viết `row.get("src_datasets") or []`. Với bản phát
    hành Overture 2026-08-19, cột đó về dưới dạng **mảng numpy**, và `mảng or []` ném
    `ValueError: The truth value of an array with more than one element is ambiguous` —
    cả lượt cào 40.000 quán chết ngay giữa chừng.

    Không dùng `or` với thứ có thể là mảng. Kiểm `None` tường minh, rồi ép sang list.
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    try:
        return list(value)
    except TypeError:
        return []


def _first_of(value: Any) -> Optional[str]:
    """Overture trả mảng cho phones/websites. Lấy phần tử đầu, rỗng thì None."""
    if value is None:
        return None
    if isinstance(value, str):
        return value or None
    # Đi qua `_danh_sach` để không lặp lại lỗi `mảng or []` — xem ghi chú ở đó.
    items = [str(v) for v in _danh_sach(value) if v is not None and str(v)]
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

"""
MoodBite - Cào dữ liệu quán ăn/nhà hàng Hà Nội từ OpenStreetMap (Overpass API).

VÌ SAO DÙNG OSM THAY VÌ APIFY/GOOGLE MAPS:
- Hoàn toàn miễn phí, không giới hạn số lượng, không cần tài khoản/API key.
- Dữ liệu công khai (Open Database License - ODbL), hợp pháp để dùng cho nghiên cứu/sản phẩm,
  miễn là ghi công nguồn "© OpenStreetMap contributors" khi hiển thị dữ liệu ra người dùng cuối.
- Nhược điểm: độ phủ tại Việt Nam có thể mỏng hơn Google Maps ở một số khu vực (phụ thuộc
  cộng đồng OSM địa phương đã map tới đâu) -> nên dùng BỔ SUNG cho data Apify đã có,
  không thay thế hoàn toàn.

CHỈ LẤY ĐỒ ĂN CHO NGƯỜI:
  Danh sách amenity/shop dùng ở đây được chọn thủ công, CHỈ gồm các loại phục vụ đồ ăn/thức uống
  cho người (restaurant, fast_food, cafe, bar, pub, food_court, ice_cream). KHÔNG có bất kỳ tag
  liên quan thú cưng nào (shop=pet, amenity=veterinary, ...) vì đây là whitelist (chỉ lấy đúng
  loại đã liệt kê), không phải blacklist -> không có rủi ro lọt đồ thú cưng vào.

  Lưu ý: KHÔNG lấy shop=bakery — nhất quán với quy tắc đã có trong filter_restaurants.py
  (dự án đã quyết định loại tiệm bánh ra khỏi phạm vi đề xuất món ăn).

OUTPUT: file JSON có field TRÙNG với schema của *_raw_places.json đã có sẵn
  (title, address, categoryName, location.lat/lng, phone, ...) để chạy thẳng qua
  `python -m data_pipeline.merge_and_prepare_raw` mà không cần sửa gì thêm.

CÁCH DÙNG:
    pip install requests --break-system-packages
    python -m data_pipeline.scrape_osm_hanoi

LƯU Ý: Script này cần kết nối mạng tới overpass-api.de - môi trường sandbox dùng để
phát triển code này KHÔNG có quyền truy cập domain đó, nên chưa được test chạy thật.
Hãy tự chạy thử trên máy bạn và báo lại nếu Overpass đổi format response.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Danh sách endpoint công khai của Overpass API - thử lần lượt nếu 1 server quá tải (rate limit).
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# Whitelist các loại địa điểm phục vụ đồ ăn/uống cho NGƯỜI.
# Xem đầy đủ giá trị amenity tại: https://wiki.openstreetmap.org/wiki/Key:amenity
FOOD_AMENITY_VALUES = [
    "restaurant",
    "fast_food",
    "cafe",
    "bar",
    "pub",
    "biergarten",
    "food_court",
    "ice_cream",
]

# Tên khu vực để Overpass tự phân giải ranh giới hành chính (chính xác hơn bounding box thủ công).
DEFAULT_AREA_NAME = "Hà Nội"


def _build_overpass_query(area_name: str, amenity_values: List[str], timeout_s: int = 180) -> str:
    amenity_regex = "|".join(amenity_values)
    # Hà Nội thật trải dài 20°53'-21°23' N, 105°44'-106°02' E (nguồn: Cổng thông tin
    # điện tử Hà Nội). Bbox trước đó (21.0,105.7,21.15,105.9) chỉ phủ khu vực trung
    # tâm, BỎ SÓT toàn bộ dải phía bắc (Sóc Sơn, Đông Anh, khu vực sân bay Nội Bài) -
    # đây là nguyên nhân chính khiến nhiều quán ở các quận/huyện ngoại thành bị thiếu.
    # Dùng bbox rộng hơn 1 chút so với ranh giới hành chính chính thức cho an toàn.
    return f"""
[out:json][timeout:{timeout_s}];
(
  nwr["amenity"~"^({amenity_regex})$"](20.85,105.70,21.40,106.05);
);
out center tags;
""".strip()


def _fetch_overpass(query: str) -> Optional[Dict[str, Any]]:
    # overpass-api.de bắt đầu chặn (406) các request thiếu header Accept/Accept-Encoding
    # đầy đủ hoặc dùng User-Agent generic (kể từ 2026). Cần gửi đủ 3 header dưới đây,
    # không chỉ User-Agent, để không bị coi là bot và bị từ chối.
    headers = {
        "User-Agent": "MoodBiteThesisProject/1.0 (dat-do-an-tot-nghiep; contact-via-github-Shmily2004)",
        "Accept": "application/json, application/osm3s+xml, */*",
        "Accept-Encoding": "gzip, deflate, br",
    }
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            logger.info(f"Đang gọi Overpass API: {endpoint}")
            response = requests.post(endpoint, data={"data": query}, headers=headers, timeout=200)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Endpoint {endpoint} lỗi: {e}. Thử endpoint tiếp theo...")
            time.sleep(2)
    logger.error("Tất cả endpoint Overpass đều lỗi.")
    return None


def _element_to_place_record(element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Chuyển 1 element Overpass (node/way/relation) thành record đúng schema
    của *_raw_places.json để tương thích trực tiếp với filter_restaurants.py
    và merge_and_prepare_raw.py."""
    tags = element.get("tags", {})
    name = tags.get("name") or tags.get("name:vi") or tags.get("name:en")
    if not name:
        # Bỏ qua địa điểm không có tên - không dùng được cho việc đề xuất món ăn.
        return None

    # node có lat/lon trực tiếp; way/relation dùng "center" (do query có `out center`).
    lat = element.get("lat") or (element.get("center") or {}).get("lat")
    lon = element.get("lon") or (element.get("center") or {}).get("lon")
    if lat is None or lon is None:
        return None

    amenity = tags.get("amenity", "")
    category_map = {
        "restaurant": "Nhà hàng",
        "fast_food": "Nhà hàng ăn nhanh",
        "cafe": "Quán cà phê",
        "bar": "Quán bar",
        "pub": "Quán bia",
        "biergarten": "Quán bia sân vườn",
        "food_court": "Khu ăn uống",
        "ice_cream": "Nhà hàng tráng miệng",
    }
    category_name = category_map.get(amenity, amenity)

    address_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb") or tags.get("addr:neighbourhood"),
        tags.get("addr:district"),
        tags.get("addr:city", "Hà Nội"),
    ]
    address = ", ".join(p for p in address_parts if p) or None

    return {
        "title": name,
        "subTitle": None,
        "description": tags.get("description"),
        "price": tags.get("price_range"),
        "categoryName": category_name,
        "address": address,
        "neighborhood": tags.get("addr:suburb") or tags.get("addr:neighbourhood"),
        "street": tags.get("addr:street"),
        "city": tags.get("addr:city", "Hà Nội"),
        "postalCode": tags.get("addr:postcode"),
        "state": tags.get("addr:city", "Hà Nội"),
        "countryCode": "VN",
        "phone": tags.get("phone") or tags.get("contact:phone"),
        "phoneUnformatted": tags.get("phone") or tags.get("contact:phone"),
        "location": {"lat": str(lat), "lng": str(lon)},
        "plusCode": None,
        "placeId": f"osm-{element.get('type')}-{element.get('id')}",
        "categories": [category_name],
        "fid": None,
        "cid": None,
        "reviewsCount": None,
        "imagesCount": None,
        "scrapedAt": None,
        "source": "openstreetmap",
        "website": tags.get("website") or tags.get("contact:website"),
        "openingHours": tags.get("opening_hours"),
        "cuisine": tags.get("cuisine"),
    }


def scrape_hanoi_food_places(
    area_name: str = DEFAULT_AREA_NAME,
    amenity_values: Optional[List[str]] = None,
    output_path: Optional[Path] = None,
) -> Optional[Path]:
    amenity_values = amenity_values or FOOD_AMENITY_VALUES
    query = _build_overpass_query(area_name, amenity_values)

    result = _fetch_overpass(query)
    if not result:
        return None

    elements = result.get("elements", [])
    logger.info(f"Overpass trả về {len(elements)} element thô (node/way/relation).")

    records = []
    for el in elements:
        record = _element_to_place_record(el)
        if record:
            records.append(record)

    logger.info(f"Chuyển đổi thành công {len(records)} record có tên hợp lệ.")

    if not records:
        logger.warning("Không có record nào - kiểm tra lại area_name hoặc kết nối mạng.")
        return None

    if output_path is None:
        output_path = Path.cwd() / "data_pipeline" / "data_raw" / "04_raw_places_osm.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    logger.info(f"Đã lưu {len(records)} record vào {output_path}")
    logger.info("Bước tiếp theo: chạy `python -m data_pipeline.merge_and_prepare_raw` để gộp với data Apify cũ.")
    logger.info('Lưu ý: khi hiển thị dữ liệu này ra người dùng, cần ghi công "© OpenStreetMap contributors".')

    return output_path


if __name__ == "__main__":
    scrape_hanoi_food_places()
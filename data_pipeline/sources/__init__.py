"""Đăng ký các nguồn dữ liệu.

THÊM NGUỒN MỚI (VD Google Places) chỉ gồm 3 bước, KHÔNG đụng vào pipeline:
    1. Tạo `sources/<ten_nguon>.py` với class thoả `SourceAdapter` ở `base.py`
    2. Thêm vào `AVAILABLE_SOURCES` bên dưới
    3. Chạy `python -m data_pipeline.harvest --source <ten_nguon>`
"""
from data_pipeline.sources.base import (
    CONFIDENCE_COMMUNITY,
    CONFIDENCE_DERIVED,
    CONFIDENCE_VERIFIED,
    RawPlace,
    SourceAdapter,
    dedupe_places,
)
from data_pipeline.sources.osm_overpass import OsmOverpassSource
from data_pipeline.sources.overture_places import OverturePlacesSource

# {tên nguồn: hàm khởi tạo}. Dùng lambda để chỉ khởi tạo khi thực sự cần.
AVAILABLE_SOURCES = {
    "openstreetmap": OsmOverpassSource,
    # Overture Maps (CDLA Permissive 2.0) - dữ liệu POI của Meta/Microsoft, KHÔNG phải
    # OSM và KHÔNG phải Google. Cần `pip install duckdb`.
    "overture": OverturePlacesSource,
}

__all__ = [
    "AVAILABLE_SOURCES",
    "RawPlace",
    "SourceAdapter",
    "OsmOverpassSource",
    "OverturePlacesSource",
    "dedupe_places",
    "CONFIDENCE_COMMUNITY",
    "CONFIDENCE_DERIVED",
    "CONFIDENCE_VERIFIED",
]

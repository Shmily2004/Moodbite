"""USE CASE: lấy chi tiết 1 quán (giá, review thật, ảnh, giờ mở cửa)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.application.errors import DataNotReadyError
from src.application.ports.restaurant_details_repository import (
    RestaurantDetailsRepository,
)

# Lý do trả về khi quán tồn tại nhưng chưa cào được phần chi tiết.
NO_DETAILS_REASON = (
    "Quán này lấy từ OpenStreetMap, chưa có dữ liệu giá/review/ảnh."
)


@dataclass(frozen=True)
class RestaurantDetails:
    place_id: str
    has_details: bool
    reason: Optional[str] = None
    name: Optional[str] = None
    price: Optional[str] = None
    atmosphere: Optional[object] = None
    opening_hours: Optional[object] = None
    images: List[str] = field(default_factory=list)
    reviews: List[dict] = field(default_factory=list)
    menu_url: Optional[str] = None
    website: Optional[str] = None
    google_maps_url: Optional[str] = None


class GetRestaurantDetailsUseCase:
    def __init__(self, details: RestaurantDetailsRepository) -> None:
        self._details = details

    def execute(self, place_id: str) -> RestaurantDetails:
        if not self._details.is_ready:
            raise DataNotReadyError(
                "dữ liệu chi tiết quán",
                "chạy python -m data_pipeline.feature_engineering",
            )

        raw = self._details.get(place_id)
        if raw is None:
            # KHÔNG phải 404: quán vẫn tồn tại và vẫn được đề xuất, chỉ là chưa cào được
            # phần chi tiết. Trả has_details=False để UI hiện "chưa có dữ liệu".
            return RestaurantDetails(
                place_id=place_id, has_details=False, reason=NO_DETAILS_REASON
            )

        return RestaurantDetails(
            place_id=place_id,
            has_details=True,
            name=raw.get("title"),
            price=raw.get("price"),
            atmosphere=raw.get("additionalInfo/Bầu không khí"),
            opening_hours=raw.get("openingHours"),
            images=raw.get("imageUrls", []) or [],
            reviews=raw.get("reviews", []) or [],
            # Google Maps hầu như KHÔNG có menu có cấu trúc (chỉ ~2% quán ở Hà Nội),
            # nên thay vì bịa dữ liệu, trả link để người dùng tự xem menu tại nguồn.
            menu_url=raw.get("menu"),
            website=raw.get("website"),
            google_maps_url=raw.get("url"),
        )

"""Toạ độ và khoảng cách. Thuần Python - KHÔNG import pandas/FastAPI."""
from __future__ import annotations

import math
from dataclasses import dataclass

EARTH_RADIUS_KM = 6371.0

# Điểm mặc định của API khi client không gửi vị trí: Hồ Hoàn Kiếm, Hà Nội.
HANOI_CENTER_LAT = 21.0285
HANOI_CENTER_LNG = 105.8542


@dataclass(frozen=True)
class Location:
    lat: float
    lng: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.lat <= 90.0:
            raise ValueError(f"lat phải trong [-90, 90], nhận được {self.lat}")
        if not -180.0 <= self.lng <= 180.0:
            raise ValueError(f"lng phải trong [-180, 180], nhận được {self.lng}")

    def distance_km(self, other: "Location") -> float:
        """Khoảng cách đường chim bay (haversine).

        LƯU Ý: đây KHÔNG phải quãng đường đi thật. Quán cách 2km đường chim bay có thể
        phải đi 4km vì sông/ngõ cụt. Muốn số thật cần Google Routes API (tốn tiền/request)
        - xem docs/google_maps_integration.md.
        """
        lat1, lng1, lat2, lng2 = map(
            math.radians, [self.lat, self.lng, other.lat, other.lng]
        )
        d_lat = lat2 - lat1
        d_lng = lng2 - lng1
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(d_lng / 2) ** 2
        )
        return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


HANOI_CENTER = Location(lat=HANOI_CENTER_LAT, lng=HANOI_CENTER_LNG)

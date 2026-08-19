"""USE CASE: lấy chi tiết 1 quán (giá, review thật, ảnh, giờ mở cửa)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping, Optional

from src.application.errors import DataNotReadyError
from src.application.ports.restaurant_details_repository import (
    RestaurantDetailsRepository,
)
from src.application.ports.restaurant_repository import RestaurantRepository
from src.application.use_cases.log_interaction import RestaurantNotFoundError

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
    # LỚP 4 đề án: nhận xét tổng hợp từ review. `None` = quán chưa đủ review để tóm tắt
    # (dưới 3 review), KHÔNG phải "quán không có gì để nói".
    review_summary: Optional[dict] = None


class GetRestaurantDetailsUseCase:
    def __init__(
        self,
        details: RestaurantDetailsRepository,
        restaurants: Optional[RestaurantRepository] = None,
        review_summaries: Optional[Mapping[str, dict]] = None,
    ) -> None:
        """`restaurants` để kiểm quán CÓ TỒN TẠI và CÓ ĐANG HIỆN hay không.

        VÌ SAO CẦN THÊM (bug thật, phát hiện 2026-08-17 bằng test end-to-end):
        use case này trước đây chỉ biết kho CHI TIẾT, mà kho đó không có khái niệm
        `is_active`. Hậu quả: admin ẩn một quán, quán biến mất khỏi /search đúng như
        mong đợi, NHƯNG `GET /restaurants/{id}` vẫn trả 200 — quán bị ẩn vẫn xem được
        nếu biết link. Test đơn vị không bắt được vì chúng chỉ kiểm ở tầng repository.

        `review_summaries` là kết quả LỚP 4 đã tính sẵn offline
        (`python -m data_pipeline.review_summary`). Nhận qua tham số thay vì tự đọc file:
        use case không được biết đường dẫn file nào cả - việc lắp dây là của
        `dependencies.py`. Không truyền -> phần nhận xét tổng hợp đơn giản là vắng mặt,
        các thứ khác vẫn chạy.
        """
        self._details = details
        self._review_summaries = review_summaries or {}
        self._restaurants = restaurants

    def execute(self, place_id: str) -> RestaurantDetails:
        if not self._details.is_ready:
            raise DataNotReadyError(
                "dữ liệu chi tiết quán",
                "chạy python -m data_pipeline.feature_engineering",
            )

        # Không tồn tại HOẶC đã bị ẩn (is_active=false) -> 404, theo bảng mã lỗi ở
        # CLAUDE.md mục 5. `get_by_place_id()` đã tự lọc quán bị ẩn.
        # Kho quán chưa sẵn sàng thì BỎ QUA phép kiểm này thay vì trả 404 cho tất cả:
        # thiếu một nguồn dữ liệu không được biến thành "mọi quán đều không tồn tại".
        if self._restaurants is not None and self._restaurants.is_ready:
            if self._restaurants.get_by_place_id(place_id) is None:
                raise RestaurantNotFoundError(f"Không tìm thấy quán: {place_id}")

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
            # LỚP 4: nhận xét tổng hợp đã tính sẵn. Quán chưa đủ review thì vắng mặt.
            review_summary=self._review_summaries.get(place_id),
        )

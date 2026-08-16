"""PORT: hợp đồng đọc CHI TIẾT 1 quán (giá, review thật, ảnh, giờ mở cửa).

Tách khỏi RestaurantRepository vì 2 việc có đặc tính hoàn toàn khác nhau:
  - Xếp hạng: cần TOÀN BỘ 4170 quán nhưng chỉ vài cột nhẹ, chạy ở mọi request.
  - Xem chi tiết: chỉ cần ĐÚNG 1 quán nhưng kèm dữ liệu nặng (review, ảnh).
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class RestaurantDetailsRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        ...

    def get(self, place_id: str) -> Optional[dict]:
        """Chi tiết 1 quán, None nếu quán chưa có dữ liệu chi tiết.

        None là trường hợp BÌNH THƯỜNG chứ không phải lỗi: phần lớn quán đến từ
        OpenStreetMap vốn không có giá/review/ảnh.
        """
        ...

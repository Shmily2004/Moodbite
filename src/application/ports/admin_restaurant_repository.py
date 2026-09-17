"""PORT: hợp đồng GHI dữ liệu quán, dành riêng cho luồng quản trị.

Tách khỏi `RestaurantRepository` (chỉ đọc) CÓ CHỦ ĐÍCH: luồng của người dùng cuối
tuyệt đối không cần khả năng ghi, nên không được nhìn thấy nó. Repository CSV cố tình
KHÔNG triển khai port này — CSV không ghi an toàn được (ghi đè cả file, không có
transaction). Chỉ `SqliteRestaurantRepository` triển khai.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping, Optional, Protocol, Sequence, Tuple, runtime_checkable

from src.domain.entities.restaurant import Restaurant


class RestaurantAlreadyExists(Exception):
    """`place_id` đã tồn tại -> HTTP 409."""


# Giá trị `source` của quán do NGƯỜI nhập qua trang quản trị. `CreateRestaurantUseCase`
# ghi `manual`; `admin` giữ lại cho dữ liệu cũ/nhập hàng loạt về sau.
MANUAL_SOURCES: Tuple[str, ...] = ("manual", "admin")

# Trạng thái hợp lệ của bộ lọc. Giá trị lạ = không lọc (cùng quy ước với `loc`).
ADMIN_STATUS_VISIBLE = "visible"
ADMIN_STATUS_HIDDEN = "hidden"


@dataclass(frozen=True)
class AdminRestaurantFilter:
    """Bộ lọc của bảng quản trị quán. Mọi trường `None` = không lọc theo trường đó."""

    query: Optional[str] = None
    include_hidden: bool = True
    loc: Optional[str] = None
    district: Optional[str] = None
    # `manual` gộp cả `MANUAL_SOURCES` — tab "Nhập tay" của bản thiết kế.
    source: Optional[str] = None
    status: Optional[str] = None


@dataclass(frozen=True)
class AdminRestaurantStats:
    """Thẻ số + giá trị cho các ô chọn ở đầu trang quản lý quán. Tính trên TOÀN BỘ bảng."""

    total: int
    visible: int
    hidden: int
    manual: int
    # [(giá trị, số quán)], nhiều nhất đứng đầu.
    districts: List[Tuple[str, int]] = field(default_factory=list)
    sources: List[Tuple[str, int]] = field(default_factory=list)


@runtime_checkable
class AdminRestaurantRepository(Protocol):
    def list_for_admin(
        self,
        query: Optional[str] = None,
        limit: int = 50,
        include_hidden: bool = True,
        loc: Optional[str] = None,
    ) -> List[Restaurant]:
        """Danh sách cho trang quản trị. `loc` lọc theo VIỆC CẦN XỬ LÝ.

        `loc` hợp lệ: `dong_tam` (nguồn báo đóng tạm) · `thieu_lien_he` (không có cả
        điện thoại lẫn website). Giá trị lạ = không lọc, không báo lỗi.

        KHÁC `list_all()` ở chỗ MẶC ĐỊNH có cả quán đã ẩn — admin phải nhìn thấy quán
        mình vừa ẩn, nếu không sẽ không có cách nào bỏ ẩn lại.
        """
        ...

    def page_for_admin(
        self, filters: AdminRestaurantFilter, offset: int, limit: int
    ) -> Tuple[List[Restaurant], int]:
        """Một TRANG kết quả + TỔNG số quán khớp bộ lọc (để phân trang ở server).

        Tổng phải do tầng lưu trữ đếm (COUNT), không phải kéo hết rồi `len()`: bảng có
        52.854 quán.
        """
        ...

    def stats_for_admin(self) -> AdminRestaurantStats:
        """Đếm tổng / đang hiện / đã ẩn / nhập tay + danh sách khu vực và nguồn."""
        ...

    def set_active_many(self, place_ids: Sequence[str], is_active: bool) -> List[str]:
        """Ẩn/bỏ ẩn NHIỀU quán trong MỘT giao dịch. Trả các `place_id` thật sự tồn tại.

        Có riêng vì `set_active` từng cái sẽ nạp lại bộ đệm 52.854 quán sau MỖI quán — chọn
        50 quán là 50 lần nạp lại.
        """
        ...

    def get_for_admin(self, place_id: str) -> Optional[Restaurant]:
        """1 quán, KỂ CẢ khi đã ẩn. `get_by_place_id()` thường bỏ qua quán ẩn."""
        ...

    def create(self, restaurant: Restaurant) -> Restaurant:
        """Thêm quán MỚI. Ném `RestaurantAlreadyExists` nếu `place_id` đã có.

        Kiểm trùng phải do TẦNG LƯU TRỮ làm (ràng buộc UNIQUE), không phải SELECT trước
        rồi INSERT — hai request cùng lúc sẽ cùng vượt qua phép kiểm đó.
        """
        ...

    def update_fields(self, place_id: str, changes: Mapping[str, object]) -> bool:
        """Ghi các trường đã được kiểm tra. Trả False nếu không có quán nào khớp."""
        ...

    def set_active(self, place_id: str, is_active: bool) -> bool:
        """Ẩn (soft-delete) hoặc bỏ ẩn. Trả False nếu không có quán nào khớp."""
        ...

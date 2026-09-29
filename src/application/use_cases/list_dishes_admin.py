"""USE CASE quản trị: liệt kê DANH MỤC MÓN.

Khoảng trống rõ nhất của trang quản trị trước 2026-08-26: admin quản lý được quán nhưng
KHÔNG có màn nào cho 855 món — trong khi "chọn món trước, tìm quán sau" mới là luồng
chính của sản phẩm.

KHÁC HẲN `/dishes/suggest` CỦA NGƯỜI DÙNG, và đây là điểm dễ nhầm nhất:

  |                    | người dùng                  | quản trị (file này)          |
  |--------------------|-----------------------------|------------------------------|
  | Món chưa có quán   | ẨN HẲN                      | **PHẢI THẤY** (557 món)      |
  | Danh mục ("Bún")   | ẩn khỏi lưới gợi ý          | **PHẢI THẤY** (14 mục)       |
  | Xếp theo           | điểm phù hợp với ngữ cảnh   | số quán, rồi tên             |
  | Cần vị trí         | có                          | không                        |

Admin cần thấy ĐÚNG những thứ người dùng không được thấy — đó chính là việc của họ: tìm
món thiếu ảnh, thiếu mô tả, hoặc chưa khớp được quán nào.

PHÂN TRANG Ở SERVER (2026-09-16): trước đó bảng bị cắt cứng 50 dòng, nên 805 món còn lại
không có cách nào xem được ngoài việc gõ tìm kiếm.

⚠️ CHỈ ĐỌC. Sửa/ẩn món qua trang quản trị chưa làm: `dish_catalog.json` là file do
`scripts/build_dish_catalog.py` SINH RA, nên ghi thẳng vào đó sẽ bị lần chạy sau xoá
sạch. Muốn sửa được thì phải chuyển danh mục món sang SQLite trước — việc riêng, chưa làm.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from src.application.errors import DataNotReadyError
from src.domain.entities.dish import Dish
from src.domain.value_objects.text import contains_phrase, normalize

MAX_TRANG = 200
# Mặc định 20 dòng/trang: bản thiết kế `dish management admin.png` vẽ 10, nhưng bảng món
# có ảnh + mô tả hai dòng nên 20 dòng vẫn vừa một lần cuộn trên laptop.
DEFAULT_PAGE_SIZE = 20
# Tab "Danh sách quán" ở trang chi tiết món chỉ cần đủ để admin kiểm "khớp có đúng không".
MAX_QUAN_CUA_MON = 100


class DishCatalogNotReady(DataNotReadyError):
    def __init__(self) -> None:
        super().__init__(
            "danh mục món chưa nạp được",
            "Chạy: python scripts/build_dish_catalog.py rồi khởi động lại backend.",
        )


@dataclass(frozen=True)
class DishAdminRow:
    """Một dòng trong bảng quản trị món. Chỉ những trường bảng thật sự hiện."""

    dish_id: str
    name: str
    cuisine: Optional[str]
    image_url: Optional[str]
    has_description: bool
    is_category: bool
    is_active: bool
    source: Optional[str]
    # Đoạn giới thiệu ĐẦY ĐỦ (dài nhất đo được 320 ký tự, 2026-09-16). Trước khi có phân
    # trang, bảng kéo cả 855 đoạn nên chỉ trả cờ; nay mỗi trang tối đa `MAX_TRANG` dòng
    # nên trả thẳng, giao diện tự cắt hiển thị.
    description: Optional[str] = None
    # Ngày NGUỒN cập nhật giới thiệu món. Chỉ 126/855 món có (2026-09-16) — `None` thì
    # giao diện hiện "—", KHÔNG được thay bằng ngày dựng danh mục.
    last_updated: Optional[str] = None
    # Số quán khớp món — ĐÚNG chỉ mục mà `/dishes/{id}/restaurants` dùng. `None` = chỉ mục
    # chưa được lắp (khác hẳn 0 quán).
    restaurant_count: Optional[int] = None

    @classmethod
    def tu_dish(cls, d: Dish, so_quan: Optional[int] = None) -> "DishAdminRow":
        return cls(
            dish_id=d.identifier,
            name=d.name,
            cuisine=d.cuisine,
            image_url=d.image_url,
            has_description=d.has_description,
            is_category=d.is_category,
            is_active=d.is_active,
            source=d.source,
            description=d.description if d.has_description else None,
            last_updated=d.last_updated or None,
            restaurant_count=so_quan,
        )


# Bộ lọc trên giao diện. Khoá là chuỗi client gửi lên.
BO_LOC = ("all", "with_restaurants", "without_restaurants", "missing_image", "missing_description")


def _dieu_kien_loc(loc: str):
    if loc == "with_restaurants":
        return lambda d: d.is_active
    if loc == "without_restaurants":
        return lambda d: not d.is_active
    if loc == "missing_image":
        return lambda d: not (d.image_url or "").strip()
    if loc == "missing_description":
        return lambda d: not d.has_description
    return lambda d: True


@dataclass(frozen=True)
class DishAdminPage:
    rows: List[DishAdminRow]
    # Tổng khớp (từ khoá + bộ lọc) — để phân trang.
    total: int
    page: int
    page_size: int
    # Số món của TỪNG bộ lọc, tính SAU từ khoá nhưng TRƯỚC bộ lọc: đúng con số người quản
    # trị sẽ thấy nếu bấm nút đó.
    counts: Dict[str, int] = field(default_factory=dict)
    # Hai thẻ số đầu trang — trên TOÀN BỘ danh mục, không đổi theo tìm kiếm.
    dishes_total: int = 0
    dishes_with_restaurants: int = 0


class ListDishesForAdminUseCase:
    """Danh mục món cho quản trị, PHÂN TRANG ở server.

    `dish_restaurant_index` là CHÍNH chỉ mục `{dish_id: [DishMatch]}` dựng một lần lúc khởi
    động ở `dependencies.py` và dùng cho `/dishes/{id}/restaurants`. Dùng lại nó thay vì
    đếm lại: viết bộ khớp thứ hai là hai con số "có bao nhiêu quán" lệch nhau ngay lần đầu
    ai đó sửa luật khớp. Đếm `len()` trên chỉ mục đã có là O(số món), không tốn gì.
    """

    def __init__(
        self,
        dish_catalog: object,
        dish_restaurant_index: Optional[Mapping[str, Sequence]] = None,
    ) -> None:
        self.dish_catalog = dish_catalog
        self._index = dish_restaurant_index

    def _so_quan(self, d: Dish) -> Optional[int]:
        if self._index is None:
            return None
        # Chỉ mục dựng từ món ĐANG BẬT; món tắt vắng mặt nghĩa là chưa khớp quán nào.
        return len(self._index.get(d.identifier, ()))

    def execute(
        self,
        query: Optional[str] = None,
        loc: str = "all",
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> DishAdminPage:
        if not getattr(self.dish_catalog, "is_ready", False):
            raise DishCatalogNotReady()

        # TOÀN BỘ món kể cả món tắt — xem bảng so sánh ở đầu file.
        tat_ca: List[Dish] = list(self.dish_catalog.list_all_dishes())

        tu_khoa = (query or "").strip()
        theo_tu_khoa = [d for d in tat_ca if _khop(d, tu_khoa)] if tu_khoa else tat_ca

        counts = {
            khoa: sum(1 for d in theo_tu_khoa if _dieu_kien_loc(khoa)(d)) for khoa in BO_LOC
        }
        mon = [d for d in theo_tu_khoa if _dieu_kien_loc(loc)(d)]

        # Xếp: món CÓ quán trước (việc chính của admin nằm ở đó), rồi theo tên không dấu
        # để "Ốc" không bị đẩy xuống cuối bảng chữ cái.
        mon.sort(key=lambda d: (not d.is_active, normalize(d.name)))

        co = max(1, min(int(page_size), MAX_TRANG))
        trang = max(1, int(page))
        dau = (trang - 1) * co
        return DishAdminPage(
            rows=[DishAdminRow.tu_dish(d, self._so_quan(d)) for d in mon[dau : dau + co]],
            total=len(mon),
            page=trang,
            page_size=co,
            counts=counts,
            dishes_total=len(tat_ca),
            dishes_with_restaurants=sum(1 for d in tat_ca if d.is_active),
        )


def _khop(d: Dish, tu_khoa: str) -> bool:
    """Khớp theo TÊN hoặc MÃ món.

    Dùng `contains_phrase` của domain chứ KHÔNG tự viết `in`: quy tắc bỏ dấu + khớp từ
    nguyên vẹn + "dấu là bằng chứng" đã có ba bug thật vì viết lại bằng tay
    (CLAUDE.md mục 4 quy tắc 5). Ở đây admin gõ "pho" phải ra "Phở bò" chứ không ra
    "Tào phớ".
    """
    if contains_phrase(d.name, tu_khoa):
        return True
    # Mã món là chuỗi slug không dấu, so trực tiếp là đúng.
    return normalize(tu_khoa).replace(" ", "-") in d.identifier


@dataclass(frozen=True)
class DishRestaurantMatch:
    """Một quán khớp món, kèm CÁCH khớp — cho tab "Danh sách quán" ở trang chi tiết món.

    Trả kèm `matched_by` vì đây là thứ admin cần nhất khi kiểm tra: quán ghi đúng tên món
    ("Bún Chả Hương Liên") khác hẳn quán chỉ được review nhắc tới. Món là SUY LUẬN theo
    tên quán, không phải thực đơn thật (CLAUDE.md mục 4 quy tắc 4).
    """

    restaurant: object
    matched_by: str


@dataclass(frozen=True)
class DishRestaurantsPage:
    total: int
    results: List[DishRestaurantMatch]


class GetDishForAdminUseCase:
    """Một món cho trang quản trị, KỂ CẢ món đang tắt.

    ⚠️ KHÔNG dùng lại `GET /dishes/{id}` của người dùng: endpoint đó đọc `list_dishes()`
    nên 557 món chưa có quán sẽ trả 404 — đúng với người dùng, sai hoàn toàn với admin.
    Admin mở trang quản lý món chính là để xem những món đó.
    """

    def __init__(
        self,
        dish_catalog: object,
        dish_restaurant_index: Optional[Mapping[str, Sequence]] = None,
    ) -> None:
        self.dish_catalog = dish_catalog
        self._index = dish_restaurant_index

    def execute(self, dish_id: str) -> Optional[Dish]:
        if not getattr(self.dish_catalog, "is_ready", False):
            raise DishCatalogNotReady()
        ma = (dish_id or "").strip()
        return next(
            (d for d in self.dish_catalog.list_all_dishes() if d.identifier == ma), None
        )

    def restaurant_count(self, dish: Dish) -> Optional[int]:
        """Số quán khớp — cùng chỉ mục với bảng món. `None` = chỉ mục chưa lắp."""
        if self._index is None:
            return None
        return len(self._index.get(dish.identifier, ()))

    def restaurants(self, dish: Dish, limit: int = 20) -> DishRestaurantsPage:
        """Các quán khớp món, cho tab "Danh sách quán".

        KHÔNG xếp theo khoảng cách hay ngữ cảnh như luồng người dùng — admin không đứng ở
        vị trí nào cả. Thứ tự: khớp MẠNH trước (tên quán ghi đúng tên món > từ khoá chung >
        chỉ khớp loại hình > chỉ review nhắc, xem `DishMatch.strength`), cùng mức thì quán CÓ đánh giá trước, rồi theo số lượt đánh giá.
        Quán chưa có đánh giá (`None`) xếp sau chứ KHÔNG bị coi là 0 sao.
        """
        khop = list(self._index.get(dish.identifier, ())) if self._index else []

        def khoa_xep(m) -> Tuple:
            r = m.restaurant
            rating = getattr(r, "rating", None)
            so_danh_gia = getattr(r, "reviews_count", None)
            return (
                -m.strength,
                rating is None,
                -(rating or 0.0),
                -(so_danh_gia or 0),
                normalize(getattr(r, "name", "") or ""),
            )

        khop.sort(key=khoa_xep)
        so = max(1, min(int(limit), MAX_QUAN_CUA_MON))
        return DishRestaurantsPage(
            total=len(khop),
            results=[DishRestaurantMatch(m.restaurant, m.matched_by) for m in khop[:so]],
        )


__all__ = [
    "DishAdminPage",
    "DishRestaurantMatch",
    "DishRestaurantsPage",
    "DEFAULT_PAGE_SIZE",
    "ListDishesForAdminUseCase",
    "GetDishForAdminUseCase",
    "DishAdminRow",
    "DishCatalogNotReady",
    "BO_LOC",
]

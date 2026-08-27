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

⚠️ CHỈ ĐỌC. Sửa/ẩn món qua trang quản trị chưa làm: `dish_catalog.json` là file do
`scripts/build_dish_catalog.py` SINH RA, nên ghi thẳng vào đó sẽ bị lần chạy sau xoá
sạch. Muốn sửa được thì phải chuyển danh mục món sang SQLite trước — việc riêng, chưa làm.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.application.errors import DataNotReadyError
from src.domain.entities.dish import Dish
from src.domain.value_objects.text import contains_phrase, normalize

MAX_TRANG = 200


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

    @classmethod
    def tu_dish(cls, d: Dish) -> "DishAdminRow":
        return cls(
            dish_id=d.identifier,
            name=d.name,
            cuisine=d.cuisine,
            image_url=d.image_url,
            # Trả CỜ chứ không trả cả đoạn giới thiệu: bảng chỉ cần biết "có hay không",
            # còn kéo 855 đoạn văn qua JSON cho một cột đánh dấu là lãng phí.
            has_description=bool((d.description or "").strip()),
            is_category=d.is_category,
            is_active=d.is_active,
            source=d.source,
        )


# Bộ lọc trên giao diện. Khoá là chuỗi client gửi lên.
BO_LOC = ("all", "with_restaurants", "without_restaurants", "missing_image", "missing_description")


@dataclass
class ListDishesForAdminUseCase:
    dish_catalog: object

    def execute(
        self,
        query: Optional[str] = None,
        loc: str = "all",
        limit: int = 50,
    ) -> tuple:
        """Trả `(danh_sach_dong, tong_sau_khi_loc)`.

        Trả kèm TỔNG vì bảng bị cắt theo `limit`: không có tổng thì giao diện hiện "50
        món" trong khi bộ lọc khớp 557 — người quản trị sẽ tưởng chỉ có 50.
        """
        if not getattr(self.dish_catalog, "is_ready", False):
            raise DishCatalogNotReady()

        # TOÀN BỘ món kể cả món tắt — xem bảng so sánh ở đầu file.
        mon: List[Dish] = list(self.dish_catalog.list_all_dishes())

        if loc == "with_restaurants":
            mon = [d for d in mon if d.is_active]
        elif loc == "without_restaurants":
            mon = [d for d in mon if not d.is_active]
        elif loc == "missing_image":
            mon = [d for d in mon if not (d.image_url or "").strip()]
        elif loc == "missing_description":
            mon = [d for d in mon if not (d.description or "").strip()]

        tu_khoa = (query or "").strip()
        if tu_khoa:
            mon = [d for d in mon if _khop(d, tu_khoa)]

        # Xếp: món CÓ quán trước (việc chính của admin nằm ở đó), rồi theo tên không dấu
        # để "Ốc" không bị đẩy xuống cuối bảng chữ cái.
        mon.sort(key=lambda d: (not d.is_active, normalize(d.name)))

        so = max(1, min(int(limit), MAX_TRANG))
        return [DishAdminRow.tu_dish(d) for d in mon[:so]], len(mon)


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


__all__ = ["ListDishesForAdminUseCase", "DishAdminRow", "DishCatalogNotReady", "BO_LOC"]

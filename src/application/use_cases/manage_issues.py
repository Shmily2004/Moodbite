"""USE CASE: màn "CẦN XỬ LÝ" — inbox vấn đề của người quản trị.

Bản thiết kế: `frontend/design/needs to be handled admin.png`.

Ba việc:
  1. `LietKeVanDeUseCase`  — bảng các NHÓM vấn đề + năm thẻ số ở đầu trang.
  2. `XemChiTietVanDeUseCase` — bấm "Xem danh sách" của một nhóm ra các bản ghi cụ thể.
  3. `DanhDauXongUseCase`  — đánh dấu / gỡ đánh dấu một bản ghi đã xử lý.

CHỈ ĐIỀU PHỐI. Mọi quy tắc ("thế nào là nghiêm trọng", "trùng lặp là gì") nằm ở
`domain/services/data_issues.py`.

⚠️ ĐÁNH DẤU XONG ≠ SỬA DỮ LIỆU. Xem `domain/entities/issue_resolution.py`. Ở đây chỉ ghi
lại rằng người quản trị đã xem và kết luận không phải làm gì thêm.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from src.application.errors import DataNotReadyError
from src.domain.entities.issue_resolution import DanhDauXong
from src.domain.services.data_issues import (
    THU_TU_UU_TIEN,
    BanGhiVanDe,
    ViecCanXuLy,
    ban_ghi_dinh_loi,
    viec_can_xu_ly,
)
from src.domain.services.data_quality_history import dem_theo_uu_tien

# Trần số bản ghi trả về một lần khi mở chi tiết một nhóm.
#
# VÌ SAO CÓ TRẦN: nhóm "quán không có cách nào liên hệ" có 8.920 bản ghi (đo 2026-09-08).
# Trả hết về trình duyệt là một response vài MB cho một bảng người ta chỉ xem 20 dòng đầu.
MAX_CHI_TIET = 200


class IssuesNotAvailable(DataNotReadyError):
    def __init__(self, ly_do: str) -> None:
        super().__init__(
            f"chưa dựng được danh sách cần xử lý ({ly_do})",
            "Chạy: python -m data_pipeline.merge_and_prepare_raw rồi khởi động lại backend.",
        )


@dataclass(frozen=True)
class BangVanDe:
    """Dữ liệu của cả màn "Cần xử lý"."""

    nhom: List[ViecCanXuLy]
    dem_uu_tien: dict
    tong_van_de: int
    da_xu_ly_hom_nay: int
    da_xu_ly_tong: int
    # `False` khi kho đánh dấu không mở được — nút "Đánh dấu đã xử lý" phải bị vô hiệu
    # hoá kèm lý do, chứ không bấm được rồi im lặng không lưu.
    co_the_danh_dau: bool


class LietKeVanDeUseCase:
    def __init__(
        self,
        restaurant_repository,
        dish_catalog_repository,
        issue_resolution_repository=None,
    ) -> None:
        self._restaurants = restaurant_repository
        self._dishes = dish_catalog_repository
        self._resolutions = issue_resolution_repository

    def execute(
        self, uu_tien: Optional[str] = None, hom_nay: Optional[date] = None
    ) -> BangVanDe:
        """`uu_tien` lọc theo mức gấp; khoá lạ thì KHÔNG lọc (trả về tất cả).

        Không lọc khi gặp khoá lạ thay vì trả rỗng: một tham số gõ sai làm bảng trống
        trơn sẽ khiến người quản trị tưởng hệ thống sạch lỗi.
        """
        if not getattr(self._restaurants, "is_ready", False):
            raise IssuesNotAvailable("kho quán chưa mở được")

        quan = self._restaurants.list_all()
        mon = self._dishes.list_all_dishes() if self._dishes is not None else []
        tat_ca = viec_can_xu_ly(quan, mon)

        # Đếm theo ưu tiên tính trên TOÀN BỘ nhóm, không phải trên phần đã lọc: năm thẻ
        # số ở đầu trang phải giữ nguyên khi người dùng bấm đổi tab, nếu không thì bấm
        # vào tab "Nghiêm trọng" sẽ thấy ba thẻ kia tụt về 0.
        dem = dem_theo_uu_tien(tat_ca)

        nhom = tat_ca
        if uu_tien in THU_TU_UU_TIEN:
            nhom = [v for v in tat_ca if v.uu_tien == uu_tien]

        ngay = (hom_nay or date.today()).isoformat()
        return BangVanDe(
            nhom=self._sap_theo_uu_tien(nhom),
            dem_uu_tien=dem,
            tong_van_de=sum(dem.values()),
            da_xu_ly_hom_nay=self._dem_an_toan(lambda: self._resolutions.dem_trong_ngay(ngay)),
            da_xu_ly_tong=self._dem_an_toan(lambda: self._resolutions.dem()),
            co_the_danh_dau=bool(
                self._resolutions is not None
                and getattr(self._resolutions, "is_ready", False)
            ),
        )

    @staticmethod
    def _sap_theo_uu_tien(nhom: List[ViecCanXuLy]) -> List[ViecCanXuLy]:
        """Gấp nhất lên đầu; cùng mức thì nhiều bản ghi hơn lên trước."""
        return sorted(
            nhom,
            key=lambda v: (
                THU_TU_UU_TIEN.index(v.uu_tien)
                if v.uu_tien in THU_TU_UU_TIEN
                else len(THU_TU_UU_TIEN),
                -v.so_luong,
            ),
        )

    def _dem_an_toan(self, lay) -> int:
        """Kho đánh dấu hỏng thì trả 0 chứ KHÔNG làm trắng cả bảng vì một thẻ số."""
        if self._resolutions is None:
            return 0
        try:
            return int(lay())
        except Exception:  # noqa: BLE001 - xem docstring
            return 0


@dataclass(frozen=True)
class ChiTietVanDe:
    khoa: str
    tong: int
    ban_ghi: List[BanGhiVanDe]
    # {target_id: bản ghi đánh dấu} — để giao diện tô mờ dòng đã xử lý thay vì giấu đi.
    # Giấu đi thì người vừa bấm nhầm không còn cách nào tìm lại để gỡ.
    da_xong: dict


class XemChiTietVanDeUseCase:
    def __init__(
        self,
        restaurant_repository,
        dish_catalog_repository,
        issue_resolution_repository=None,
    ) -> None:
        self._restaurants = restaurant_repository
        self._dishes = dish_catalog_repository
        self._resolutions = issue_resolution_repository

    def execute(self, khoa: str, limit: int = 50) -> ChiTietVanDe:
        if not getattr(self._restaurants, "is_ready", False):
            raise IssuesNotAvailable("kho quán chưa mở được")

        quan = self._restaurants.list_all()
        mon = self._dishes.list_all_dishes() if self._dishes is not None else []
        gioi_han = min(max(limit, 1), MAX_CHI_TIET)
        ban_ghi = ban_ghi_dinh_loi(quan, mon, khoa, gioi_han=gioi_han)
        tong = next(
            (v.so_luong for v in viec_can_xu_ly(quan, mon) if v.khoa == khoa), 0
        )

        da_xong = {}
        if self._resolutions is not None and ban_ghi:
            try:
                da_xong = self._resolutions.da_xong(khoa, [b.id for b in ban_ghi])
            except Exception:  # noqa: BLE001 - trạng thái đánh dấu là phần làm giàu
                da_xong = {}

        return ChiTietVanDe(khoa=khoa, tong=tong, ban_ghi=ban_ghi, da_xong=da_xong)


class DanhDauXongUseCase:
    """Đánh dấu / gỡ đánh dấu. Kho chưa sẵn sàng thì BÁO LỖI RÕ, không nuốt."""

    def __init__(self, issue_resolution_repository) -> None:
        self._repo = issue_resolution_repository

    def _bat_buoc_co_kho(self) -> None:
        if self._repo is None or not getattr(self._repo, "is_ready", False):
            raise IssuesNotAvailable("kho đánh dấu xử lý chưa mở được")

    def danh_dau(
        self, khoa: str, target_id: str, actor: str, ghi_chu: Optional[str] = None
    ) -> DanhDauXong:
        self._bat_buoc_co_kho()
        return self._repo.danh_dau(
            DanhDauXong(khoa=khoa, target_id=target_id, actor=actor, ghi_chu=ghi_chu)
        )

    def bo_danh_dau(self, khoa: str, target_id: str) -> bool:
        self._bat_buoc_co_kho()
        return self._repo.bo_danh_dau(khoa, target_id)


__all__ = [
    "BangVanDe",
    "ChiTietVanDe",
    "DanhDauXongUseCase",
    "IssuesNotAvailable",
    "LietKeVanDeUseCase",
    "XemChiTietVanDeUseCase",
    "MAX_CHI_TIET",
]

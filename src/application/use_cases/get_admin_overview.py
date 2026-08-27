"""USE CASE: số liệu cho màn "Tổng quan" của trang quản trị.

Chỉ ĐIỀU PHỐI: lấy dữ liệu từ các kho rồi giao cho `domain/services/data_quality.py` tính.
Không có công thức nào ở đây — "thế nào là đủ thông tin cơ bản" là quy tắc nghiệp vụ và
phải nằm ở domain (CLAUDE.md mục 2).

CÓ BỘ NHỚ ĐỆM, VÀ ĐÂY LÀ LÝ DO
------------------------------
Tính toàn bộ thống kê mất **0,20 giây** (đo trên 52.854 quán, 2026-08-26). Nhanh, nhưng
không phải rẻ: màn tổng quan tự tải lại mỗi lần người quản trị quay lại tab, và 0,2 giây
CPU cho một con số không đổi trong nhiều giờ là lãng phí. Đệm `TTL_GIAY` giây.

Đệm theo THỜI GIAN chứ không theo "dữ liệu có đổi không": dataset chỉ đổi khi chạy lại
`data_pipeline`, mà lúc đó backend phải khởi động lại — nên không có đường nào để dữ liệu
đổi giữa chừng mà đệm không biết.

⚠️ KHÔNG BỊA SỐ (CLAUDE.md mục 4). Bản thiết kế `Dashboard admin.png` vẽ sẵn:
    "+1.248 so với tuần trước" · "CTR 8.7%" · "Lượt gợi ý hôm nay 1.306" · các đường
    sparkline · "Cập nhật lần cuối 20/05/2025"
Dự án KHÔNG lưu ảnh chụp dữ liệu theo ngày và KHÔNG ghi nhật ký lượt tìm kiếm, nên không
có cách nào tính được những con số đó. Use case này chỉ trả về thứ đếm được thật; giao
diện nói rõ phần nào chưa có thay vì vẽ số cho đẹp.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from src.application.errors import DataNotReadyError
from src.domain.services.data_quality import (
    DoPhuTruong,
    ThongKeNguon,
    ViecCanXuLy,
    do_phu_mon,
    do_phu_quan,
    thong_ke_nguon,
    viec_can_xu_ly,
)

# 5 phút. Đủ lâu để nút "tải lại" của trình duyệt không bắt tính lại mỗi lần, đủ ngắn để
# người quản trị vừa thêm một quán thì thấy số nhích lên trong lần xem sau.
TTL_GIAY = 300


@dataclass(frozen=True)
class DemQuan:
    tong: int
    dang_hien: int
    da_an: int


@dataclass(frozen=True)
class DemMon:
    tong: int
    co_quan: int
    chua_co_quan: int


@dataclass(frozen=True)
class AdminOverview:
    quan: DemQuan
    mon: DemMon
    do_phu: List[DoPhuTruong]
    nguon: List[ThongKeNguon]
    can_xu_ly: List[ViecCanXuLy]
    so_tuong_tac: int
    # Giây kể từ epoch, do người gọi ở tầng trên đổi sang chuỗi ISO. Domain và application
    # không được tự lấy giờ hệ thống để định dạng — việc đó là trình bày.
    tinh_luc: float = field(default_factory=time.time)

    @property
    def tong_can_xu_ly(self) -> int:
        """Chỉ đếm mục mức `canh_bao`. Mục `thong_tin` không phải việc phải làm."""
        return sum(v.so_luong for v in self.can_xu_ly if v.muc_do == "canh_bao")


class AdminOverviewNotAvailable(DataNotReadyError):
    def __init__(self, ly_do: str) -> None:
        super().__init__(
            f"chưa dựng được số liệu tổng quan ({ly_do})",
            "Chạy: python -m data_pipeline.merge_and_prepare_raw rồi khởi động lại backend.",
        )


class GetAdminOverviewUseCase:
    def __init__(
        self,
        restaurant_repository,
        dish_catalog_repository,
        interaction_repository=None,
    ) -> None:
        self._restaurants = restaurant_repository
        self._dishes = dish_catalog_repository
        self._interactions = interaction_repository
        self._dem: Optional[AdminOverview] = None

    def _con_han(self) -> bool:
        return self._dem is not None and (time.time() - self._dem.tinh_luc) < TTL_GIAY

    def execute(self, bo_qua_dem: bool = False) -> AdminOverview:
        if not bo_qua_dem and self._con_han():
            assert self._dem is not None
            return self._dem

        if not getattr(self._restaurants, "is_ready", False):
            raise AdminOverviewNotAvailable("kho quán chưa mở được")

        quan = self._restaurants.list_all()
        # TOÀN BỘ món kể cả món tắt — trang quản trị phải nói được cả ba con số.
        mon = self._dishes.list_all_dishes() if self._dishes is not None else []

        dang_hien = sum(1 for r in quan if getattr(r, "is_active", True))
        co_quan = sum(1 for d in mon if getattr(d, "is_active", True))

        self._dem = AdminOverview(
            quan=DemQuan(
                tong=len(quan), dang_hien=dang_hien, da_an=len(quan) - dang_hien
            ),
            mon=DemMon(
                tong=len(mon), co_quan=co_quan, chua_co_quan=len(mon) - co_quan
            ),
            do_phu=[*do_phu_quan(quan), *do_phu_mon(mon)],
            nguon=thong_ke_nguon(quan),
            can_xu_ly=viec_can_xu_ly(quan, mon),
            so_tuong_tac=self._dem_tuong_tac(),
        )
        return self._dem

    def _dem_tuong_tac(self) -> int:
        """Số lượt tương tác đã ghi. Kho hỏng thì trả 0 chứ KHÔNG làm hỏng cả màn hình.

        Tương tác là dữ liệu phụ ở đây; mất nó thì mục đó hiện 0, còn ném lỗi ra ngoài sẽ
        làm trắng toàn bộ trang tổng quan vì một con số bên lề.
        """
        if self._interactions is None:
            return 0
        try:
            trang_thai = self._interactions.status()
            return int(trang_thai.get("count", 0) or 0)
        except Exception:  # noqa: BLE001 - xem docstring
            return 0


__all__ = [
    "GetAdminOverviewUseCase",
    "AdminOverview",
    "AdminOverviewNotAvailable",
    "DemQuan",
    "DemMon",
    "TTL_GIAY",
]

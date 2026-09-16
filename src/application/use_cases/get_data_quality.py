"""USE CASE: số liệu cho màn "CHẤT LƯỢNG DỮ LIỆU" của trang quản trị.

Bản thiết kế: `frontend/design/quality data admin.png`.

QUAN HỆ VỚI `get_admin_overview.py`
------------------------------------
Use case này DÙNG LẠI `GetAdminOverviewUseCase` thay vì tự đếm lại từ đầu. Lý do đo được:
tính toàn bộ độ phủ + hộp việc trên 52.871 quán mất **0,35 giây**; hai màn hình cùng cần
đúng bộ số đó, và người quản trị thường mở cả hai trong một phiên. Đếm hai lần là tốn
gấp đôi cho một kết quả giống hệt, lại còn mở đường cho hai màn hiện hai con số lệch nhau
nếu sau này một bên sửa công thức mà bên kia quên.

Phần RIÊNG của màn này — không có ở Tổng quan:
  1. Lịch sử: "so với tháng trước" và biểu đồ xu hướng 7 ngày.
  2. Ví dụ CỤ THỂ: bốn dòng "Cần xử lý ngay" có tên quán, tên món, ảnh.
  3. "Đã xử lý hôm nay": đếm từ kho `IssueResolutionRepository`.

VÌ SAO MỘT LƯỢT ĐỌC LẠI GHI DỮ LIỆU
------------------------------------
`execute()` tự lưu ảnh chụp của HÔM NAY nếu chưa có. Bình thường một thao tác đọc không
nên ghi, và đây là ngoại lệ có chủ ý:

Không có nó thì biểu đồ xu hướng vĩnh viễn trống, vì dự án không có cron và chủ dự án
không có máy chủ chạy nền — bảo người dùng "nhớ chạy script mỗi ngày" là cách chắc chắn
để sau ba tháng vẫn có đúng một điểm. Thao tác ghi là BẤT BIẾN THEO NGÀY (`INSERT OR
REPLACE` trên khoá `ngay`), nên mở trang 50 lần trong ngày vẫn chỉ có một dòng.

Ai muốn ghi chủ động (cron, Task Scheduler) thì dùng `scripts/ghi_anh_chup_chat_luong.py`.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

from src.domain.services.data_issues import (
    CAN_KIEM_TRA,
    NGHIEM_TRONG,
    QUAN_TRONG,
    THU_TU_UU_TIEN,
    BanGhiVanDe,
    ViecCanXuLy,
    ban_ghi_dinh_loi,
)
from src.domain.services.data_quality import DoPhuTruong, ThongKeNguon
from src.domain.services.data_quality_history import (
    SO_NGAY_MOC_THANG,
    AnhChupChatLuong,
    ThayDoi,
    chuoi_xu_huong,
    dem_theo_uu_tien,
    moc_gan_nhat_truoc,
    so_sanh,
)

# Số dòng ví dụ ở khối "Cần xử lý ngay". Bản thiết kế vẽ đúng 4 dòng.
SO_VI_DU = 4

# Cùng TTL với màn Tổng quan — hai màn đọc chung một bộ số, đệm lệch nhau sẽ làm chúng
# hiện hai giá trị khác nhau trong cùng một phiên.
TTL_GIAY = 300


@dataclass(frozen=True)
class ChatLuongDuLieu:
    """Toàn bộ số liệu màn "Chất lượng dữ liệu"."""

    tong_quan: ThayDoi
    tong_mon: ThayDoi
    quan_trong_ha_noi: int
    # Tỷ lệ quán có đủ thông tin cơ bản — số ở giữa vòng tròn của bản thiết kế.
    hoan_thien_phan_tram: float
    dem_uu_tien: dict
    do_phu: List[DoPhuTruong]
    nguon: List[ThongKeNguon]
    can_xu_ly: List[ViecCanXuLy]
    can_xu_ly_ngay: List[BanGhiVanDe]
    xu_huong: List[AnhChupChatLuong]
    da_xu_ly_hom_nay: int
    # `False` khi kho lịch sử không mở được — giao diện phải nói "chưa theo dõi được"
    # thay vì vẽ một biểu đồ trống trông như "không có vấn đề gì".
    co_lich_su: bool
    tinh_luc: float = field(default_factory=time.time)

    @property
    def phan_tram_ha_noi(self) -> float:
        tong = self.tong_quan.hien_tai
        if tong <= 0:
            return 0.0
        return round(self.quan_trong_ha_noi / tong * 100, 1)


class GetDataQualityUseCase:
    def __init__(
        self,
        admin_overview_use_case,
        restaurant_repository,
        dish_catalog_repository,
        snapshot_repository=None,
        issue_resolution_repository=None,
    ) -> None:
        self._overview = admin_overview_use_case
        self._restaurants = restaurant_repository
        self._dishes = dish_catalog_repository
        self._snapshots = snapshot_repository
        self._resolutions = issue_resolution_repository
        self._dem: Optional[ChatLuongDuLieu] = None

    def _con_han(self) -> bool:
        return self._dem is not None and (time.time() - self._dem.tinh_luc) < TTL_GIAY

    def execute(
        self, bo_qua_dem: bool = False, hom_nay: Optional[date] = None
    ) -> ChatLuongDuLieu:
        """`hom_nay` chỉ để TEST cố định được ngày; chạy thật thì để `None`."""
        if not bo_qua_dem and self._con_han():
            assert self._dem is not None
            return self._dem

        ngay = hom_nay or date.today()
        tong_quan_so = self._overview.execute(bo_qua_dem=bo_qua_dem)

        dem_uu_tien = dem_theo_uu_tien(tong_quan_so.can_xu_ly)
        hoan_thien = self._ty_le_hoan_thien(tong_quan_so.do_phu)
        ngoai_hn = next(
            (v.so_luong for v in tong_quan_so.can_xu_ly if v.khoa == "ngoai_ha_noi"), 0
        )

        anh_chup_hom_nay = AnhChupChatLuong(
            ngay=ngay.isoformat(),
            tong_quan=tong_quan_so.quan.tong,
            tong_mon=tong_quan_so.mon.tong,
            hoan_thien_phan_tram=hoan_thien,
            nghiem_trong=dem_uu_tien.get(NGHIEM_TRONG, 0),
            quan_trong=dem_uu_tien.get(QUAN_TRONG, 0),
            can_kiem_tra=dem_uu_tien.get(CAN_KIEM_TRA, 0),
        )
        lich_su = self._cap_nhat_lich_su(anh_chup_hom_nay)
        moc = moc_gan_nhat_truoc(lich_su, ngay, SO_NGAY_MOC_THANG)

        self._dem = ChatLuongDuLieu(
            tong_quan=so_sanh(tong_quan_so.quan.tong, moc, "tong_quan"),
            tong_mon=so_sanh(tong_quan_so.mon.tong, moc, "tong_mon"),
            quan_trong_ha_noi=tong_quan_so.quan.tong - ngoai_hn,
            hoan_thien_phan_tram=hoan_thien,
            dem_uu_tien=dem_uu_tien,
            do_phu=tong_quan_so.do_phu,
            nguon=tong_quan_so.nguon,
            can_xu_ly=tong_quan_so.can_xu_ly,
            can_xu_ly_ngay=self._vi_du_gap_nhat(tong_quan_so.can_xu_ly),
            xu_huong=chuoi_xu_huong(lich_su, ngay),
            da_xu_ly_hom_nay=self._dem_da_xu_ly(ngay),
            co_lich_su=bool(
                self._snapshots is not None
                and getattr(self._snapshots, "is_ready", False)
            ),
        )
        return self._dem

    @staticmethod
    def _ty_le_hoan_thien(do_phu: List[DoPhuTruong]) -> float:
        """Tỷ lệ quán có đủ thông tin cơ bản.

        Lấy đúng dòng `co_ban` chứ KHÔNG lấy trung bình các dòng: trung bình của "địa chỉ
        100%" và "website 26%" là 63%, một con số không có nghĩa gì cả và cũng không phải
        tỷ lệ quán dùng được.
        """
        for x in do_phu:
            if x.khoa == "co_ban":
                return x.phan_tram
        return 0.0

    def _vi_du_gap_nhat(self, can_xu_ly: List[ViecCanXuLy]) -> List[BanGhiVanDe]:
        """Vài bản ghi cụ thể, ưu tiên nhóm GẤP nhất trước.

        Lấy mỗi nhóm MỘT bản ghi trước khi quay lại lấy bản thứ hai của nhóm đầu: khối
        này để người quản trị thấy TOÀN CẢNH đang hỏng những gì, không phải để liệt kê
        cạn một loại lỗi rồi bỏ sót các loại còn lại.
        """
        if not getattr(self._restaurants, "is_ready", False):
            return []
        quan = self._restaurants.list_all()
        mon = self._dishes.list_all_dishes() if self._dishes is not None else []

        theo_uu_tien = sorted(
            (v for v in can_xu_ly if v.so_luong > 0),
            key=lambda v: THU_TU_UU_TIEN.index(v.uu_tien)
            if v.uu_tien in THU_TU_UU_TIEN
            else len(THU_TU_UU_TIEN),
        )
        ket_qua: List[BanGhiVanDe] = []
        for viec in theo_uu_tien:
            if len(ket_qua) >= SO_VI_DU:
                break
            ket_qua.extend(ban_ghi_dinh_loi(quan, mon, viec.khoa, gioi_han=1))
        return ket_qua[:SO_VI_DU]

    def _cap_nhat_lich_su(
        self, anh_chup: AnhChupChatLuong
    ) -> List[AnhChupChatLuong]:
        """Ghi ảnh chụp hôm nay rồi đọc lại cả chuỗi. Kho hỏng thì chỉ có mỗi hôm nay."""
        if self._snapshots is None or not getattr(self._snapshots, "is_ready", False):
            return [anh_chup]
        self._snapshots.ghi(anh_chup)
        lich_su = self._snapshots.doc_gan_day()
        # Kho vừa ghi mà đọc lại không thấy (đĩa đầy, quyền ghi) thì vẫn phải có điểm
        # hôm nay để biểu đồ không trống trơn một cách khó hiểu.
        return lich_su or [anh_chup]

    def _dem_da_xu_ly(self, ngay: date) -> int:
        """Số vấn đề được đánh dấu xong hôm nay. Kho hỏng thì trả 0, không làm hỏng màn."""
        if self._resolutions is None:
            return 0
        try:
            return self._resolutions.dem_trong_ngay(ngay.isoformat())
        except Exception:  # noqa: BLE001 - xem docstring
            return 0


__all__ = ["GetDataQualityUseCase", "ChatLuongDuLieu", "SO_VI_DU", "TTL_GIAY"]

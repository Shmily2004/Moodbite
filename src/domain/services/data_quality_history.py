"""QUY TẮC NGHIỆP VỤ: LỊCH SỬ chất lượng dữ liệu — so sánh theo thời gian.

Bản thiết kế `frontend/design/quality data admin.png` có hai thứ mà một ảnh chụp tại một
thời điểm KHÔNG trả lời được:

    "Tổng số quán 52.854   ↗ +12 so với tháng trước"
    biểu đồ "Xu hướng dữ liệu" — 7 ngày gần nhất

Muốn có chúng thì phải LƯU LẠI số của những ngày trước. File này định nghĩa *cái gì được
lưu* và *so sánh thế nào*; việc lưu ở đâu là của `infrastructure`.

⚠️ NGUYÊN TẮC QUAN TRỌNG NHẤT CỦA FILE NÀY: CHƯA CÓ MỐC THÌ TRẢ `None`, KHÔNG TRẢ 0.
Ngày đầu tiên bật tính năng này, dự án chỉ có đúng MỘT ảnh chụp — không có gì để so.
Lúc đó "so với tháng trước" phải là "chưa có dữ liệu để so", tuyệt đối không phải "+0"
(nghe như đã so và không đổi) và càng không phải "+52.854" (so với số 0 tưởng tượng).
Đây chính là CLAUDE.md mục 4 quy tắc 1 áp cho chiều thời gian.

VÌ SAO MỖI NGÀY MỘT DÒNG
------------------------
Khoá là NGÀY (`YYYY-MM-DD`) chứ không phải mốc thời gian đầy đủ: người quản trị mở trang
này nhiều lần trong ngày, và mỗi lần mở lại đẻ một điểm trên biểu đồ thì đường xu hướng
sẽ dày đặc ở hôm nay và thưa ở hôm qua — nhìn ra một xu hướng không có thật. Một ngày
một điểm, lần ghi sau trong cùng ngày GHI ĐÈ lần trước.

File này THUẦN PYTHON — không sqlite, không datetime "lấy giờ hiện tại". Ngày luôn do
người gọi truyền vào, để test không phụ thuộc vào đồng hồ máy.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Sequence

from src.domain.services.data_issues import THU_TU_UU_TIEN

# Số ngày hiển thị trên biểu đồ "Xu hướng dữ liệu".
#
# VÌ SAO 7: bản thiết kế vẽ đúng 7 nhãn ngày (14/05 → 20/05). Giữ nguyên để khớp bản vẽ.
SO_NGAY_XU_HUONG = 7

# Mốc so sánh của dòng "so với tháng trước" dưới hai thẻ số lớn.
SO_NGAY_MOC_THANG = 30


@dataclass(frozen=True)
class AnhChupChatLuong:
    """Số liệu chất lượng dữ liệu của MỘT ngày.

    Cố ý chỉ giữ 6 con số thay vì chụp nguyên trạng thái: ảnh chụp là thứ lưu mãi mãi,
    mỗi trường thêm vào là một trường phải bảo trì suốt đời dự án. Sáu con số này đủ dựng
    lại toàn bộ phần "so với trước" và biểu đồ xu hướng của bản thiết kế.
    """

    ngay: str  # ISO `YYYY-MM-DD`
    tong_quan: int
    tong_mon: int
    # Tỷ lệ quán có đủ thông tin cơ bản (khoá `co_ban` của `data_quality.do_phu_quan`).
    hoan_thien_phan_tram: float
    # Ba con số này đếm theo TRỤC ƯU TIÊN của `data_issues.py`.
    nghiem_trong: int
    quan_trong: int
    can_kiem_tra: int


@dataclass(frozen=True)
class ThayDoi:
    """Chênh lệch giữa hôm nay và một mốc trong quá khứ.

    `moc` là `None` nghĩa là CHƯA CÓ ảnh chụp nào đủ cũ để so — giao diện phải nói
    "chưa có dữ liệu để so sánh", không được hiện một mũi tên nào.
    """

    hien_tai: int
    moc: Optional[int] = None
    ngay_moc: Optional[str] = None

    @property
    def chenh_lech(self) -> Optional[int]:
        if self.moc is None:
            return None
        return self.hien_tai - self.moc

    @property
    def co_so_sanh(self) -> bool:
        return self.moc is not None


def _tro_ve_ngay(gia_tri) -> Optional[date]:
    """Đổi chuỗi `YYYY-MM-DD` sang `date`. Chuỗi hỏng trả `None` thay vì ném lỗi.

    Ảnh chụp là dữ liệu ghi dần suốt đời dự án; một dòng hỏng (sửa tay, lỗi ghi đĩa)
    không được phép làm trắng cả màn hình chất lượng dữ liệu.
    """
    try:
        return date.fromisoformat(str(gia_tri))
    except (TypeError, ValueError):
        return None


def sap_xep_theo_ngay(
    anh_chup: Sequence[AnhChupChatLuong],
) -> List[AnhChupChatLuong]:
    """Sắp xếp CŨ TRƯỚC, và loại dòng có ngày không đọc được."""
    hop_le = [a for a in anh_chup if _tro_ve_ngay(a.ngay) is not None]
    return sorted(hop_le, key=lambda a: a.ngay)


def moc_gan_nhat_truoc(
    anh_chup: Sequence[AnhChupChatLuong],
    hom_nay: date,
    so_ngay: int = SO_NGAY_MOC_THANG,
) -> Optional[AnhChupChatLuong]:
    """Ảnh chụp gần nhất CŨ HƠN `so_ngay` ngày. Không có thì `None`.

    Dùng "gần nhất cũ hơn N ngày" thay vì "đúng N ngày trước", vì người quản trị không
    mở trang mỗi ngày nên sẽ có ngày trống. Lấy đúng ngày thì hầu hết thời gian sẽ báo
    "chưa có dữ liệu" dù đã lưu hàng chục ảnh chụp.
    """
    han = hom_nay - timedelta(days=so_ngay)
    ung_vien = [
        a
        for a in sap_xep_theo_ngay(anh_chup)
        if (d := _tro_ve_ngay(a.ngay)) is not None and d <= han
    ]
    return ung_vien[-1] if ung_vien else None


def so_sanh(
    hien_tai: int,
    moc: Optional[AnhChupChatLuong],
    lay: str,
) -> ThayDoi:
    """Dựng `ThayDoi` cho một trường của ảnh chụp mốc.

    `lay` là tên trường trong `AnhChupChatLuong` (ví dụ `"tong_quan"`).
    """
    if moc is None:
        return ThayDoi(hien_tai=hien_tai)
    return ThayDoi(
        hien_tai=hien_tai,
        moc=int(getattr(moc, lay, 0)),
        ngay_moc=moc.ngay,
    )


def chuoi_xu_huong(
    anh_chup: Sequence[AnhChupChatLuong],
    hom_nay: date,
    so_ngay: int = SO_NGAY_XU_HUONG,
) -> List[AnhChupChatLuong]:
    """`so_ngay` điểm gần nhất, CŨ TRƯỚC — dữ liệu cho biểu đồ đường.

    KHÔNG bù ngày trống bằng số 0 hay bằng giá trị ngày liền trước. Bù 0 vẽ ra một cú
    sụt không có thật; bù giá trị cũ vẽ ra một đường phẳng như thể đã đo mà không đo.
    Ngày nào không có ảnh chụp thì đơn giản là không có điểm, và giao diện nối hai điểm
    thật lại với nhau.
    """
    han = hom_nay - timedelta(days=so_ngay - 1)
    trong_khoang = [
        a
        for a in sap_xep_theo_ngay(anh_chup)
        if (d := _tro_ve_ngay(a.ngay)) is not None and han <= d <= hom_nay
    ]
    return trong_khoang[-so_ngay:]


def dem_theo_uu_tien(viec: Sequence) -> Dict[str, int]:
    """Cộng `so_luong` của các nhóm việc theo từng mức ưu tiên.

    Trả về dict CÓ ĐỦ ba khoá kể cả khi bằng 0 — giao diện vẽ đủ ba thẻ số, và một thẻ
    biến mất vì hôm nay không có lỗi nào loại đó sẽ làm bố cục nhảy.
    """
    dem = {muc: 0 for muc in THU_TU_UU_TIEN}
    for v in viec:
        muc = getattr(v, "uu_tien", None)
        if muc in dem:
            dem[muc] += int(getattr(v, "so_luong", 0) or 0)
    return dem


__all__ = [
    "AnhChupChatLuong",
    "ThayDoi",
    "chuoi_xu_huong",
    "dem_theo_uu_tien",
    "moc_gan_nhat_truoc",
    "sap_xep_theo_ngay",
    "so_sanh",
    "SO_NGAY_XU_HUONG",
    "SO_NGAY_MOC_THANG",
]

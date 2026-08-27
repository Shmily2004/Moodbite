"""QUY TẮC NGHIỆP VỤ: đo CHẤT LƯỢNG DỮ LIỆU của dataset.

Đây là ruột của màn "Tổng quan" và "Chất lượng dữ liệu" ở trang quản trị
(`frontend/design/Dashboard admin.png`, chủ dự án gửi 2026-08-26).

VÌ SAO NẰM Ở `domain/` CHỨ KHÔNG PHẢI `infrastructure/`
--------------------------------------------------------
Câu "một quán có ĐỦ thông tin cơ bản" là một QUY TẮC NGHIỆP VỤ, không phải chuyện kỹ
thuật. Nó quyết định con số hiện lên trước mặt người quản trị và quyết định quán nào bị
xếp vào danh sách "cần xử lý". Đặt ở tầng khác thì mỗi nơi lại định nghĩa "đủ thông tin"
một kiểu.

File này THUẦN PYTHON — không pandas, không sqlite. Đo thật: duyệt 52.854 quán và tính
toàn bộ thống kê ở đây mất **0,20 giây**, nên không cần pandas và cũng không cần đọc lại
file lần thứ hai (dữ liệu đã nằm sẵn trong RAM của repository).

⚠️ QUY TẮC "KHÔNG BỊA SỐ" (CLAUDE.md mục 4) ÁP DỤNG RẤT CHẶT Ở ĐÂY.
Bản thiết kế vẽ sẵn nhiều con số minh hoạ — `+1.248 so với tuần trước`, `CTR 8.7%`,
`Lượt gợi ý hôm nay 1.306`. Dự án KHÔNG lưu ảnh chụp dữ liệu theo ngày, nên không có
cách nào biết "so với tuần trước". File này chỉ tính những gì ĐẾM ĐƯỢC TỪ DỮ LIỆU ĐANG
CÓ; phần nào không có nguồn thì không xuất hiện ở đây, và giao diện phải nói rõ là chưa
có thay vì vẽ một con số cho đẹp.

Số đo thật ngày 2026-08-26 (để người sau đối chiếu khi nghi ngờ):
    địa chỉ 100,0% · khu vực 100,0% · loại hình 100,0%
    điện thoại 81,7% · website 26,1% · giá 1,2% · đánh giá 2,2%
    nguồn: overture 48.427 · openstreetmap 3.026 · google_maps_apify 1.401
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sequence

# Ngưỡng tô màu cho thanh tiến độ ở giao diện. Đặt tên thay vì rải số 80/50 trong code.
#
# VÌ SAO 80 VÀ 50: không phải chuẩn ngành, mà chọn theo dữ liệu THẬT của dự án. Ba trường
# xương sống (địa chỉ · khu vực · loại hình) đều ~100%; điện thoại 81,7% là mức "dùng
# được"; website 26,1% là mức "thiếu nhiều". Hai ngưỡng này tách đúng ba nhóm đó.
NGUONG_TOT = 80.0
NGUONG_TRUNG_BINH = 50.0


@dataclass(frozen=True)
class DoPhuTruong:
    """Độ phủ của MỘT trường dữ liệu."""

    khoa: str
    nhan: str
    mo_ta: str
    so_co: int
    tong: int

    @property
    def phan_tram(self) -> float:
        # Dataset rỗng -> 0%, KHÔNG phải 100%. "Không thiếu gì" và "không có gì" là hai
        # chuyện khác hẳn nhau, và ở đây cái đúng là cái bi quan.
        if self.tong <= 0:
            return 0.0
        return round(self.so_co / self.tong * 100, 1)

    @property
    def muc(self) -> str:
        """`tot` / `trung_binh` / `kem` — giao diện tô màu theo đây, không tự tính lại."""
        if self.phan_tram >= NGUONG_TOT:
            return "tot"
        if self.phan_tram >= NGUONG_TRUNG_BINH:
            return "trung_binh"
        return "kem"


@dataclass(frozen=True)
class ThongKeNguon:
    """Số quán theo từng nguồn thu thập."""

    nguon: str
    so_luong: int
    tong: int

    @property
    def phan_tram(self) -> float:
        if self.tong <= 0:
            return 0.0
        return round(self.so_luong / self.tong * 100, 1)


@dataclass(frozen=True)
class ViecCanXuLy:
    """Một nhóm việc trong hộp "Cần xử lý" — inbox của người quản trị.

    `so_luong = 0` vẫn được giữ lại chứ KHÔNG lọc bỏ: "0 quán có khả năng đã đóng cửa"
    là một câu trả lời có ích ("đã kiểm rồi, không có gì"), khác hẳn với việc dòng đó
    biến mất khiến người dùng không biết hệ thống có kiểm hay không.
    """

    khoa: str
    nhan: str
    mo_ta: str
    so_luong: int
    # `muc_do`: 'canh_bao' (cần làm) hoặc 'thong_tin' (biết cho biết).
    muc_do: str = "canh_bao"


def _co_gia_tri(x: Optional[str]) -> bool:
    """Chuỗi rỗng và chuỗi toàn khoảng trắng đều tính là CHƯA CÓ.

    Nguồn dữ liệu hay trả `""` thay vì bỏ trống hẳn; coi `""` là "có" sẽ thổi phồng độ
    phủ — đúng loại sai mà cả bảng thống kê này sinh ra để tránh.
    """
    return bool(x and str(x).strip())


# Các trường được đo, theo đúng thứ tự hiện lên giao diện.
#
# ⚠️ `rating` và `price` CỐ Ý không nằm trong nhóm "thông tin cơ bản": chúng đến từ nguồn
# làm giàu (Apify Google Maps) chứ không phải từ OSM/Overture, nên độ phủ thấp là chuyện
# ĐÃ BIẾT và không phải lỗi cần sửa. Gộp chung sẽ kéo tỷ lệ "cơ bản" xuống và làm người
# đọc tưởng dữ liệu nền đang hỏng.
_TRUONG_CO_BAN: Sequence[tuple] = (
    ("address", "Địa chỉ", "Có thể tìm đến nơi"),
    ("district", "Khu vực", "Thuộc quận/phường nào"),
    ("category", "Loại hình", "Quán ăn, cà phê, nhà hàng…"),
)

_TRUONG_LIEN_HE: Sequence[tuple] = (
    ("phone", "Số điện thoại", "Có thể liên hệ"),
    ("website", "Website", "Thông tin bổ sung"),
)


def do_phu_quan(restaurants: Sequence) -> List[DoPhuTruong]:
    """Độ phủ từng trường của danh sách quán, theo thứ tự hiện lên giao diện."""
    tong = len(restaurants)
    ket_qua: List[DoPhuTruong] = []

    # "Đủ thông tin cơ bản" = có ĐỦ CẢ BA trường nền, không phải trung bình cộng của ba
    # tỷ lệ. Một quán thiếu địa chỉ thì không dùng được, dù có đủ hai trường kia.
    du_co_ban = sum(
        1
        for r in restaurants
        if all(_co_gia_tri(getattr(r, ten, None)) for ten, _, _ in _TRUONG_CO_BAN)
    )
    ket_qua.append(
        DoPhuTruong(
            khoa="co_ban",
            nhan="Quán có đủ thông tin cơ bản",
            mo_ta="Địa chỉ, khu vực, loại hình",
            so_co=du_co_ban,
            tong=tong,
        )
    )

    for ten, nhan, mo_ta in _TRUONG_LIEN_HE:
        ket_qua.append(
            DoPhuTruong(
                khoa=ten,
                nhan=f"Quán có {nhan.lower()}",
                mo_ta=mo_ta,
                so_co=sum(1 for r in restaurants if _co_gia_tri(getattr(r, ten, None))),
                tong=tong,
            )
        )

    return ket_qua


def do_phu_mon(dishes: Sequence) -> List[DoPhuTruong]:
    """Độ phủ của danh mục món. `dishes` phải là TOÀN BỘ món, kể cả món chưa có quán."""
    tong = len(dishes)
    return [
        DoPhuTruong(
            khoa="mon_mo_ta",
            nhan="Món ăn có mô tả",
            mo_ta="Giới thiệu món",
            so_co=sum(1 for d in dishes if _co_gia_tri(getattr(d, "description", None))),
            tong=tong,
        ),
        DoPhuTruong(
            khoa="mon_anh",
            nhan="Món ăn có ảnh",
            mo_ta="Hình ảnh đại diện",
            so_co=sum(1 for d in dishes if _co_gia_tri(getattr(d, "image_url", None))),
            tong=tong,
        ),
    ]


def thong_ke_nguon(restaurants: Sequence) -> List[ThongKeNguon]:
    """Số quán theo nguồn, NHIỀU NHẤT ĐỨNG ĐẦU.

    Không dùng `collections.Counter` cho gọn hơn được mấy dòng, nhưng dùng thì mất luôn
    thứ tự ổn định khi hai nguồn bằng nhau — sắp xếp thêm khoá phụ là tên nguồn để bảng
    không nhảy lung tung giữa hai lần tải trang.
    """
    tong = len(restaurants)
    dem: dict = {}
    for r in restaurants:
        ten = getattr(r, "source", None) or "(không rõ nguồn)"
        dem[ten] = dem.get(ten, 0) + 1
    return [
        ThongKeNguon(nguon=ten, so_luong=so, tong=tong)
        for ten, so in sorted(dem.items(), key=lambda x: (-x[1], x[0]))
    ]


def viec_can_xu_ly(restaurants: Sequence, dishes: Sequence) -> List[ViecCanXuLy]:
    """Hộp "Cần xử lý" — mỗi dòng là một nhóm bản ghi người quản trị nên xem lại.

    ⚠️ MỖI DÒNG PHẢI ĐẾM ĐƯỢC TỪ DỮ LIỆU THẬT. Bản thiết kế có dòng "9 dữ liệu cần kiểm
    tra" không nói rõ là gì — cố tình KHÔNG dựng, vì một con số không định nghĩa được thì
    người quản trị bấm vào cũng không biết phải làm gì.
    """
    thieu_lien_he = sum(
        1
        for r in restaurants
        if not _co_gia_tri(getattr(r, "phone", None))
        and not _co_gia_tri(getattr(r, "website", None))
    )

    return [
        ViecCanXuLy(
            khoa="dong_tam",
            nhan="Quán có khả năng đã đóng cửa",
            mo_ta="Nguồn đánh dấu đóng tạm thời — cần kiểm tra và xác nhận",
            so_luong=sum(1 for r in restaurants if getattr(r, "temporarily_closed", None)),
        ),
        ViecCanXuLy(
            khoa="thieu_lien_he",
            nhan="Quán không có cách nào liên hệ",
            mo_ta="Thiếu CẢ số điện thoại lẫn website",
            so_luong=thieu_lien_he,
        ),
        ViecCanXuLy(
            khoa="mon_thieu_anh",
            nhan="Món chưa có ảnh",
            mo_ta="Thiếu hình ảnh đại diện món",
            so_luong=sum(
                1 for d in dishes if not _co_gia_tri(getattr(d, "image_url", None))
            ),
        ),
        ViecCanXuLy(
            khoa="mon_thieu_mo_ta",
            nhan="Món chưa có mô tả",
            mo_ta="Chưa tra được giới thiệu từ Wikipedia",
            so_luong=sum(
                1 for d in dishes if not _co_gia_tri(getattr(d, "description", None))
            ),
        ),
        ViecCanXuLy(
            khoa="mon_khong_quan",
            nhan="Món chưa tìm được quán",
            mo_ta="Chưa có quán nào ở Hà Nội bán món này",
            so_luong=sum(
                1 for d in dishes if not getattr(d, "is_active", True)
            ),
            # THÔNG TIN, không phải cảnh báo: phần lớn là món quốc tế chưa quán nào ở Hà
            # Nội bán. Đây là sự thật về thị trường, không phải lỗi dữ liệu cần đi sửa.
            muc_do="thong_tin",
        ),
    ]


__all__ = [
    "DoPhuTruong",
    "ThongKeNguon",
    "ViecCanXuLy",
    "do_phu_quan",
    "do_phu_mon",
    "thong_ke_nguon",
    "viec_can_xu_ly",
    "NGUONG_TOT",
    "NGUONG_TRUNG_BINH",
]

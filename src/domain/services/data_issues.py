"""QUY TẮC NGHIỆP VỤ: hộp việc "CẦN XỬ LÝ" của người quản trị.

Đây là ruột của màn `frontend/design/needs to be handled admin.png` và của khối
"Cần xử lý ngay" trong `frontend/design/quality data admin.png`.

VÌ SAO TÁCH KHỎI `data_quality.py`
-----------------------------------
`data_quality.py` trả lời câu "dữ liệu đầy tới đâu" (ĐỘ PHỦ — một tỷ lệ phần trăm).
File này trả lời câu khác hẳn: "người quản trị phải đi sửa cái gì trước" (DANH SÁCH
VIỆC — có mức ưu tiên, có ví dụ cụ thể để bấm vào). Gộp chung thì file vượt 300 dòng và
trộn hai câu hỏi khác nhau vào một chỗ (CLAUDE.md mục 6).

Hướng phụ thuộc: `data_quality.py` → `data_issues.py`. KHÔNG có chiều ngược lại, nếu
không sẽ vòng tròn import.

HAI TRỤC ĐÁNH GIÁ, ĐỪNG NHẦM
-----------------------------
Mỗi việc mang HAI nhãn, vì bản thiết kế hỏi hai câu khác nhau:

- `muc_do`  — "đây có phải việc PHẢI LÀM không": `canh_bao` / `thong_tin`.
  Khối "Cần xử lý: N" ở trang Tổng quan cộng theo trục này.
- `uu_tien` — "GẤP tới đâu": `nghiem_trong` / `quan_trong` / `can_kiem_tra`.
  Năm thẻ số và các tab của màn "Cần xử lý" lọc theo trục này.

Một việc có thể vừa `thong_tin` (không phải lỗi cần sửa) vừa `can_kiem_tra` (đáng liếc
qua) — ví dụ "món chưa tìm được quán": phần lớn là món quốc tế chưa quán nào ở Hà Nội
bán, đó là sự thật về thị trường chứ không phải lỗi dữ liệu.

⚠️ KHÔNG BỊA SỐ (CLAUDE.md mục 4). Mọi con số ở đây đều đếm được từ dữ liệu đang có.
Bản thiết kế còn vẽ "Đã xử lý hôm nay: 5" — con số đó KHÔNG nằm ở file này vì nó không
phải thuộc tính của dữ liệu quán/món, mà là lịch sử thao tác của người quản trị; nó đến
từ kho `IssueResolutionRepository` và được ghép ở tầng use case.

File này THUẦN PYTHON — không pandas, không sqlite.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from src.domain.value_objects.location import trong_ha_noi
from src.domain.value_objects.text import normalize

# --- Trục 1: việc phải làm hay chỉ để biết -----------------------------------
CANH_BAO = "canh_bao"
THONG_TIN = "thong_tin"

# --- Trục 2: mức ưu tiên, theo đúng ba nhãn của bản thiết kế ------------------
NGHIEM_TRONG = "nghiem_trong"
QUAN_TRONG = "quan_trong"
CAN_KIEM_TRA = "can_kiem_tra"

# Thứ tự GẤP DẦN → dùng để sắp xếp bảng. Khai ở đây để giao diện không tự đoán.
THU_TU_UU_TIEN = (NGHIEM_TRONG, QUAN_TRONG, CAN_KIEM_TRA)

# --- Loại đối tượng, để lọc theo cột "Loại vấn đề" ---------------------------
LOAI_QUAN = "quan_an"
LOAI_MON = "mon_an"
LOAI_DU_LIEU = "du_lieu"

# Số chữ số thập phân khi gom nhóm toạ độ để dò trùng lặp.
#
# VÌ SAO 4: 4 chữ số ≈ 11m ở vĩ độ Hà Nội. Đủ chặt để hai chi nhánh khác nhau của cùng
# một chuỗi (Highlands, Cộng Cà Phê — cách nhau hàng trăm mét) KHÔNG bị chấm là trùng,
# và đủ rộng để cùng một quán được hai nguồn ghi lệch vài mét thì vẫn gom về một ô.
#
# ⚠️ HẠN CHẾ ĐÃ BIẾT, đừng "sửa" mà không đọc: cách gom theo Ô LƯỚI này bỏ sót cặp trùng
# nằm vắt qua ranh giới hai ô. Chấp nhận bỏ sót thay vì dò từng cặp — 52.854 quán mà so
# đôi một là 1,4 tỷ phép so sánh. Con số trả về vì vậy là CẬN DƯỚI ("ít nhất N bản ghi
# nghi trùng"), và giao diện phải nói đúng như vậy.
SO_LE_TOA_DO = 4


def co_gia_tri(x: Optional[str]) -> bool:
    """Chuỗi rỗng và chuỗi toàn khoảng trắng đều tính là CHƯA CÓ.

    Nguồn dữ liệu hay trả `""` thay vì bỏ trống hẳn; coi `""` là "có" sẽ thổi phồng độ
    phủ — đúng loại sai mà cả bảng thống kê này sinh ra để tránh.
    """
    return bool(x and str(x).strip())


@dataclass(frozen=True)
class ViecCanXuLy:
    """Một NHÓM việc trong hộp "Cần xử lý" — inbox của người quản trị.

    `so_luong = 0` vẫn được giữ lại chứ KHÔNG lọc bỏ: "0 quán có khả năng đã đóng cửa"
    là một câu trả lời có ích ("đã kiểm rồi, không có gì"), khác hẳn với việc dòng đó
    biến mất khiến người dùng không biết hệ thống có kiểm hay không.
    """

    khoa: str
    nhan: str
    mo_ta: str
    so_luong: int
    # Xem "HAI TRỤC ĐÁNH GIÁ" ở đầu file trước khi đổi hai trường này.
    muc_do: str = CANH_BAO
    uu_tien: str = CAN_KIEM_TRA
    loai: str = LOAI_DU_LIEU


@dataclass(frozen=True)
class BanGhiVanDe:
    """MỘT bản ghi cụ thể dính lỗi — để người quản trị bấm thẳng vào mà sửa.

    Khác `ViecCanXuLy` (một con số tổng) ở chỗ đây là ví dụ có tên tuổi. Bản thiết kế
    `quality data admin.png` hiện 4 dòng kiểu này ở khối "Cần xử lý ngay".
    """

    khoa: str
    id: str
    ten: str
    # Dòng phụ dưới tên: khu vực với quán, loại ẩm thực với món. Rỗng = chưa có.
    mo_ta: str = ""
    anh_url: Optional[str] = None
    # Ngày NGUỒN cập nhật bản ghi (ISO-8601), để giao diện hiện "N ngày trước".
    #
    # ⚠️ Đây là ngày NGUỒN sửa, KHÔNG phải ngày ta phát hiện lỗi — dự án không lưu lịch
    # sử phát hiện. `None` = chưa biết, và giao diện phải im lặng chứ không được đoán.
    cap_nhat: Optional[str] = None


def _thieu_lien_he(r) -> bool:
    """Không có CÁCH NÀO liên hệ: thiếu CẢ số điện thoại LẪN website."""
    return not co_gia_tri(getattr(r, "phone", None)) and not co_gia_tri(
        getattr(r, "website", None)
    )


def _o_luoi(r) -> Optional[tuple]:
    """Khoá gom nhóm dò trùng: (tên đã bỏ dấu, ô lưới toạ độ). None = không đủ dữ liệu."""
    ten = normalize(getattr(r, "name", None))
    vi_tri = getattr(r, "location", None)
    if not ten or vi_tri is None:
        return None
    return (
        ten,
        round(getattr(vi_tri, "lat", 0.0), SO_LE_TOA_DO),
        round(getattr(vi_tri, "lng", 0.0), SO_LE_TOA_DO),
    )


def nhom_trung_lap(restaurants: Sequence) -> List[List]:
    """Các nhóm quán NGHI trùng nhau: cùng tên (đã bỏ dấu) và cùng một ô lưới ~11m.

    Trả về danh sách nhóm, mỗi nhóm ≥ 2 quán. Nhóm 1 quán không phải trùng nên bị loại.

    Dùng `normalize` của `value_objects/text.py` chứ KHÔNG tự so chuỗi: quán "Phở Bò" và
    "Pho Bo" là một, và ba bug thật của dự án đều đến từ việc tự viết lại phép so khớp
    tiếng Việt (CLAUDE.md mục 4 quy tắc 5).
    """
    gom: dict = {}
    for r in restaurants:
        khoa = _o_luoi(r)
        if khoa is None:
            continue
        gom.setdefault(khoa, []).append(r)
    return [nhom for nhom in gom.values() if len(nhom) > 1]


def dem_trung_lap(restaurants: Sequence) -> int:
    """Số bản ghi THỪA do trùng lặp = tổng bản ghi trong các nhóm trừ đi số nhóm.

    Đếm bản thừa chứ không đếm cả nhóm: một nhóm 3 bản ghi nghĩa là có 1 quán thật và
    2 bản ghi cần gỡ, nên con số đúng là 2 — đó mới là khối lượng việc phải làm.
    """
    return sum(len(nhom) - 1 for nhom in nhom_trung_lap(restaurants))


def quan_ngoai_ha_noi(restaurants: Sequence) -> List:
    """Quán có toạ độ nằm NGOÀI khung bao Hà Nội — tức lọt khỏi phạm vi sản phẩm.

    Quán thiếu toạ độ KHÔNG bị tính vào đây: "không biết ở đâu" khác "biết chắc ở tỉnh
    khác", và gộp hai thứ đó lại sẽ đẩy người quản trị đi xoá nhầm (CLAUDE.md mục 4
    quy tắc 1).
    """
    ra_ngoai = []
    for r in restaurants:
        vi_tri = getattr(r, "location", None)
        if vi_tri is None:
            continue
        lat = getattr(vi_tri, "lat", None)
        lng = getattr(vi_tri, "lng", None)
        if lat is None or lng is None:
            continue
        if not trong_ha_noi(lat, lng):
            ra_ngoai.append(r)
    return ra_ngoai


def viec_can_xu_ly(restaurants: Sequence, dishes: Sequence) -> List[ViecCanXuLy]:
    """Bảy nhóm việc, theo đúng thứ tự hiện lên bản thiết kế.

    ⚠️ MỖI DÒNG PHẢI ĐẾM ĐƯỢC TỪ DỮ LIỆU THẬT. Bản thiết kế có dòng "9 dữ liệu cần kiểm
    tra" không nói rõ là gì — CỐ TÌNH không dựng, vì một con số không định nghĩa được thì
    người quản trị bấm vào cũng không biết phải làm gì.
    """
    return [
        ViecCanXuLy(
            khoa="dong_tam",
            nhan="Quán có khả năng đã đóng cửa",
            mo_ta="Nguồn đánh dấu đóng tạm thời — cần kiểm tra và xác nhận",
            so_luong=sum(
                1 for r in restaurants if getattr(r, "temporarily_closed", None)
            ),
            muc_do=CANH_BAO,
            # NGHIÊM TRỌNG vì đây là nhóm duy nhất dẫn người dùng tới một cánh cửa đóng.
            # Mọi lỗi còn lại chỉ làm thông tin nghèo đi, lỗi này làm người ta đi phí công.
            uu_tien=NGHIEM_TRONG,
            loai=LOAI_QUAN,
        ),
        ViecCanXuLy(
            khoa="thieu_lien_he",
            nhan="Quán không có cách nào liên hệ",
            mo_ta="Thiếu CẢ số điện thoại lẫn website",
            so_luong=sum(1 for r in restaurants if _thieu_lien_he(r)),
            muc_do=CANH_BAO,
            uu_tien=QUAN_TRONG,
            loai=LOAI_QUAN,
        ),
        ViecCanXuLy(
            khoa="trung_lap",
            nhan="Dữ liệu trùng lặp cần kiểm tra",
            mo_ta="Cùng tên và cùng vị trí (~11m) — nhiều nguồn ghi về một quán",
            so_luong=dem_trung_lap(restaurants),
            muc_do=CANH_BAO,
            uu_tien=QUAN_TRONG,
            loai=LOAI_DU_LIEU,
        ),
        ViecCanXuLy(
            khoa="mon_thieu_anh",
            nhan="Món chưa có ảnh",
            mo_ta="Thiếu hình ảnh đại diện món",
            so_luong=sum(
                1 for d in dishes if not co_gia_tri(getattr(d, "image_url", None))
            ),
            muc_do=CANH_BAO,
            uu_tien=CAN_KIEM_TRA,
            loai=LOAI_MON,
        ),
        ViecCanXuLy(
            khoa="mon_thieu_mo_ta",
            nhan="Món chưa có mô tả",
            mo_ta="Chưa tra được giới thiệu từ Wikipedia",
            so_luong=sum(
                1 for d in dishes if not co_gia_tri(getattr(d, "description", None))
            ),
            muc_do=CANH_BAO,
            uu_tien=CAN_KIEM_TRA,
            loai=LOAI_MON,
        ),
        ViecCanXuLy(
            khoa="ngoai_ha_noi",
            nhan="Dữ liệu ngoài Hà Nội",
            mo_ta="Toạ độ nằm ngoài phạm vi sản phẩm (chốt 2026-08-19)",
            so_luong=len(quan_ngoai_ha_noi(restaurants)),
            muc_do=CANH_BAO,
            uu_tien=CAN_KIEM_TRA,
            loai=LOAI_DU_LIEU,
        ),
        ViecCanXuLy(
            khoa="mon_khong_quan",
            nhan="Món chưa tìm được quán",
            mo_ta="Chưa có quán nào ở Hà Nội bán món này",
            so_luong=sum(1 for d in dishes if not getattr(d, "is_active", True)),
            # THÔNG TIN, không phải cảnh báo: phần lớn là món quốc tế chưa quán nào ở Hà
            # Nội bán. Đây là sự thật về thị trường, không phải lỗi dữ liệu cần đi sửa.
            muc_do=THONG_TIN,
            uu_tien=CAN_KIEM_TRA,
            loai=LOAI_MON,
        ),
    ]


def _quan_thanh_ban_ghi(khoa: str, r) -> BanGhiVanDe:
    return BanGhiVanDe(
        khoa=khoa,
        id=str(getattr(r, "place_id", "") or getattr(r, "name", "")),
        ten=getattr(r, "name", "") or "(không có tên)",
        mo_ta=getattr(r, "district", None) or getattr(r, "address", None) or "",
        anh_url=getattr(r, "thumbnail_url", None),
        cap_nhat=getattr(r, "source_updated_at", None),
    )


def _mon_thanh_ban_ghi(khoa: str, d) -> BanGhiVanDe:
    return BanGhiVanDe(
        khoa=khoa,
        id=str(getattr(d, "dish_id", "") or getattr(d, "name", "")),
        ten=getattr(d, "name", "") or "(không có tên)",
        mo_ta=getattr(d, "cuisine", None) or "",
        anh_url=getattr(d, "image_url", None),
    )


# Mỗi khoá → hàm lọc ra những bản ghi dính lỗi đó.
#
# Viết thành bảng tra thay vì `if/elif` dài: thêm một loại vấn đề mới chỉ phải thêm một
# dòng ở đây và một dòng ở `viec_can_xu_ly`, không phải sửa thân hàm.
_BO_LOC_QUAN = {
    "dong_tam": lambda r: bool(getattr(r, "temporarily_closed", None)),
    "thieu_lien_he": _thieu_lien_he,
}
_BO_LOC_MON = {
    "mon_thieu_anh": lambda d: not co_gia_tri(getattr(d, "image_url", None)),
    "mon_thieu_mo_ta": lambda d: not co_gia_tri(getattr(d, "description", None)),
    "mon_khong_quan": lambda d: not getattr(d, "is_active", True),
}


def ban_ghi_dinh_loi(
    restaurants: Sequence,
    dishes: Sequence,
    khoa: str,
    gioi_han: int = 20,
) -> List[BanGhiVanDe]:
    """Ví dụ CỤ THỂ của một loại vấn đề — tối đa `gioi_han` bản ghi.

    Khoá lạ trả về danh sách RỖNG chứ không ném lỗi: giao diện gọi hàm này để dựng một
    khối phụ, và một khoá gõ sai không đáng làm trắng cả trang quản trị.
    """
    if gioi_han <= 0:
        return []

    if khoa in _BO_LOC_QUAN:
        loc = _BO_LOC_QUAN[khoa]
        ket_qua = []
        for r in restaurants:
            if loc(r):
                ket_qua.append(_quan_thanh_ban_ghi(khoa, r))
                if len(ket_qua) >= gioi_han:
                    break
        return ket_qua

    if khoa in _BO_LOC_MON:
        loc = _BO_LOC_MON[khoa]
        ket_qua = []
        for d in dishes:
            if loc(d):
                ket_qua.append(_mon_thanh_ban_ghi(khoa, d))
                if len(ket_qua) >= gioi_han:
                    break
        return ket_qua

    if khoa == "ngoai_ha_noi":
        return [
            _quan_thanh_ban_ghi(khoa, r)
            for r in quan_ngoai_ha_noi(restaurants)[:gioi_han]
        ]

    if khoa == "trung_lap":
        # Lấy các BẢN THỪA (bỏ bản đầu mỗi nhóm) — đúng thứ người quản trị phải gỡ.
        ket_qua: List[BanGhiVanDe] = []
        for nhom in nhom_trung_lap(restaurants):
            for r in nhom[1:]:
                ket_qua.append(_quan_thanh_ban_ghi(khoa, r))
                if len(ket_qua) >= gioi_han:
                    return ket_qua
        return ket_qua

    return []


__all__ = [
    "BanGhiVanDe",
    "ViecCanXuLy",
    "ban_ghi_dinh_loi",
    "co_gia_tri",
    "dem_trung_lap",
    "nhom_trung_lap",
    "quan_ngoai_ha_noi",
    "viec_can_xu_ly",
    "CANH_BAO",
    "THONG_TIN",
    "NGHIEM_TRONG",
    "QUAN_TRONG",
    "CAN_KIEM_TRA",
    "THU_TU_UU_TIEN",
    "LOAI_QUAN",
    "LOAI_MON",
    "LOAI_DU_LIEU",
]

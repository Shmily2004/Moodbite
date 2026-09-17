"""QUY TẮC NGHIỆP VỤ: tổng hợp NHẬT KÝ TƯƠNG TÁC cho khối "Hệ thống gợi ý" ở màn Tổng quan.

Bản thiết kế `frontend/design/Dashboard admin.png` vẽ bốn ô: Lượt gợi ý hôm nay · CTR ·
Lượt tương tác · Độ phủ món, mỗi ô kèm một đường sparkline. File này chỉ tính những gì
ĐẾM ĐƯỢC từ `interactions.jsonl`:

    tổng lượt tương tác · tỷ lệ tín hiệu tích cực · số phiên / tài khoản khác nhau ·
    số lượt theo từng loại hành động · số lượt theo ngày trong 7 ngày gần nhất

⚠️ KHÔNG CÓ CTR, VÀ KHÔNG ĐƯỢC TỰ SUY RA.
CTR = số lượt bấm / số lượt HIỂN THỊ. Dự án chỉ ghi hành động của người dùng
(`view_detail`, `save`, …) — KHÔNG ghi lượt một quán được hiện ra trong kết quả
(impression). Thiếu mẫu số thì mọi con số "CTR" đều là bịa. Lấy `view_detail / tổng`
thay thế cũng sai: đó là tỷ trọng trong các lượt đã bấm, luôn cao vô lý.
Cũng vì lý do đó không có "Lượt gợi ý hôm nay": lượt tìm kiếm không được ghi lại.

⚠️ `is_positive_signal` LẤY TỪ BẢN GHI, không tính lại ở đây. Server đã đóng dấu nhãn đó
lúc ghi (`InteractionEvent.is_positive_signal`); tính lại theo luật hôm nay sẽ đổi nghĩa
của dữ liệu cũ mỗi lần luật đổi. Bản ghi thiếu nhãn -> KHÔNG tính vào mẫu số của tỷ lệ.

THUẦN PYTHON — không đọc file, không biết JSONL là gì. Adapter đọc, file này chỉ đếm.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Sequence

# Sparkline 7 ngày: đúng khoảng bản thiết kế vẽ, và đủ ngắn để một đồ án chưa có người
# dùng thật không bị một đường thẳng 0 dài 30 ngày.
SO_NGAY_XU_HUONG = 7


@dataclass(frozen=True)
class BanGhiTuongTac:
    """Một dòng nhật ký tương tác, chỉ những trường cần để thống kê.

    `created_at` là chuỗi ISO-8601 như adapter đã ghi. Để chuỗi chứ không ép `datetime`
    ở đây: bản ghi cũ hỏng ngày vẫn phải được đếm vào tổng, chỉ không vào được biểu đồ.
    """

    action_type: str
    created_at: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    is_positive_signal: Optional[bool] = None


@dataclass(frozen=True)
class DiemNgay:
    ngay: str  # YYYY-MM-DD
    so_luot: int


@dataclass(frozen=True)
class ThongKeTuongTac:
    tong: int
    # `None` khi chưa có bản ghi nào mang nhãn — "chưa đo được" khác hẳn "0% tích cực".
    ty_le_tich_cuc: Optional[float]
    so_phien: int
    so_tai_khoan: int
    theo_hanh_dong: Dict[str, int] = field(default_factory=dict)
    theo_ngay: List[DiemNgay] = field(default_factory=list)


def thong_ke_tuong_tac(
    ban_ghi: Sequence[BanGhiTuongTac], hom_nay: date
) -> ThongKeTuongTac:
    """Tổng hợp một lượt. `hom_nay` truyền vào để test cố định được thời gian."""
    tong = len(ban_ghi)
    co_nhan = [b for b in ban_ghi if b.is_positive_signal is not None]
    tich_cuc = sum(1 for b in co_nhan if b.is_positive_signal)

    theo_hanh_dong: Dict[str, int] = {}
    for b in ban_ghi:
        theo_hanh_dong[b.action_type] = theo_hanh_dong.get(b.action_type, 0) + 1

    # Khung 7 ngày ĐỦ NGÀY, kể cả ngày 0 lượt: sparkline thiếu ngày sẽ nối thẳng hai điểm
    # xa nhau và trông như có hoạt động liên tục.
    ngay_dau = hom_nay - timedelta(days=SO_NGAY_XU_HUONG - 1)
    khung = {
        (ngay_dau + timedelta(days=i)).isoformat(): 0 for i in range(SO_NGAY_XU_HUONG)
    }
    for b in ban_ghi:
        ngay = (b.created_at or "")[:10]
        if ngay in khung:
            khung[ngay] += 1

    return ThongKeTuongTac(
        tong=tong,
        ty_le_tich_cuc=(
            round(tich_cuc / len(co_nhan) * 100, 1) if co_nhan else None
        ),
        so_phien=len({b.session_id for b in ban_ghi if b.session_id}),
        so_tai_khoan=len({b.user_id for b in ban_ghi if b.user_id}),
        theo_hanh_dong=dict(
            sorted(theo_hanh_dong.items(), key=lambda kv: (-kv[1], kv[0]))
        ),
        theo_ngay=[DiemNgay(ngay=k, so_luot=v) for k, v in khung.items()],
    )


__all__ = [
    "BanGhiTuongTac",
    "DiemNgay",
    "SO_NGAY_XU_HUONG",
    "ThongKeTuongTac",
    "thong_ke_tuong_tac",
]

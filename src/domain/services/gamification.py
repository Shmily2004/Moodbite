"""CẤP ĐỘ · ĐIỂM · HUY HIỆU — quy tắc nghiệp vụ, thuần Python.

Chủ dự án chốt 2026-08-22: làm cấp độ và huy hiệu, KHÔNG làm review người dùng.

BA NGUYÊN TẮC KHI THIẾT KẾ BẢNG ĐIỂM (đứng ở vai người thiết kế hệ thống, không phải
chép đại một con số cho đẹp):

  1. CHỈ CHO ĐIỂM THỨ ĐẾM ĐƯỢC THẬT.
     Mọi mục dưới đây đều suy ra từ `interactions.jsonl` hoặc bảng `saved_items` — hai
     nguồn đã tồn tại. Không có mục nào cần dữ liệu ta không có (viết review, đăng ảnh,
     mời bạn bè...). Bịa một con số "128 lượt khám phá" là đúng thứ CLAUDE.md mục 4 cấm.

  2. ĐẾM THỨ KHÁC NHAU, KHÔNG ĐẾM SỐ LẦN BẤM.
     Điểm tính trên số QUÁN KHÁC NHAU đã xem, số MÓN KHÁC NHAU đã lưu. Bấm F5 hai chục
     lần vào cùng một quán vẫn chỉ được điểm một lần. Không có luật này thì cấp độ chỉ đo
     được ai rảnh tay hơn, và cả tính năng thành vô nghĩa.
     (Cùng tinh thần với `closure_reports.py`: đếm phiên khác nhau, không đếm lượt bấm.)

  3. ĐÓNG GÓP CHO NGƯỜI KHÁC THÌ ĐÁNG GIÁ HƠN TIÊU THỤ.
     Báo một quán đã đóng cửa được +10, gấp năm lần xem một quán. Vì hành động đó sửa dữ
     liệu cho TẤT CẢ mọi người, còn xem quán thì chỉ có lợi cho chính mình. Thang điểm
     nên khuyến khích đúng thứ dự án cần.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1. Bảng điểm
# ---------------------------------------------------------------------------

# Điểm cho MỖI ĐỐI TƯỢNG KHÁC NHAU, không phải mỗi lượt bấm.
#
# Tỉ lệ 2 : 3 : 5 : 10 chọn theo "công sức bỏ ra và giá trị đem lại", không theo cảm tính:
#   xem quán (2)      - rẻ nhất, ai cũng làm được, chỉ có lợi cho bản thân
#   chỉ đường (3)     - tín hiệu mạnh hơn: người dùng thật sự định tới đó
#   lưu (5)           - người dùng chủ động tuyên bố "tôi thích cái này"
#   báo đóng cửa (10) - sửa dữ liệu cho cả cộng đồng, và tốn công đi xác nhận tận nơi
DIEM_XEM_QUAN = 2
DIEM_CHI_DUONG = 3
DIEM_LUU = 5
DIEM_DANH_GIA = 3
DIEM_BAO_DONG_CUA = 10


@dataclass(frozen=True)
class UserActivity:
    """Số liệu THẬT của một người, đã khử trùng lặp.

    Mọi trường đều là "số đối tượng KHÁC NHAU", trừ `active_days` là số NGÀY khác nhau.
    Ai dựng dataclass này phải bảo đảm điều đó — xem `ActivityTally`.
    """

    viewed_restaurants: int = 0
    directions: int = 0
    saved_items: int = 0
    ratings: int = 0
    closure_reports: int = 0
    active_days: int = 0

    @property
    def explorations(self) -> int:
        """"LƯỢT KHÁM PHÁ" hiện trên trang tài khoản.

        Định nghĩa: SỐ QUÁN KHÁC NHAU người này đã mở xem chi tiết. Cố ý chọn cách đếm
        hẹp và dễ giải thích, thay vì cộng gộp mọi loại tương tác — người dùng nhìn con
        số phải hiểu ngay nó đếm cái gì, nếu không thì nó chỉ là con số trang trí.
        """
        return self.viewed_restaurants

    @property
    def points(self) -> int:
        return (
            self.viewed_restaurants * DIEM_XEM_QUAN
            + self.directions * DIEM_CHI_DUONG
            + self.saved_items * DIEM_LUU
            + self.ratings * DIEM_DANH_GIA
            + self.closure_reports * DIEM_BAO_DONG_CUA
        )


# ---------------------------------------------------------------------------
# 2. Cấp độ
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Level:
    number: int
    name: str
    min_points: int


# NĂM CẤP. Mốc điểm chọn theo "bao lâu thì tới", không phải theo số tròn cho đẹp:
#
#   Cấp 2 (50đ)   ~ xem 15 quán + lưu 4 món  -> đạt được ngay trong buổi dùng thử đầu
#                   tiên nếu dùng nghiêm túc. Cấp đầu tiên phải TỚI ĐƯỢC, nếu không thì
#                   thanh tiến độ chỉ làm người ta nản.
#   Cấp 3 (150đ)  ~ vài buổi dùng
#   Cấp 4 (400đ)  ~ dùng đều một thời gian, hoặc có đóng góp báo đóng cửa
#   Cấp 5 (900đ)  ~ người dùng thật sự gắn bó. Cố ý để xa: một cấp cao nhất mà ai cũng
#                   chạm tới trong một tuần thì không còn là mốc gì nữa.
#
# Khoảng cách giữa các cấp tăng dần (50 -> 100 -> 250 -> 500) — chuẩn mực của mọi hệ cấp
# độ: giữ nhịp thưởng dày ở đầu, thưa dần về sau.
LEVELS: Tuple[Level, ...] = (
    Level(1, "Người mới", 0),
    Level(2, "Foodie Explorer", 50),
    Level(3, "Thổ địa Hà Nội", 150),
    Level(4, "Sành ăn", 400),
    Level(5, "Huyền thoại ẩm thực", 900),
)


@dataclass(frozen=True)
class LevelProgress:
    level: Level
    points: int
    next_level: Optional[Level]

    @property
    def points_to_next(self) -> Optional[int]:
        if self.next_level is None:
            return None
        return max(0, self.next_level.min_points - self.points)

    @property
    def ratio(self) -> float:
        """Tỉ lệ [0,1] để vẽ thanh tiến độ.

        Tính trong KHOẢNG GIỮA HAI CẤP, không phải trên tổng điểm tối đa. Nếu tính trên
        tổng thì người ở cấp 2 nhìn thấy thanh gần như trống suốt nhiều tuần.
        Cấp cuối thì thanh đầy — không còn gì để tiến tới nữa.
        """
        if self.next_level is None:
            return 1.0
        khoang = self.next_level.min_points - self.level.min_points
        if khoang <= 0:
            return 1.0
        return min(1.0, max(0.0, (self.points - self.level.min_points) / khoang))


def tinh_cap_do(points: int) -> LevelProgress:
    """Điểm -> cấp hiện tại + cấp kế tiếp. Hàm thuần, dễ test."""
    diem = max(0, int(points))
    hien_tai = LEVELS[0]
    ke_tiep: Optional[Level] = None
    for i, cap in enumerate(LEVELS):
        if diem >= cap.min_points:
            hien_tai = cap
            ke_tiep = LEVELS[i + 1] if i + 1 < len(LEVELS) else None
    return LevelProgress(level=hien_tai, points=diem, next_level=ke_tiep)


# ---------------------------------------------------------------------------
# 3. Huy hiệu
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BadgeRule:
    badge_id: str
    name: str
    description: str
    emoji: str
    # Tên thuộc tính trên `UserActivity` và ngưỡng cần đạt. Dùng TÊN THUỘC TÍNH (chuỗi)
    # thay vì lambda để bảng này còn là dữ liệu thuần: serialize được, test được, và
    # sau này đưa vào CSDL cũng không phải viết lại.
    field_name: str
    target: int


# Mỗi huy hiệu phải KIỂM CHỨNG ĐƯỢC từ `UserActivity`. Không có huy hiệu nào kiểu
# "Người nếm thử 5 sao" — ta không có review, nên trao nó là bịa.
BADGES: Tuple[BadgeRule, ...] = (
    BadgeRule(
        "explorer", "Explorer", "Xem chi tiết 20 quán khác nhau", "🧭",
        "viewed_restaurants", 20,
    ),
    BadgeRule(
        "nguoi_sanh_an", "Người sành ăn", "Lưu 10 món hoặc quán", "👨‍🍳",
        "saved_items", 10,
    ),
    BadgeRule(
        "khach_quen", "Khách quen", "Hoạt động trong 3 ngày khác nhau", "📅",
        "active_days", 3,
    ),
    BadgeRule(
        "nguoi_dan_duong", "Người dẫn đường", "Bấm chỉ đường tới 5 quán", "🗺️",
        "directions", 5,
    ),
    BadgeRule(
        # Ngưỡng 1 CÓ CHỦ ĐÍCH: đây là hành động ta muốn khuyến khích nhất (nó sửa dữ
        # liệu cho mọi người) nên phải thưởng ngay từ lần đầu.
        "nguoi_giu_ban_do", "Người giữ bản đồ", "Báo 1 quán đã đóng cửa", "🛡️",
        "closure_reports", 1,
    ),
)


@dataclass(frozen=True)
class BadgeProgress:
    rule: BadgeRule
    current: int

    @property
    def earned(self) -> bool:
        return self.current >= self.rule.target


def tinh_huy_hieu(activity: UserActivity) -> List[BadgeProgress]:
    """Trả về TOÀN BỘ huy hiệu kèm tiến độ, kể cả cái chưa đạt.

    Cố ý trả cả cái chưa đạt: huy hiệu mờ kèm "12/20" cho người dùng biết phải làm gì
    tiếp. Chỉ trả cái đã đạt thì người mới nhìn vào một ô trống, không hiểu gì.
    """
    return [
        BadgeProgress(rule=rule, current=int(getattr(activity, rule.field_name, 0)))
        for rule in BADGES
    ]


__all__ = [
    "UserActivity", "Level", "LevelProgress", "LEVELS", "tinh_cap_do",
    "BadgeRule", "BadgeProgress", "BADGES", "tinh_huy_hieu",
    "DIEM_XEM_QUAN", "DIEM_CHI_DUONG", "DIEM_LUU", "DIEM_DANH_GIA",
    "DIEM_BAO_DONG_CUA",
]

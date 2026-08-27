"""Entity Dish và DishRule (1 rule trong dish_knowledge_base.json).

Thuần Python - KHÔNG import pandas/FastAPI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.domain.value_objects.text import contains_phrase, normalize

# Mức độ tin cậy của việc suy luận "quán này bán món gì".
# Đây là suy luận HEURISTIC từ categoryName, KHÔNG phải menu thật của quán.
CONFIDENCE_SPECIFIC = "specific"          # khớp rule cụ thể: "phở", "lẩu"...
CONFIDENCE_GENERIC = "generic_fallback"   # suy luận rộng từ nhóm chung: "nhà hàng"
CONFIDENCE_UNKNOWN = "unknown"            # không khớp rule nào
CONFIDENCE_ML = "ml"                      # rule do model ML gán

# CÁCH CHẾ BIẾN. Đây là thứ bộ lọc "đồ nướng" thực sự cần: trước đây chỉ có
# `temperature` (hot/cold) nên không có cách nào phân biệt "phở nóng" với "thịt nướng" -
# cả hai đều hot. Danh sách đóng, vì để tự do nhập chữ thì "nướng"/"Nướng"/"nuong" sẽ
# thành 3 giá trị khác nhau và bộ lọc trượt hết.
METHOD_GRILLED = "nuong"     # nướng, quay
METHOD_FRIED = "chien"       # chiên, rán
METHOD_BOILED = "luoc"       # luộc, chần
METHOD_STEAMED = "hap"       # hấp, đồ
METHOD_STIR_FRIED = "xao"    # xào, rang
METHOD_SOUP = "nuoc"         # món nước: phở, bún, miến, lẩu
METHOD_RAW = "song"          # gỏi, sashimi, salad
METHOD_MIXED = "tron"        # trộn, nộm
METHOD_BAKED = "nuong_lo"    # bánh nướng lò: pizza, bánh mì

COOKING_METHODS: tuple[str, ...] = (
    METHOD_GRILLED, METHOD_FRIED, METHOD_BOILED, METHOD_STEAMED,
    METHOD_STIR_FRIED, METHOD_SOUP, METHOD_RAW, METHOD_MIXED, METHOD_BAKED,
)

# Bữa trong ngày. Dùng để khớp với ngữ cảnh giờ (ContextSignal.meal_time).
MEAL_BREAKFAST = "sang"
MEAL_LUNCH = "trua"
MEAL_DINNER = "toi"
MEAL_LATE_NIGHT = "khuya"
MEAL_SNACK = "an_vat"

MEAL_TIMES: tuple[str, ...] = (
    MEAL_BREAKFAST, MEAL_LUNCH, MEAL_DINNER, MEAL_LATE_NIGHT, MEAL_SNACK,
)

# Nguồn gốc dữ liệu GIỚI THIỆU món (CLAUDE.md mục 4b: mọi bản ghi phải truy được nguồn).
DISH_SOURCE_WIKIPEDIA = "wikipedia_vi"
DISH_SOURCE_MANUAL = "manual"
DISH_SOURCE_SEED = "seed_kb"      # sinh từ dish_knowledge_base.json có sẵn
DISH_SOURCE_ADMIN = "admin"       # admin tự thêm qua trang quản trị


def slugify_dish(name: str) -> str:
    """'Phở Bò' -> 'pho-bo'. Dùng làm `dish_id` ổn định trên URL.

    Bỏ dấu trước khi tạo slug: id có dấu sẽ bị mã hoá phần trăm trên URL
    (`ph%E1%BB%9F-b%C3%B2`), vừa xấu vừa khó đối chiếu khi đọc log.
    """
    cleaned = "".join(c if c.isalnum() else " " for c in normalize(name))
    return "-".join(cleaned.split())


@dataclass(frozen=True)
class Dish:
    """Một MÓN ĂN.

    Trước đây món chỉ là nhãn gắn kèm quán (`suggested_dish`). Nay món là thực thể có
    trang riêng - người dùng chọn món TRƯỚC rồi mới tìm quán - nên cần đủ thông tin để
    (a) lọc được, (b) giới thiệu được cho người đọc, (c) tìm ngược ra quán.

    MỌI FIELD MỚI ĐỀU CÓ MẶC ĐỊNH: `dish_knowledge_base.json` cũ chưa có các field này,
    và món cũ vẫn phải dựng được như thường.

    `None`/rỗng nghĩa là CHƯA CÓ DỮ LIỆU, không phải "không có" (CLAUDE.md mục 4 quy tắc 1).
    Món chưa tra được giới thiệu thì `description` để None và UI phải nói "chưa có dữ liệu",
    tuyệt đối không để một khoảng trắng như thể món đó không có gì để nói.
    """

    name: str
    cuisine: Optional[str] = None
    spice_level: Optional[int] = None
    temperature: Optional[str] = None
    portion_size: Optional[str] = None
    mood_keywords: List[str] = field(default_factory=list)

    # --- định danh ---
    # Để trống thì suy từ `name`. Có field riêng vì admin cần sửa TÊN món mà không làm
    # gãy URL/liên kết đã chia sẻ.
    dish_id: Optional[str] = None

    # --- thuộc tính lọc (Phase 1: thứ bộ lọc trang chủ dựa vào) ---
    cooking_method: Optional[str] = None      # một trong COOKING_METHODS
    meal_times: List[str] = field(default_factory=list)

    # --- nội dung hiển thị ở TRANG CHI TIẾT MÓN ---
    # GIỚI THIỆU NGẮN: món này là gì, ăn thế nào. Chốt 2026-08-19 thay cho danh sách
    # nguyên liệu. Lý do: đoạn mở đầu bài Wikipedia vốn đã kể luôn nguyên liệu chính
    # ngay trong câu văn, vừa dễ đọc hơn danh sách rời rạc vừa phủ được nhiều món hơn.
    description: Optional[str] = None
    # CHỈ LÀ ĐƯỜNG DẪN, không bao giờ là ảnh tải về: máy chủ dự án là laptop cá nhân.
    # Lưu URL tốn ~100 byte/món thay vì ~200KB/món.
    image_url: Optional[str] = None

    # --- tìm ngược ra QUÁN ---
    # Từ khoá dùng để khớp TÊN QUÁN. Rỗng -> suy từ `name` lúc khớp (xem
    # `restaurant_match_keywords`). Tách riêng để admin thêm biến thể ("bún bò Huế" nên
    # khớp cả quán chỉ ghi "bún bò").
    match_keywords: List[str] = field(default_factory=list)

    # --- xuất xứ dữ liệu (CLAUDE.md mục 4b) ---
    source: Optional[str] = None
    source_url: Optional[str] = None
    last_updated: Optional[str] = None
    data_confidence: Optional[str] = None

    # ĐÂY LÀ DANH MỤC hay MỘT MÓN CỤ THỂ.
    #
    # Chủ dự án chỉ ra 2026-08-24: "Bún" là DANH MỤC, còn "bún bò", "bún cá", "bún dọc
    # mùng" mới là MÓN. Trước đó danh mục trộn lẫn cả hai, nên trang chủ hiện thẻ "Bún —
    # 2.370 quán" (vô nghĩa với người đang đói) và nút đề xuất nhanh cũng trả về "Bún".
    #
    # Đo trên dữ liệu thật: 52/855 mục là danh mục theo ngưỡng "có >= 3 món con", trong
    # đó Bún(29 con) · Bánh mì(26) · Cơm(16) · Kem(16) · Chè(13) · Phở(8) · Mì(8).
    # Ngưỡng 3 do chủ dự án chốt: để 2 thì "Bún chả"(2 con) bị gọi là danh mục, mà đó là
    # món ai cũng gọi đích danh.
    #
    # KHÔNG xoá danh mục khỏi dữ liệu — chúng là đường điều hướng tốt ("cho tôi xem mọi
    # loại bún"). Chỉ là lưới món và nút đề xuất phải bỏ qua chúng.
    is_category: bool = False

    # BẬT / TẮT — soft-delete, cùng quy ước với quán.
    #
    # Trong `dish_catalog.json`, `is_active=false` nghĩa là CHƯA TÌM ĐƯỢC QUÁN NÀO ở Hà
    # Nội bán món đó (đo 2026-08-26: 557/855 món, phần lớn là món quốc tế). Người dùng
    # KHÔNG được thấy chúng — bấm vào chỉ gặp danh sách quán rỗng.
    #
    # Vì sao vẫn phải có trên entity dù người dùng không thấy: trang quản trị cần đếm
    # được "855 tổng / 298 có quán / 557 chưa có quán". Trước 2026-08-26 trường này bị
    # bỏ khi dựng entity, nên mọi phép đếm ở tầng trên đều tưởng mọi món đều đang bật.
    is_active: bool = True

    @property
    def identifier(self) -> str:
        """`dish_id` đã đặt, hoặc slug suy từ tên."""
        return self.dish_id or slugify_dish(self.name)

    @property
    def restaurant_match_keywords(self) -> List[str]:
        """Từ khoá dùng để tìm quán bán món này.

        Mặc định là chính TÊN MÓN. Đo trên dataset thật: tên quán mang tín hiệu món gấp
        ~10 lần `categoryName` (144 quán có "phở" trong tên, chỉ 14 quán có trong
        category) - nên khớp tên món vào tên quán là đường đi chính, không phải phương án dự phòng.
        """
        return self.match_keywords or [self.name]

    @property
    def has_description(self) -> bool:
        """Đã có giới thiệu chưa.

        UI dùng cờ này để chọn giữa hiện đoạn giới thiệu và hiện "chưa có dữ liệu".
        Có cờ riêng thay vì để UI tự đoán từ chuỗi rỗng, vì rỗng ở đây nghĩa là CHƯA TRA
        ĐƯỢC chứ không phải "món này không có gì để nói" (CLAUDE.md mục 4 quy tắc 1).
        """
        return bool(self.description and self.description.strip())

    def matches_any_mood_keyword(self, keywords: List[str]) -> bool:
        return any(k in self.mood_keywords for k in keywords)

    def matches_restaurant_text(self, text: Optional[str]) -> bool:
        """Tên/loại hình quán `text` có gợi ý quán này bán món đó không.

        Dùng `contains_phrase` (khớp TỪ NGUYÊN VẸN sau khi bỏ dấu) chứ không phải `in`:
        đây đúng là chỗ bug "oc khớp Ngọc" từng xảy ra - xem `value_objects/text.py`.
        """
        return any(
            contains_phrase(text, keyword) for keyword in self.restaurant_match_keywords
        )


@dataclass(frozen=True)
class DishRule:
    """1 rule ánh xạ categoryName -> danh sách món."""

    id: str
    confidence: str
    dishes: List[Dish] = field(default_factory=list)
    match_category: List[str] = field(default_factory=list)
    match_cuisine: List[str] = field(default_factory=list)

    def matches_text(self, text: Optional[str]) -> bool:
        """Rule này có khớp một đoạn chữ không (tên quán hoặc loại hình).

        Khớp theo CỤM TỪ NGUYÊN VẸN sau khi bỏ dấu, vì hai lý do đo được trên dữ liệu thật:
          - Nhiều quán tự đặt tên không dấu ("Pho Bo", "O Bun Cha") -> phải bỏ dấu mới khớp.
          - Bỏ dấu xong "ốc" thành "oc"; nếu khớp chuỗi con thì "oc" khớp luôn "Ngọc",
            "Học", "Cốc" -> gợi ý món ốc cho quán chè. Khớp theo từ nguyên vẹn loại bỏ
            hoàn toàn lỗi này.
        """
        return any(contains_phrase(text, keyword) for keyword in self.match_category)

    # Tên cũ, giữ lại để không phải sửa mọi nơi gọi cùng lúc.
    def matches_category(self, category_name: Optional[str]) -> bool:
        return self.matches_text(category_name)

"""Đối chiếu MÓN <-> QUÁN: quán nào bán món này.

Thuần Python. Đây là chiều NGƯỢC với thứ dự án vẫn làm từ trước: trước đây có quán rồi
đoán món (`suggested_dish`), giờ người dùng chọn món trước rồi mới cần tìm quán.

DÙNG CHUNG một phép so khớp với chiều cũ (`Dish.matches_restaurant_text` ->
`contains_phrase_tokens`), nên hai chiều không thể nói khác nhau: nếu quán X được gợi ý
món "bún chả" thì trang món "Bún chả" chắc chắn liệt kê quán X.

VÌ SAO DỰNG CHỈ MỤC MỘT LẦN thay vì quét lúc có yêu cầu: quét 79 món x 4938 quán mất
~11 giây (đã đo). Không ai chờ 11 giây cho một lần bấm bộ lọc. Dựng sẵn lúc khởi động thì
mỗi yêu cầu chỉ còn là tra một khoá trong dict.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from src.domain.entities.dish import Dish
from src.domain.value_objects.text import (
    Token,
    contains_phrase,
    token_sequence_at,
    tokenize_pairs,
)

# Món khớp quán BẰNG CÁCH NÀO. Thứ tự này là thứ tự ĐỘ TIN CẬY giảm dần.
MATCHED_BY_DISH_NAME = "dish_name"  # tên quán chứa ĐÚNG TÊN MÓN ("Phở Gà Nguyệt")
MATCHED_BY_NAME = "name"            # tên quán/loại hình khớp TỪ KHOÁ chung ("phở")
MATCHED_BY_REVIEW = "review"        # chỉ có review nhắc tới -> yếu hơn nhiều
# Quán ĐỒ UỐNG khớp tên CHỈ nhờ chữ không dấu - xem `_is_ambiguous_drink_venue_match`.
MATCHED_BY_UNACCENTED_AT_DRINK_VENUE = "unaccented_name_at_drink_venue"

# Độ mạnh để XẾP HẠNG. Số lớn = đáng tin hơn.
#
# VÌ SAO CẦN TẦNG "ĐÚNG TÊN MÓN": Phở bò, Phở gà và Phở đều dùng chung từ khoá "phở" nên
# ba trang món trả về ĐÚNG một danh sách 1135 quán như nhau - chọn món xong mà không thay
# đổi gì thì luồng "chọn món trước" mất hết ý nghĩa. Nhưng đo trên dữ liệu thật ngày
# 2026-08-19: 178 quán ghi rõ "phở bò" và 202 quán ghi rõ "phở gà" trong TÊN. Đó là tín
# hiệu cụ thể đang bị vứt đi.
#
# Vẫn KHÔNG khẳng định quán chỉ bán đúng món đó - ta chưa bao giờ đọc thực đơn thật
# (CLAUDE.md mục 4 quy tắc 4). Chỉ là: quán tên "Phở Gà Nguyệt" đáng đứng trên quán tên
# "Phở Thìn" ở TRANG MÓN PHỞ GÀ. Cả hai vẫn có mặt.
#
# TẦNG "QUÁN ĐỒ UỐNG KHỚP TÊN KHÔNG DẤU" (thêm 2026-09-16). Đo trên trang món Phở thật:
# 1491 quán, 39 quán có loại hình đồ uống, 19 quán trong đó khớp CHỈ nhờ chữ "pho" không
# dấu ("Pho Co Coffee", "Ca phe pho", "Cafe Goc pho" - gần như chắc là "phố"), và hai quán
# như thế đứng hạng 2 và 5. Quy tắc "dấu là bằng chứng" KHÔNG đổi (chủ dự án chưa chốt):
# quán vẫn CÓ MẶT, chỉ xếp dưới quán khớp tên có bằng chứng, và vẫn trên quán chỉ được
# review nhắc tới. Quán đồ uống ghi CÓ DẤU ("Phở Cuốn Hoa Lan" - Quán cà phê) giữ nguyên tầng.
MATCH_STRENGTH = {
    MATCHED_BY_DISH_NAME: 4,
    MATCHED_BY_NAME: 3,
    MATCHED_BY_UNACCENTED_AT_DRINK_VENUE: 2,
    MATCHED_BY_REVIEW: 1,
}

# Trường dữ liệu đã khớp, dùng làm `match_source` trả cho client. Dùng ĐÚNG bộ từ vựng của
# `text_relevance` ("name"/"category"/"review") để giao diện chỉ cần một bảng nhãn.
FIELD_NAME = "name"
FIELD_CATEGORY = "category"
FIELD_REVIEW = "review"

# Loại hình quán ĐỒ UỐNG (so qua `contains_phrase` với `categoryName`). Giá trị thật đo
# 2026-09-16 trên trang món Phở: "Quán cà phê" (32 quán), "Quán bar" (4), "Quán trà" (3).
DRINK_VENUE_CATEGORY_PHRASES: tuple[str, ...] = (
    "cà phê", "cafe", "coffee", "quán trà", "trà sữa", "quán bar", "quán rượu", "pub",
    "giải khát",
)
# Món mà bản thân nó là ĐỒ UỐNG: quán cà phê bán cà phê là đương nhiên, không được hạ.
DRINK_DISH_PHRASES: tuple[str, ...] = (
    "cà phê", "cafe", "coffee", "trà", "bia", "rượu", "cocktail", "sinh tố", "nước ép",
)


@dataclass(frozen=True)
class DishMatch:
    """Một cặp (quán, vì sao khớp).

    VÌ SAO PHẢI GHI CÁCH KHỚP: quán tên "Bún Chả Hương Liên" và quán tên "Nhà Hàng Hoàng"
    mà review có nhắc "bún chả" KHÔNG đáng tin như nhau. Bản đầu trộn chung hai loại, và
    trên dữ liệu thật (40.720 quán) kết quả là "Nhà Hàng Hoàng" cách 870m đứng TRÊN
    "Bun Cha Nem Cua Be" cách 310m ở trang món Bún chả - vô lý với người dùng.
    """

    restaurant: object
    matched_by: str
    # Khớp ở TÊN hay LOẠI HÌNH quán. Mặc định "name" để mọi chỗ dựng `DishMatch(quán,
    # MATCHED_BY_NAME)` cũ vẫn đúng nghĩa. Với khớp qua review thì trường này bị bỏ qua.
    matched_field: str = FIELD_NAME

    @property
    def match_source(self) -> str:
        """Nguồn khớp để trả cho client: "name" / "category" / "review"."""
        if self.matched_by == MATCHED_BY_REVIEW:
            return FIELD_REVIEW
        return self.matched_field

    @property
    def is_strong(self) -> bool:
        """Khớp qua TÊN/LOẠI HÌNH quán (bất kể tầng nào) chứ không phải chỉ qua review."""
        return self.matched_by != MATCHED_BY_REVIEW

    @property
    def strength(self) -> int:
        """Số càng lớn càng đáng tin. Dùng để xếp hạng theo tầng."""
        return MATCH_STRENGTH.get(self.matched_by, 0)


# Số từ TỐI THIỂU của tên món để được phép khớp vào REVIEW.
#
# Vì sao phải chặn tên một từ: review dài trung bình 670 ký tự và nói đủ thứ chuyện. Tên
# một từ như "Cơm", "Bún", "Trà" xuất hiện trong gần như mọi review, nên khớp vào review
# sẽ gán món đó cho hàng nghìn quán không liên quan. Tên từ hai từ trở lên ("bún chả",
# "bánh đa cua") thì việc được nhắc tới trong review là tín hiệu thật.
MIN_TOKENS_FOR_REVIEW_MATCH = 2


def build_dish_restaurant_index(
    dishes: Sequence[Dish], restaurants: Sequence, use_reviews: bool = True
) -> Dict[str, List]:
    """{dish_id: [quán bán món đó]}.

    Một quán có thể nằm ở NHIỀU món - đó là đúng, không phải lỗi: quán "Bún chả Nem cua bể"
    bán cả bún chả lẫn nem. Ép mỗi quán về đúng một món chính là cách làm mất thông tin.

    Món không khớp quán nào vẫn có mặt trong kết quả với danh sách RỖNG, để phía gọi phân
    biệt được "món không có quán" với "món không tồn tại".

    CÁCH LÀM: đảo bài toán lại. Thay vì với mỗi quán thử cả 79 món (79 x 4938 phép so),
    gom từ khoá món theo TỪ ĐẦU TIÊN, rồi với mỗi từ trong tên quán chỉ xét đúng những món
    có từ khoá bắt đầu bằng từ đó. Tên quán "Phở Thìn" chỉ phải xét các món bắt đầu bằng
    "pho", không phải cả danh mục.

    `use_reviews`: ngoài TÊN QUÁN và LOẠI HÌNH, còn dò cả nội dung REVIEW. Đây đúng là
    phương án dự phòng mà đề án mục 7 nêu: "với các quán không có thực đơn cấu trúc sẵn,
    món ăn được trích xuất từ nội dung review". Đo được trên dữ liệu thật: 1076 quán có
    review (trung bình 670 ký tự), và review bổ sung tín hiệu cho 65 món.
    """
    index: Dict[str, List[DishMatch]] = {dish.identifier: [] for dish in dishes}
    # Ô riêng cho ĐÚNG TÊN MÓN, tách khỏi ô từ khoá chung: tên món là bằng chứng mạnh hơn
    # hẳn nên phải phân biệt được, xem `MATCH_STRENGTH`.
    name_buckets = _bucket_keywords_by_first_token(dishes, keywords_of=lambda d: [d.name])
    buckets = _bucket_keywords_by_first_token(dishes)
    # Dò review dùng CẢ từ khoá LẪN tên món. Không có tên món thì những món mà mọi từ
    # khoá đều dài 1 chữ ("phở", "bún") sẽ không bao giờ dò được review, vì ngưỡng 2 chữ
    # loại sạch - trong khi "phở gà" xuất hiện trong review lại đúng là tín hiệu tốt.
    review_buckets = (
        _bucket_keywords_by_first_token(
            dishes,
            min_tokens=MIN_TOKENS_FOR_REVIEW_MATCH,
            keywords_of=lambda d: list(d.restaurant_match_keywords) + [d.name],
        )
        if use_reviews
        else {}
    )

    drink_dish_ids = {
        dish.identifier for dish in dishes
        if any(
            contains_phrase(text, phrase)
            for text in [dish.name, *dish.restaurant_match_keywords]
            for phrase in DRINK_DISH_PHRASES
        )
    }
    drink_venue_cache: Dict[str, bool] = {}

    for restaurant in restaurants:
        by_dish_name = _matching_dish_ids(restaurant, name_buckets)
        by_name = _matching_dish_ids(restaurant, buckets)
        for dish_id in by_name.keys() | by_dish_name.keys():
            if dish_id in by_dish_name:
                cach, (field_name, has_evidence) = MATCHED_BY_DISH_NAME, by_dish_name[dish_id]
            else:
                cach, (field_name, has_evidence) = MATCHED_BY_NAME, by_name[dish_id]
            if (
                not has_evidence
                and dish_id not in drink_dish_ids
                and _is_drink_venue(restaurant, drink_venue_cache)
            ):
                cach = MATCHED_BY_UNACCENTED_AT_DRINK_VENUE
            index[dish_id].append(DishMatch(restaurant, cach, field_name))
        by_name = by_name.keys() | by_dish_name.keys()

        if review_buckets:
            # Chỉ ghi nhận qua review nếu tên quán CHƯA khớp - tránh đếm một quán hai lần.
            for dish_id in _matching_dish_ids_in_review(restaurant, review_buckets):
                if dish_id not in by_name:
                    index[dish_id].append(DishMatch(restaurant, MATCHED_BY_REVIEW))

    return index


def _bucket_keywords_by_first_token(
    dishes: Sequence[Dish], min_tokens: int = 1, keywords_of=None
) -> Dict[str, List[Tuple[str, List[Token]]]]:
    """{từ đầu tiên ĐÃ BỎ DẤU: [(dish_id, các từ của từ khoá)]}.

    Tách từ khoá món đúng MỘT lần. `min_tokens`: bỏ qua từ khoá ngắn hơn ngưỡng. Dùng khi
    dò review - xem `MIN_TOKENS_FOR_REVIEW_MATCH`.

    ⚠️ KHOÁ GOM NHÓM PHẢI LÀ BẢN BỎ DẤU, dù việc so khớp thì có xét dấu.
    Gom theo bản có dấu thì quán ghi biển không dấu ("Pho Bo Gia Truyen") sẽ rơi vào ô
    "pho" trong khi từ khoá món nằm ở ô "phở" - hai ô không bao giờ gặp nhau và toàn bộ
    nhóm quán mà quy tắc bỏ dấu sinh ra để phục vụ sẽ biến mất. Lọc theo dấu là việc của
    `tokens_match`, xảy ra SAU khi đã vào đúng ô.
    """
    buckets: Dict[str, List[Tuple[str, List[Token]]]] = defaultdict(list)
    lay_tu_khoa = keywords_of or (lambda d: d.restaurant_match_keywords)
    for dish in dishes:
        for keyword in lay_tu_khoa(dish):
            tokens = tokenize_pairs(keyword, min_length=1)
            if len(tokens) >= min_tokens and tokens:
                buckets[tokens[0][0]].append((dish.identifier, tokens))
    return buckets


def _matching_dish_ids_in_review(
    restaurant, buckets: Dict[str, List[Tuple[str, List[Token]]]]
) -> set:
    """Món được NHẮC TỚI trong review của quán.

    Tín hiệu YẾU HƠN tên quán: quán tên "Bún Chả Hương Liên" thì chắc chắn bán bún chả,
    còn review nhắc "bún chả" có thể chỉ là so sánh ("ngon hơn bún chả ở kia"). Vẫn dùng
    vì đây là cách duy nhất tìm ra quán bán món mà không ghi tên món lên biển hiệu - đúng
    phương án dự phòng ở đề án mục 7.

    Quán chưa cào được review thì bỏ qua, KHÔNG bị coi là "không bán món nào".
    """
    review_text = getattr(restaurant, "review_text", None)
    if not review_text:
        return set()

    matched: set = set()
    tokens = tokenize_pairs(review_text, min_length=1)
    for position, (plain, _) in enumerate(tokens):
        for dish_id, needle_tokens in buckets.get(plain, ()):
            if dish_id in matched:
                continue
            if token_sequence_at(tokens, position, needle_tokens):
                matched.add(dish_id)
    return matched


def _is_drink_venue(restaurant, cache: Dict[str, bool]) -> bool:
    """Loại hình quán là đồ uống. Nhớ theo chuỗi loại hình: cả kho chỉ có vài trăm giá trị
    khác nhau, không cần dò lại cụm từ cho từng quán."""
    category = getattr(restaurant, "category", None)
    if not category:
        return False
    if category not in cache:
        cache[category] = any(
            contains_phrase(category, phrase) for phrase in DRINK_VENUE_CATEGORY_PHRASES
        )
    return cache[category]


def _has_accent_evidence(window: List[Token], needle: List[Token]) -> bool:
    """Chỗ khớp này có BẰNG CHỨNG DẤU không.

    Từ khoá có từ mang dấu ("phở") mà ở tên quán TẤT CẢ các từ đó đều viết không dấu
    ("Pho") -> không có bằng chứng: "Pho Co Coffee" có thể là phở, cũng có thể là phố.
    Từ khoá vốn không dấu ("pizza") thì không có gì mơ hồ -> coi là có bằng chứng.

    KHÔNG thay `tokens_match`: quán không dấu VẪN khớp như cũ. Hàm này chỉ trả lời câu
    hỏi phụ "khớp chắc tới đâu" để xếp tầng.
    """
    accented = [
        (found, wanted) for found, wanted in zip(window, needle) if wanted[0] != wanted[1]
    ]
    if not accented:
        return True
    return any(found[0] != found[1] for found, _ in accented)


def _matching_dish_ids(
    restaurant, buckets: Dict[str, List[Tuple[str, List[Token]]]]
) -> Dict[str, Tuple[str, bool]]:
    """Món mà quán này bán. TÊN QUÁN trước, LOẠI HÌNH sau.

    Đo trên dataset thật: 144 quán có "phở" trong TÊN nhưng chỉ 14 quán có trong
    `categoryName` - tên quán mang tín hiệu món gấp ~10 lần. Bug thật khi chỉ dùng
    category: quán "Bún Chả - Nem Cua Bể" bị Google gắn nhãn "Nhà hàng ăn nhanh".

    Xét tên và loại hình thành HAI danh sách từ RIÊNG, không nối lại: nối vào nhau thì một
    cụm từ có thể vắt qua ranh giới (tên kết thúc bằng "bún", loại hình mở đầu bằng "chả"
    -> khớp nhầm "bún chả").

    Trả {dish_id: (trường đã khớp, có bằng chứng dấu không)}. Một món có thể khớp nhiều
    chỗ; chỉ cần MỘT chỗ có bằng chứng dấu là đủ ("Pho Co - Phở Bò" vẫn là quán phở).
    Tên quán được xét trước nên thắng loại hình khi cả hai cùng khớp.
    """
    matched: Dict[str, Tuple[str, bool]] = {}
    name_tokens = tokenize_pairs(restaurant.name, min_length=1)
    category_tokens = tokenize_pairs(getattr(restaurant, "category", None), min_length=1)

    for field_name, tokens in ((FIELD_NAME, name_tokens), (FIELD_CATEGORY, category_tokens)):
        for position, (plain, _) in enumerate(tokens):
            for dish_id, needle_tokens in buckets.get(plain, ()):
                if dish_id in matched and matched[dish_id][1]:
                    continue
                if token_sequence_at(tokens, position, needle_tokens):
                    window = tokens[position : position + len(needle_tokens)]
                    evidence = _has_accent_evidence(window, needle_tokens)
                    if dish_id not in matched or evidence:
                        matched[dish_id] = (
                            matched[dish_id][0] if dish_id in matched else field_name,
                            evidence,
                        )
    return matched


def count_by_dish(index: Dict[str, List]) -> Dict[str, int]:
    """{dish_id: số quán}. Dùng để xếp hạng món và để ẩn món không có quán nào."""
    return {dish_id: len(restaurants) for dish_id, restaurants in index.items()}

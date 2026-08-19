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
from src.domain.value_objects.text import Token, token_sequence_at, tokenize_pairs

# Món khớp quán BẰNG CÁCH NÀO. Thứ tự này là thứ tự ĐỘ TIN CẬY giảm dần.
MATCHED_BY_DISH_NAME = "dish_name"  # tên quán chứa ĐÚNG TÊN MÓN ("Phở Gà Nguyệt")
MATCHED_BY_NAME = "name"            # tên quán/loại hình khớp TỪ KHOÁ chung ("phở")
MATCHED_BY_REVIEW = "review"        # chỉ có review nhắc tới -> yếu hơn nhiều

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
MATCH_STRENGTH = {
    MATCHED_BY_DISH_NAME: 3,
    MATCHED_BY_NAME: 2,
    MATCHED_BY_REVIEW: 1,
}


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

    for restaurant in restaurants:
        by_dish_name = _matching_dish_ids(restaurant, name_buckets)
        by_name = _matching_dish_ids(restaurant, buckets)
        for dish_id in by_name | by_dish_name:
            cach = (
                MATCHED_BY_DISH_NAME if dish_id in by_dish_name else MATCHED_BY_NAME
            )
            index[dish_id].append(DishMatch(restaurant, cach))
        by_name = by_name | by_dish_name

        if review_buckets:
            # Chỉ ghi nhận qua review nếu tên quán CHƯA khớp - tránh đếm một quán hai lần.
            for dish_id in _matching_dish_ids_in_review(restaurant, review_buckets):
                if dish_id not in by_name:
                    index[dish_id].append(DishMatch(restaurant, MATCHED_BY_REVIEW))

    return index


def restaurants_of(matches: Sequence[DishMatch]) -> List:
    """Chỉ lấy quán, bỏ phần "khớp bằng cách nào"."""
    return [m.restaurant for m in matches]


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


def _matching_dish_ids(
    restaurant, buckets: Dict[str, List[Tuple[str, List[Token]]]]
) -> set:
    """Món mà quán này bán. TÊN QUÁN trước, LOẠI HÌNH sau.

    Đo trên dataset thật: 144 quán có "phở" trong TÊN nhưng chỉ 14 quán có trong
    `categoryName` - tên quán mang tín hiệu món gấp ~10 lần. Bug thật khi chỉ dùng
    category: quán "Bún Chả - Nem Cua Bể" bị Google gắn nhãn "Nhà hàng ăn nhanh".

    Xét tên và loại hình thành HAI danh sách từ RIÊNG, không nối lại: nối vào nhau thì một
    cụm từ có thể vắt qua ranh giới (tên kết thúc bằng "bún", loại hình mở đầu bằng "chả"
    -> khớp nhầm "bún chả").
    """
    matched: set = set()
    name_tokens = tokenize_pairs(restaurant.name, min_length=1)
    category_tokens = tokenize_pairs(getattr(restaurant, "category", None), min_length=1)

    for tokens in (name_tokens, category_tokens):
        for position, (plain, _) in enumerate(tokens):
            for dish_id, needle_tokens in buckets.get(plain, ()):
                if dish_id in matched:
                    continue
                if token_sequence_at(tokens, position, needle_tokens):
                    matched.add(dish_id)
    return matched


def count_by_dish(index: Dict[str, List]) -> Dict[str, int]:
    """{dish_id: số quán}. Dùng để xếp hạng món và để ẩn món không có quán nào."""
    return {dish_id: len(restaurants) for dish_id, restaurants in index.items()}

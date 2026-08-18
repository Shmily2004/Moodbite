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
from typing import Dict, List, Sequence, Tuple

from src.domain.entities.dish import Dish
from src.domain.value_objects.text import token_sequence_at, tokenize


def build_dish_restaurant_index(
    dishes: Sequence[Dish], restaurants: Sequence
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
    """
    index: Dict[str, List] = {dish.identifier: [] for dish in dishes}
    buckets = _bucket_keywords_by_first_token(dishes)

    for restaurant in restaurants:
        matched = _matching_dish_ids(restaurant, buckets)
        for dish_id in matched:
            index[dish_id].append(restaurant)

    return index


def _bucket_keywords_by_first_token(
    dishes: Sequence[Dish],
) -> Dict[str, List[Tuple[str, List[str]]]]:
    """{từ đầu tiên: [(dish_id, các từ của từ khoá)]}. Tách từ khoá món đúng MỘT lần."""
    buckets: Dict[str, List[Tuple[str, List[str]]]] = defaultdict(list)
    for dish in dishes:
        for keyword in dish.restaurant_match_keywords:
            tokens = tokenize(keyword, min_length=1)
            if tokens:
                buckets[tokens[0]].append((dish.identifier, tokens))
    return buckets


def _matching_dish_ids(
    restaurant, buckets: Dict[str, List[Tuple[str, List[str]]]]
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
    name_tokens = tokenize(restaurant.name, min_length=1)
    category_tokens = tokenize(getattr(restaurant, "category", None), min_length=1)

    for tokens in (name_tokens, category_tokens):
        for position, token in enumerate(tokens):
            for dish_id, needle_tokens in buckets.get(token, ()):
                if dish_id in matched:
                    continue
                if token_sequence_at(tokens, position, needle_tokens):
                    matched.add(dish_id)
    return matched


def count_by_dish(index: Dict[str, List]) -> Dict[str, int]:
    """{dish_id: số quán}. Dùng để xếp hạng món và để ẩn món không có quán nào."""
    return {dish_id: len(restaurants) for dish_id, restaurants in index.items()}

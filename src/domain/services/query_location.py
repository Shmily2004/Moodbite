"""Hiểu CỤM ĐỊA ĐIỂM trong câu tìm kiếm tự do: "bún chả GẦN HỒ GƯƠM".

Thuần Python - chỉ dùng bộ tách từ chung ở `value_objects/text.py`.

BUG THẬT 2026-09-16 (gọi API thật trên 52.871 quán): "bún chả gần hồ gươm" trả top-3 là
"Ho Guom Bar", "GóC HỒ GƯƠM", "Hồ Gươm - Hồ Hoàn Kiếm" - không quán nào bán bún chả.
Nguyên nhân: "gần" nằm trong từ dừng nên bị bỏ, nhưng "hồ gươm" thì còn nguyên và được
đem đi khớp TÊN QUÁN như thể nó là món ăn. Tên quán lại là tín hiệu nặng nhất
(`WEIGHT_NAME = 1.0`), nên mọi quán có chữ "Hồ Gươm" trong tên đều nhảy lên đầu.

Hàm ở đây chỉ TÁCH câu thành hai phần: phần để khớp món/tên quán, và tên địa điểm.
Đổi địa điểm thành toạ độ là việc của tầng gọi, và CHỈ làm được khi có dữ liệu thật -
xem `build_ward_centroids`. Không có bảng toạ độ địa danh (Hồ Gươm, Lotte...) nên ta
TUYỆT ĐỐI không đoán toạ độ cho chúng.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from src.domain.value_objects.location import Location
from src.domain.value_objects.text import Token, token_sequence_at, tokenize_pairs

# Giới từ báo hiệu "phía sau là một địa điểm". Cụm dài đứng TRƯỚC để "ở gần" không bị
# hiểu thành "ở" + địa điểm "gần ...".
LOCATION_PREPOSITIONS: tuple[str, ...] = (
    "ở gần", "xung quanh", "khu vực", "gần", "quanh", "ở", "tại", "khu",
)

# Từ báo hiệu đã HẾT tên địa điểm. Cần vì cụm địa điểm có thể đứng đầu câu:
# "gần hồ gươm CÓ quán bún chả nào" - không dừng ở "có" thì cả câu thành tên địa điểm.
# So theo bản CÓ DẤU: "có" là từ nối nhưng "cổ" (phố cổ) là một phần tên địa danh.
PLACE_TERMINATORS = frozenset(
    {"có", "bán", "ăn", "uống", "nào", "không", "mà", "với", "và", "để", "thì",
     "ngon", "rẻ", "đang", "còn", "mở"}
)

# Tên địa điểm dài hơn ngưỡng này gần như chắc chắn là đã nuốt nhầm phần sau của câu.
# Tên phường dài nhất trong dữ liệu là "Văn Miếu - Quốc Tử Giám" = 5 từ.
MAX_PLACE_TOKENS = 5

# "gần ĐÂY", "gần NHÀ" = vị trí hiện tại của người dùng, không phải một địa danh.
CURRENT_LOCATION_WORDS = frozenset({"đây", "nhà", "tôi", "mình", "chỗ", "em", "bạn"})

# Tiền tố hành chính. Bỏ đi khi so tên: người dùng gõ "cầu giấy", dữ liệu ghi
# "Phường Cầu Giấy".
ADMIN_PREFIXES: tuple[str, ...] = ("thị trấn", "phường", "quận", "huyện", "xã")


@dataclass(frozen=True)
class QueryLocation:
    """Câu tìm kiếm đã tách cụm địa điểm.

    `text`  : phần còn lại để khớp món / tên quán. None = không còn gì.
    `place` : tên địa điểm người dùng nêu, giữ nguyên chữ (đã hạ chữ thường).
    `near_current_location`: người dùng nói "gần đây" - không cần đổi toạ độ.
    """

    text: Optional[str]
    place: Optional[str] = None
    near_current_location: bool = False


def split_location_phrase(
    query_text: Optional[str],
    is_known_place: Optional[Callable[[str], bool]] = None,
) -> QueryLocation:
    """Tách cụm "<giới từ> <địa điểm>" ĐẦU TIÊN khỏi câu.

    DẤU CỦA GIỚI TỪ LÀ BẰNG CHỨNG, và ở đây phải CHẶT hơn `tokens_match`:
      - Gõ CÓ DẤU ("gần", "ở", "tại") -> chắc chắn là giới từ, tách luôn.
      - Gõ KHÔNG DẤU ("gan", "o", "tai") -> MƠ HỒ: "gan" còn là lá gan ("pate gan
        ngỗng"), "tai" là tai heo. Chỉ dám tách khi phần phía sau đúng là một địa danh
        ta biết (`is_known_place`). Không biết thì để nguyên câu - nuốt mất tên món còn
        tệ hơn để sót một cụm địa điểm.
      - Có dấu nhưng KHÁC ("ổ" trong bánh mì ổ) -> không phải giới từ.
    `tokens_match` bao dung với vế không dấu vì ở đó sót một quán chỉ là thiếu; ở đây
    bao dung nghĩa là XOÁ chữ của người dùng, nên phải đòi bằng chứng.
    """
    if not query_text or not query_text.strip():
        return QueryLocation(text=None)

    tokens = tokenize_pairs(query_text, min_length=1)
    for start in range(len(tokens)):
        for preposition in _PREPOSITION_TOKENS:
            found = _match_preposition(tokens, start, preposition)
            if found is None:
                continue
            place_tokens = _take_place(tokens, start + len(preposition))
            if not place_tokens:
                continue
            place = _join(place_tokens)
            rest = tokens[:start] + tokens[start + len(preposition) + len(place_tokens):]

            if place_tokens[0][1] in CURRENT_LOCATION_WORDS:
                if found == _CONFIDENT:
                    return QueryLocation(text=_join(rest), near_current_location=True)
                continue
            if found == _AMBIGUOUS and not (is_known_place and is_known_place(place)):
                continue
            return QueryLocation(text=_join(rest), place=place)

    return QueryLocation(text=_join(tokens))


# --- Tâm phường suy từ dữ liệu -----------------------------------------------


@dataclass(frozen=True)
class WardCentroid:
    """Vị trí ƯỚC LƯỢNG của một phường/xã = trung bình toạ độ các quán ghi phường đó.

    VÌ SAO DÙNG ĐƯỢC: cột `district` có ở 100% quán (đo 2026-09-16: 125 phường/xã trên
    52.871 quán), nên đây là "bảng địa danh" suy từ dữ liệu có sẵn, không phải số bịa.
    Không phải tâm hành chính chính thức - giao diện phải nói rõ là ước lượng.
    """

    name: str
    location: Location
    restaurant_count: int


def build_ward_centroids(restaurants: Iterable) -> List[WardCentroid]:
    sums: Dict[str, List[float]] = {}
    for restaurant in restaurants:
        district = getattr(restaurant, "district", None)
        if not district:
            continue
        acc = sums.setdefault(district, [0.0, 0.0, 0.0])
        acc[0] += restaurant.location.lat
        acc[1] += restaurant.location.lng
        acc[2] += 1
    return [
        WardCentroid(
            name=name,
            location=Location(lat=lat / count, lng=lng / count),
            restaurant_count=int(count),
        )
        for name, (lat, lng, count) in sums.items()
    ]


def find_ward(place: Optional[str], wards: Sequence[WardCentroid]) -> Optional[WardCentroid]:
    """Phường có tên TRÙNG NGUYÊN VẸN với `place` (bỏ tiền tố hành chính).

    Nguyên vẹn chứ không phải chứa: "kiếm" không được khớp "Hoàn Kiếm". Dùng
    `token_sequence_at` nên vẫn theo đúng quy tắc bỏ dấu + dấu là bằng chứng.
    Nhiều phường trùng tên (hiếm) -> lấy phường nhiều quán hơn.
    """
    wanted = _strip_admin_prefix(tokenize_pairs(place, min_length=1))
    if not wanted:
        return None
    matches = [
        ward for ward in wards
        if len(core := _strip_admin_prefix(tokenize_pairs(ward.name, min_length=1)))
        == len(wanted)
        and token_sequence_at(core, 0, wanted)
    ]
    if not matches:
        return None
    return max(matches, key=lambda w: w.restaurant_count)


# --- nội bộ ---------------------------------------------------------------------

_CONFIDENT = "confident"
_AMBIGUOUS = "ambiguous"

_PREPOSITION_TOKENS: List[List[Token]] = [
    tokenize_pairs(p, min_length=1) for p in LOCATION_PREPOSITIONS
]
_ADMIN_PREFIX_TOKENS: List[List[Token]] = [
    tokenize_pairs(p, min_length=1) for p in ADMIN_PREFIXES
]


def _match_preposition(
    tokens: List[Token], start: int, preposition: List[Token]
) -> Optional[str]:
    window = tokens[start : start + len(preposition)]
    if len(window) != len(preposition):
        return None
    if any(w[0] != p[0] for w, p in zip(window, preposition)):
        return None
    if all(w[1] == p[1] for w, p in zip(window, preposition)):
        return _CONFIDENT
    # Bản bỏ dấu trùng nhưng chữ gõ vào khác: chỉ chấp nhận khi người dùng gõ HOÀN TOÀN
    # không dấu. Gõ có dấu mà khác dấu ("ổ" vs "ở") là một từ khác hẳn.
    if all(w[0] == w[1] for w in window):
        return _AMBIGUOUS
    return None


def _take_place(tokens: List[Token], start: int) -> List[Token]:
    place: List[Token] = []
    for token in tokens[start:]:
        if token[1] in PLACE_TERMINATORS or len(place) >= MAX_PLACE_TOKENS:
            break
        place.append(token)
    return place


def _strip_admin_prefix(tokens: List[Token]) -> List[Token]:
    for prefix in _ADMIN_PREFIX_TOKENS:
        if len(tokens) > len(prefix) and token_sequence_at(tokens, 0, prefix):
            return tokens[len(prefix):]
    return tokens


def _join(tokens: Sequence[Token]) -> Optional[str]:
    return " ".join(raw for _, raw in tokens) or None

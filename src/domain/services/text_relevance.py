"""So khớp câu tìm kiếm TỰ DO với nhà hàng (Lớp 2 của đề án, bản khả thi trên dữ liệu thật).

Thuần Python - không cần model embedding, không cần GPU.

VÌ SAO KHÔNG DÙNG EMBEDDING NGAY: đề án mô tả tìm kiếm ngữ nghĩa bằng vector embedding.
Nhưng dữ liệu thật chỉ có review text cho 350/4170 quán (8.4%), và tag "Bầu không khí"
gần như rỗng ("Yên tĩnh" chỉ gắn cho ĐÚNG 2 quán). Một mô hình embedding chạy trên 8% dữ
liệu sẽ không tìm được gì cho 92% còn lại - tệ hơn hẳn cách khớp từ khoá trên tên + loại
hình vốn phủ 100%.

Vì vậy dùng cách LAI, xếp theo độ tin cậy giảm dần, và LUÔN nói rõ kết quả đến từ nguồn
nào qua `match_source` để giao diện không nói dối người dùng.

Nâng cấp lên embedding thật là việc hợp lý KHI đã cào đủ review - khi đó chỉ cần thêm một
nguồn tín hiệu vào hàm `relevance()` này, không phải sửa use case.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from sys import intern
from typing import Dict, List, Optional, Tuple

from src.domain.entities.restaurant import Restaurant
from src.domain.value_objects.mood import MOOD_PROFILES
from src.domain.value_objects.text import (
    Token,
    contains_token_sequence,
    normalize,
    tokenize_pairs,
    tokens_match,
)
from src.domain.value_objects.text import tokenize as base_tokenize

# Trọng số theo ĐỘ CHÍNH XÁC của từng nguồn (không phải độ "phong phú").
#
# Tên và loại hình đứng trên review, dù review là lời người thật viết. Lý do đo được:
# review dài trung bình 106 ký tự và nhắc tới NHIỀU món cùng lúc, nên gần như câu tìm
# kiếm nào cũng khớp được vài từ. Khi để review nặng nhất, truy vấn "phở bò" trả về
# "Bánh Tráng Bé My" (review có nhắc "bò") thay vì quán tên "Phở Bò 83" - sai rõ ràng.
#
# Tên quán là tín hiệu CHẮC CHẮN nhất: quán tên "Phở Bò" thì bán phở bò.
WEIGHT_NAME = 1.0
WEIGHT_CATEGORY = 0.9
WEIGHT_ATMOSPHERE = 0.7
WEIGHT_REVIEW = 0.55

# Thưởng thêm khi khớp nguyên CỤM chứ không chỉ các từ rời rạc: "yên tĩnh" xuất hiện
# nguyên cụm đáng tin hơn nhiều so với một chỗ có "yên" và chỗ khác có "tĩnh".
PHRASE_BONUS = 0.35

# Từ dừng tiếng Việt hay gặp trong câu tìm kiếm - bỏ đi để không khớp bừa.
STOP_WORDS = {
    "quán", "chỗ", "nơi", "chỉ", "cho", "của", "và", "hay", "hoặc", "là", "có",
    "muốn", "tìm", "kiếm", "ăn", "đi", "một", "cái", "gì", "nào", "ở", "tại",
    "gần", "đây", "này", "với", "để", "được", "thì", "mà", "rất", "hơi", "khá",
    "tôi", "mình", "bạn", "em", "anh", "chị", "the", "a", "an", "to", "for",
}

# Câu tự do -> mood có sẵn trong dữ liệu. Đây là cầu nối giữa "người dùng gõ tự do"
# và 5 cột mood-score mà data_pipeline đã tính sẵn.
MOOD_KEYWORDS: Dict[str, List[str]] = {
    "sad": ["buồn", "cô đơn", "mệt", "chán", "an ủi", "ấm bụng", "comfort", "tâm trạng"],
    "happy": ["vui", "tươi", "healthy", "lành mạnh", "nhẹ", "thanh đạm", "rau", "salad",
              "tốt cho sức khoẻ", "sức khỏe"],
    "excited": ["cay", "nóng", "lẩu", "nướng", "hào hứng", "kích thích", "đậm đà", "mạnh"],
    "relaxed": ["yên tĩnh", "thư giãn", "chill", "cà phê", "cafe", "ngồi lâu", "làm việc",
                "học bài", "trò chuyện", "tâm sự", "riêng tư", "lãng mạn"],
}


_NORMALIZED_STOP_WORDS = {normalize(s) for s in STOP_WORDS}


def tokenize(text: Optional[str]) -> List[str]:
    """Tách từ và bỏ từ dừng. Dùng lại bộ tách từ chung ở value_objects/text.py."""
    return [w for w in base_tokenize(text) if w not in _NORMALIZED_STOP_WORDS]


def _tokenize_pairs(text: Optional[str]) -> List[Token]:
    """Như `tokenize` nhưng giữ cặp (bỏ dấu, giữ dấu) để so theo quy tắc dấu."""
    return [t for t in tokenize_pairs(text) if t[0] not in _NORMALIZED_STOP_WORDS]


# Số đoạn văn bản (tên / loại hình / review / không khí của quán) được nhớ sẵn bản đã tách.
# Đo 2026-10-02: mỗi lượt `/search` có câu chữ mất ~2,1 giây, ~2/3 thời gian là TÁCH TỪ LẠI
# chính những đoạn văn đó (160.876 lần `tokenize_pairs` mỗi lượt) dù dữ liệu quán không đổi
# giữa các lượt. 52.871 quán × tối đa 4 trường -> 262.144 đủ chứa hết; vượt thì LRU tự bỏ
# đoạn ít dùng nhất, không phình vô hạn.
# ĐÁNH ĐỔI ĐÃ ĐO: "phở bò" 2.070 -> 836 ms (kết quả giống hệt), đổi lại RAM tiến trình
# +62 MB (471 -> 533 MB, đã intern chuỗi; chưa intern là +88 MB). Lượt tìm ĐẦU TIÊN sau khi
# khởi động vẫn ~2 giây vì phải điền bộ nhớ đệm.
SO_DOAN_NHO_SAN = 262_144


@lru_cache(maxsize=SO_DOAN_NHO_SAN)
def _chi_muc_van_ban(text: str) -> Tuple[Tuple[Token, ...], Dict[str, Tuple[Token, ...]]]:
    """Tách từ MỘT LẦN cho mỗi đoạn văn, kèm bảng gom theo bản bỏ dấu.

    Trả tuple (bất biến) để bản nhớ đệm dùng chung không bị ai sửa nhầm. Bảng gom giúp mỗi
    từ câu hỏi chỉ phải so với đúng các từ đồng âm. ⚠️ Người gọi KHÔNG được sửa dict trả về.
    """
    # `sys.intern`: "quán", "phở", "nhà", "hàng"... lặp lại hàng chục nghìn lần giữa các
    # đoạn văn; intern để mọi bản dùng CHUNG một chuỗi trong bộ nhớ thay vì mỗi lần một bản.
    tokens = tuple((intern(p), intern(r)) for p, r in _tokenize_pairs(text))
    by_plain: Dict[str, List[Token]] = {}
    for token in tokens:
        by_plain.setdefault(token[0], []).append(token)
    return tokens, {k: tuple(v) for k, v in by_plain.items()}


@dataclass(frozen=True)
class RelevanceResult:
    score: float          # 0.0 - 1.0
    sources: List[str]    # nguồn nào đã khớp, để giải thích cho người dùng

    @property
    def matched(self) -> bool:
        return self.score > 0.0


def _overlap(query_tokens: List[Token], target: Optional[str]) -> float:
    """Mức khớp giữa từ khoá câu hỏi và một đoạn văn bản, trong khoảng [0, 1].

    So khớp theo TỪ NGUYÊN VẸN, không phải chuỗi con: nếu dùng `"bo" in text` thì "bo"
    khớp luôn cả "bột", "bò né"... khiến truy vấn "phở bò" trả về quán bánh tráng.

    Từng từ đi qua `tokens_match` (CLAUDE.md §4.5 "dấu là bằng chứng"). Bug thật trước
    2026-09-29: hàm này so tập từ ĐÃ BỎ DẤU, nên tìm "phở" ra "Nhà Hàng Phố Cổ", "Gà Phố"
    (đo: 7 kết quả trùng âm trong top-20 của 8 truy vấn, `scripts/do_trung_am_tim_kiem.py`).
    """
    if not query_tokens or not target:
        return 0.0
    target_tokens, by_plain = _chi_muc_van_ban(target)
    if not target_tokens:
        return 0.0

    hits = sum(
        1 for q in query_tokens
        if any(tokens_match(t, q) for t in by_plain.get(q[0], ()))
    )
    if not hits:
        return 0.0
    score = hits / len(query_tokens)

    # Khớp nguyên cụm 2 từ thì cộng thêm - cũng qua quy tắc dấu, để "Phố Bò" không được
    # thưởng như "Phở Bò".
    if any(
        contains_token_sequence(list(target_tokens), list(pair))
        for pair in zip(query_tokens, query_tokens[1:])
    ):
        score = min(1.0, score + PHRASE_BONUS)

    return score


def relevance(restaurant: Restaurant, query_text: Optional[str]) -> RelevanceResult:
    """Độ liên quan giữa câu tìm kiếm tự do và 1 nhà hàng.

    Không có câu tìm kiếm -> điểm 0 và không nguồn nào: tầng gọi sẽ chỉ dùng các tín hiệu
    khác (mood/ngữ cảnh/khoảng cách), chứ KHÔNG loại quán nào.
    """
    tokens = _tokenize_pairs(query_text)
    if not tokens:
        return RelevanceResult(score=0.0, sources=[])

    signals: List[tuple[float, float, str]] = [
        (_overlap(tokens, restaurant.review_text), WEIGHT_REVIEW, "review"),
        (_overlap(tokens, restaurant.atmosphere_text), WEIGHT_ATMOSPHERE, "atmosphere"),
        (_overlap(tokens, restaurant.category), WEIGHT_CATEGORY, "category"),
        (_overlap(tokens, restaurant.name), WEIGHT_NAME, "name"),
    ]

    matched = [(overlap, weight, source) for overlap, weight, source in signals if overlap > 0]
    if not matched:
        return RelevanceResult(score=0.0, sources=[])

    # Lấy tín hiệu MẠNH NHẤT làm điểm chính, các tín hiệu còn lại chỉ cộng thêm nhẹ.
    # Cộng dồn thẳng sẽ thiên vị quán có nhiều trường dữ liệu, tức là thiên vị quán từ
    # Google Maps so với quán từ OpenStreetMap - đó là thiên vị theo NGUỒN, không phải
    # theo mức độ phù hợp.
    matched.sort(key=lambda m: m[0] * m[1], reverse=True)
    best_overlap, best_weight, _ = matched[0]
    score = best_overlap * best_weight
    for overlap, weight, _ in matched[1:]:
        score += overlap * weight * 0.25

    return RelevanceResult(
        score=min(score, 1.0),
        sources=[source for _, _, source in matched],
    )


def infer_mood_weights(query_text: Optional[str]) -> Optional[Dict[str, float]]:
    """Đoán mood từ câu tự do -> trả về bộ trọng số mood-score tương ứng.

    Đây là cầu nối cho 92% quán KHÔNG có review: dù không khớp được chữ nào trong review,
    ta vẫn hiểu được "muốn ăn gì đó ấm bụng" nghĩa là ưu tiên comfort_cozy_score.

    None = câu tìm kiếm không gợi ý mood nào.
    """
    if not query_text:
        return None
    normalized = normalize(query_text)

    hits: Dict[str, int] = {}
    for mood, keywords in MOOD_KEYWORDS.items():
        count = sum(1 for kw in keywords if normalize(kw) in normalized)
        if count:
            hits[mood] = count
    if not hits:
        return None

    # Câu có thể gợi nhiều mood ("yên tĩnh mà ấm cúng") -> trộn trọng số theo số từ khớp.
    total = sum(hits.values())
    blended: Dict[str, float] = {}
    for mood, count in hits.items():
        share = count / total
        for column, weight in MOOD_PROFILES[mood].items():
            blended[column] = blended.get(column, 0.0) + weight * share
    return blended

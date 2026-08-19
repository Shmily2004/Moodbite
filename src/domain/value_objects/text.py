"""Tiện ích XỬ LÝ VĂN BẢN tiếng Việt, dùng chung cho mọi chỗ cần so khớp chữ.

Thuần Python, không phụ thuộc gì khác trong dự án - đây là tầng thấp nhất, để cả entity
(dish.py) lẫn service (text_relevance.py) đều import được mà không tạo vòng phụ thuộc.

BA QUY TẮC ĐÃ TRẢ GIÁ ĐỂ HỌC:

1. BỎ DẤU khi so khớp. Người dùng gõ "pho bo", tên quán ghi "Phở Bò" - không bỏ dấu thì
   không bao giờ khớp. Đo trên dataset: rất nhiều quán tự đặt tên không dấu ("Pho Bo",
   "O Bun Cha", "Banh mi long hoi").

2. So khớp theo TỪ NGUYÊN VẸN, không phải chuỗi con. Sau khi bỏ dấu, "ốc" thành "oc" -
   nếu dùng `"oc" in text` thì khớp luôn "Ngọc", "Học", "Cốc"... Bug này vừa có thật ở
   tìm kiếm ("bo" khớp "bột"), đừng lặp lại ở chỗ khác.

3. DẤU LÀ BẰNG CHỨNG - khi cả hai vế đều có dấu thì dấu phải TRÙNG.
   Quy tắc 1 và 2 vẫn để lọt một loại lỗi thứ ba: hai từ KHÁC HẲN nhau mà bỏ dấu xong
   thành một, và cả hai đều là TỪ NGUYÊN VẸN nên quy tắc 2 không cứu được.

       phở (món)  ·  phố (đường)  ·  phớ (tào phớ - món tráng miệng)   -> đều là "pho"
       cơm        ·  cốm                                               -> đều là "com"
       cháo       ·  chao (đậu phụ nhự)  ·  chảo                       -> đều là "chao"

   Đo trên dữ liệu thật ngày 2026-08-19: trong 1948 quán trả về cho món "Phở" có
   763 quán (39,2%) là "Tào Phớ ..." hoặc có chữ "Phố" trong tên. Chúng còn được xếp
   vào nhóm TIN CẬY CAO (khớp bằng tên quán) nên đứng trên cả quán phở thật.

   Cách sửa - xem `tokens_match`: chỉ loại khi CẢ HAI vế đều mang dấu. Một vế không dấu
   nghĩa là ta KHÔNG có bằng chứng, và phải bao dung, nếu không quy tắc 1 sẽ mất tác dụng.
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Set, Tuple

# Một "từ" sau khi tách: (bản BỎ DẤU, bản GIỮ DẤU).
#
# Vì sao đi thành cặp thay vì tính lại khi cần: bản bỏ dấu dùng để gom nhóm và so nhanh,
# bản giữ dấu dùng để phân biệt phở/phố/phớ. Chỉ mục món gọi phép so này ~780.000 lần cho
# mỗi lần dựng - tính `normalize` lại ở trong vòng lặp đó là quay về đúng bản 11 giây đã
# bỏ đi. Tách từ MỘT lần, mang theo cả hai bản.
Token = Tuple[str, str]

# `[^\W_]+`: chữ-số theo Unicode, bỏ gạch dưới. Phải giữ được chữ có dấu để dựng vế phải
# của cặp - `[a-z0-9]+` sẽ cắt vụn "phở" thành "ph".
_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)
_ASCII_RE = re.compile(r"[a-z0-9]+")


def normalize(text: Optional[str]) -> str:
    """Bỏ dấu + hạ chữ thường. 'Phở Bò' -> 'pho bo'."""
    if not text:
        return ""
    lowered = str(text).lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    # đ/Đ không tách được bằng NFD nên phải xử lý riêng.
    return stripped.replace("đ", "d")


def tokenize_pairs(text: Optional[str], min_length: int = 2) -> List[Token]:
    """Tách văn bản thành các cặp (bỏ dấu, giữ dấu).

    ĐÂY LÀ NƠI DUY NHẤT quyết định "thế nào là một từ". `tokenize` chỉ là hình chiếu của
    hàm này. Có hai cách cắt từ song song là chắc chắn có ngày chỉ mục tra nhầm ô và
    quán biến mất mà không ai biết vì sao.
    """
    pairs: List[Token] = []
    for raw in _WORD_RE.findall(str(text or "").lower()):
        # Nối lại vì một "từ" theo Unicode có thể lẫn ký tự không phải chữ Latin
        # (tên quán Nhật/Hàn). Phần không phải a-z0-9 bị bỏ đi đúng như bản cũ.
        plain = "".join(_ASCII_RE.findall(normalize(raw)))
        if len(plain) >= min_length:
            pairs.append((plain, raw))
    return pairs


def tokenize(text: Optional[str], min_length: int = 2) -> List[str]:
    """Tách thành các từ đã bỏ dấu.

    `min_length=2` (mặc định) dùng cho CÂU TÌM KIẾM của người dùng: bỏ từ 1 ký tự để
    tránh nhiễu.

    `min_length=1` BẮT BUỘC dùng khi so khớp từ khoá rule. Tiếng Việt có từ 1 ký tự mang
    nghĩa đầy đủ ("ý" = nước Ý, "gà", "mì"). Bug thật đã xảy ra: bộ lọc mặc định nuốt mất
    "ý" khiến rule "nhà hàng ý" (đồ Ý) rút gọn thành "nhà hàng" và khớp MỌI quán -> nhà
    hàng Nhật/Quảng Đông đều bị gợi ý "Mì Ý sốt bò bằm".
    """
    return [plain for plain, _ in tokenize_pairs(text, min_length)]


def tokens_match(haystack: Token, needle: Token) -> bool:
    """Hai từ có được coi là MỘT không - quy tắc 3 nằm ở đây.

    Ba trường hợp:
      - Bỏ dấu đã khác nhau            -> khác. Xong.
      - Cả hai đều CÓ DẤU              -> dấu phải trùng ("phở" != "phố").
      - Ít nhất một vế KHÔNG DẤU       -> coi là trùng.

    Vế thứ ba là phần quan trọng nhất và dễ bị "dọn dẹp" nhầm nhất: quán ghi biển
    "Tao Pho Ganh" (không dấu) thì ta KHÔNG biết họ định viết "phở" hay "phớ". Đoán bừa
    theo hướng loại bỏ sẽ đánh mất đúng nhóm quán mà quy tắc 1 sinh ra để phục vụ.
    """
    h_plain, h_raw = haystack
    n_plain, n_raw = needle
    if h_plain != n_plain:
        return False
    # `plain != raw` tức là "từ này có dấu" - so chuỗi thẳng, KHÔNG gọi lại `normalize`
    # trong vòng lặp nóng.
    if h_plain != h_raw and n_plain != n_raw:
        return h_raw == n_raw
    return True


def contains_phrase(haystack: Optional[str], needle: Optional[str]) -> bool:
    """`needle` có xuất hiện trong `haystack` dưới dạng CỤM TỪ NGUYÊN VẸN không.

    Khớp theo ranh giới từ, nên "oc" KHÔNG khớp "ngoc"; khớp theo dấu, nên "phở" KHÔNG
    khớp "Tào Phớ"; nhưng "bun cha" vẫn khớp "quan bun cha ngon".

    Giữ nguyên từ 1 ký tự ở CẢ HAI phía - xem giải thích ở `tokenize`.
    """
    return contains_phrase_tokens(tokenize_pairs(haystack, min_length=1), needle)


def contains_phrase_tokens(haystack_tokens: List[Token], needle: Optional[str]) -> bool:
    """Như `contains_phrase` nhưng nhận SẴN danh sách từ của vế trái."""
    return contains_token_sequence(
        haystack_tokens, tokenize_pairs(needle, min_length=1)
    )


def contains_token_sequence(
    haystack_tokens: List[Token], needle_tokens: List[Token]
) -> bool:
    """Lõi của phép "khớp cụm từ nguyên vẹn": cả hai vế đều đã tách từ sẵn.

    VÌ SAO CÓ BA LỚP BỌC QUANH MỘT PHÉP SO SÁNH: đối chiếu 747 món với 40.720 quán gọi
    phép này hàng triệu lần. Bản đầu tiên tách từ LẠI cả tên quán lẫn từ khoá món ở mỗi
    lần gọi và mất 11 giây. Cho phép người gọi tách sẵn từng vế đưa xuống đây thì phần
    tách từ chỉ còn chạy vài nghìn lần.

    Chỉ có DUY NHẤT hàm này định nghĩa thế nào là khớp; `contains_phrase` và
    `contains_phrase_tokens` đều gọi xuống đây. Chép logic ra thành bản thứ hai là cách
    chắc chắn để bug "oc khớp Ngọc" quay lại ở cái bản không ai nhớ để sửa.
    """
    if not haystack_tokens or not needle_tokens:
        return False

    span = len(needle_tokens)
    return any(
        token_sequence_at(haystack_tokens, i, needle_tokens)
        for i in range(len(haystack_tokens) - span + 1)
    )


def token_sequence_at(
    haystack_tokens: List[Token], start: int, needle_tokens: List[Token]
) -> bool:
    """`needle_tokens` có nằm đúng tại vị trí `start` không.

    Tách riêng để bên dựng chỉ mục (dish_matching) nhảy thẳng tới vị trí ứng viên thay vì
    quét mọi vị trí - nhưng vẫn dùng CHUNG định nghĩa khớp với mọi nơi khác.
    """
    if start + len(needle_tokens) > len(haystack_tokens):
        return False
    return all(
        tokens_match(haystack_tokens[start + offset], needle)
        for offset, needle in enumerate(needle_tokens)
    )


# Số từ tối đa của một cụm được đánh chỉ mục trong `PhraseLookup`.
# 4 là đủ cho mọi từ khoá đang dùng ("ngọt tự nhiên", "không phải đợi"); dựng thêm bậc
# nữa chỉ tốn bộ nhớ cho những cụm không ai hỏi tới.
MAX_PHRASE_TOKENS = 4


class PhraseLookup:
    """Hỏi NHIỀU LẦN "cụm từ này có trong văn bản không" trên CÙNG một văn bản.

    VÌ SAO TỒN TẠI: chấm điểm mood phải hỏi ~70 cụm từ cho mỗi quán, trên 40.720 quán.
    Gọi `contains_phrase` 2,8 triệu lần nghĩa là quét lại toàn bộ văn bản 2,8 triệu lượt -
    với những quán có review (trung bình ~1200 từ) thì mất hàng chục phút. Dựng sẵn tập
    n-gram MỘT lần cho mỗi quán thì mỗi câu hỏi chỉ còn một phép tra bảng băm.

    Tra bằng khoá ĐÃ BỎ DẤU rồi mới đối chiếu dấu trên các ứng viên, nên vẫn dùng chung
    `tokens_match` với mọi nơi khác - không đẻ ra định nghĩa "khớp" thứ hai.
    """

    __slots__ = ("_grams",)

    def __init__(self, text: Optional[str], max_tokens: int = MAX_PHRASE_TOKENS) -> None:
        pairs = tokenize_pairs(text, min_length=1)
        grams: Dict[Tuple[str, ...], Set[Tuple[Token, ...]]] = defaultdict(set)
        for size in range(1, max_tokens + 1):
            for start in range(len(pairs) - size + 1):
                window = tuple(pairs[start : start + size])
                grams[tuple(plain for plain, _ in window)].add(window)
        self._grams = grams

    def contains(self, phrase: Optional[str]) -> bool:
        needle = tuple(tokenize_pairs(phrase, min_length=1))
        if not needle:
            return False
        key = tuple(plain for plain, _ in needle)
        return any(
            all(tokens_match(found, wanted) for found, wanted in zip(candidate, needle))
            for candidate in self._grams.get(key, ())
        )

    def count_present(self, phrases: Iterable[Optional[str]]) -> int:
        """Số cụm từ KHÁC NHAU có mặt.

        Đếm cụm RIÊNG BIỆT chứ không đếm số lần xuất hiện: một review nhắc "rẻ" 20 lần
        không làm quán đó rẻ gấp 20 lần quán được nhắc 1 lần. Đếm số lần là cách cũ, và
        nó khiến quán có review (chữ nhiều) luôn thắng quán chỉ có tên - tức là chấm điểm
        theo LƯỢNG CHỮ CÀO ĐƯỢC chứ không theo tính chất của quán.
        """
        return sum(1 for phrase in phrases if self.contains(phrase))

"""TÌM MÓN từ NGUỒN THỨ BA: chính TÊN QUÁN trong dataset.

    python scripts/mine_dish_names.py                      # đào, chỉ báo cáo
    python scripts/mine_dish_names.py --min-restaurants 20 # khắt khe hơn
    python scripts/mine_dish_names.py --apply              # + thêm vào seed

VÌ SAO CẦN NGUỒN NÀY khi đã có Wikipedia + Wikidata
---------------------------------------------------
Hai nguồn kia trả lời câu "món này CÓ TỒN TẠI không". Chúng không trả lời được câu quan
trọng hơn với người dùng MoodBite: "món này CÓ AI BÁN Ở HÀ NỘI không". Bằng chứng ngay
trong danh mục hiện tại: **565/747 món (75,6%) không khớp một quán nào** — chúng đến từ
Wikipedia, đúng là món thật, nhưng ở Hà Nội thì là ngõ cụt.

Script này đi NGƯỢC LẠI: đọc tên của 43.000+ quán có thật rồi hỏi "cụm từ nào hay xuất
hiện mà danh mục chưa phủ". Món tìm được ở đây **luôn có quán bán**, vì chính tên quán
sinh ra nó. Đây cũng đúng cách phần soạn tay của `dish_seed_manual.json` ra đời hồi
2026-08-18, chỉ khác là làm bằng tay trên 4.938 quán.

Đo thử ngày 2026-08-24 trên 43.119 quán, những cụm hay gặp mà danh mục CHƯA có:
    bánh mỳ 120 · nước ép 103 · cháo lòng 87 · lẩu ếch 85 · lẩu cua 81 · lẩu bò 72

"bánh mỳ" đáng chú ý nhất: danh mục có "bánh mì" nhưng KHÔNG khớp được 120 quán viết
"mỳ", vì bỏ dấu xong "mi" vẫn khác "my". Đó là lỗ hổng không nguồn ngoài nào chỉ ra được.

NEO VÀO TỪ ĐỨNG ĐẦU — MẤU CHỐT ĐỂ KHÔNG NGẬP RÁC
------------------------------------------------
Đếm n-gram trần trên tên quán cho ra toàn tên hành chính và thương hiệu: "ha noi" 1373,
"ha dong" 316, "trung nguyen" 222, "long bien" 181. Lọc bằng danh sách chặn địa danh thì
SAI, vì "bún bò Huế" và "nem nướng Nha Trang" là tên món thật có chứa địa danh.

Cách đúng: bắt cụm phải BẮT ĐẦU bằng một TỪ CHỈ MÓN (`FOOD_HEAD_WORDS`). "bún chả" đạt,
"quán bún" không (đầu là "quán"), "ha noi" không. Quy tắc này một mình dọn sạch gần hết
rác kể trên mà không cần chặn địa danh cái nào.

KHÔNG TỰ ĐỘNG TIN — CHẠY MẶC ĐỊNH LÀ CHỈ BÁO CÁO
------------------------------------------------
Kết quả là ỨNG VIÊN, không phải sự thật. Có cụm rất hay gặp nhưng không phải món
("bia hơi Hà Nội" là thương hiệu), có cụm là món nhưng ta không muốn đưa lên trang chủ.
Phải có người đọc rồi mới `--apply`. Trường độ cay / bữa ăn / cách chế biến để TRỐNG —
không đoán, đúng CLAUDE.md mục 4b.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.domain.entities.dish import Dish, slugify_dish  # noqa: E402
from src.domain.services.dish_matching import (  # noqa: E402
    build_dish_restaurant_index,
    count_by_dish,
)
from src.domain.value_objects.text import (  # noqa: E402
    tokenize,
    tokenize_pairs,
    tokens_match,
)
from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.repositories.csv_restaurant_repository import (  # noqa: E402
    CsvRestaurantRepository,
)

# Console Windows mặc định là cp1252 và NỔ khi in chữ tiếng Việt (đã xảy ra thật ở
# `data_report.py`). Ép UTF-8 trước khi in bất cứ thứ gì.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("mine_dish_names")

SEED_PATH = ROOT / "data_pipeline" / "dish_seed_manual.json"
CATALOG_PATH = ROOT / "data_pipeline" / "data_cleaned" / "dish_catalog.json"
CANDIDATES_PATH = ROOT / "data_pipeline" / "data_cleaned" / "dish_name_candidates.json"

DISH_SOURCE = "dataset_ten_quan"

# TỪ ĐỨNG ĐẦU MỘT TÊN MÓN — VIẾT CÓ DẤU, CỐ Ý.
#
# ⚠️ BẢN ĐẦU VIẾT KHÔNG DẤU VÀ ĐÃ HỎNG (đo 2026-08-24). Neo vào bản bỏ dấu thì đúng cái
# bẫy "đụng độ sau khi bỏ dấu" mà CLAUDE.md mục 4 quy tắc 5 đã cảnh báo: lượt chạy đầu
# trả về "Phố cổ" 155 quán (vì `phố` -> `pho`, trùng `phở`), "Long Biên" 201 (`long` ->
# trùng `lòng`), "Trung Nguyên" 234 (`trung` -> trùng `trứng`), "Mỹ Đình" 75 (`mỹ` ->
# trùng `mỳ`), "Số 1" 100 (`số` -> trùng `sò`). Toàn địa danh và thương hiệu.
#
# Nay so bằng `tokens_match` của domain: hai vế cùng có dấu thì dấu phải trùng, còn vế
# nào không dấu thì vẫn bao dung (quán tự ghi biển "Pho Bo" vẫn khớp). Dùng LẠI hàm của
# domain chứ không tự viết — đây đã là bug thứ tư của dự án về so khớp tiếng Việt.
FOOD_HEAD_WORDS_ACCENTED = frozenset({
    # món nước / sợi
    "bún", "phở", "miến", "mì", "mỳ", "hủ", "bánh", "súp", "lẩu", "canh", "cháo",
    # cơm / xôi
    "cơm", "xôi",
    # thịt / hải sản chế biến
    "gà", "bò", "heo", "lợn", "vịt", "ngan", "cua", "ghẹ", "ốc", "sò", "mực",
    "tôm", "cá", "ếch", "dê", "cừu", "chim", "lươn", "trâu", "bào",
    # món cuốn / rán / nướng
    "nem", "chả", "gỏi", "chân", "thịt", "sườn", "lòng", "dừa", "trứng", "nộm",
    # đồ ngọt / tráng miệng
    "chè", "kem", "sữa", "sinh", "sương", "tào",
    # đồ uống
    "trà", "nước", "bia", "rượu", "cà",
    # món ngoại phổ biến ở Hà Nội (vốn không dấu)
    "pizza", "burger", "sushi", "sashimi", "ramen", "udon", "kimbap", "gimbap",
    "tokbokki", "topokki", "pasta", "spaghetti", "steak", "salad", "sandwich",
    "taco", "kebab", "hotdog", "waffle", "pancake", "donut", "croissant",
    "dimsum", "hotpot", "bbq", "buffet", "cafe", "coffee", "soda", "juice",
    "smoothie", "yaourt", "pudding",
})

# Cùng danh sách trên ở dạng `Token` (bỏ dấu, giữ dấu) để đem so bằng `tokens_match`.
# Gom theo bản bỏ dấu để tra một phát, không phải quét cả tập cho từng từ.
_HEAD_TOKENS: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
for _word in FOOD_HEAD_WORDS_ACCENTED:
    for _pair in tokenize_pairs(_word, 1):
        _HEAD_TOKENS[_pair[0]].append(_pair)


def is_food_head(token: Tuple[str, str]) -> bool:
    """Từ này có phải TỪ CHỈ MÓN đứng đầu tên món không (đã xét dấu)."""
    return any(tokens_match(token, head) for head in _HEAD_TOKENS.get(token[0], ()))


# `tokenize` mặc định bỏ từ 1 ký tự, nhưng tiếng Việt có từ 1 ký tự mang nghĩa đầy đủ
# ("ý" = nước Ý) - dùng 1 để không mất chúng, đúng cảnh báo ở `value_objects/text.py`.
MIN_TOKEN_LENGTH = 1

# Độ dài cụm xét tới. 2 từ là ngắn nhất còn ra nghĩa ("bún chả"); trên 4 từ thì gần như
# luôn là tên riêng của một quán cụ thể chứ không phải tên món.
NGRAM_SIZES = (2, 3, 4)

# Số quán tối thiểu để một cụm được coi là đáng xem. Đo 2026-08-24: hạ xuống dưới 15 thì
# danh sách bắt đầu ngập tên riêng của từng quán lẻ.
DEFAULT_MIN_RESTAURANTS = 15

# Cụm chỉ có ý nghĩa thương hiệu/khuyến mại chứ không phải tên món. Chặn đích danh kèm
# lý do, KHÔNG chặn theo từ - "bia hơi" là món, "bia hơi Hà Nội" là thương hiệu.
# Từ chỉ có trong TÊN QUÁN, không bao giờ nằm trong tên món. Cụm nào chứa một trong
# những từ này thì bỏ cả cụm. Rút từ lượt chạy thật 2026-08-24: "coffee and tea" (168
# quán), "coffee house" (107), "cafe and" (58) - đúng là cụm hay gặp, nhưng là cách đặt
# biển hiệu chứ không phải món ai gọi bao giờ.
NAME_ONLY_TOKENS = frozenset({
    "and", "the", "house", "shop", "store", "center", "cs", "quan", "tiem",
    "nha", "hang", "tam", "trung", "co", "so",
})

PHRASE_BLOCKLIST = {
    "bia hoi ha noi",   # thương hiệu bia, không phải tên món
    "bia hoi ha",       # cụm cắt dở của trên
    "com van phong",    # dịch vụ giao cơm, không phải món
    "com binh dan",     # hạng quán, không phải món
}


def load_covered_phrases() -> Set[str]:
    """Mọi cụm từ khoá danh mục ĐANG phủ, kèm mọi cụm con của chúng.

    Vì sao phải tính cả cụm con: nếu danh mục đã có "bún chả" thì "bún" và "chả" đứng
    riêng cũng coi như đã phủ, và ứng viên "bún chả que tre" cũng vậy - nó chỉ là một
    quán cụ thể của món đã có, thêm vào chỉ làm loãng danh mục.
    """
    phrases: Set[str] = set()
    if CATALOG_PATH.exists():
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        for dish in catalog.get("dishes", []):
            for text in list(dish.get("match_keywords") or []) + [dish.get("name")]:
                if text:
                    phrases.add(" ".join(tokenize(text, MIN_TOKEN_LENGTH)))

    covered: Set[str] = set()
    for phrase in phrases:
        parts = phrase.split()
        for size in range(1, len(parts) + 1):
            for start in range(len(parts) - size + 1):
                covered.add(" ".join(parts[start:start + size]))
    covered.discard("")
    return covered


def mine_phrases(
    titles: List[str],
) -> Tuple[Counter, Dict[str, Counter], Dict[str, Set[str]]]:
    """Đếm cụm ứng viên trên tên quán.

    Trả (số QUÁN chứa cụm, dạng viết CÓ DẤU hay gặp nhất của cụm).

    Đếm theo QUÁN chứ không theo lần xuất hiện: một tên quán lặp lại "lẩu" hai lần vẫn
    chỉ là một quán, đếm hai sẽ thổi phồng con số đem đi xếp hạng.
    """
    counts: Counter = Counter()
    surfaces: Dict[str, Counter] = defaultdict(Counter)
    # Mọi dạng viết của TỪ ĐẦU đã gặp cho từng cụm - dùng làm bằng chứng về dấu, xem
    # `co_bang_chung_dau`.
    head_forms: Dict[str, Set[str]] = defaultdict(set)

    for title in titles:
        pairs = tokenize_pairs(title, MIN_TOKEN_LENGTH)
        plains = [plain for plain, _ in pairs]
        raws = [raw for _, raw in pairs]
        trong_ten_nay: Set[str] = set()
        for size in NGRAM_SIZES:
            for start in range(len(plains) - size + 1):
                if not is_food_head(pairs[start]):
                    continue  # phải NEO vào từ chỉ món - xem giải thích ở đầu file
                if any(t in NAME_ONLY_TOKENS for t in plains[start:start + size]):
                    continue  # cách đặt biển hiệu, không phải tên món
                key = " ".join(plains[start:start + size])
                trong_ten_nay.add(key)
                surfaces[key][" ".join(raws[start:start + size])] += 1
                head_forms[key].add(raws[start])
        counts.update(trong_ten_nay)

    return counts, surfaces, head_forms


def co_bang_chung_dau(head_forms: Set[str]) -> bool:
    """Trong 53.000 tên quán, có quán nào viết TỪ ĐẦU của cụm này CÓ DẤU đúng như một từ
    chỉ món không?

    VÌ SAO CẦN TẦNG NÀY: quy tắc "dấu là bằng chứng" xét từng từ một nên buộc phải bao
    dung khi một vế không dấu - và đúng chỗ đó lọt "Trung Nguyên" (234 quán, `trung`
    không dấu nên khớp `trứng`) với "Long Biên" (201 quán, `long` khớp `lòng`).
    Ở mức CẢ TẬP DỮ LIỆU thì có thêm bằng chứng: món thật kiểu gì cũng có ít nhất một
    quán viết có dấu ("Cháo Lòng", "Trứng Vịt Lộn"), còn địa danh/thương hiệu thì KHÔNG
    BAO GIỜ xuất hiện dưới dạng từ chỉ món có dấu.

    Từ chỉ món vốn không có dấu (pizza, coffee, buffet) thì không áp được luật này - trả
    True và để người duyệt quyết.
    """
    for form in head_forms:
        pair = tokenize_pairs(form, MIN_TOKEN_LENGTH)
        if not pair:
            continue
        plain, raw = pair[0]
        if plain == raw:
            # Dạng viết này không dấu -> không nói lên điều gì. Nhưng nếu CHÍNH từ chỉ
            # món cũng không dấu (pizza) thì đây đã là bằng chứng đủ.
            if any(h_plain == h_raw for h_plain, h_raw in _HEAD_TOKENS.get(plain, ())):
                return True
            continue
        if any(raw == h_raw for _, h_raw in _HEAD_TOKENS.get(plain, ())):
            return True
    return False


def display_name(key: str, surfaces: Counter) -> str:
    """Dạng CÓ DẤU hay gặp nhất, viết hoa chữ đầu.

    Bắt buộc phải lấy lại dấu: cụm được gom theo bản BỎ DẤU nên nếu lấy thẳng khoá thì
    danh mục sẽ hiện "chao long" thay vì "Cháo lòng" - vừa xấu vừa sai chính tả.
    """
    best = surfaces.most_common(1)[0][0] if surfaces else key
    return best[:1].upper() + best[1:]


# Cụm A bị cụm dài hơn B "nuốt" khi A gần như chỉ xuất hiện với tư cách phần đầu của B.
# 0.9 = nếu >=90% số quán chứa A cũng chứa B thì A là cụm CẮT DỞ, không phải tên món.
# Ví dụ thật ở lượt chạy 2026-08-24: "nem nướng nha" 138 quán / "nem nướng nha trang" 135
# -> "nem nướng nha" là rác. Ngược lại "gà tươi" 133 / "gà tươi mạnh hoạch" 77 (58%) là
# hai món khác nhau, giữ cả hai.
ABSORB_RATIO = 0.9


def drop_truncated(counts: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
    """Bỏ những cụm chỉ là phần đầu bị cắt dở của một cụm dài hơn."""
    by_phrase = dict(counts)
    result = []
    for phrase, so_quan in counts:
        bi_nuot = False
        for other, so_quan_other in by_phrase.items():
            if other != phrase and other.startswith(phrase + " "):
                if so_quan_other >= ABSORB_RATIO * so_quan:
                    bi_nuot = True
                    break
        if not bi_nuot:
            result.append((phrase, so_quan))
    return result


APPROVED_PATH = ROOT / "data_pipeline" / "dish_approved.json"


def load_approved() -> Set[str]:
    """`dish_id` đã được người duyệt cho phép thêm vào danh mục.

    VÌ SAO CÓ CỬA KIỂM DUYỆT NÀY: cả hai nguồn tìm món đều trả về ứng viên lẫn rác, và
    rác ở đây không vô hại - đo 2026-08-24: "Coffee tea" 357 quán, "kho" 310 quán,
    "Trung Nguyên" 234 quán. Thêm thẳng thì trang chủ hiện "Coffee tea" như một món ăn.
    Xem `data_pipeline/dish_approved.json`.
    """
    if not APPROVED_PATH.exists():
        return set()
    raw = json.loads(APPROVED_PATH.read_text(encoding="utf-8"))
    return {e["dish_id"] for e in raw.get("approved", []) if e.get("dish_id")}


def filter_approved(records: List[dict], apply_all: bool) -> tuple[List[dict], int]:
    """Giữ lại món đã duyệt. Trả (danh sách giữ, số bị chặn)."""
    if apply_all:
        return records, 0
    approved = load_approved()
    giu = [r for r in records if r["dish_id"] in approved]
    return giu, len(records) - len(giu)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dao ten mon tu ten quan that")
    parser.add_argument("--min-restaurants", type=int, default=DEFAULT_MIN_RESTAURANTS,
                        help=f"So quan toi thieu (mac dinh {DEFAULT_MIN_RESTAURANTS})")
    parser.add_argument("--top", type=int, default=200,
                        help="So ung vien dem di do lai bang bo khop that")
    parser.add_argument("--apply", action="store_true",
                        help="Them mon DA DUOC DUYET vao dish_seed_manual.json")
    parser.add_argument("--apply-all", action="store_true",
                        help="Bo qua cua kiem duyet - KHONG khuyen khich, se them ca rac")
    args = parser.parse_args()

    settings = Settings.from_env()
    repo = CsvRestaurantRepository(settings.restaurants_csv)
    if not repo.is_ready:
        logger.error("Chua co dataset quan: %s", repo.load_error)
        logger.error("Chay truoc: python -m data_pipeline.feature_engineering")
        return 1
    restaurants = repo.list_all()
    logger.info("Doc %d quan tu %s", len(restaurants), settings.restaurants_csv)

    # Entity dùng `name`, không phải `title` (cột CSV mới là `title`).
    titles = [r.name for r in restaurants if getattr(r, "name", None)]
    counts, surfaces, head_forms = mine_phrases(titles)
    logger.info("Cum ung vien neo vao tu chi mon: %d", len(counts))

    covered = load_covered_phrases()
    logger.info("Cum danh muc dang phu (ke ca cum con): %d", len(covered))

    fresh = [
        (key, so_quan) for key, so_quan in counts.most_common()
        if key not in covered
        and key not in PHRASE_BLOCKLIST
        and so_quan >= args.min_restaurants
        and co_bang_chung_dau(head_forms[key])
    ]
    logger.info("Cum MOI dat nguong >=%d quan: %d", args.min_restaurants, len(fresh))
    truoc = len(fresh)
    fresh = drop_truncated(fresh)
    logger.info("Bo %d cum CAT DO (phan dau cua cum dai hon)", truoc - len(fresh))
    if not fresh:
        logger.info("Khong co ung vien nao - danh muc da phu het cum hay gap.")
        return 0

    # ĐO LẠI bằng CHÍNH bộ khớp mà lúc chạy thật sẽ dùng. Đếm n-gram ở trên nhanh nhưng
    # bỏ qua quy tắc "dấu là bằng chứng" (phở/phố/phớ), nên con số đem đi quyết định
    # phải là con số của `dish_matching`, không phải con số đếm thô.
    shortlist = fresh[: args.top]
    probes = []
    for key, _ in shortlist:
        name = display_name(key, surfaces[key])
        probes.append(Dish(name=name, dish_id=slugify_dish(name), match_keywords=[name]))
    logger.info("Do lai %d ung vien bang bo khop that (mat vai phut)...", len(probes))
    measured = count_by_dish(build_dish_restaurant_index(probes, restaurants))

    records = []
    for (key, tho), probe in zip(shortlist, probes):
        records.append({
            "dish_id": probe.dish_id,
            "name": probe.name,
            "match_keywords": [probe.name],
            "restaurant_count": measured.get(probe.dish_id, 0),
            "restaurant_count_ngram": tho,
            "source": DISH_SOURCE,
            "source_url": None,
        })
    records = [r for r in records if r["restaurant_count"] >= args.min_restaurants]
    records.sort(key=lambda r: -r["restaurant_count"])

    logger.info("")
    logger.info("=" * 68)
    logger.info("UNG VIEN MON DAO TU TEN QUAN (%d cum)", len(records))
    logger.info("=" * 68)
    for record in records[:40]:
        logger.info("  %5d quan  %-32s (dem tho %d)",
                    record["restaurant_count"], record["name"],
                    record["restaurant_count_ngram"])

    CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATES_PATH.write_text(json.dumps({
        "_readme": (
            "SINH TU DONG boi scripts/mine_dish_names.py tu TEN QUAN that. Day la UNG "
            "VIEN chua duoc nguoi doc duyet - khong dung truc tiep. Cot "
            "'restaurant_count' do bang bo khop that (dish_matching), cot "
            "'restaurant_count_ngram' la dem tho n-gram, hai so lech nhau la binh thuong."
        ),
        "min_restaurants": args.min_restaurants,
        "candidates": records,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("")
    logger.info("Da ghi ung vien: %s", CANDIDATES_PATH)

    if not (args.apply or args.apply_all):
        logger.info("Doc lai file tren roi chay --apply de them vao seed.")
        return 0

    records, bi_chan = filter_approved(records, args.apply_all)
    logger.info("Qua cua kiem duyet: %d mon (chan %d chua duyet)", len(records), bi_chan)

    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    da_co = {d.get("dish_id") for d in raw.get("dishes", [])}
    them = 0
    for record in records:
        if record["dish_id"] in da_co:
            continue
        raw["dishes"].append({
            "dish_id": record["dish_id"],
            "name": record["name"],
            "match_keywords": record["match_keywords"],
            # Độ cay / bữa ăn / cách chế biến để TRỐNG. Tên quán không nói gì về mấy thứ
            # đó, đoán bừa là bịa dữ liệu.
            "source": DISH_SOURCE,
            "source_url": None,
        })
        da_co.add(record["dish_id"])
        them += 1
    SEED_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Da them %d mon vao %s", them, SEED_PATH.name)
    logger.info("Chay tiep: python scripts/build_dish_catalog.py --enrich")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

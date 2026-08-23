"""Dựng DANH MỤC MÓN ĂN (`dish_catalog.json`) từ ba nguồn, rồi ĐO xem mỗi món có bao
nhiêu quán thật bán nó.

    python scripts/build_dish_catalog.py                  # dựng, không gọi mạng
    python scripts/build_dish_catalog.py --enrich         # + tra Wikipedia/Wikidata
    python scripts/build_dish_catalog.py --report-only    # chỉ đo, không ghi file

Chạy được trên PowerShell 5.1 y như trên bash - đó là lý do mọi thứ nằm trong script
Python thay vì một chuỗi lệnh shell (CLAUDE.md mục 1).

BA NGUỒN, theo thứ tự ưu tiên giảm dần:

  1. `dish_knowledge_base.json`  - 38 rule sẵn có. Đã gắn với quán thật, đang chạy tốt.
  2. `dish_seed_manual.json`     - món soạn tay, lấy từ việc KHAI THÁC TÊN QUÁN thật.
  3. Wikipedia tiếng Việt        - giới thiệu ngắn + đường dẫn ảnh (tuỳ chọn `--enrich`).

VÌ SAO PHẢI ĐO SỐ QUÁN: người dùng chọn món trước rồi mới tìm quán. Món không khớp quán
nào là NGÕ CỤT - bấm vào rồi nhận danh sách rỗng. Script này in ra đúng danh sách món
đang bị ngõ cụt để còn sửa từ khoá, thay vì để người dùng phát hiện hộ.

KHÔNG BỊA DỮ LIỆU: món tra không ra giới thiệu thì để `description` bằng None và
`has_description` bằng false. Giao diện nói "chưa có dữ liệu" chứ không để khoảng trắng.

ẢNH: chỉ lưu ĐƯỜNG DẪN, không tải file về - máy chủ dự án là laptop cá nhân.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.domain.entities.dish import (  # noqa: E402
    CONFIDENCE_SPECIFIC,
    DISH_SOURCE_MANUAL,
    DISH_SOURCE_SEED,
    DISH_SOURCE_WIKIPEDIA,
    Dish,
    slugify_dish,
)
from src.domain.services.dish_matching import (  # noqa: E402
    build_dish_restaurant_index,
    count_by_dish,
)
from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.repositories.csv_restaurant_repository import (  # noqa: E402
    CsvRestaurantRepository,
)
from src.infrastructure.repositories.json_dish_knowledge_repository import (  # noqa: E402
    JsonDishKnowledgeRepository,
)
from src.infrastructure.repositories.json_restaurant_details_repository import (  # noqa: E402


    JsonRestaurantDetailsRepository,
)

# Console Windows mặc định là cp1252 và sẽ NỔ khi in chữ tiếng Việt — script
# đang chạy dở bị dừng giữa chừng. Lỗi này đã xảy ra thật với
# "additionalInfo/Bầu không khí" trong `data_report.py`.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("build_dish_catalog")

MANUAL_SEED_PATH = ROOT / "data_pipeline" / "dish_seed_manual.json"
OUTPUT_PATH = ROOT / "data_pipeline" / "data_cleaned" / "dish_catalog.json"


def load_from_knowledge_base(path: Path) -> List[Dish]:
    """Rule -> Dish. Từ khoá khớp quán lấy TỪ CHÍNH RULE (`match_category`).

    Đây là điểm mấu chốt khiến chiều "món -> quán" khớp y hệt chiều "quán -> món" đang
    chạy: hai chiều dùng CHUNG một bộ từ khoá, nên không thể lệch nhau.
    """
    repo = JsonDishKnowledgeRepository(path)
    if not repo.is_ready:
        raise SystemExit(f"Không đọc được knowledge base: {repo.load_error}")

    dishes: List[Dish] = []
    for rule in repo.list_rules():
        for dish in rule.dishes:
            dishes.append(
                Dish(
                    name=dish.name,
                    dish_id=slugify_dish(dish.name),
                    cuisine=dish.cuisine,
                    spice_level=dish.spice_level,
                    temperature=dish.temperature,
                    portion_size=dish.portion_size,
                    mood_keywords=list(dish.mood_keywords),
                    match_keywords=_keywords_for(rule, dish),
                    source=DISH_SOURCE_SEED,
                    data_confidence=rule.confidence,
                )
            )
    return dishes


def _keywords_for(rule, dish) -> List[str]:
    """Từ khoá tìm quán cho một món sinh ra từ rule.

    RULE CỤ THỂ ("bún chả", "phở") -> dùng từ khoá của rule: nó bắt được quán
    "Bún Chả Hương Liên" mà tên món "Nem rán" thì không bắt được.

    RULE CHUNG ("nhà hàng", "cà phê") -> dùng TÊN MÓN, tuyệt đối không dùng từ khoá rule.
    Bug đã đo được khi làm ngược lại: rule `nha_hang_generic` khớp "nhà hàng" và có 3 món
    (Phở, Cơm, Bún chả), nên cả ba món đều nhận đúng 2744 quán - tức là gần như MỌI nhà
    hàng trong dataset đều bị coi là bán phở. Chiều "quán -> món" chấp nhận được chuyện đó
    (đoán đại một món cho quán chưa rõ loại hình), nhưng chiều "món -> quán" thì nó biến
    trang chi tiết món Phở thành danh sách 2744 quán phần lớn không bán phở.
    """
    if rule.confidence == CONFIDENCE_SPECIFIC:
        return list(rule.match_category)
    return [dish.name]


def load_manual_seed(path: Path) -> List[Dish]:
    if not path.exists():
        logger.warning("Không có %s - bỏ qua nguồn soạn tay.", path.name)
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    dishes: List[Dish] = []
    for entry in raw.get("dishes", []):
        name = entry.get("name")
        if not name:
            continue
        dishes.append(
            Dish(
                name=name,
                dish_id=entry.get("dish_id") or slugify_dish(name),
                cuisine=entry.get("cuisine"),
                spice_level=entry.get("spice_level"),
                temperature=entry.get("temperature"),
                cooking_method=entry.get("cooking_method"),
                meal_times=list(entry.get("meal_times", [])),
                portion_size=entry.get("portion_size"),
                mood_keywords=list(entry.get("mood_keywords", [])),
                description=entry.get("description"),
                # ĐỌC CẢ `image_url` TỪ SEED.
                # Bản cũ chỉ đọc `description` mà bỏ qua `image_url`, nên ảnh chỉ tồn tại
                # khi chạy kèm `--enrich` (có gọi mạng). Hệ quả: dựng lại danh mục lúc
                # không có mạng làm ảnh tụt từ 87,1% xuống 0% mà không có gì báo -
                # pipeline không tự dựng lại nổi kết quả của chính nó. Seed đang giữ sẵn
                # 607 đường dẫn ảnh, chỉ là chưa ai đọc lên.
                image_url=entry.get("image_url"),
                match_keywords=list(entry.get("match_keywords", [])),
                source=entry.get("source", DISH_SOURCE_MANUAL),
                source_url=entry.get("source_url"),
                last_updated=entry.get("last_updated"),
                data_confidence="manual",
            )
        )
    return dishes


def load_skip_wikipedia_ids(path: Path) -> set[str]:
    """Món KHÔNG được để Wikipedia ghi đè giới thiệu.

    Lý do có cờ này: bài Wikipedia trùng tên nhiều khi nói về NGUYÊN LIỆU hoặc CON VẬT
    chứ không phải MÓN ĂN. Đã kiểm bằng tay: bài "Ốc" nói về lớp Chân bụng và minh hoạ
    bằng ảnh con ốc sên - đưa lên trang món "Ốc luộc" thì vừa sai vừa mất ngon.
    """
    if not path.exists():
        return set()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        entry["dish_id"]
        for entry in raw.get("dishes", [])
        if entry.get("skip_wikipedia") and entry.get("dish_id")
    }


def merge(seed: List[Dish], manual: List[Dish]) -> List[Dish]:
    """Gộp theo `dish_id`. MÓN SOẠN TAY THẮNG.

    Vì sao soạn tay thắng: nó có giới thiệu, cách chế biến và bữa ăn - những thứ rule cũ
    hoàn toàn không có. Để rule cũ ghi đè lên thì công soạn tay thành vô ích.
    Từ khoá khớp quán thì GỘP CẢ HAI để không mất quán nào.
    """
    by_id: Dict[str, Dish] = {d.identifier: d for d in seed}

    for dish in manual:
        existing = by_id.get(dish.identifier)
        if existing is None:
            by_id[dish.identifier] = dish
            continue

        merged_keywords = list(
            dict.fromkeys(dish.restaurant_match_keywords + existing.restaurant_match_keywords)
        )
        by_id[dish.identifier] = Dish(
            name=dish.name,
            dish_id=dish.identifier,
            cuisine=dish.cuisine or existing.cuisine,
            spice_level=dish.spice_level if dish.spice_level is not None else existing.spice_level,
            temperature=dish.temperature or existing.temperature,
            cooking_method=dish.cooking_method,
            meal_times=list(dish.meal_times),
            portion_size=dish.portion_size or existing.portion_size,
            mood_keywords=list(dish.mood_keywords or existing.mood_keywords),
            description=dish.description,
            match_keywords=merged_keywords,
            source=dish.source,
            data_confidence=dish.data_confidence,
        )
    return list(by_id.values())


def count_restaurants(dishes: List[Dish], restaurants) -> Dict[str, int]:
    """Đếm số quán khớp từng món.

    Dùng THẲNG `build_dish_restaurant_index` - chính hàm mà lúc chạy thật sẽ dùng - thay vì
    viết lại phép so khớp ở đây. Viết lại nghĩa là có hai bản, và đến một ngày nào đó số đo
    trong báo cáo sẽ không còn khớp với thứ người dùng nhìn thấy.

    Bản đầu tiên của hàm này lặp `for quán: for món:` và mất 11 giây với 79 món. Với danh
    mục đã mở rộng (hàng trăm món) thì cách đó là hàng phút - đó là lý do phải dùng chỉ mục.
    """
    started = time.time()
    index = build_dish_restaurant_index(dishes, restaurants)
    counts = count_by_dish(index)
    logger.info("Do xong trong %.1fs", time.time() - started)
    return counts


def enrich(dishes: List[Dish], skip_ids: set[str]) -> tuple[List[Dish], int]:
    """Tra Wikipedia lấy GIỚI THIỆU NGẮN + ẢNH. Trả (danh sách mới, số món được bổ sung).

    CHỈ ĐIỀN VÀO CHỖ TRỐNG: món đã có giới thiệu soạn tay thì giữ nguyên. Bản soạn tay
    bám sát MÓN ĂN hơn, còn Wikipedia lắm khi nói về nguyên liệu.

    `skip_ids`: món mà bài Wikipedia cùng tên nói về NGUYÊN LIỆU hoặc CON VẬT chứ không
    phải món ăn. Kiểm bằng tay: bài "Ốc" nói về lớp Chân bụng (con ốc) và kèm ảnh con ốc
    sên - đưa lên trang món "Ốc luộc" thì vừa sai vừa mất ngon. Với các món này chỉ dùng
    bản soạn tay, KHÔNG để Wikipedia ghi đè.
    """
    from data_pipeline.sources.wikipedia_dish import WikipediaDishSource

    source = WikipediaDishSource()
    available, reason = source.is_available()
    if not available:
        # Không có mạng KHÔNG được làm hỏng cả lượt dựng danh mục.
        logger.warning("Bo qua buoc lam giau: %s", reason)
        return dishes, 0

    # Chỉ tra món còn THIẾU - món đã đủ thì không tốn thêm lần gọi mạng nào.
    need = [
        d for d in dishes
        if d.identifier not in skip_ids and (not d.has_description or not d.image_url)
    ]
    logger.info("Tra Wikipedia cho %d mon...", len(need))
    fetched = source.fetch_many([d.name for d in need])

    enriched_count = 0
    result: List[Dish] = []
    for dish in dishes:
        data = fetched.get(dish.name)
        if data is None or data.is_empty:
            result.append(dish)
            continue

        description = dish.description or data.description
        if not dish.has_description and data.description:
            enriched_count += 1

        result.append(
            Dish(
                name=dish.name,
                dish_id=dish.identifier,
                cuisine=dish.cuisine,
                spice_level=dish.spice_level,
                temperature=dish.temperature,
                cooking_method=dish.cooking_method,
                meal_times=list(dish.meal_times),
                portion_size=dish.portion_size,
                mood_keywords=list(dish.mood_keywords),
                description=description,
                # Ảnh: chỉ giữ ĐƯỜNG DẪN, không tải file về. Xem `sources/wikipedia_dish.py`.
                image_url=dish.image_url or data.image_url,
                match_keywords=list(dish.restaurant_match_keywords),
                # Ghi đúng nguồn của phần VỪA điền thêm. Món tự soạn mà ghi là lấy từ
                # Wikipedia là nói dối về xuất xứ dữ liệu.
                source=(
                    dish.source
                    if dish.has_description
                    else (DISH_SOURCE_WIKIPEDIA if data.description else dish.source)
                ),
                source_url=data.source_url or dish.source_url,
                last_updated=data.last_updated,
                data_confidence=dish.data_confidence,
            )
        )
    return result, enriched_count


def to_record(dish: Dish, restaurant_count: int) -> dict:
    return {
        "dish_id": dish.identifier,
        "name": dish.name,
        "cuisine": dish.cuisine,
        "spice_level": dish.spice_level,
        "temperature": dish.temperature,
        "cooking_method": dish.cooking_method,
        "meal_times": list(dish.meal_times),
        "portion_size": dish.portion_size,
        "mood_keywords": list(dish.mood_keywords),
        "description": dish.description,
        "image_url": dish.image_url,
        "match_keywords": list(dish.restaurant_match_keywords),
        # ĐO ĐƯỢC, không phải ước lượng. 0 nghĩa là thật sự không quán nào khớp.
        "restaurant_count": restaurant_count,
        "source": dish.source,
        "source_url": dish.source_url,
        "last_updated": dish.last_updated,
        "data_confidence": dish.data_confidence,
        # TẮT món KHÔNG QUÁN NÀO BÁN. Chủ dự án chốt 2026-08-19: "đừng cố tình kiếm
        # những món rất khó kiếm quán hoặc thậm chí không có quán bán".
        #
        # Đo được: 565/747 món không có quán nào, và CẢ 565 đều đến từ đợt quét tự động
        # thể loại Wikipedia (`discover_dishes.py`) - toàn món quốc tế như 'Nduja,
        # Acarajé, Aligot mà Hà Nội không ai bán. Món Việt chỉ có đúng 1 món không tìm
        # được quán (Khoai deo Quảng Bình - đặc sản vùng khác, đúng là Hà Nội không có).
        #
        # TẮT chứ KHÔNG XOÁ, và tính LẠI mỗi lần dựng: mai có quán mở bán Aligot thì lần
        # dựng sau món đó tự bật lại. Xoá hẳn thì phải nhớ mà thêm vào bằng tay.
        "is_active": restaurant_count > 0,
    }


def report(dishes: List[Dish], counts: Dict[str, int]) -> None:
    total = len(dishes)
    with_restaurants = sum(1 for d in dishes if counts.get(d.identifier, 0) > 0)
    with_description = sum(1 for d in dishes if d.has_description)
    with_image = sum(1 for d in dishes if d.image_url)
    dead_ends = sorted(
        (d for d in dishes if counts.get(d.identifier, 0) == 0), key=lambda d: d.name
    )

    logger.info("")
    logger.info("=" * 68)
    logger.info("DANH MỤC MÓN ĂN")
    logger.info("=" * 68)
    logger.info("Tổng số món            : %d", total)
    logger.info(
        "Có quán bán (>0 quán)  : %d (%.1f%%)",
        with_restaurants, 100 * with_restaurants / total if total else 0,
    )
    logger.info(
        "Co gioi thieu ngan     : %d (%.1f%%)",
        with_description, 100 * with_description / total if total else 0,
    )
    logger.info(
        "Co anh (chi luu URL)   : %d (%.1f%%)",
        with_image, 100 * with_image / total if total else 0,
    )
    logger.info("")
    logger.info("--- 15 món nhiều quán nhất ---")
    for dish in sorted(dishes, key=lambda d: -counts.get(d.identifier, 0))[:15]:
        logger.info("  %5d quán  %s", counts.get(dish.identifier, 0), dish.name)

    if dead_ends:
        logger.info("")
        logger.info(
            "--- %d MÓN KHÔNG KHỚP QUÁN NÀO (bị ẩn khỏi trang chủ) ---", len(dead_ends)
        )
        logger.info("  Sửa `match_keywords` trong dish_seed_manual.json nếu là từ khoá sai.")
        for dish in dead_ends[:20]:
            logger.info("  - %s  (từ khoá: %s)", dish.name, dish.restaurant_match_keywords)
        if len(dead_ends) > 20:
            logger.info("  ... và %d món nữa", len(dead_ends) - 20)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dựng danh mục món ăn cho MoodBite")
    parser.add_argument("--enrich", action="store_true",
                        help="Tra Wikipedia bo sung gioi thieu ngan + duong dan anh")
    parser.add_argument("--report-only", action="store_true",
                        help="Chỉ in báo cáo, KHÔNG ghi đè dish_catalog.json")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    settings = Settings.from_env()

    logger.info("Nguồn 1: %s", settings.dish_knowledge_json.name)
    seed = load_from_knowledge_base(settings.dish_knowledge_json)
    logger.info("  -> %d món từ rule", len(seed))

    logger.info("Nguồn 2: %s", MANUAL_SEED_PATH.name)
    manual = load_manual_seed(MANUAL_SEED_PATH)
    logger.info("  -> %d món soạn tay", len(manual))
    skip_ids = load_skip_wikipedia_ids(MANUAL_SEED_PATH)

    dishes = merge(seed, manual)
    logger.info("Gộp lại: %d món duy nhất", len(dishes))

    enriched_count = 0
    if args.enrich:
        dishes, enriched_count = enrich(dishes, skip_ids)
        logger.info("  -> bo sung gioi thieu cho %d mon", enriched_count)

    # Ghép review vào giống hệt lúc chạy thật (`dependencies.py`), nếu không số đo ở đây
    # sẽ thấp hơn thực tế: chỉ mục lúc chạy có dò cả nội dung review.
    details = JsonRestaurantDetailsRepository(settings.restaurant_details_json)
    review_texts = details.review_texts() if details.is_ready else {}
    repo = CsvRestaurantRepository(settings.restaurants_csv, review_texts=review_texts)
    if not repo.is_ready:
        raise SystemExit(
            f"Chưa có dataset quán: {repo.load_error}\n"
            "Chạy: python -m data_pipeline.merge_and_prepare_raw"
        )
    restaurants = repo.list_all()
    logger.info("Đo trên %d quán thật...", len(restaurants))
    counts = count_restaurants(dishes, restaurants)

    report(dishes, counts)

    if args.report_only:
        logger.info("")
        logger.info("--report-only: KHÔNG ghi file.")
        return 0

    payload = {
        "_readme": (
            "SINH TỰ ĐỘNG bởi scripts/build_dish_catalog.py - đừng sửa tay file này. "
            "Sửa dish_seed_manual.json hoặc dish_knowledge_base.json rồi chạy lại script."
        ),
        "generated_from": [
            str(settings.dish_knowledge_json.name),
            MANUAL_SEED_PATH.name,
        ] + (["wikipedia_vi"] if args.enrich else []),
        "dish_count": len(dishes),
        "dishes": [
            to_record(d, counts.get(d.identifier, 0))
            for d in sorted(dishes, key=lambda d: -counts.get(d.identifier, 0))
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("")
    logger.info("Đã ghi %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

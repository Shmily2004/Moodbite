"""TÌM MÓN MỚI từ Wikipedia rồi ĐO xem món nào thật sự có quán bán ở Việt Nam.

    python scripts/discover_dishes.py                      # tìm, chỉ báo cáo
    python scripts/discover_dishes.py --apply              # + thêm món CÓ QUÁN vào seed
    python scripts/discover_dishes.py --min-restaurants 3  # khắt khe hơn

VÌ SAO CẦN SCRIPT NÀY
---------------------
Danh mục món hiện dựng từ 38 rule cũ + phần soạn tay. Muốn "càng nhiều món càng tốt" thì
phải có nguồn sinh món tự động. Wikipedia tiếng Việt có sẵn hàng trăm bài món ăn, miễn phí
và hợp pháp (CC BY-SA), lại kèm luôn ảnh và đoạn giới thiệu.

BA BỘ LỌC, VÌ CATEGORY WIKIPEDIA RẤT BẨN
----------------------------------------
Đo thật ngày 2026-08-18: "Thể loại:Ẩm thực Việt Nam" + 27 thể loại con cho ra 506 trang,
nhưng lẫn đủ thứ không phải món: "Ẩm thực Việt Nam" (bài tổng quan), "Lễ hội Văn hóa Ẩm
thực Thế giới 2010", "Ăn độn", "Đầu bếp Việt Nam". Nên phải lọc:

  1. NGÀNH TÊN (ns=0): bỏ "Bản mẫu:", "Thể loại:"...
  2. LÀ MÓN ĂN THẬT: dựa vào `description` ngắn của REST summary ("món ăn Việt Nam",
     "món tráng miệng"...). Đây là trường do người biên tập đặt, sạch hơn đoán từ thân bài.
  3. CÓ QUÁN BÁN: đối chiếu tên món với TÊN QUÁN trong dataset thật. Món không khớp quán
     nào là NGÕ CỤT với người dùng - vẫn ghi ra file ứng viên để xem, nhưng KHÔNG tự thêm.

Bộ lọc 3 là quan trọng nhất. Thêm 300 món Nhật Bản mà Hà Nội không có quán nào bán thì chỉ
làm loãng trang chủ chứ không giúp được ai.

KHÔNG BỊA DỮ LIỆU: món thêm vào đều ghi `source=wikipedia_vi` kèm `source_url`. Không tự
đoán độ cay, cách chế biến hay bữa ăn - các trường đó để trống cho người soạn điền sau,
và bộ lọc sẽ cho điểm trung tính (chưa biết KHÁC biết là không phải).

DUNG LƯỢNG: chỉ lưu ĐƯỜNG DẪN ảnh, không tải ảnh về. Xem `sources/wikipedia_dish.py`.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data_pipeline.sources.wikipedia_dish import (  # noqa: E402
    USER_AGENT,
    WikipediaDishSource,
)
from src.domain.entities.dish import Dish, slugify_dish  # noqa: E402
from src.domain.services.dish_matching import (  # noqa: E402
    build_dish_restaurant_index,
    count_by_dish,
)
from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.repositories.csv_restaurant_repository import (  # noqa: E402


    CsvRestaurantRepository,
)

# Console Windows mặc định là cp1252 và sẽ NỔ khi in chữ tiếng Việt — script
# đang chạy dở bị dừng giữa chừng. Lỗi này đã xảy ra thật với
# "additionalInfo/Bầu không khí" trong `data_report.py`.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("discover_dishes")

WIKIPEDIA_API = "https://vi.wikipedia.org/w/api.php"
SEED_PATH = ROOT / "data_pipeline" / "dish_seed_manual.json"
CANDIDATES_PATH = ROOT / "data_pipeline" / "data_cleaned" / "dish_candidates.json"

# Thể loại gốc. Mỗi thể loại được duyệt thêm MỘT cấp con (đủ để bắt "Bánh Việt Nam",
# "Bún", "Chè"... mà không lạc sang "Đầu bếp Việt Nam").
ROOT_CATEGORIES = [
    # --- Việt Nam (nguồn chính) ---
    "Thể loại:Ẩm thực Việt Nam",
    "Thể loại:Món ăn Việt Nam",
    "Thể loại:Đặc sản Việt Nam",
    # --- Châu Á ---
    "Thể loại:Ẩm thực Nhật Bản",
    "Thể loại:Ẩm thực Hàn Quốc",
    "Thể loại:Ẩm thực Trung Quốc",
    "Thể loại:Ẩm thực Thái Lan",
    "Thể loại:Ẩm thực Ấn Độ",
    "Thể loại:Ẩm thực Indonesia",
    "Thể loại:Ẩm thực Malaysia",
    "Thể loại:Ẩm thực Philippines",
    "Thể loại:Ẩm thực Đài Loan",
    "Thể loại:Ẩm thực Hồng Kông",
    "Thể loại:Ẩm thực Singapore",
    "Thể loại:Ẩm thực Thổ Nhĩ Kỳ",
    # --- Âu Mỹ ---
    "Thể loại:Ẩm thực Ý",
    "Thể loại:Ẩm thực Pháp",
    "Thể loại:Ẩm thực Mỹ",
    "Thể loại:Ẩm thực Mexico",
    "Thể loại:Ẩm thực Tây Ban Nha",
    "Thể loại:Ẩm thực Đức",
    "Thể loại:Ẩm thực Nga",
    # --- Theo LOẠI món, không theo nước ---
    "Thể loại:Món ăn",
    "Thể loại:Món tráng miệng",
    "Thể loại:Món khai vị",
    "Thể loại:Súp",
    "Thể loại:Món mì",
    "Thể loại:Món cơm",
    "Thể loại:Món hải sản",
    "Thể loại:Món thịt",
    "Thể loại:Món rau",
    "Thể loại:Bánh",
    "Thể loại:Bánh ngọt",
    "Thể loại:Đồ uống",
    "Thể loại:Món chay",
    "Thể loại:Đồ ăn nhanh",
    "Thể loại:Thức ăn đường phố",
]

# Thể loại con CHẮC CHẮN không chứa món ăn - bỏ sớm để khỏi tốn lần gọi mạng nào.
SKIP_SUBCATEGORY_HINTS = (
    "đầu bếp", "chuyên gia", "nhà hàng", "công ty", "thương hiệu",
    "nhân vật", "sách", "phim", "chương trình",
)

# Từ khoá trong `description` ngắn của Wikipedia cho biết đây LÀ MÓN ĂN/ĐỒ UỐNG.
DISH_DESCRIPTION_HINTS = (
    "món", "bánh", "đồ uống", "thức uống", "ẩm thực", "dish", "food",
    "soup", "noodle", "beverage", "dessert", "canh", "chè", "cháo",
)

# Trang tổng quan/khái niệm, KHÔNG phải một món cụ thể.
TITLE_BLOCKLIST_HINTS = (
    "ẩm thực", "văn hóa", "lễ hội", "danh sách", "lịch sử", "công nghiệp",
    # Nhóm/khái niệm chứ không phải một món cụ thể. Lọt vào từ các thể loại theo LOẠI món.
    "món chính", "món khai vị", "món tráng miệng", "món ăn nhanh", "món hầm",
    "món nướng", "món xào", "món chay", "đồ uống", "thức ăn", "thực phẩm",
    "nhà hàng", "quán ăn", "đầu bếp",
)

# Dấu hiệu trong `description` cho biết đây là NGUYÊN LIỆU / LOÀI SINH VẬT / THƯƠNG HIỆU
# chứ không phải MÓN ĂN. Rút ra từ lượt chạy thật 2026-08-19, khi bộ lọc cũ cho đậu:
#   "Trà" (181 quán), "Chanh" (39), "Mẻ" (11), "Tương" (8)  -> nguyên liệu/gia vị
#   "KFC" (27)                                              -> thương hiệu
#   "Đuông" (43)                                            -> loài côn trùng
# Mấy thứ này lọt được vì description của chúng vẫn chứa chữ "món"/"ẩm thực".
NOT_A_DISH_HINTS = (
    "nguyên liệu", "gia vị", "thực vật", "động vật", "loài", "chi ", "họ ",
    "công ty", "chuỗi", "thương hiệu", "nhãn hiệu", "tập đoàn", "cửa hàng",
    "ấu trùng", "côn trùng", "cây ", "quả ", "hạt ", "lá ", "gạo", "bột mì",
    "đồ uống có cồn", "rượu", "trà xanh", "cà phê là",
)

# ĐỤNG ĐỘ BỎ DẤU: bài Wikipedia có thật, là món ăn thật, nhưng số quán đo được lại đến từ
# một món KHÁC hẳn chỉ vì bỏ dấu xong hai tên trùng nhau. Đã kiểm từng cái bằng tay:
#   "Chao"      = đậu phụ lên men (Quảng Đông) -> 37 quán đó thật ra là quán CHÁO
#   "Chao long" = món súp Philippines ở Palawan -> 5 quán đó thật ra là quán CHÁO LÒNG
# Đây là mặt trái của việc bỏ dấu khi so khớp: đúng cho việc tìm quán (quán hay ghi không
# dấu) nhưng sinh dương tính giả giữa các từ khác nghĩa. Chặn đích danh, kèm lý do.
ACCENT_COLLISION_BLOCKLIST = {"chao", "chao long"}

# Tên món chỉ có MỘT từ và nằm trong nhóm này thì gần như chắc chắn là nguyên liệu.
# Giữ danh sách ngắn và cụ thể: chặn quá tay sẽ mất cả món thật ("Phở", "Xôi").
SINGLE_WORD_INGREDIENTS = {
    "trà", "chanh", "mẻ", "tương", "giò", "dồi", "cốm", "quẩy", "muối", "đường",
    "mắm", "dầu", "bơ", "sữa", "trứng", "thịt", "cá", "tôm", "cua", "gạo", "nếp",
    "đậu", "rau", "nấm", "ớt", "tỏi", "hành", "gừng", "nghệ", "sả", "me", "dừa",
}


# Mã lỗi TẠM THỜI - phải thử lại, không được bỏ qua.
# 429 = bị chặn tốc độ. 5xx = phía Wikipedia trục trặc.
TRANSIENT_STATUS = frozenset({429, 500, 502, 503, 504})

# Số vòng thử lại và thời gian chờ ban đầu (giây), tăng gấp đôi mỗi vòng.
MAX_RETRIES = 5
BACKOFF_SECONDS = 2.0

# Nghỉ giữa hai lần gọi. 0.15s từng đủ khi chỉ có `discover_dishes` chạy, nhưng khi gọi
# liên tiếp vài chục thể loại thì Wikipedia trả 429 hàng loạt (đã gặp thật 2026-08-19).
POLITE_DELAY_SECONDS = 0.4


class WikipediaUnavailable(RuntimeError):
    """Hỏi lại đủ số vòng vẫn không xong. Người gọi PHẢI xử lý, không được coi là rỗng."""


def fetch_category_members(
    session: requests.Session, category: str, member_type: str
) -> List[dict]:
    """Thành viên của một thể loại. `member_type` = 'page' hoặc 'subcat'.

    Có phân trang: thể loại lớn trả về nhiều hơn 500 mục.

    ⚠️ THỬ LẠI KHI GẶP LỖI TẠM THỜI, và NÉM LỖI nếu hết vòng thử.
    Bản cũ bắt mọi lỗi rồi `return members` - tức là 429 (bị chặn tốc độ) biến thành
    "thể loại này rỗng". Ngày 2026-08-19, script điền `cuisine` bị chặn và ghi nhận 13 nền
    ẩm thực có 0 món; nếu lúc đó ghi thẳng vào file thì đã xoá sạch dữ liệu đúng bằng một
    lỗi mạng thoáng qua. Đây đúng bài học đã ghi trong CLAUDE.md mục 4b cho Overpass:
    "504 là lỗi TẠM THỜI... Bỏ ô = mất vĩnh viễn toàn bộ quán khu vực đó".
    """
    members: List[dict] = []
    cont: Optional[str] = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmlimit": "500",
            "cmtype": member_type,
            "format": "json",
            "formatversion": "2",
        }
        if cont:
            params["cmcontinue"] = cont

        payload = None
        cho = BACKOFF_SECONDS
        for lan in range(1, MAX_RETRIES + 1):
            try:
                response = session.get(WIKIPEDIA_API, params=params, timeout=30)
                if response.status_code in TRANSIENT_STATUS:
                    raise requests.HTTPError(f"HTTP {response.status_code}")
                response.raise_for_status()
                payload = response.json()
                break
            except (requests.RequestException, ValueError) as exc:
                if lan == MAX_RETRIES:
                    raise WikipediaUnavailable(
                        f"{category} ({member_type}): thu {MAX_RETRIES} lan van loi - {exc}"
                    ) from exc
                logger.warning("  %s: %s -> cho %.0fs roi thu lai (lan %d/%d)",
                               category, exc, cho, lan, MAX_RETRIES)
                time.sleep(cho)
                cho *= 2

        members.extend(payload.get("query", {}).get("categorymembers", []))
        cont = payload.get("continue", {}).get("cmcontinue")
        time.sleep(POLITE_DELAY_SECONDS)
        if not cont:
            return members


def collect_candidate_titles(session: requests.Session) -> List[str]:
    """Tên bài ứng viên từ các thể loại gốc + một cấp con."""
    titles: Set[str] = set()

    for category in ROOT_CATEGORIES:
        logger.info("Duyet %s", category)
        for member in fetch_category_members(session, category, "page"):
            if member.get("ns") == 0:
                titles.add(member["title"])

        for sub in fetch_category_members(session, category, "subcat"):
            name = sub.get("title", "")
            lowered = name.lower()
            if any(hint in lowered for hint in SKIP_SUBCATEGORY_HINTS):
                continue
            for member in fetch_category_members(session, name, "page"):
                if member.get("ns") == 0:
                    titles.add(member["title"])

    return sorted(titles)


def looks_like_dish(title: str, description: Optional[str], extract: Optional[str]) -> bool:
    """Bài này nói về MỘT MÓN ĂN cụ thể chứ không phải nguyên liệu/thương hiệu/bài tổng quan?

    Ưu tiên `description` (dòng mô tả ngắn do người biên tập đặt) vì nó sạch hơn hẳn việc
    đoán từ thân bài - chính là bài học từ lần thử dùng regex trên nội dung bài.
    """
    lowered_title = title.lower().strip()
    if any(hint in lowered_title for hint in TITLE_BLOCKLIST_HINTS):
        return False

    # Tên một từ và nằm trong nhóm nguyên liệu -> loại ngay, khỏi đọc mô tả.
    if lowered_title in SINGLE_WORD_INGREDIENTS:
        return False
    if lowered_title in ACCENT_COLLISION_BLOCKLIST:
        return False

    haystack = f"{description or ''} {extract or ''}".lower()
    if not haystack.strip():
        return False

    # LOẠI trước, NHẬN sau: "Trà" có mô tả nhắc cả "đồ uống" lẫn "thực vật" - phải để
    # tín hiệu loại thắng, nếu không nguyên liệu sẽ lọt vào danh mục món.
    if any(hint in haystack for hint in NOT_A_DISH_HINTS):
        return False

    return any(hint in haystack for hint in DISH_DESCRIPTION_HINTS)


def collides_with_existing(dish_id: str, name: str, taken: Dict[str, str]) -> Optional[str]:
    """Slug này đã bị một món KHÁC TÊN chiếm chưa? Trả tên món đang giữ slug, hoặc None.

    VÌ SAO PHẢI KIỂM: `slugify_dish` bỏ dấu, nên "Cốm" và "Cơm" cùng ra `com`, "Chao" và
    "Cháo" cùng ra `chao`. Lượt chạy thật 2026-08-19 cho thấy cả hai cặp đều lọt vào danh
    sách ứng viên với số quán y hệt nhau (120 và 37) - dấu hiệu rõ ràng của đụng độ chứ
    không phải trùng hợp. Thêm cả hai vào danh mục thì món sau ghi đè món trước một cách
    im lặng, và người dùng bấm "Cốm" lại ra quán cơm.

    Bỏ dấu là quyết định ĐÚNG cho việc so khớp tên quán (quán hay ghi không dấu), nhưng
    dùng nó làm khoá chính thì phải chấp nhận kiểm đụng độ ở đây.
    """
    holder = taken.get(dish_id)
    if holder and holder.strip().lower() != name.strip().lower():
        return holder
    return None


def load_existing_names() -> Dict[str, str]:
    """{dish_id: tên món} đã có trong seed - để không thêm trùng VÀ để bắt đụng độ slug."""
    if not SEED_PATH.exists():
        return {}
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return {
        e["dish_id"]: e.get("name", "")
        for e in raw.get("dishes", [])
        if e.get("dish_id")
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Tim mon an moi tu Wikipedia")
    parser.add_argument("--apply", action="store_true",
                        help="Them mon CO QUAN vao dish_seed_manual.json")
    parser.add_argument("--min-restaurants", type=int, default=1,
                        help="So quan toi thieu de duoc them (mac dinh 1)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Chi xu ly N ung vien dau (0 = khong gioi han). De chay thu.")
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    titles = collect_candidate_titles(session)
    logger.info("")
    logger.info("Tong ung vien tu category: %d trang", len(titles))
    if args.limit:
        titles = titles[: args.limit]
        logger.info("  (chi xu ly %d dau theo --limit)", len(titles))

    # Tra Wikipedia MỘT LẦN cho mỗi bài, có cache đĩa dùng chung với bước làm giàu.
    source = WikipediaDishSource()
    available, reason = source.is_available()
    if not available:
        logger.error("Khong goi duoc Wikipedia: %s", reason)
        return 1

    infos = source.fetch_many(titles)

    # Lọc 2: có phải MÓN ĂN không.
    dish_like = {
        title: info
        for title, info in infos.items()
        if looks_like_dish(title, None, info.description)
    }
    logger.info("Qua loc 'la mon an'    : %d", len(dish_like))

    # Lọc 3: có quán bán không. Dùng CHÍNH bộ khớp mà lúc chạy thật sẽ dùng.
    settings = Settings.from_env()
    repo = CsvRestaurantRepository(settings.restaurants_csv)
    if not repo.is_ready:
        logger.error("Chua co dataset quan: %s", repo.load_error)
        return 1
    restaurants = repo.list_all()

    probes = [Dish(name=t, dish_id=slugify_dish(t)) for t in dish_like]
    counts = count_by_dish(build_dish_restaurant_index(probes, restaurants))

    existing = load_existing_names()
    # Slug đã bị chiếm: gồm slug trong seed + slug của các món vừa nhận trong lượt này.
    taken: Dict[str, str] = dict(existing)
    grounded, ungrounded, duplicates, collisions = [], [], [], []
    for title, info in sorted(dish_like.items()):
        dish_id = slugify_dish(title)
        clash = collides_with_existing(dish_id, title, taken)
        if clash:
            collisions.append({"name": title, "dish_id": dish_id, "clashes_with": clash})
            continue
        record = {
            "dish_id": dish_id,
            "name": title,
            "description": info.description,
            "image_url": info.image_url,
            "match_keywords": [title],
            "restaurant_count": counts.get(dish_id, 0),
            "source": "wikipedia_vi",
            "source_url": info.source_url,
        }
        if dish_id in existing:
            duplicates.append(record)
        elif record["restaurant_count"] >= args.min_restaurants:
            grounded.append(record)
            taken[dish_id] = title
        else:
            ungrounded.append(record)
            taken[dish_id] = title

    grounded.sort(key=lambda r: -r["restaurant_count"])

    logger.info("")
    logger.info("=" * 68)
    logger.info("KET QUA TIM MON")
    logger.info("=" * 68)
    logger.info("Da co trong seed        : %d", len(duplicates))
    logger.info("MOI + co quan ban       : %d  <- se them neu chay --apply", len(grounded))
    logger.info("MOI nhung 0 quan        : %d  (chi ghi ra file ung vien)", len(ungrounded))
    logger.info("BI LOAI vi dung do slug : %d  (VD Com/Com, Chao/Chao)", len(collisions))
    logger.info("")
    logger.info("--- 20 mon moi nhieu quan nhat ---")
    for record in grounded[:20]:
        logger.info("  %5d quan  %s", record["restaurant_count"], record["name"])

    CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATES_PATH.write_text(
        json.dumps(
            {
                "_readme": (
                    "SINH TU DONG boi scripts/discover_dishes.py. Day la UNG VIEN, chua "
                    "vao danh muc. Mon '0 quan' giu lai de sau nay co them du lieu quan "
                    "thi dung lai duoc, khong phai tim lai tu dau."
                ),
                "grounded": grounded,
                "ungrounded": ungrounded,
                "slug_collisions": collisions,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("")
    logger.info("Da ghi ung vien: %s", CANDIDATES_PATH)

    if not args.apply:
        logger.info("Chay lai voi --apply de them %d mon vao seed.", len(grounded))
        return 0

    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    for record in grounded:
        raw["dishes"].append(
            {
                "dish_id": record["dish_id"],
                "name": record["name"],
                "description": record["description"],
                "image_url": record["image_url"],
                "match_keywords": record["match_keywords"],
                # KHÔNG tự đoán cách chế biến/độ cay/bữa ăn. Để trống -> bộ lọc cho điểm
                # trung tính, và người soạn có thể điền dần.
                "source": "wikipedia_vi",
                "source_url": record["source_url"],
            }
        )
    SEED_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Da them %d mon vao %s", len(grounded), SEED_PATH.name)
    logger.info("Chay tiep: python scripts/build_dish_catalog.py --enrich")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

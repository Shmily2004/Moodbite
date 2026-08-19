"""Điền cột `cuisine` còn trống của danh mục món, LẤY TỪ NGUỒN GỐC THẬT.

    python scripts/backfill_dish_cuisine.py            # xem trước, KHÔNG ghi
    python scripts/backfill_dish_cuisine.py --apply    # ghi vào dish_seed_manual.json

VÌ SAO CẦN
----------
Đo ngày 2026-08-19: 669/747 món (89,6%) có `cuisine = None`, nên bộ lọc "ẩm thực" ở trang
chủ gần như không lọc được gì - người dùng chọn "Nhật Bản" vẫn ra nguyên danh sách, vì
luật lọc CỐ TÌNH cho món thiếu dữ liệu đi qua (`dish_ranking._passes_hard_filter`).
Đó là luật đúng; cái sai là ta chưa điền dữ liệu.

KHÔNG BỊA - ĐÂY LÀ SUY RA TỪ NGUỒN
----------------------------------
Món trong danh mục được tìm ra bằng cách duyệt "Thể loại:Ẩm thực <nước>" trên Wikipedia
tiếng Việt (`scripts/discover_dishes.py`). Bản thân THỂ LOẠI đã là câu trả lời cho câu hỏi
"món này thuộc ẩm thực nước nào" - chỉ là lúc thu thập ta không ghi lại. Script này hỏi
lại đúng những thể loại đó và ghép ngược tên trang -> nước.

Vì vậy đây KHÔNG phải đoán mò: mỗi giá trị điền vào đều truy được về một thể loại
Wikipedia có thật. Món nào không nằm trong thể loại theo nước nào thì để NGUYÊN `None` -
CLAUDE.md mục 4b: thiếu thì để trống, tuyệt đối không suy đoán.

MỘT MÓN CÓ THỂ Ở NHIỀU NƯỚC
---------------------------
"Bánh bao" nằm trong cả ẩm thực Trung Quốc lẫn Việt Nam. Quy tắc: ưu tiên thể loại xuất
hiện SỚM NHẤT trong `CUISINE_BY_CATEGORY` (đã xếp Việt Nam lên đầu, vì đây là ứng dụng
cho người ăn ở Hà Nội). Ghi nhận các nước còn lại vào `cuisine_also` để không mất thông
tin và để người soạn tay đối chiếu được.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.discover_dishes import (  # noqa: E402
    POLITE_DELAY_SECONDS,
    SKIP_SUBCATEGORY_HINTS,
    WIKIPEDIA_API,
    WikipediaUnavailable,
    fetch_category_members,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("backfill_cuisine")

SEED_PATH = ROOT / "data_pipeline" / "dish_seed_manual.json"
CACHE_DIR = ROOT / "data_pipeline" / ".cache" / "cuisine"
CACHE_PATH = CACHE_DIR / "_ban_do_hoan_chinh.json"

# Thể loại -> tên ẩm thực dùng trong ứng dụng.
#
# THỨ TỰ CÓ Ý NGHĨA: món nằm trong nhiều thể loại thì lấy cái đứng trước. Việt Nam đứng
# đầu vì đây là ứng dụng cho người đang ăn ở Hà Nội - "Bánh bao" nên hiện ra khi lọc
# "Việt Nam", dù gốc gác là Trung Quốc.
#
# Tên nước dùng ĐÚNG chuỗi đang có sẵn trong `dish_seed_manual.json` ("Việt Nam", "Ý",
# "Hàn Quốc"...) để bộ lọc không sinh ra hai cách gọi cho cùng một nền ẩm thực.
CUISINE_BY_CATEGORY: Dict[str, str] = {
    "Thể loại:Ẩm thực Việt Nam": "Việt Nam",
    "Thể loại:Món ăn Việt Nam": "Việt Nam",
    "Thể loại:Đặc sản Việt Nam": "Việt Nam",
    "Thể loại:Ẩm thực Nhật Bản": "Nhật Bản",
    "Thể loại:Ẩm thực Hàn Quốc": "Hàn Quốc",
    "Thể loại:Ẩm thực Trung Quốc": "Trung Quốc",
    "Thể loại:Ẩm thực Thái Lan": "Thái Lan",
    "Thể loại:Ẩm thực Ấn Độ": "Ấn Độ",
    "Thể loại:Ẩm thực Indonesia": "Indonesia",
    "Thể loại:Ẩm thực Malaysia": "Malaysia",
    "Thể loại:Ẩm thực Philippines": "Philippines",
    "Thể loại:Ẩm thực Đài Loan": "Đài Loan",
    "Thể loại:Ẩm thực Hồng Kông": "Hồng Kông",
    "Thể loại:Ẩm thực Singapore": "Singapore",
    "Thể loại:Ẩm thực Thổ Nhĩ Kỳ": "Thổ Nhĩ Kỳ",
    "Thể loại:Ẩm thực Ý": "Ý",
    "Thể loại:Ẩm thực Pháp": "Pháp",
    "Thể loại:Ẩm thực Mỹ": "Âu Mỹ",
    "Thể loại:Ẩm thực Mexico": "Mexico",
    "Thể loại:Ẩm thực Tây Ban Nha": "Tây Ban Nha",
    "Thể loại:Ẩm thực Đức": "Đức",
    "Thể loại:Ẩm thực Nga": "Nga",
}


def _titles_of_category(session: requests.Session, category: str) -> Set[str]:
    """Tên các trang trong một thể loại, có duyệt thêm MỘT cấp con.

    Một cấp con là đủ ("Thể loại:Ẩm thực Việt Nam" -> "Thể loại:Bánh Việt Nam") và giữ
    đúng phạm vi mà `discover_dishes.py` đã dùng để lấy món về - hai bên phải soi cùng một
    vùng, nếu không sẽ có món trong danh mục mà script này không bao giờ thấy.
    """
    titles: Set[str] = {m["title"] for m in fetch_category_members(session, category, "page")}

    for sub in fetch_category_members(session, category, "subcat"):
        ten = sub["title"]
        if any(hint in ten.lower() for hint in SKIP_SUBCATEGORY_HINTS):
            continue
        titles.update(m["title"] for m in fetch_category_members(session, ten, "page"))
        # Nghỉ giữa các lần gọi. `fetch_category_members` đã nghỉ sẵn, đây là phần nghỉ
        # THÊM giữa hai thể loại con - hỏi vài chục thể loại liên tiếp là đủ để Wikipedia
        # trả 429 (đã gặp thật).
        time.sleep(POLITE_DELAY_SECONDS)

    return titles


def _cache_file(category: str) -> Path:
    """Mỗi thể loại một file cache riêng."""
    an_toan = "".join(c if c.isalnum() else "_" for c in category)
    return CACHE_DIR / f"{an_toan}.json"


def _titles_cached(session: requests.Session, category: str, refresh: bool) -> Set[str]:
    """Tên trang của một thể loại, CÓ CACHE THEO TỪNG THỂ LOẠI.

    Đây đúng bài học Overpass ở CLAUDE.md mục 4b: "Luôn cache theo ô để chạy lại không tốn
    công". Wikipedia chặn tốc độ khá gắt, nên hỏi một mạch 22 thể loại gần như chắc chắn
    hỏng vài cái. Cache từng thể loại thì mỗi lần chạy lại chỉ hỏi phần CÒN THIẾU - chạy
    vài lần là đủ, thay vì mãi mãi không xong vì lần nào cũng có cái hỏng.
    """
    f = _cache_file(category)
    if f.exists() and not refresh:
        return set(json.loads(f.read_text(encoding="utf-8")))
    titles = _titles_of_category(session, category)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(sorted(titles), ensure_ascii=False), encoding="utf-8")
    return titles


def build_title_to_cuisine(session: requests.Session, refresh: bool = False):
    """({tên trang: [nền ẩm thực]}, [thể loại hỏi không xong]).

    TRẢ VỀ CẢ DANH SÁCH HỎNG, và người gọi PHẢI xem. Không được coi thể loại hỏi không
    xong là thể loại rỗng: lần chạy đầu ngày 2026-08-19 bị chặn 429, 13/22 nền ẩm thực ra
    0 trang, và nếu ghi thẳng thì "Ẩm thực Pháp không có món nào" đã thành sự thật trong
    dữ liệu. Thiếu dữ liệu phải trông KHÁC HẲN dữ liệu rỗng.
    """
    mapping: Dict[str, List[str]] = {}
    hong: List[str] = []
    for category, cuisine in CUISINE_BY_CATEGORY.items():
        try:
            titles = _titles_cached(session, category, refresh)
        except WikipediaUnavailable as exc:
            logger.error("  [HONG] %s: %s", category, exc)
            hong.append(category)
            continue
        dau = "cache" if _cache_file(category).exists() else "moi "
        logger.info("  [%s] %-30s %4d trang", dau,
                    category.replace("Thể loại:", ""), len(titles))
        for title in titles:
            danh_sach = mapping.setdefault(title, [])
            if cuisine not in danh_sach:
                danh_sach.append(cuisine)
    return mapping, hong


def _load_cache() -> Optional[Dict[str, List[str]]]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return None


def _save_cache(mapping: Dict[str, List[str]]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Dien cuisine con trong cho danh muc mon")
    parser.add_argument("--apply", action="store_true",
                        help="Ghi that vao dish_seed_manual.json (mac dinh chi xem truoc)")
    parser.add_argument("--refresh", action="store_true",
                        help="Bo qua cache, hoi lai Wikipedia")
    parser.add_argument("--cho-phep-thieu", action="store_true", dest="cho_phep_thieu",
                        help="Cho phep ghi ke ca khi chua hoi xong het the loai")
    args = parser.parse_args()

    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    dishes = seed["dishes"] if isinstance(seed, dict) and "dishes" in seed else seed
    thieu = [d for d in dishes if not (d.get("cuisine") or "").strip()]
    logger.info("Danh muc: %d mon, thieu cuisine: %d (%.1f%%)",
                len(dishes), len(thieu), 100 * len(thieu) / len(dishes))

    mapping = None if args.refresh else _load_cache()
    if mapping is None:
        logger.info("Hoi Wikipedia (%d the loai)...", len(CUISINE_BY_CATEGORY))
        session = requests.Session()
        session.headers["User-Agent"] = "MoodBite/1.0 (do an tot nghiep; lien he qua GitHub)"
        mapping, hong = build_title_to_cuisine(session, args.refresh)
        if hong:
            logger.warning("")
            logger.warning("THIEU %d/%d the loai (Wikipedia chan toc do):",
                           len(hong), len(CUISINE_BY_CATEGORY))
            for ten in hong:
                logger.warning("  - %s", ten)
            logger.warning("")
            # VÌ SAO CHỈ CẢNH BÁO CHỨ KHÔNG CHẶN HẲN (sửa lại sau khi nghĩ kỹ hơn):
            # `--apply` chỉ ĐIỀN VÀO CHỖ ĐANG TRỐNG, không bao giờ ghi đè hay xoá. Nên
            # thiếu thể loại chỉ có nghĩa "điền được ít hơn", chứ KHÔNG làm hỏng dữ liệu:
            # món thuộc thể loại chưa hỏi được vẫn giữ nguyên `cuisine = None` như trước.
            #
            # Bản đầu tiên chặn cứng ở đây. Nghe thì an toàn, nhưng hậu quả là không bao
            # giờ điền được gì cả - Wikipedia gần như luôn chặn ít nhất một thể loại. Chốt
            # chặn phải cản CÁI SAI, không được cản CẢ VIỆC ĐÚNG.
            #
            # Vẫn bắt khai báo tường minh `--cho-phep-thieu`: người chạy phải BIẾT là bộ
            # dữ liệu chưa đầy đủ, thay vì tưởng đã xong.
            if args.apply and not args.cho_phep_thieu:
                logger.error("Dung lai: dang thieu du lieu ma lai co --apply.")
                logger.error("  - Chay lai lenh nay vai lan de lay not (co cache, khong")
                logger.error("    ton cong hoi lai phan da xong), HOAC")
                logger.error("  - Them --cho-phep-thieu neu chap nhan dien thieu lan nay.")
                return 1
        # Chỉ lưu bản đồ gộp khi ĐẦY ĐỦ, để lần sau không nhầm bản thiếu là bản đủ.
        if not hong:
            _save_cache(mapping)
            logger.info("Da luu ban do day du: %s", CACHE_PATH.name)

    else:
        logger.info("Dung cache %s (%d trang). Them --refresh de hoi lai.",
                    CACHE_PATH.name, len(mapping))

    dien_duoc = 0
    theo_nuoc: Dict[str, int] = {}
    for dish in thieu:
        # Danh mục lấy tên món ĐÚNG BẰNG tên trang Wikipedia, nên tra thẳng bằng tên.
        found = mapping.get(dish["name"])
        if not found:
            continue
        dish["cuisine"] = found[0]
        if len(found) > 1:
            dish["cuisine_also"] = found[1:]
        dien_duoc += 1
        theo_nuoc[found[0]] = theo_nuoc.get(found[0], 0) + 1

    logger.info("")
    logger.info("Dien duoc: %d/%d mon", dien_duoc, len(thieu))
    for nuoc, so in sorted(theo_nuoc.items(), key=lambda x: -x[1]):
        logger.info("  %-16s %4d", nuoc, so)
    con_trong = len(thieu) - dien_duoc
    logger.info("Van de trong (khong nam trong the loai theo nuoc nao): %d", con_trong)

    if not args.apply:
        logger.info("")
        logger.info("XEM TRUOC - chua ghi gi. Them --apply de ghi that.")
        return 0

    SEED_PATH.write_text(
        json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("Da ghi %s", SEED_PATH.name)
    logger.info("Chay tiep: python scripts/build_dish_catalog.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

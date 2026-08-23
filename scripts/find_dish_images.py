"""Tìm ảnh cho những món CHƯA có ảnh — miễn phí, hợp pháp, không cần khoá API.

    python scripts/find_dish_images.py                 # thử, KHÔNG ghi gì (mặc định)
    python scripts/find_dish_images.py --apply         # ghi vào dish_catalog.json
    python scripts/find_dish_images.py --limit 20      # chỉ thử 20 món đầu

VÌ SAO CẦN: `build_dish_catalog.py --enrich` chỉ hỏi Wikipedia TIẾNG VIỆT. Đo được
2026-08-22: **140/747 món chưa có ảnh**, và xui là mấy món xếp đầu trang chủ (Cà phê sữa
đá, Bia hơi, Bún, Burger, Gà rán) nằm đúng nhóm đó — nên trang chủ toàn ô chữ cái.

BA NGUỒN, THỬ LẦN LƯỢT, đều MIỄN PHÍ và KHÔNG CẦN THẺ/KHOÁ:

  1. Wikipedia TIẾNG VIỆT — TÌM KIẾM rồi lấy ảnh của bài khớp nhất (khác `build_dish_
                            catalog.py`: script đó tra THẲNG tên món nên trượt khi tên bài
                            khác tên món).
  2. Wikipedia TIẾNG ANH  — nhiều món có bài tiếng Anh kèm ảnh dù bài tiếng Việt không có.
                            "Gà rán" -> "Fried chicken", "Cơm hộp" -> "Bento".
  3. Wikimedia Commons    — kho ảnh tự do, tìm theo tên món. API `action=query` công khai.
  4. (dừng)               — không tìm được thì ĐỂ TRỐNG. Giao diện đã có ô chữ cái.

⚠️ KHÔNG DÙNG Google Images / Bing / cào ảnh từ ShopeeFood, Foody, Facebook: ảnh ở đó có
bản quyền của người khác và ToS cấm truy cập tự động (CLAUDE.md mục 4b). Đồ án tốt nghiệp
không nên xây trên nền vi phạm — đây cũng là chỗ dễ bị hỏi nhất khi bảo vệ.

⚠️ MỌI ẢNH LẤY VỀ ĐỀU GHI NGUỒN. Script ghi thêm hai trường cạnh `image_url`:
      "image_source": "wikipedia_en" | "wikimedia_commons"
      "image_credit": "<tên file/bài> — <giấy phép>"
Không ghi được nguồn thì không lấy ảnh đó.

⚠️ CHỈ LƯU ĐƯỜNG DẪN, KHÔNG TẢI ẢNH VỀ MÁY. Giống cách làm sẵn có: ~2000 ảnh cache chỉ
tốn ~1,4 MB đường dẫn, còn tải về là ~400 MB.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
CATALOG = ROOT / "data_pipeline" / "data_cleaned" / "dish_catalog.json"

# Dùng lại đúng bộ so khớp tiếng Việt của domain — tuyệt đối không tự viết lại
# (CLAUDE.md mục 4.5: ba bug thật đã xảy ra vì tự viết lại).
from src.domain.value_objects.text import contains_phrase  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Wikipedia yêu cầu User-Agent nói rõ mình là ai; thiếu là bị chặn 403.
USER_AGENT = "MoodBite/1.0 (do an tot nghiep; lien he qua kho ma nguon)"

SUMMARY = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
SEARCH_API = "https://{lang}.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# Nghỉ giữa hai lần gọi.
#
# ĐÃ ĐO (2026-08-22): để 0,3 giây thì chạy tới món thứ ~49 là Wikimedia bắt đầu từ chối
# hàng loạt — kết quả tụt xuống 19/87 dù chạy lẻ từng món vẫn ra ảnh bình thường. Đó là
# CHẶN TẦN SUẤT chứ không phải "món không có ảnh". 0,8 giây + thử lại có chờ thì hết.
NGHI_GIAY = 0.8

# Số lần thử lại khi bị từ chối tạm thời (429/503) — cùng cách xử lý với Overpass ở
# `data_pipeline` (CLAUDE.md mục 4b: 504 là lỗi TẠM THỜI, bỏ đi là mất vĩnh viễn).
SO_LAN_THU = 3
CHO_KHI_BI_CHAN = 5.0

# Ảnh nhỏ hơn mức này thường là icon/cờ/logo chứ không phải ảnh món.
RONG_TOI_THIEU = 200


#: Đếm số lần bị từ chối, để cuối lượt nói rõ "bị chặn" thay vì im lặng báo không có ảnh.
SO_LAN_BI_CHAN = 0


def goi_json(url: str, params: Optional[dict] = None) -> Optional[dict]:
    """Gọi API trả JSON, có THỬ LẠI khi bị từ chối tạm thời.

    Lỗi cuối cùng -> None chứ không ném ra ngoài: một món không tìm được ảnh thì bỏ qua
    món đó, không được để cả lượt chạy chết giữa chừng.
    """
    global SO_LAN_BI_CHAN

    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    for lan in range(SO_LAN_THU):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # 404 = thật sự không có bài -> thử lại vô nghĩa.
            if exc.code == 404:
                return None
            # 429/403/5xx = bị chặn tạm thời -> chờ rồi thử lại, chờ lâu dần.
            SO_LAN_BI_CHAN += 1
            if lan == SO_LAN_THU - 1:
                return None
            time.sleep(CHO_KHI_BI_CHAN * (lan + 1))
        except (urllib.error.URLError, TimeoutError, ValueError):
            if lan == SO_LAN_THU - 1:
                return None
            time.sleep(CHO_KHI_BI_CHAN)
    return None


def tim_tieu_de(lang: str, ten_mon: str) -> Optional[str]:
    """Tìm TÊN BÀI khớp nhất trên một wiki.

    VÌ SAO KHÔNG TRA THẲNG TÊN MÓN: tên bài hiếm khi trùng tên ta đặt. "Gà rán" trên
    Wikipedia tiếng Anh nằm ở bài "Fried chicken", "Cơm hộp" là "Bento". Tra thẳng thì
    trượt hết — đo được lần chạy đầu chỉ tìm ra 6/12 món.
    """
    data = goi_json(
        SEARCH_API.format(lang=lang),
        {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": ten_mon,
            "srlimit": "1",
            "srnamespace": "0",     # chỉ bài viết, không lấy trang thảo luận/thể loại
        },
    )
    ket_qua = ((data or {}).get("query") or {}).get("search") or []
    return ket_qua[0]["title"] if ket_qua else None


# Cụm từ trong MÔ TẢ NGẮN (Wikidata) cho thấy bài KHÔNG nói về món ăn.
#
# ⚠️ CHỐT CHẶN NÀY LÀ BẮT BUỘC, không phải cho đẹp. Máy tìm kiếm chấm bài về ĐỊA PHƯƠNG
# điểm cao nhất khi món là đặc sản vùng đó, và trước 2026-08-23 script này im lặng nhận:
#     "Lẩu gà lá é"        -> bài "Tuy Hòa (thành phố)"  -> ảnh BÃI BIỂN trên trang chủ
#     "Sữa chua trân châu" -> bài "Hoa Kỳ"               -> ảnh nước Mỹ
# Bốn món đã dính lỗi này; `scripts/audit_dish_images.py` tìm ra và gỡ.
#
# Chỉ xét `description`, KHÔNG xét phần tóm tắt: tóm tắt của bài món ăn thật vẫn hay nhắc
# tên tỉnh thành. Và khớp TỪ NGUYÊN VẸN qua `contains_phrase` — khớp chuỗi con thì "song"
# nằm trong "rau sống" (CLAUDE.md mục 4.5).
KHONG_PHAI_MON = [
    "thành phố", "tỉnh", "quốc gia", "huyện", "thị xã", "phường", "quận", "xã",
    "con sông", "ngọn núi", "hòn đảo", "vịnh", "hồ nước", "vùng đất",
    "city in", "province", "country in", "district in", "river", "mountain",
    "island", "human settlement", "municipality", "capital of", "commune", "town in",
    "nhà văn", "ca sĩ", "diễn viên", "chính trị gia", "cầu thủ",
]


def la_thuc_the_khong_phai_mon(mo_ta: Optional[str]) -> bool:
    """True khi mô tả ngắn cho thấy bài nói về một nơi chốn / một con người.

    Không có mô tả ngắn -> trả False (chưa rõ, không kết luận). "Chưa rõ" khác "sai".
    """
    if not mo_ta:
        return False
    return any(contains_phrase(mo_ta, cum) for cum in KHONG_PHAI_MON)


def tu_wikipedia(lang: str, ten_mon: str) -> Optional[tuple[str, str]]:
    """Thử một wiki (`vi` hoặc `en`): tìm bài -> lấy ảnh đại diện của bài đó."""
    tieu_de = tim_tieu_de(lang, ten_mon)
    if not tieu_de:
        return None

    time.sleep(NGHI_GIAY)
    data = goi_json(
        SUMMARY.format(lang=lang, title=urllib.parse.quote(tieu_de.replace(" ", "_")))
    )
    if not data:
        return None

    # Bài tìm được có nói về MÓN ĂN không? Không thì bỏ, thà để trống còn hơn ảnh sai.
    if la_thuc_the_khong_phai_mon(data.get("description")):
        return None

    # `thumbnail` (~320px) chứ không phải `originalimage`: ảnh gốc có cái nặng 8MB.
    thumb = data.get("thumbnail") or {}
    if not thumb.get("source") or thumb.get("width", 0) < RONG_TOI_THIEU:
        return None

    ten_viet_tat = {"vi": "VI", "en": "EN"}[lang]
    return thumb["source"], f"Wikipedia ({ten_viet_tat}): {data.get('title', tieu_de)} — CC BY-SA"


def tu_commons(ten_mon: str) -> Optional[tuple[str, str]]:
    """Thử kho ảnh Wikimedia Commons. Trả (đường dẫn ảnh, ghi công) hoặc None."""
    data = goi_json(
        COMMONS_API,
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            # `filetype:bitmap` để không dính SVG (biểu đồ, icon) — ta cần ẢNH CHỤP.
            "gsrsearch": f'{ten_mon} filetype:bitmap',
            "gsrnamespace": "6",   # namespace 6 = File:
            "gsrlimit": "5",
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": "480",
        },
    )
    if not data:
        return None

    trang = (data.get("query") or {}).get("pages") or {}
    # `pages` là dict không có thứ tự ổn định -> sắp theo `index` của kết quả tìm kiếm để
    # lần chạy nào cũng ra cùng một ảnh.
    for muc in sorted(trang.values(), key=lambda p: p.get("index", 999)):
        thong_tin = (muc.get("imageinfo") or [{}])[0]
        url = thong_tin.get("thumburl") or thong_tin.get("url")
        if not url or thong_tin.get("width", 0) < RONG_TOI_THIEU:
            continue
        meta = thong_tin.get("extmetadata") or {}
        giay_phep = (meta.get("LicenseShortName") or {}).get("value") or "xem trang Commons"
        ten_file = (muc.get("title") or "").replace("File:", "")
        return url, f"Wikimedia Commons: {ten_file} — {giay_phep}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Ghi kết quả vào dish_catalog.json. Không có cờ này thì chỉ THỬ và in ra.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Chỉ xử lý N món đầu.")
    args = parser.parse_args()

    if not CATALOG.exists():
        print(f"Không thấy {CATALOG}. Chạy `python scripts/build_dish_catalog.py` trước.")
        return 1

    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    dishes = data["dishes"]

    thieu = [d for d in dishes if not d.get("image_url") and d.get("is_active", True)]
    if args.limit:
        thieu = thieu[: args.limit]

    print("=" * 68)
    print("TÌM ẢNH CHO MÓN CHƯA CÓ ẢNH")
    print("=" * 68)
    print(f"  Tổng số món      : {len(dishes)}")
    print(f"  Đã có ảnh        : {sum(1 for d in dishes if d.get('image_url'))}")
    print(f"  Sẽ đi tìm lần này: {len(thieu)}")
    print(f"  Chế độ           : {'GHI THẬT (--apply)' if args.apply else 'chỉ thử, không ghi'}")
    print()

    tim_duoc = 0
    theo_nguon: dict[str, int] = {}

    for i, mon in enumerate(thieu, start=1):
        ten = mon.get("name") or ""
        # Thứ tự: wiki tiếng Việt (sát nghĩa món Việt nhất) -> wiki tiếng Anh -> Commons.
        ket_qua = tu_wikipedia("vi", ten)
        nguon = "wikipedia_vi"
        if ket_qua is None:
            time.sleep(NGHI_GIAY)
            ket_qua = tu_wikipedia("en", ten)
            nguon = "wikipedia_en"
        if ket_qua is None:
            time.sleep(NGHI_GIAY)
            ket_qua = tu_commons(ten)
            nguon = "wikimedia_commons"

        if ket_qua is None:
            print(f"  [{i:>3}/{len(thieu)}] {ten:<28} — không tìm được, để trống")
        else:
            url, ghi_cong = ket_qua
            tim_duoc += 1
            theo_nguon[nguon] = theo_nguon.get(nguon, 0) + 1
            # In luôn NGUỒN ĐẦY ĐỦ: tìm kiếm có thể ra bài lệch nghĩa ("Bún nước" -> bài
            # "Bún"), nên phải cho người chạy soi được trước khi --apply.
            print(f"  [{i:>3}/{len(thieu)}] {ten:<26} ✓ {ghi_cong}")
            if args.apply:
                mon["image_url"] = url
                # GHI NGUỒN cùng lúc với ảnh. Không có nguồn thì không được nhận ảnh.
                mon["image_source"] = nguon
                mon["image_credit"] = ghi_cong

        time.sleep(NGHI_GIAY)

    print()
    print(f"  Tìm được: {tim_duoc}/{len(thieu)}  {theo_nguon}")
    if SO_LAN_BI_CHAN:
        print(
            f"  ⚠ Bị máy chủ từ chối {SO_LAN_BI_CHAN} lượt (đã tự thử lại). Nếu tỉ lệ tìm "
            "được thấp bất thường thì chạy lại lần nữa — món đã có ảnh sẽ được bỏ qua."
        )

    if args.apply and tim_duoc:
        CATALOG.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  Đã ghi vào {CATALOG.name}.")
        print("  ⚠️ Backend đọc file này lúc KHỞI ĐỘNG -> khởi động lại server mới thấy ảnh mới.")
    elif tim_duoc:
        print("  Chưa ghi gì. Thêm cờ --apply để ghi thật.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

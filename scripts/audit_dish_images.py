"""Soát ảnh món: tìm ảnh GẮN NHẦM và gỡ bỏ.

    python scripts/audit_dish_images.py            # chỉ soát và in ra
    python scripts/audit_dish_images.py --clear    # gỡ những ảnh sai

VÌ SAO CẦN — LỖI CÓ THẬT, PHÁT HIỆN 2026-08-23
----------------------------------------------
`find_dish_images.py` tìm ảnh bằng cách hỏi Wikipedia "bài nào khớp tên món này nhất",
rồi lấy ảnh đại diện của bài đó. Cách này cần thiết (tên bài hiếm khi trùng tên món:
"Gà rán" nằm ở bài "Fried chicken"), NHƯNG nó im lặng nhận cả những bài chẳng liên quan:

    Lẩu gà lá é       -> bài "Tuy Hòa (thành phố)"  -> ảnh BÃI BIỂN
    Trà đào cam sả    -> bài "Lào Cai"              -> ảnh một tỉnh miền núi
    Sữa chua trân châu-> bài "Hoa Kỳ"               -> ảnh nước Mỹ

Lý do: món là ĐẶC SẢN của địa phương nào đó, nên máy tìm kiếm chấm bài về địa phương đó
điểm cao nhất. Trang chủ hiện ảnh bãi biển cho món lẩu — người dùng mất tin ngay.

CÁCH SOÁT: hỏi Wikipedia phần `description` (mô tả ngắn lấy từ Wikidata) của chính bài đã
dùng, rồi loại những bài mô tả một THỰC THỂ KHÔNG PHẢI MÓN ĂN (thành phố, tỉnh, quốc gia,
sông, núi...). Dùng mô tả chứ không so tên vì so tên cho kết quả sai cả hai chiều:
"Burger -> Hamburger" và "Dimsum -> Điểm tâm Quảng Đông" là ĐÚNG dù không trùng chữ nào.

Chỉ soát được món có `image_credit` (ghi rõ tên bài). Ảnh nhập từ đợt
`build_dish_catalog.py --enrich` đi theo đường khác (khớp đúng tên bài) nên không nằm
trong nhóm rủi ro này — script nói rõ số lượng thay vì lặng lẽ bỏ qua.
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
CATALOG = ROOT / "data_pipeline" / "data_cleaned" / "dish_catalog.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

USER_AGENT = "MoodBite/1.0 (academic graduation project; contact via GitHub)"
SUMMARY = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"

# Nghỉ giữa hai lần gọi. Wikimedia chặn khi gọi dồn dập — đã đo ở `find_dish_images.py`:
# 0.3s cho 19/87, 0.8s cho 84/87.
NGHI_GIAY = 0.8

# Cụm từ trong MÔ TẢ NGẮN cho thấy bài KHÔNG nói về món ăn.
#
# ⚠️ HAI QUY TẮC ĐÃ PHẢI TRẢ GIÁ MỚI CÓ (lần chạy đầu 2026-08-23 báo nhầm 5/9 món):
#
# 1. CHỈ XÉT `description` (mô tả ngắn từ Wikidata), KHÔNG xét phần tóm tắt.
#    Tóm tắt của bài "Bánh tráng trộn" có nhắc "Thành phố Hồ Chí Minh"; bài "Nem nướng"
#    có chữ "quốc gia". Cả hai đều là bài MÓN ĂN đúng nghĩa. Không biết loại thực thể thì
#    BỎ QUA, chứ không đoán — "chưa rõ" khác hẳn "sai".
#
# 2. KHỚP TỪ NGUYÊN VẸN, không khớp chuỗi con — dùng `contains_phrase` của domain.
#    Khớp chuỗi con thì "song" nằm trong "rau sống" (bỏ dấu thành "rau song") và món
#    salad bị chấm là "con sông". Đây đúng là lỗi kinh điển của dự án này (CLAUDE.md
#    mục 4.5), và nó vừa tái diễn ngay ở đây.
#
# Chỉ liệt kê thực thể ĐỊA LÝ/HÀNH CHÍNH và người — nhóm mà máy tìm kiếm hay trả nhầm,
# vì món ăn thường gắn với một địa phương.
KHONG_PHAI_MON = [
    "thành phố", "tỉnh", "quốc gia", "huyện", "thị xã", "phường", "quận", "xã",
    "con sông", "ngọn núi", "hòn đảo", "vịnh", "hồ nước", "vùng đất",
    "city in", "province", "country in", "district in", "river", "mountain",
    "island", "human settlement", "municipality", "capital of", "commune", "town in",
    "nhà văn", "ca sĩ", "diễn viên", "chính trị gia", "cầu thủ",
]


sys.path.insert(0, str(ROOT))
from src.domain.value_objects.text import contains_phrase  # noqa: E402


def mo_ta_bai(lang: str, tieu_de: str) -> Optional[str]:
    """`description` của một bài Wikipedia. None nếu không lấy được."""
    url = SUMMARY.format(lang=lang, title=urllib.parse.quote(tieu_de.replace(" ", "_")))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"      (không hỏi được Wikipedia: {exc})")
        return None
    # CHỈ mô tả ngắn. Bài không có thì trả chuỗi rỗng và ta không kết luận gì —
    # xem ghi chú ở `KHONG_PHAI_MON`.
    return data.get("description") or ""


def tach_tieu_de(credit: str) -> tuple[Optional[str], Optional[str]]:
    """'Wikipedia (VI): Phú Yên — CC BY-SA' -> ('vi', 'Phú Yên')."""
    if "): " not in credit:
        return None, None
    dau, sau = credit.split("): ", 1)
    lang = "vi" if "(VI" in dau else ("en" if "(EN" in dau else None)
    return lang, sau.rsplit(" — ", 1)[0].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--clear", action="store_true",
        help="Gỡ ảnh của những món bị đánh dấu sai. Không có cờ này thì chỉ in ra.",
    )
    args = parser.parse_args()

    if not CATALOG.exists():
        print(f"Không thấy {CATALOG}.")
        return 1

    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    dishes = data["dishes"]

    co_anh = [d for d in dishes if d.get("image_url")]
    soat_duoc = [d for d in co_anh if d.get("image_credit")]

    print("=" * 68)
    print("SOÁT ẢNH MÓN — TÌM ẢNH GẮN NHẦM")
    print("=" * 68)
    print(f"  Món có ảnh              : {len(co_anh)}")
    print(f"  Soát được (có ghi công) : {len(soat_duoc)}")
    print(f"  Không soát được         : {len(co_anh) - len(soat_duoc)}"
          f"  (nhập từ build_dish_catalog --enrich, đi đường khớp đúng tên bài)")
    print(f"  Chế độ                  : {'GỠ ẢNH SAI (--clear)' if args.clear else 'chỉ in ra'}")
    print()

    sai = []
    for i, mon in enumerate(soat_duoc, start=1):
        lang, tieu_de = tach_tieu_de(mon["image_credit"])
        if not lang or not tieu_de:
            continue

        mo_ta = mo_ta_bai(lang, tieu_de)
        time.sleep(NGHI_GIAY)
        if mo_ta is None:
            continue

        if not mo_ta:
            continue  # không có mô tả ngắn -> chưa rõ, không kết luận
        khong_dat = next((k for k in KHONG_PHAI_MON if contains_phrase(mo_ta, k)), None)
        if khong_dat:
            sai.append((mon, tieu_de, mo_ta))
            print(f"  [{i:>3}/{len(soat_duoc)}] ✗ {mon['name']:<24} -> bài “{tieu_de}” ({mo_ta})")
            if args.clear:
                # Gỡ CẢ BA trường cùng lúc: để sót `image_credit` thì lần soát sau sẽ
                # tưởng món này vẫn có ảnh.
                mon["image_url"] = None
                mon["image_source"] = None
                mon["image_credit"] = None

    print()
    print(f"  Ảnh gắn nhầm: {len(sai)}")
    if sai and not args.clear:
        print("  Chạy lại với --clear để gỡ.")
    if sai and args.clear:
        CATALOG.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  Đã ghi lại {CATALOG}")
        print("  Món vừa bị gỡ ảnh sẽ trống chỗ ảnh — thà trống còn hơn hiện ảnh sai.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

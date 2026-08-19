"""Kiểm tra website của quán còn sống không — TÍN HIỆU YẾU, chỉ để tham khảo.

    python scripts/check_websites.py --gioi-han 200      # thử 200 quán
    python scripts/check_websites.py                     # chạy hết (lâu)
    python scripts/check_websites.py --xuat bao_cao.json

⚠️ ĐỌC KỸ PHẦN NÀY TRƯỚC KHI DÙNG KẾT QUẢ
------------------------------------------
Website chết KHÔNG có nghĩa là quán đóng cửa, và website sống KHÔNG có nghĩa là quán còn
mở. Cụ thể:

  - Rất nhiều quán vỉa hè làm ăn tốt vẫn để tên miền hết hạn vì không ai dùng tới.
  - Ngược lại, tên miền đã bán lại cho người khác vẫn trả về HTTP 200 bình thường.
  - Trang bị đỗ (parked domain) cũng trả 200.

Vì vậy script này CHỈ IN BÁO CÁO. Không tự ẩn quán nào, và không được dùng một mình để
kết luận quán đã đóng. Nó chỉ đáng dùng làm tín hiệu PHỤ, cộng thêm vào các tín hiệu khác
(ngày cập nhật thật, số nguồn xác nhận, lượt người dùng báo đóng cửa).

BỎ QUA LINK NỀN TẢNG
--------------------
Đo ngày 2026-08-19 trên 10.514 quán có website: một phần đáng kể thực ra là link tới
facebook.com, instagram.com, tiktok.com, shopeefood.vn, maps.app.goo.gl, m.me...
Những địa chỉ đó LUÔN sống vì bản thân nền tảng luôn sống, nên kiểm tra chúng chỉ tốn
thời gian mà không thu được tin gì. Chỉ kiểm TÊN MIỀN RIÊNG của quán.

LỊCH SỰ VỚI MÁY CHỦ NGƯỜI TA
----------------------------
Dùng HEAD (không tải nội dung), có timeout ngắn, có giới hạn số luồng, và mỗi tên miền
chỉ hỏi một lần dù nhiều quán cùng trỏ tới. Đây là truy cập công khai bình thường, không
phải cào nội dung - không đụng tới ToS của ai.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import urllib.parse as urlparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.infrastructure.config.settings import Settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("check_websites")

CACHE_PATH = ROOT / "data_pipeline" / ".cache" / "website_status.json"

# Tên miền của NỀN TẢNG, không phải của quán. Kiểm tra chúng là vô nghĩa: facebook.com
# luôn sống, kể cả khi trang của quán đã bị xoá.
NEN_TANG = frozenset({
    "facebook.com", "m.facebook.com", "fb.com", "fb.me", "m.me", "messenger.com",
    "instagram.com", "tiktok.com", "youtube.com", "youtu.be", "threads.net",
    "zalo.me", "shopeefood.vn", "shopee.vn", "foody.vn", "grab.com",
    "maps.app.goo.gl", "goo.gl", "g.page", "google.com", "maps.google.com",
    "linktr.ee", "order.ipos.vn", "now.vn", "beamin.vn", "baemin.vn",
})

TIMEOUT_GIAY = 8
SO_LUONG = 12          # số luồng chạy song song
USER_AGENT = "MoodBite/1.0 (do an tot nghiep; kiem tra lien ket con song)"


def _ten_mien(url: Optional[str]) -> Optional[str]:
    if not url or not str(url).strip():
        return None
    raw = str(url).strip()
    if "//" not in raw:
        raw = "http://" + raw
    try:
        host = urlparse.urlparse(raw).netloc.lower()
    except ValueError:
        return None
    return host[4:] if host.startswith("www.") else host or None


def _kiem_tra(url: str) -> Tuple[str, Optional[int]]:
    """('song'|'chet'|'khong_ro', mã HTTP). KHÔNG ném lỗi ra ngoài.

    HEAD trước; nhiều máy chủ chặn HEAD nên 405/501 thì thử GET với stream để không tải
    hết nội dung. Lỗi mạng phía TA (hết giờ chờ, DNS trục trặc tạm) trả 'khong_ro' chứ
    KHÔNG trả 'chet' - đổ lỗi cho quán vì mạng nhà mình là sai.
    """
    dich = url if "//" in url else "http://" + url
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.head(dich, timeout=TIMEOUT_GIAY, allow_redirects=True, headers=headers)
        if r.status_code in (403, 405, 501):
            r = requests.get(dich, timeout=TIMEOUT_GIAY, allow_redirects=True,
                             headers=headers, stream=True)
            r.close()
        if r.status_code < 400:
            return "song", r.status_code
        if r.status_code in (404, 410):
            return "chet", r.status_code
        # 5xx là máy chủ trục trặc TẠM THỜI, không phải bằng chứng quán đóng.
        return "khong_ro", r.status_code
    except requests.exceptions.SSLError:
        # Chứng chỉ hỏng/hết hạn: máy chủ vẫn còn đó, chỉ là không ai chăm.
        return "khong_ro", None
    except requests.exceptions.ConnectionError:
        # Không phân giải được tên miền hoặc bị từ chối kết nối -> dấu hiệu chết rõ nhất.
        return "chet", None
    except requests.RequestException:
        return "khong_ro", None


def main() -> int:
    parser = argparse.ArgumentParser(description="Kiem tra website quan con song khong")
    parser.add_argument("--gioi-han", type=int, dest="gioi_han",
                        help="Chi kiem N ten mien dau (de thu nhanh)")
    parser.add_argument("--xuat", type=Path, help="Ghi bao cao JSON")
    parser.add_argument("--lam-moi", action="store_true", dest="lam_moi",
                        help="Bo qua cache, kiem lai tu dau")
    args = parser.parse_args()

    settings = Settings.from_env()
    df = pd.read_csv(settings.restaurants_csv, low_memory=False)

    co_web = df[df["website"].notna()]
    theo_mien: Dict[str, list] = {}
    bo_qua_nen_tang = 0
    for row in co_web.itertuples():
        mien = _ten_mien(row.website)
        if not mien:
            continue
        if mien in NEN_TANG:
            bo_qua_nen_tang += 1
            continue
        theo_mien.setdefault(mien, []).append(row.title)

    logger.info("Quan co website        : %d/%d (%.1f%%)", len(co_web), len(df),
                100 * len(co_web) / len(df))
    logger.info("La link nen tang, bo qua: %d (luon song nen khong mang tin hieu gi)",
                bo_qua_nen_tang)
    logger.info("Ten mien RIENG can kiem : %d", len(theo_mien))

    cache: Dict[str, list] = {}
    if CACHE_PATH.exists() and not args.lam_moi:
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        logger.info("Da co ket qua cu cho %d ten mien (them --lam-moi de kiem lai)",
                    len(cache))

    can_kiem = [m for m in theo_mien if m not in cache]
    if args.gioi_han:
        can_kiem = can_kiem[: args.gioi_han]
    logger.info("Lan nay kiem            : %d ten mien", len(can_kiem))

    if can_kiem:
        with ThreadPoolExecutor(max_workers=SO_LUONG) as pool:
            for mien, ket_qua in zip(can_kiem, pool.map(_kiem_tra, can_kiem)):
                cache[mien] = list(ket_qua)
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    da_kiem = {m: cache[m] for m in theo_mien if m in cache}
    dem = {"song": 0, "chet": 0, "khong_ro": 0}
    for trang_thai, _ in da_kiem.values():
        dem[trang_thai] = dem.get(trang_thai, 0) + 1

    tong = max(1, len(da_kiem))
    logger.info("")
    logger.info("=" * 62)
    logger.info("KET QUA (tren %d ten mien da kiem)", len(da_kiem))
    logger.info("=" * 62)
    logger.info("  Con song  : %5d (%.1f%%)", dem["song"], 100 * dem["song"] / tong)
    logger.info("  Da chet   : %5d (%.1f%%)", dem["chet"], 100 * dem["chet"] / tong)
    logger.info("  Khong ro  : %5d (%.1f%%)  <- loi mang/5xx, KHONG ket luan gi",
                dem["khong_ro"], 100 * dem["khong_ro"] / tong)

    chet = [(m, theo_mien[m]) for m, (tt, _) in da_kiem.items() if tt == "chet"]
    if chet:
        logger.info("")
        logger.info("--- TEN MIEN CHET (%d) ---", len(chet))
        for mien, quans in chet[:15]:
            logger.info("  %-34s %s", mien[:34], ", ".join(str(q)[:24] for q in quans[:2]))
        if len(chet) > 15:
            logger.info("  ... con %d nua", len(chet) - 15)

    logger.info("")
    logger.info("⚠️  Website chet KHONG dong nghia quan da dong cua - nhieu quan via he")
    logger.info("   lam an tot van de ten mien het han. Chi dung lam tin hieu PHU.")

    if args.xuat:
        args.xuat.write_text(json.dumps(
            {"tom_tat": dem,
             "chet": [{"ten_mien": m, "quan": q} for m, q in chet]},
            ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Da ghi %s", args.xuat)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

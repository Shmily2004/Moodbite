"""Dựng BẢNG SOÁT ẢNH MÓN để xem bằng mắt và đánh dấu ảnh sai.

    python scripts/review_dish_images.py           # dựng file rồi in đường dẫn
    python scripts/review_dish_images.py --mo      # dựng xong mở luôn trình duyệt

VÌ SAO CẦN CÁI NÀY — `audit_dish_images.py` KHÔNG ĐỦ
----------------------------------------------------
Script kia chỉ bắt được ảnh lấy từ bài KHÔNG PHẢI MÓN ĂN (bài "Tuy Hoà (thành phố)" cho
món lẩu). Nó BẤT LỰC trước loại lỗi thứ hai, và loại này mới nhiều:

    ảnh ĐÚNG BÀI nhưng là MỘT TẤM ẢNH TỆ.

Ví dụ thật (chủ dự án chỉ ra 2026-08-23): "Nem nướng" lấy ảnh đại diện của đúng bài
"Nem nướng" trên Wikipedia — nhưng tấm đó chụp mấy xiên thịt đang nướng trên vỉ than, đỏ
au, nhìn như thịt sống. Đúng về dữ liệu, sai về cảm nhận: người dùng nhìn vào không nhận
ra món.

Không có cách nào để MÁY tự biết "tấm ảnh này trông có giống món đó không" nếu không dùng
mô hình thị giác. Nhưng MẮT NGƯỜI làm việc đó trong nửa giây. Việc của script này là bày
toàn bộ ảnh ra một trang để soát 691 món trong vài phút, thay vì mở từng món một.

CÁCH DÙNG
---------
1. Chạy script, mở file HTML hiện ra.
2. Bấm vào ảnh nào SAI -> nó chuyển đỏ. Bấm lại để bỏ đánh dấu.
3. Đánh dấu tới đâu lưu tới đó (localStorage) — đóng trang rồi mở lại vẫn còn.
4. Cuối trang có sẵn LỆNH để chạy, gỡ hết ảnh đã đánh dấu.

Ảnh bị gỡ sẽ để trống chỗ ảnh. Thà trống còn hơn ảnh sai — trống thì người dùng biết là
chưa có, còn ảnh sai thì họ tin đó là món.
"""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data_pipeline" / "data_cleaned" / "dish_catalog.json"
OUTPUT = ROOT / "runs" / "soat_anh_mon.html"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


TRANG = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<title>Soát ảnh món — MoodBite</title>
<style>
  body {{ margin:0; font:15px/1.5 system-ui,sans-serif; background:#FDF4E9; color:#10203C; }}
  header {{ position:sticky; top:0; z-index:5; background:#FDF4E9;
            border-bottom:1px solid #F0E2CD; padding:14px 20px; }}
  h1 {{ margin:0 0 4px; font-size:1.15rem; }}
  .huong-dan {{ color:#4A5769; font-size:.88rem; margin:0; }}
  .luoi {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
           gap:12px; padding:16px 20px 220px; }}
  figure {{ margin:0; border:2px solid #F0E2CD; border-radius:12px; overflow:hidden;
            background:#FEF7EE; cursor:pointer; }}
  figure img {{ display:block; width:100%; height:120px; object-fit:cover;
                background:#EEE; }}
  figcaption {{ padding:6px 8px; font-size:.8rem; line-height:1.3; }}
  .ma {{ color:#8792A5; font-size:.72rem; word-break:break-all; }}
  figure.sai {{ border-color:#D63A24; background:#FBEAE7; }}
  figure.sai img {{ opacity:.35; }}
  figure.sai figcaption::before {{ content:"✗ SAI — "; color:#D63A24; font-weight:800; }}
  footer {{ position:fixed; bottom:0; left:0; right:0; background:#fff;
            border-top:2px solid #F39206; padding:12px 20px; }}
  textarea {{ width:100%; height:70px; font:12px/1.4 monospace; }}
  button {{ font:inherit; padding:6px 12px; border-radius:8px; cursor:pointer;
            border:1px solid #F0E2CD; background:#FEF7EE; }}
</style></head><body>
<header>
  <h1>Soát ảnh món — {tong} món có ảnh</h1>
  <p class="huong-dan">Bấm vào ảnh nào <strong>không giống món</strong> để đánh dấu đỏ.
     Đánh dấu được lưu lại, đóng trang mở lại vẫn còn.</p>
</header>

<div class="luoi" id="luoi"></div>

<footer>
  <div style="display:flex;gap:10px;align-items:center;margin-bottom:6px">
    <strong id="dem">0 món bị đánh dấu</strong>
    <button onclick="xoaHet()">Bỏ hết đánh dấu</button>
    <button onclick="chep()">Chép lệnh</button>
  </div>
  <textarea id="lenh" readonly></textarea>
</footer>

<script>
const MON = {du_lieu};
const KHOA = 'moodbite.anh_sai';
let sai = new Set(JSON.parse(localStorage.getItem(KHOA) || '[]'));

const luoi = document.getElementById('luoi');
for (const m of MON) {{
  const f = document.createElement('figure');
  f.dataset.id = m.id;
  if (sai.has(m.id)) f.classList.add('sai');
  // `loading=lazy`: 691 ảnh tải cùng lúc sẽ treo trình duyệt và bị Wikimedia chặn.
  f.innerHTML = '<img loading="lazy" src="' + m.url + '" alt="">' +
                '<figcaption>' + m.ten + '<br><span class="ma">' + m.id + '</span></figcaption>';
  f.onclick = () => {{
    f.classList.toggle('sai');
    if (f.classList.contains('sai')) sai.add(m.id); else sai.delete(m.id);
    luu();
  }};
  luoi.appendChild(f);
}}

function luu() {{
  localStorage.setItem(KHOA, JSON.stringify([...sai]));
  document.getElementById('dem').textContent = sai.size + ' món bị đánh dấu';
  document.getElementById('lenh').value = sai.size === 0
    ? 'Chưa đánh dấu món nào.'
    : [...sai].map(id => 'python scripts/set_dish_image.py --dish ' + id + ' --clear').join('\\n');
}}
function xoaHet() {{
  sai.clear();
  document.querySelectorAll('figure.sai').forEach(f => f.classList.remove('sai'));
  luu();
}}
function chep() {{
  const t = document.getElementById('lenh');
  t.select(); document.execCommand('copy');
}}
luu();
</script>
</body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--mo", action="store_true", help="Mở trình duyệt luôn.")
    args = parser.parse_args()

    if not CATALOG.exists():
        print(f"Không thấy {CATALOG}.")
        return 1

    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    # Chỉ soát món ĐANG BẬT: 565 món không quán nào bán đã bị tắt, soát ảnh cho chúng là
    # tốn công vào thứ người dùng không bao giờ nhìn thấy.
    mon = [
        {"id": d.get("dish_id"), "ten": d.get("name"), "url": d.get("image_url")}
        for d in data["dishes"]
        if d.get("image_url") and d.get("is_active", True)
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        TRANG.format(tong=len(mon), du_lieu=json.dumps(mon, ensure_ascii=False)),
        encoding="utf-8",
    )

    print("=" * 68)
    print("BẢNG SOÁT ẢNH MÓN")
    print("=" * 68)
    print(f"  Món đang bật và có ảnh : {len(mon)}")
    print(f"  Đã ghi                 : {OUTPUT}")
    print()
    print("  Mở file trên bằng trình duyệt, bấm vào ảnh nào không giống món.")
    print("  Cuối trang có sẵn lệnh để gỡ những ảnh đã đánh dấu.")

    if args.mo:
        webbrowser.open(OUTPUT.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

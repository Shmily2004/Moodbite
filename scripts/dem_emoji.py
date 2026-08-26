"""ĐẾM EMOJI CÒN SÓT trong mã nguồn frontend.

    python scripts/dem_emoji.py            # bảng tổng hợp
    python scripts/dem_emoji.py --chi-tiet # kèm từng dòng

VÌ SAO CÓ SCRIPT NÀY: chủ dự án chốt 2026-08-24 "những cái không phải icon tôi gửi thì
hãy dùng icon thay vì emoji". Emoji mỗi hệ điều hành vẽ một kiểu, không đổi màu theo giao
diện sáng/tối, và không khớp bộ nhận diện. Việc thay là làm dần nhiều đợt, nên cần một
cách ĐẾM LẠI thay vì tin vào con số ghi trong tài liệu — đúng tinh thần CLAUDE.md mục 0.

KHÔNG tính vào kết quả:
  - mũi tên và ký hiệu chữ (`←` `→` `✕` `›` `☰`): đây là KÝ TỰ CHỮ, hiện đúng ở mọi phông
    và không có icon SVG nào thay thế cho gọn hơn;
  - dòng bình luận: emoji trong comment là để người đọc code, không hiện ra giao diện;
  - file test: chúng chỉ đối chiếu chuỗi.

⚠️ Script này ĐẾM, không sửa. Thay emoji bằng icon là việc phải nhìn từng chỗ: có chỗ
cần icon mới ở `shared/ui/icons.tsx`, có chỗ nên bỏ hẳn.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOC = ROOT / "frontend" / "apps" / "client" / "src"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Các dải Unicode chứa emoji. Cố ý KHÔNG lấy cả dải  -⯿ vì trong đó có mũi tên
# và dấu nháy kiểu chữ — xem danh sách miễn trừ bên dưới.
EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"   # ký hiệu & hình vẽ, mặt cười, đồ vật, cờ
    "☀-⛿"           # ký hiệu linh tinh (☀ ☕ ⚠ …)
    "✀-➿"           # dingbats (✂ ✅ ✨ …)
    "⬀-⯿"           # mũi tên & hình khối bổ sung (⭐ …)
    "️"                  # dấu chọn kiểu hiển thị emoji
    "]"
)

# KÝ TỰ CHỮ, không phải emoji — xem docstring.
MIEN_TRU = set("←→↑↓⇒›‹✕✓★☰⚠")


def _la_dong_binh_luan(dong: str) -> bool:
    t = dong.lstrip()
    return t.startswith("*") or t.startswith("//") or t.startswith("/*")


def quet() -> dict[str, list[tuple[int, str, str]]]:
    ket_qua: dict[str, list[tuple[int, str, str]]] = {}
    for f in sorted([*GOC.rglob("*.tsx"), *GOC.rglob("*.ts")]):
        if ".test." in f.name:
            continue
        cac_dong: list[tuple[int, str, str]] = []
        for i, dong in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if _la_dong_binh_luan(dong):
                continue
            thay = [c for c in EMOJI.findall(dong) if c not in MIEN_TRU]
            if thay:
                cac_dong.append((i, "".join(thay), dong.strip()[:70]))
        if cac_dong:
            ket_qua[f.relative_to(ROOT).as_posix()] = cac_dong
    return ket_qua


def main() -> int:
    parser = argparse.ArgumentParser(description="Dem emoji con sot trong frontend")
    parser.add_argument("--chi-tiet", action="store_true", help="In tung dong")
    args = parser.parse_args()

    if not GOC.exists():
        print(f"Không thấy thư mục {GOC}")
        return 1

    ket_qua = quet()
    tong = sum(len(v) for v in ket_qua.values())

    print("=" * 70)
    print("EMOJI CÒN SÓT TRONG FRONTEND")
    print("=" * 70)
    if not ket_qua:
        print("Không còn emoji nào. (Mũi tên và ký tự chữ không tính — xem docstring.)")
        return 0

    for f, ds in sorted(ket_qua.items(), key=lambda x: (-len(x[1]), x[0])):
        print(f"  {len(ds):3d}  {f}")
        if args.chi_tiet:
            for so, e, noi_dung in ds:
                print(f"           {so:5d}: {e}   {noi_dung}")

    print("-" * 70)
    print(f"TỔNG: {tong} dòng trong {len(ket_qua)} file")
    print()
    print("Xem từng dòng:  python scripts/dem_emoji.py --chi-tiet")
    # Trả 0 dù còn emoji: đây là công cụ ĐO, không phải cổng chặn CI. Cho nó làm CI đỏ
    # sẽ chặn mọi thay đổi không liên quan chỉ vì một emoji ở màn hình khác.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

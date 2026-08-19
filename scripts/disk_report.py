"""ĐO DUNG LƯỢNG dự án đang chiếm, và chỉ ra chỗ có thể dọn.

    python scripts/disk_report.py              # chỉ đo
    python scripts/disk_report.py --clean-cache  # xoá cache tra cứu (lấy lại được)

VÌ SAO CÓ FILE NÀY: máy chủ dự án là laptop cá nhân. Việc mở rộng dữ liệu (thêm thành phố,
thêm món) làm thư mục `data_raw/` phình ra âm thầm, và người dùng chỉ phát hiện khi ổ đầy.

NGUYÊN TẮC ĐÃ ÁP DỤNG ĐỂ KHÔNG PHÌNH:
  - ẢNH MÓN chỉ lưu ĐƯỜNG DẪN, không tải file về. 500 món ≈ 50KB thay vì ≈ 100MB.
  - Cache tra Wikipedia là JSON nhỏ (~400 byte/món) và XOÁ ĐƯỢC - mất thì chỉ tốn công
    gọi lại mạng, không mất dữ liệu gốc.
  - Dữ liệu thô của mỗi nguồn nằm riêng một file, xoá được từng nguồn.

Chạy giống nhau trên PowerShell và bash (CLAUDE.md mục 1).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

ROOT = Path(__file__).resolve().parent.parent

# Thư mục xoá được mà KHÔNG mất dữ liệu gốc: chỉ là kết quả tra cứu, gọi lại là có.
DISPOSABLE_CACHES = [
    ROOT / "data_pipeline" / "data_raw" / ".wikipedia_dish_cache",
    ROOT / "data_pipeline" / "data_raw" / ".osm_cache",
]

# Thư mục thuộc tính năng ĐÃ TẠM DỪNG. Không tự xoá - chỉ báo để chủ dự án quyết định,
# đúng CLAUDE.md mục 8 (xoá thứ đang tồn tại thì phải hỏi trước).
PAUSED_FEATURE_DIRS = [
    (
        ROOT / "data_pipeline" / "data_raw" / "floorplans_yolo",
        "Ảnh huấn luyện cho tính năng floorplan -> 3D ĐÃ TẠM DỪNG "
        "(code nằm ở archive/spatial-3d/). Xoá được nếu không định làm tiếp.",
    ),
]


def dir_size(path: Path) -> int:
    """Tổng số byte trong một thư mục. Thư mục không tồn tại -> 0, không nổ."""
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            # File bị xoá giữa chừng hoặc không đọc được -> bỏ qua, đừng làm hỏng báo cáo.
            continue
    return total


def human(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num_bytes) < 1024 or unit == "GB":
            return f"{num_bytes:,.1f} {unit}" if unit != "B" else f"{num_bytes} B"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} GB"


def top_entries(path: Path, limit: int = 10) -> List[Tuple[str, int]]:
    if not path.exists():
        return []
    rows = [(child.name, dir_size(child)) for child in path.iterdir()]
    rows.sort(key=lambda r: -r[1])
    return rows[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Do dung luong du an MoodBite")
    parser.add_argument("--clean-cache", action="store_true",
                        help="Xoa cache tra cuu (lay lai duoc bang cach chay lai script)")
    args = parser.parse_args()

    raw = ROOT / "data_pipeline" / "data_raw"
    cleaned = ROOT / "data_pipeline" / "data_cleaned"

    print("=" * 68)
    print("DUNG LUONG MOODBITE")
    print("=" * 68)

    for label, path in (("data_raw   (du lieu tho)", raw),
                        ("data_cleaned (da xu ly)", cleaned)):
        print(f"{label:26s} {human(dir_size(path)):>12s}")

    print()
    print("--- 10 muc lon nhat trong data_raw ---")
    for name, size in top_entries(raw):
        print(f"  {human(size):>12s}  {name}")

    print()
    print("--- Cache tra cuu (XOA DUOC, lay lai bang cach chay lai) ---")
    cache_total = 0
    for path in DISPOSABLE_CACHES:
        size = dir_size(path)
        cache_total += size
        count = len(list(path.glob("*.json"))) if path.exists() else 0
        print(f"  {human(size):>12s}  {path.name}  ({count} file)")
    print(f"  {human(cache_total):>12s}  TONG cache xoa duoc")

    print()
    print("--- Tinh nang DA TAM DUNG (khong tu xoa, chu du an tu quyet) ---")
    for path, note in PAUSED_FEATURE_DIRS:
        size = dir_size(path)
        if size == 0:
            continue
        print(f"  {human(size):>12s}  {path.name}")
        print(f"                {note}")
        print(f"                Xoa bang: Remove-Item -Recurse -Force \"{path}\"")

    try:
        usage = shutil.disk_usage(ROOT)
        print()
        print(f"O dia: con trong {human(usage.free)} / {human(usage.total)}")
    except OSError:
        pass

    if args.clean_cache:
        freed = 0
        for path in DISPOSABLE_CACHES:
            size = dir_size(path)
            if size and path.exists():
                shutil.rmtree(path, ignore_errors=True)
                freed += size
        print()
        print(f"Da xoa cache, giai phong {human(freed)}.")
        print("Lan chay sau se goi mang lai - khong mat du lieu goc nao.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

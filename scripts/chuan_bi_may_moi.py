"""DỰNG MÔI TRƯỜNG TRÊN MÁY MỚI — một lệnh, chạy được ở mọi shell.

    python scripts/chuan_bi_may_moi.py            # kiểm tra + hướng dẫn, KHÔNG tự cài
    python scripts/chuan_bi_may_moi.py --cai      # cài luôn thư viện Python + npm
    python scripts/chuan_bi_may_moi.py --cai --du-lieu   # + tải cả dữ liệu về

VẤN ĐỀ NÀY GIẢI QUYẾT
---------------------
`git clone`/`git pull` trên máy thứ hai KHÔNG cho ra một dự án chạy được, vì ba thứ cần
thiết đều nằm ngoài git — hoàn toàn cố ý:
    thư viện Python   -> `requirements.txt` có, nhưng chưa ai cài
    node_modules      -> .gitignore (hàng trăm MB)
    dữ liệu quán/món  -> .gitignore (~39MB, là dữ liệu dẫn xuất)
    .env.local        -> .gitignore (chứa secret — KHÔNG được lên git)

Script này kiểm đủ bốn thứ đó và nói CHÍNH XÁC còn thiếu gì, thay vì để người dùng lần
mò qua từng thông báo lỗi.

VÌ SAO LÀ PYTHON CHỨ KHÔNG PHẢI .bat/.sh: `CLAUDE.md` mục 1 — máy chủ dự án chạy
PowerShell 5.1, ở đó `&&` là lỗi cú pháp và `grep`/`cat` không tồn tại. Python chạy giống
hệt nhau ở mọi shell nên chỉ phải viết một bản.

MẶC ĐỊNH LÀ CHỈ KIỂM TRA, không tự cài. Tự chạy `npm install` trên máy công ty của người
khác là việc không nên làm mà không hỏi.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DAT = "  [ OK ]"
THIEU = "  [THIẾU]"


def _chay(lenh: list[str], cwd: Path = ROOT) -> bool:
    print(f"    $ {' '.join(lenh)}")
    return subprocess.run(lenh, cwd=str(cwd)).returncode == 0


def kiem_python() -> bool:
    try:
        import fastapi  # noqa: F401
        import pandas  # noqa: F401
        import sklearn  # noqa: F401
    except ImportError as exc:
        print(f"{THIEU} Thư viện Python — {exc.name} chưa có")
        print("          pip install -r requirements.txt")
        return False
    print(f"{DAT} Thư viện Python (fastapi · pandas · scikit-learn)")
    return True


def kiem_node() -> bool:
    if shutil.which("node") is None:
        print(f"{THIEU} Node.js chưa cài — tải ở https://nodejs.org (bản LTS)")
        return False
    if not (ROOT / "frontend" / "node_modules").exists():
        print(f"{THIEU} node_modules — chạy: npm install (trong thư mục frontend)")
        return False
    print(f"{DAT} Node.js + node_modules")
    return True


def kiem_du_lieu() -> bool:
    can = [
        ROOT / "data_pipeline" / "data_cleaned" / "moodbite.db",
        ROOT / "data_pipeline" / "data_cleaned" / "dish_catalog.json",
    ]
    thieu = [p for p in can if not p.exists()]
    if thieu:
        print(f"{THIEU} Dữ liệu quán/món ({len(thieu)}/{len(can)} file chính chưa có)")
        print("          python scripts/dong_bo_du_lieu.py --tai")
        return False
    print(f"{DAT} Dữ liệu quán/món")
    return True


def kiem_env() -> bool:
    """`.env.local` KHÔNG nằm trong git — cố ý, vì nó chứa secret."""
    if not (ROOT / ".env.local").exists():
        print(f"{THIEU} .env.local — chép từ mẫu rồi điền:")
        print("          copy .env.example .env.local        (PowerShell)")
        print("       ⚠️ Sinh secret bằng:")
        print('          python -c "import secrets; print(secrets.token_hex(32))"')
        print("          rồi DÁN KẾT QUẢ, đừng dán chính câu lệnh — lỗi này đã xảy ra thật.")
        return False
    print(f"{DAT} .env.local")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Dung moi truong MoodBite tren may moi")
    parser.add_argument("--cai", action="store_true", help="Cai thu vien Python va npm")
    parser.add_argument("--du-lieu", action="store_true", help="Tai luon du lieu ve")
    args = parser.parse_args()

    print("=" * 66)
    print("CHUẨN BỊ MÁY MỚI CHO MOODBITE")
    print("=" * 66)
    print(f"  Thư mục dự án: {ROOT}")
    print(f"  Python       : {sys.version.split()[0]}")
    print()

    if args.cai:
        print("  Đang cài thư viện Python...")
        _chay([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        if shutil.which("npm"):
            print("  Đang cài gói frontend...")
            # `shell=True` trên Windows vì `npm` là file .cmd, không phải .exe.
            subprocess.run("npm install", cwd=str(ROOT / "frontend"), shell=True)
        print()

    if args.du_lieu:
        print("  Đang tải dữ liệu...")
        _chay([sys.executable, "scripts/dong_bo_du_lieu.py", "--tai"])
        print()

    ket_qua = [kiem_python(), kiem_node(), kiem_du_lieu(), kiem_env()]

    print()
    print("=" * 66)
    if all(ket_qua):
        print("SẴN SÀNG. Chạy app:  python scripts/run_dev.py")
        print("Kiểm tra toàn bộ  :  python scripts/verify.py")
        return 0
    print(f"CÒN THIẾU {ket_qua.count(False)} mục — xem hướng dẫn ở trên.")
    print("Cài tự động       :  python scripts/chuan_bi_may_moi.py --cai --du-lieu")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

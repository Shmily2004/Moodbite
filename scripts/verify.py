"""Kiểm tra TOÀN BỘ dự án bằng MỘT lệnh duy nhất.

    python scripts/verify.py

VÌ SAO CÓ FILE NÀY: tài liệu trước đây ghi 4 lệnh nối bằng `&&`, chỉ chạy được trên
bash/macOS/Linux. PowerShell 5.1 (mặc định trên Windows) KHÔNG hỗ trợ `&&`, cũng không có
`grep`/`wc`. Viết bằng Python thì chạy được ở mọi nơi, không cần nhớ cú pháp shell nào.

Kiểm 5 việc:
  1. App FastAPI dựng được               (bug từng làm app không khởi động được)
  2. Toàn bộ test xanh
  3. Hướng phụ thuộc Clean Architecture đúng
  4. CHỈ CÓ MỘT backend                   (không có backend thứ hai lẻn vào)
  5. Frontend build được                  (bỏ qua nếu chưa cài node_modules)

Thoát mã 0 = tất cả đạt. Khác 0 = có mục hỏng, xem chi tiết ở output.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Windows console mặc định là cp1252, in emoji/tick sẽ nổ UnicodeEncodeError.
# Dùng ký tự ASCII cho chắc chắn chạy được ở mọi terminal.
PASS, FAIL, SKIP = "[ OK ]", "[FAIL]", "[SKIP]"


def run(cmd: list[str], cwd: Path = ROOT) -> tuple[int, str]:
    """Chạy lệnh, trả (mã thoát, output). Không ném exception."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", env=env,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except FileNotFoundError as exc:
        return 127, str(exc)


def check_app_boots() -> tuple[bool, str]:
    code, out = run([
        sys.executable, "-c",
        "from src.presentation.api.main import create_app; create_app()",
    ])
    if code != 0:
        return False, out.strip()[-800:]
    counts = [ln for ln in out.splitlines() if "khoi dong" in ln or "khởi động" in ln]
    return True, counts[-1].split(": ", 1)[-1] if counts else "app dung duoc"


def check_tests() -> tuple[bool, str]:
    code, out = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"])
    summary = next(
        (ln.strip() for ln in reversed(out.splitlines())
         if " passed" in ln or " failed" in ln or " error" in ln),
        "khong doc duoc ket qua",
    )
    if code != 0:
        failed = [ln for ln in out.splitlines() if ln.startswith("FAILED")][:10]
        return False, summary + ("\n        " + "\n        ".join(failed) if failed else "")
    return True, summary


def check_architecture() -> tuple[bool, str]:
    code, out = run([sys.executable, str(ROOT / "scripts" / "check_architecture.py")])
    lines = [ln for ln in out.splitlines() if ln.strip()]
    return code == 0, (lines[-1] if lines else "khong co output")


def check_single_backend() -> tuple[bool, str]:
    """Chỉ được có MỘT backend. Xem CLAUDE.md muc -1."""
    problems: list[str] = []

    apps = [
        p for p in (ROOT / "src").rglob("*.py")
        if "FastAPI(" in p.read_text(encoding="utf-8", errors="ignore")
    ]
    if len(apps) != 1:
        problems.append(f"co {len(apps)} noi tao FastAPI (phai = 1): "
                        f"{[str(p.relative_to(ROOT)) for p in apps]}")

    stray_ts = [
        p for p in ROOT.rglob("*.ts")
        if not any(part in ("archive", "node_modules", ".git") for part in p.parts)
    ]
    if stray_ts:
        problems.append(f"co {len(stray_ts)} file .ts ngoai archive/ (phai = 0): "
                        f"{[str(p.relative_to(ROOT)) for p in stray_ts[:5]]}")

    if (ROOT / "package.json").exists():
        problems.append("co package.json o thu muc goc (phai khong co)")

    if problems:
        return False, "\n        ".join(problems)
    return True, "1 app FastAPI, 0 file .ts ngoai archive/, khong co package.json o goc"


def check_frontend() -> tuple[bool, str] | tuple[None, str]:
    frontend = ROOT / "frontend"
    if not (frontend / "node_modules").exists():
        return None, "chua cai node_modules - chay: cd frontend; npm install"
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        return None, "khong tim thay npm trong PATH"

    code, out = run([npm, "run", "build"], cwd=frontend)
    if code != 0:
        return False, out.strip()[-800:]
    built = next((ln.strip() for ln in out.splitlines() if "built in" in ln), "build xong")
    return True, built


CHECKS = [
    ("1. App FastAPI dung duoc", check_app_boots),
    ("2. Test", check_tests),
    ("3. Clean Architecture", check_architecture),
    ("4. Chi mot backend", check_single_backend),
    ("5. Frontend build", check_frontend),
]


def main() -> int:
    print("=" * 68)
    print("KIEM TRA DU AN MOODBITE")
    print("=" * 68)

    failures = 0
    skipped = 0

    for label, check in CHECKS:
        try:
            ok, detail = check()
        except Exception as exc:  # bản thân checker hỏng cũng phải báo, không được im
            ok, detail = False, f"checker loi: {type(exc).__name__}: {exc}"

        if ok is None:
            mark, skipped = SKIP, skipped + 1
        elif ok:
            mark = PASS
        else:
            mark, failures = FAIL, failures + 1

        print(f"\n{mark} {label}")
        for line in str(detail).splitlines():
            print(f"        {line}")

    print("\n" + "=" * 68)
    if failures:
        print(f"KET QUA: {failures} muc HONG. Sua truoc khi danh dau xong trong "
              f"PROJECT_CHECKLIST.md")
    else:
        print("KET QUA: TAT CA DAT."
              + (f" ({skipped} muc bo qua)" if skipped else ""))
    print("=" * 68)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

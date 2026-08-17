"""Kiểm tra TOÀN BỘ dự án bằng MỘT lệnh duy nhất.

    python scripts/verify.py

VÌ SAO CÓ FILE NÀY: tài liệu trước đây ghi 4 lệnh nối bằng `&&`, chỉ chạy được trên
bash/macOS/Linux. PowerShell 5.1 (mặc định trên Windows) KHÔNG hỗ trợ `&&`, cũng không có
`grep`/`wc`. Viết bằng Python thì chạy được ở mọi nơi, không cần nhớ cú pháp shell nào.

Kiểm 8 việc:
  1. App FastAPI dựng được               (bug từng làm app không khởi động được)
  2. Toàn bộ test xanh
  3. Hướng phụ thuộc Clean Architecture đúng
  4. CHỈ CÓ MỘT backend                   (không có backend thứ hai lẻn vào)
  5. Frontend build được                  (bỏ qua nếu chưa cài node_modules)
  6. Frontend test xanh
  7. Luật import Feature-Sliced Design
  8. CI cài đặt được                      (lockfile + đường dẫn trong ci.yml)

Thoát mã 0 = tất cả đạt. Khác 0 = có mục hỏng, xem chi tiết ở output.
"""
from __future__ import annotations

import os
import re
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


# Dấu hiệu của một SERVER lẻn vào frontend. TypeScript trong `frontend/` là ĐÚNG
# (frontend dùng TS theo kiến trúc đã chốt) - thứ bị cấm là code CHẠY PHÍA SERVER.
SERVER_SIGNATURES = (
    "express(", "fastify(", "createServer(", "next/server",
    "@nestjs", "from 'http'", 'from "http"',
)


def check_single_backend() -> tuple[bool, str]:
    """Chỉ được có MỘT backend. Xem CLAUDE.md muc -1.

    LƯU Ý: luật này KHÔNG cấm TypeScript - frontend dùng TypeScript theo đúng kiến trúc
    đã chốt. Thứ bị cấm là một SERVER thứ hai, dù viết bằng ngôn ngữ gì.
    """
    problems: list[str] = []

    apps = [
        p for p in (ROOT / "src").rglob("*.py")
        if "FastAPI(" in p.read_text(encoding="utf-8", errors="ignore")
    ]
    if len(apps) != 1:
        problems.append(f"co {len(apps)} noi tao FastAPI (phai = 1): "
                        f"{[str(p.relative_to(ROOT)) for p in apps]}")

    # TypeScript chỉ được nằm trong frontend/ (hoặc archive/).
    stray_ts = [
        p for p in ROOT.rglob("*.ts")
        if not any(part in ("archive", "node_modules", ".git", "frontend") for part in p.parts)
    ]
    if stray_ts:
        problems.append(f"co {len(stray_ts)} file .ts ngoai frontend/ va archive/: "
                        f"{[str(p.relative_to(ROOT)) for p in stray_ts[:5]]}")

    # Frontend KHÔNG được chứa code chạy phía server.
    frontend_src = ROOT / "frontend"
    server_files: list[str] = []
    if frontend_src.exists():
        for pattern in ("*.ts", "*.tsx", "*.js", "*.jsx"):
            for p in frontend_src.rglob(pattern):
                if any(part in ("node_modules", "dist", ".vite") for part in p.parts):
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
                if any(sig in text for sig in SERVER_SIGNATURES):
                    server_files.append(str(p.relative_to(ROOT)))
    if server_files:
        problems.append(f"frontend chua code SERVER (backend thu hai): {server_files[:5]}")

    if (ROOT / "package.json").exists():
        problems.append("co package.json o thu muc goc (phai khong co)")

    if problems:
        return False, "\n        ".join(problems)
    return True, "1 app FastAPI, khong co server thu hai, khong co package.json o goc"


def check_frontend() -> tuple[bool, str] | tuple[None, str]:
    """Build + test + kiem tra kien truc FSD cua frontend."""
    frontend = ROOT / "frontend"
    if not (frontend / "node_modules").exists():
        return None, "chua cai node_modules - chay: cd frontend; npm install"
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        return None, "khong tim thay npm trong PATH"

    # Kiểm kiểu TRƯỚC build: `npm run build` chỉ chạy tsc cho `apps/client`, không phủ
    # `packages/**` và `steiger.config.ts` (thuộc project gốc `frontend/tsconfig.json`).
    code, out = run([npm, "run", "typecheck"], cwd=frontend)
    if code != 0:
        errors = [ln.strip() for ln in out.splitlines() if ": error TS" in ln]
        return False, "TYPECHECK LOI:\n        " + "\n        ".join(errors[:8] or [out.strip()[-500:]])

    code, out = run([npm, "run", "build"], cwd=frontend)
    if code != 0:
        return False, "BUILD LOI:\n" + out.strip()[-700:]
    built = next((ln.strip() for ln in out.splitlines() if "built in" in ln), "build xong")
    return True, "typecheck OK · " + built


def check_frontend_tests() -> tuple[bool, str] | tuple[None, str]:
    frontend = ROOT / "frontend"
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not (frontend / "node_modules").exists() or not npm:
        return None, "bo qua - chua cai node_modules"

    # Chạy test của CẢ HAI app. App admin trước đây có 0 test - nghĩa là màn hình trắng
    # ở trang quản trị sẽ lọt qua CI mà không ai biết.
    ket_qua: list[str] = []
    hong = False
    for app in ("client", "admin"):
        code, out = run(
            [npm, "run", "test", "--workspace", f"@moodbite/{app}"], cwd=frontend
        )
        summary = next(
            (ln.strip() for ln in out.splitlines()
             if "Tests " in ln and ("passed" in ln or "failed" in ln)),
            "khong doc duoc ket qua",
        )
        ket_qua.append(f"{app}: {summary}")
        hong = hong or code != 0
    return not hong, " · ".join(ket_qua)


def check_frontend_architecture() -> tuple[bool, str] | tuple[None, str]:
    """Cuong che luat import Feature-Sliced Design - ban tuong duong cua
    check_architecture.py o phia backend."""
    frontend = ROOT / "frontend"
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not (frontend / "node_modules").exists() or not npx:
        return None, "bo qua - chua cai node_modules"

    # Kiểm CẢ HAI app. Bỏ sót app admin nghĩa là kiến trúc chỉ được canh một nửa.
    problems: list[str] = []
    for app in ("client", "admin"):
        code, out = run([npx, "steiger", f"./apps/{app}/src", "--no-watch"], cwd=frontend)
        if code != 0:
            found = [ln.strip() for ln in out.splitlines() if "×" in ln or "Found" in ln]
            problems.append(f"apps/{app}: " + ("; ".join(found[-4:]) or out.strip()[-300:]))
    if problems:
        return False, "\n        ".join(problems)
    return True, "FSD OK (client + admin): khong vi pham luat import"


def check_ci_installable() -> tuple[bool, str]:
    """CI cai dat duoc — bat loi ma 5 muc tren KHONG the bat.

    VI SAO CO MUC NAY (bug that, 2026-08-17): luc chuyen frontend sang monorepo,
    `frontend/package-lock.json` bi xoa. May local van xanh het vi `node_modules` da
    cai san tu truoc, nhung CI chay `npm ci` tren may sach — ma `npm ci` BAT BUOC phai
    co lockfile, va `actions/setup-node` cung loi neu `cache-dependency-path` tro vao
    file khong ton tai. Ket qua: verify.py bao "TAT CA DAT" trong khi CI chac chan do.

    Doc ci.yml bang regex, khong dung PyYAML — de script chay duoc ma khong can cai them.
    """
    problems: list[str] = []

    # Moi workspace root (package.json co khoa "workspaces") phai co lockfile di kem,
    # neu khong `npm ci` khong the chay.
    for pkg in ROOT.rglob("package.json"):
        if any(part in ("node_modules", "archive", ".git") for part in pkg.parts):
            continue
        if '"workspaces"' not in pkg.read_text(encoding="utf-8", errors="ignore"):
            continue
        if not (pkg.parent / "package-lock.json").exists():
            problems.append(
                f"thieu {pkg.parent.relative_to(ROOT)}/package-lock.json "
                f"-> `npm ci` trong CI se loi. Sinh lai: cd "
                f"{pkg.parent.relative_to(ROOT)}; npm install --package-lock-only"
            )

    ci = ROOT / ".github" / "workflows" / "ci.yml"
    if ci.exists():
        text = ci.read_text(encoding="utf-8", errors="ignore")
        for rel in re.findall(r"cache-dependency-path:\s*(\S+)", text):
            rel = rel.strip("'\"")
            if not (ROOT / rel).exists():
                problems.append(f"ci.yml tro vao file khong ton tai: {rel}")

    if problems:
        return False, "\n        ".join(problems)
    return True, "lockfile day du, moi duong dan trong ci.yml deu ton tai"


CHECKS = [
    ("1. App FastAPI dung duoc", check_app_boots),
    ("2. Test", check_tests),
    ("3. Clean Architecture", check_architecture),
    ("4. Chi mot backend", check_single_backend),
    ("5. Frontend typecheck + build", check_frontend),
    ("6. Frontend test", check_frontend_tests),
    ("7. Frontend FSD", check_frontend_architecture),
    ("8. CI cai dat duoc", check_ci_installable),
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

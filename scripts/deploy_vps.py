"""Cập nhật MÔI TRƯỜNG PRODUCTION (VPS) bằng MỘT lệnh, chạy từ máy Windows của bạn.

    python scripts/deploy_vps.py status              # xem phiên bản + sức khoẻ, KHÔNG đổi gì
    python scripts/deploy_vps.py backend             # git pull + pip + khởi động lại backend
    python scripts/deploy_vps.py frontend            # build giao diện + chép lên VPS
    python scripts/deploy_vps.py data                # backend + dựng lại SQLite và danh mục món
    python scripts/deploy_vps.py all                 # backend + frontend
    python scripts/deploy_vps.py backup              # kéo bản sao lưu tài khoản về backups/
    python scripts/deploy_vps.py rollback <commit>   # đưa VPS về một commit cũ

Địa chỉ VPS: `--host root@tenmien` hoặc biến môi trường MOODBITE_DEPLOY_HOST. CỐ Ý không có
giá trị mặc định: lệnh nào cũng chạm vào máy thật, nhầm máy là lỗi không đảo ngược được.

Thêm `--dry-run` để chỉ IN các lệnh sẽ chạy mà không chạm vào VPS. Hướng dẫn đầy đủ:
`docs/cap_nhat_production.md`.

VÌ SAO CÓ FILE NÀY: mỗi lần cập nhật phải nhớ 5-6 lệnh ở hai nơi (Windows và VPS), và bỏ sót
một bước thì production lệch với git mà không ai thấy. Đã thấy thật khi soạn
`docs/trien_khai_vps.md`: build frontend bằng Git Bash nhúng sai địa chỉ API
(`D:/Git/api/v1`) mà build vẫn báo thành công.

Chỉ dùng thư viện chuẩn, và chạy được trên PowerShell 5.1 y như trên bash (CLAUDE.md mục 1).
Mọi dòng `print` cố ý KHÔNG DẤU: console PowerShell 5.1 hay chạy bảng mã cũ, in chữ có dấu có
thể nổ UnicodeEncodeError.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
CLIENT_DIR = FRONTEND_DIR / "apps" / "client"
BACKUP_DIR = ROOT / "backups"

# Khớp đúng `docs/trien_khai_vps.md`. Đổi ở đây thì phải đổi cả ở đó.
REMOTE_APP_DIR = "/opt/moodbite"
REMOTE_WEB_DIR = "/var/www/moodbite"
SERVICE_USER = "moodbite"
SERVICE_NAME = "moodbite"
REMOTE_HEALTH_URL = "http://127.0.0.1:8001/health"
REMOTE_USERS_DB = "data_pipeline/data_cleaned/moodbite_users.db"

# Địa chỉ API TƯƠNG ĐỐI: frontend gọi API cùng domain nó đang chạy, nên build một lần dùng
# được cho mọi domain. Giá trị này bị NHÚNG CỨNG vào file build.
RELATIVE_API_BASE = "/api/v1"

# Backend dựng chỉ mục tìm kiếm mất ~15 giây trên máy Windows (đo 2026-11-09), VPS 2 vCPU có
# thể lâu hơn. 45 lần x 2 giây = 90 giây: đủ rộng để không báo lỗi oan, đủ hẹp để không treo.
HEALTH_ATTEMPTS = 45
HEALTH_INTERVAL_SECONDS = 2

# ServerAlive: pip/build trên VPS có lúc im lặng cả phút, thiếu nó thì mạng nhà bị cắt ngang.
SSH_OPTIONS = ["-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=30"]

# Chặn chuỗi bắt đầu bằng '-' (bị ssh hiểu thành tuỳ chọn) và mọi ký tự lạ.
HOST_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*@[A-Za-z0-9][A-Za-z0-9.-]*$")
COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")
# Địa chỉ bị Git Bash đổi thành đường dẫn Windows, ví dụ `D:/Git/api/v1`. Chữ cái phải đứng
# riêng (không dính chữ khác) để KHÔNG khớp nhầm `http://localhost:8001/api/v1`.
MANGLED_API_BASE_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:/(?!/)[^\"'\s]*api/v1")

MODES = ("status", "backend", "frontend", "data", "all", "backup", "rollback")
# Chế độ nào có sao lưu tài khoản trước khi đổi gì đó trên VPS.
MODES_WITH_BACKUP = ("backend", "data", "all")


def say(message: str = "") -> None:
    print(message, flush=True)


# --- Lệnh chạy TRÊN VPS ---------------------------------------------------------------------
# QUY TẮC: không được có dấu nháy kép `"` trong chuỗi lệnh. Lệnh đi qua ssh.exe của Windows,
# nơi dấu nháy kép bị đổi thành `\"` và không chắc remote bóc lại đúng. Dùng nháy đơn.
# Có test khoá quy tắc này (tests/test_deploy_vps.py).


def parse_host(host: str) -> tuple[str, str]:
    """`root@luunguyet.id.vn` -> (`root@luunguyet.id.vn`, `luunguyet.id.vn`)."""
    if not HOST_RE.match(host or ""):
        raise ValueError(
            "Thieu hoac sai dia chi VPS. Dung --host root@tenmien hoac dat bien moi truong "
            "MOODBITE_DEPLOY_HOST (vi du root@luunguyet.id.vn)."
        )
    return host, host.split("@", 1)[1]


def as_app_user(command: str) -> str:
    # Chạy bằng user `moodbite` để file sinh ra thuộc về nó, đúng như lúc triển khai lần đầu.
    return f"sudo -u {SERVICE_USER} {command}"


def _short_head() -> str:
    return f"$({as_app_user('git rev-parse --short HEAD')})"


def wait_for_health_snippet() -> str:
    """Đợi backend trả lời /health; hết giờ thì in log và thoát lỗi."""
    return (
        f"ok=0; for i in $(seq 1 {HEALTH_ATTEMPTS}); do "
        f"if curl -fsS {REMOTE_HEALTH_URL} > /dev/null 2>&1; then ok=1; break; fi; "
        f"sleep {HEALTH_INTERVAL_SECONDS}; done; "
        "if [ $ok -ne 1 ]; then echo HEALTH_FAIL; "
        f"journalctl -u {SERVICE_NAME} -n 40 --no-pager; exit 1; fi; echo HEALTH_OK"
    )


def backend_command(with_data: bool) -> str:
    steps = [
        "set -e",
        # `cd` TRƯỚC mọi `sudo -u`: user moodbite không vào được /root, mà Python/pip gọi
        # getcwd() nên lỗi "Permission denied" nếu đứng ở đó.
        f"cd {REMOTE_APP_DIR}",
        f"echo TRUOC={_short_head()}",
        # Sau `rollback` VPS đang ở trạng thái detached HEAD, `pull` sẽ từ chối. Về main trước.
        as_app_user("git checkout -q main"),
        # --ff-only: nếu VPS lệch git (ai đó sửa tay) thì DỪNG, không tự gộp rồi sinh xung đột.
        as_app_user("git pull --ff-only"),
        as_app_user(".venv/bin/pip install -q -r requirements.txt"),
    ]
    if with_data:
        steps += [
            # --keep-hidden: giữ các quán admin đã ẩn. moodbite_users.db không bị đụng tới.
            as_app_user(".venv/bin/python scripts/build_sqlite.py --keep-hidden"),
            as_app_user(".venv/bin/python scripts/build_dish_catalog.py"),
        ]
    steps += [
        f"systemctl restart {SERVICE_NAME}",
        f"echo SAU={_short_head()}",
        wait_for_health_snippet(),
    ]
    return "; ".join(steps)


def rollback_command(commit: str) -> str:
    return "; ".join(
        [
            "set -e",
            f"cd {REMOTE_APP_DIR}",
            f"echo TRUOC={_short_head()}",
            as_app_user(f"git checkout -q {commit}"),
            f"systemctl restart {SERVICE_NAME}",
            f"echo SAU={_short_head()}",
            wait_for_health_snippet(),
        ]
    )


def status_command() -> str:
    return "; ".join(
        [
            f"cd {REMOTE_APP_DIR}",
            f"echo COMMIT={_short_head()}",
            f"echo BACKEND=$(systemctl is-active {SERVICE_NAME})",
            "echo CADDY=$(systemctl is-active caddy)",
            "free -h",
        ]
    )


def frontend_install_command(tmp_dir: str) -> str:
    # `/.` ở cuối là chủ ý: chép NỘI DUNG chứ không chép cả thư mục. KHÔNG xoá thư mục web
    # cũ: người đang mở sẵn một tab bản cũ vẫn tải được các file JS cũ (giao diện nạp theo
    # nhu cầu). File thừa tích lại dần, dọn tay thỉnh thoảng là đủ.
    return "; ".join(
        [
            "set -e",
            f"mkdir -p {REMOTE_WEB_DIR}",
            f"cp -r {tmp_dir}/. {REMOTE_WEB_DIR}/",
            f"rm -rf {tmp_dir}",
            f"ls {REMOTE_WEB_DIR}",
        ]
    )


def backup_command(remote_file: str) -> str:
    # `.backup()` của sqlite3 an toàn khi file đang được ghi (khác chép file thô). Đường dẫn
    # truyền qua argv để trong mã Python KHÔNG có dấu nháy kép.
    code = (
        "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); "
        "s.backup(d); d.close(); s.close()"
    )
    return "; ".join(
        [
            "set -e",
            f"cd {REMOTE_APP_DIR}",
            as_app_user(f".venv/bin/python -c '{code}' {REMOTE_USERS_DB} {remote_file}"),
            # File chứa chuỗi băm mật khẩu: không để người khác trên máy đọc được dù chỉ vài giây.
            f"chmod 600 {remote_file}",
        ]
    )


# --- Kiểm tra bản build và site thật --------------------------------------------------------


def check_dist(dist: Path) -> list[str]:
    """Danh sách vấn đề của bản build (rỗng = dùng được)."""
    problems: list[str] = []
    if not (dist / "index.html").is_file():
        problems.append(f"thieu index.html trong {dist}")
    js_files = sorted((dist / "assets").glob("*.js"))
    if not js_files:
        return problems + ["khong co file JS nao trong assets/"]
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in js_files)
    if f'"{RELATIVE_API_BASE}"' not in text:
        problems.append(
            f"khong thay dia chi API tuong doi \"{RELATIVE_API_BASE}\" trong file build "
            "(VITE_API_BASE chua duoc dat?)"
        )
    mangled = MANGLED_API_BASE_RE.search(text)
    if mangled:
        problems.append(
            f"dia chi API bi doi thanh duong dan Windows ({mangled.group(0)}): "
            "chay lai bang PowerShell, khong dung Git Bash"
        )
    return problems


def fetch(url: str, timeout: int = 20) -> tuple[int, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "moodbite-deploy/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, response.headers.get("Content-Type", ""), body


def verify_public(base_url: str) -> list[str]:
    """Hỏi site THẬT từ bên ngoài, giống người dùng thấy (HTTPS, Caddy, backend, đều qua)."""
    problems: list[str] = []
    try:
        status, content_type, _ = fetch(f"{base_url}/")
        if status != 200 or "text/html" not in content_type:
            problems.append(f"trang chu tra ve {status} ({content_type or 'khong ro loai'})")
    except (urllib.error.URLError, OSError) as exc:
        problems.append(f"khong mo duoc {base_url}/: {exc}")
    try:
        _, _, body = fetch(f"{base_url}{RELATIVE_API_BASE}/health")
        payload = json.loads(body)
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict) or data.get("status") != "ok":
            problems.append("/api/v1/health khong bao status=ok")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        problems.append(f"/api/v1/health loi: {exc}")
    return problems


# --- Chạy lệnh ------------------------------------------------------------------------------


def _tool(name: str, dry_run: bool) -> str:
    found = shutil.which(name)
    if found:
        return found
    if dry_run:
        return name
    raise SystemExit(
        f"Khong thay lenh '{name}'. Windows 10/11: Settings > Apps > Optional features > "
        "them 'OpenSSH Client'."
    )


def run(command: list[str], dry_run: bool, cwd: Path | None = None) -> int:
    shown = " ".join(f'"{part}"' if " " in part else part for part in command)
    say(f"  $ {shown}")
    if dry_run:
        return 0
    return subprocess.run(command, cwd=cwd).returncode


def ssh(host: str, remote_command: str, dry_run: bool) -> int:
    return run([_tool("ssh", dry_run), *SSH_OPTIONS, host, remote_command], dry_run)


def scp(arguments: list[str], dry_run: bool, cwd: Path) -> int:
    return run([_tool("scp", dry_run), *SSH_OPTIONS, *arguments], dry_run, cwd=cwd)


def git_output(*args: str) -> str | None:
    try:
        done = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return done.stdout.strip()


def git_warnings(mode: str) -> list[str]:
    """Những điều hay quên: VPS chỉ lấy nhánh main trên GitHub, không thấy máy bạn."""
    warnings: list[str] = []
    branch = git_output("branch", "--show-current")
    if branch and branch != "main":
        warnings.append(f"Ban dang o nhanh '{branch}', VPS chi lay nhanh main.")
    if mode in ("backend", "data", "all"):
        git_output("fetch", "-q", "origin")
        ahead = git_output("rev-list", "--count", "origin/main..HEAD")
        if ahead and ahead.isdigit() and int(ahead) > 0:
            warnings.append(f"Co {ahead} commit CHUA push len GitHub: VPS se khong thay chung.")
    if git_output("status", "--porcelain"):
        if mode in ("frontend", "all"):
            warnings.append("Co thay doi chua commit: giao dien se build tu chung, lech voi git.")
        else:
            warnings.append("Co thay doi chua commit: chung KHONG duoc dua len VPS.")
    return warnings


# --- Các bước -------------------------------------------------------------------------------


def step_backup(host: str, dry_run: bool) -> bool:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    remote_file = f"/tmp/mb_users_{stamp}.db"
    local_file = BACKUP_DIR / f"moodbite_users_{stamp}.db"
    say(f"[SAO LUU] tai khoan -> {local_file.relative_to(ROOT)}")
    if not dry_run:
        BACKUP_DIR.mkdir(exist_ok=True)
    if ssh(host, backup_command(remote_file), dry_run) != 0:
        return False
    # Đường dẫn TƯƠNG ĐỐI (cwd=ROOT): `E:\...` có dấu hai chấm, scp dễ hiểu nhầm là máy `E`.
    pulled = scp([f"{host}:{remote_file}", str(local_file.relative_to(ROOT))], dry_run, ROOT)
    ssh(host, f"rm -f {remote_file}", dry_run)
    return pulled == 0


def step_backend(host: str, with_data: bool, dry_run: bool) -> bool:
    say("[BACKEND] git pull + pip + khoi dong lai" + (" + dung lai du lieu" if with_data else ""))
    return ssh(host, backend_command(with_data), dry_run) == 0


def step_frontend(host: str, dry_run: bool) -> bool:
    say("[FRONTEND] build + chep len VPS")
    env = dict(os.environ, VITE_API_BASE=RELATIVE_API_BASE)
    # Đặt biến cho TIẾN TRÌNH CON bằng Python, không qua Git Bash: không bị đổi thành `D:/Git/...`.
    say("  $ npm run build   (VITE_API_BASE=" + RELATIVE_API_BASE + ")")
    if not dry_run:
        if not (FRONTEND_DIR / "node_modules").exists():
            say("[LOI] Chua cai thu vien frontend. Chay: cd frontend, roi npm install")
            return False
        if subprocess.run("npm run build", cwd=FRONTEND_DIR, shell=True, env=env).returncode != 0:
            return False
        problems = check_dist(CLIENT_DIR / "dist")
        if problems:
            say("[LOI] Ban build khong dung, DUNG chep len VPS:")
            for problem in problems:
                say(f"  - {problem}")
            return False
        say("  Ban build dung (dia chi API tuong doi, khong bi doi thanh duong dan Windows).")
    tmp_dir = f"/tmp/moodbite_dist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if scp(["-r", "dist", f"{host}:{tmp_dir}"], dry_run, CLIENT_DIR) != 0:
        return False
    return ssh(host, frontend_install_command(tmp_dir), dry_run) == 0


def plan_steps(mode: str, skip_backup: bool) -> list[str]:
    backup = [] if skip_backup or mode not in MODES_WITH_BACKUP else ["backup"]
    return {
        "status": ["status"],
        "backup": ["backup"],
        "backend": backup + ["backend"],
        "data": backup + ["data"],
        "frontend": ["frontend"],
        "all": backup + ["backend", "frontend"],
        "rollback": ["rollback"],
    }[mode]


STEP_LABELS = {
    "status": "xem phien ban va suc khoe (khong doi gi)",
    "backup": "sao luu tai khoan ve may ban (backups/)",
    "backend": "git pull, pip, khoi dong lai backend",
    "data": "nhu backend + dung lai SQLite va danh muc mon (--keep-hidden)",
    "frontend": "build giao dien (PowerShell) + chep len VPS",
    "rollback": "dua VPS ve commit cu va khoi dong lai",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cap nhat production (VPS) cua MoodBite")
    parser.add_argument("mode", choices=MODES)
    parser.add_argument("commit", nargs="?", help="ma commit (chi dung voi rollback)")
    parser.add_argument("--host", help="vi du root@tenmien (hoac bien MOODBITE_DEPLOY_HOST)")
    parser.add_argument("--url", help="dia chi site de kiem tra (mac dinh https://<ten may>)")
    parser.add_argument("--yes", "-y", action="store_true", help="khong hoi xac nhan")
    parser.add_argument("--dry-run", action="store_true", help="chi in lenh, khong chay")
    parser.add_argument("--skip-backup", action="store_true", help="bo qua buoc sao luu")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        host, hostname = parse_host(args.host or os.environ.get("MOODBITE_DEPLOY_HOST", ""))
    except ValueError as exc:
        say(f"[LOI] {exc}")
        return 1
    if args.mode == "rollback" and not COMMIT_RE.match(args.commit or ""):
        say("[LOI] rollback can ma commit dang hex 7-40 ky tu, vi du: rollback 207f86a")
        say("      Xem ma bang: python scripts/deploy_vps.py status")
        return 1
    base_url = (args.url or f"https://{hostname}").rstrip("/")
    steps = plan_steps(args.mode, args.skip_backup)

    say("=" * 70)
    say(f"CAP NHAT PRODUCTION  ->  {host}" + ("   [DRY-RUN]" if args.dry_run else ""))
    say("=" * 70)
    for number, step in enumerate(steps, 1):
        say(f"  {number}. {STEP_LABELS[step]}")
    for warning in git_warnings(args.mode):
        say(f"[CANH BAO] {warning}")
    if not (args.yes or args.dry_run or args.mode in ("status", "backup")):
        if input("Tiep tuc? [y/N] ").strip().lower() != "y":
            say("Da huy.")
            return 1

    try:
        for step in steps:
            if step == "backup":
                ok = step_backup(host, args.dry_run)
            elif step in ("backend", "data"):
                ok = step_backend(host, step == "data", args.dry_run)
            elif step == "frontend":
                ok = step_frontend(host, args.dry_run)
            elif step == "rollback":
                say(f"[ROLLBACK] dua VPS ve {args.commit}")
                ok = ssh(host, rollback_command(args.commit), args.dry_run) == 0
            else:
                ok = ssh(host, status_command(), args.dry_run) == 0
            if not ok:
                say(f"[LOI] Buoc '{step}' that bai. Cac buoc sau KHONG duoc chay.")
                return 1
    except KeyboardInterrupt:
        say("\nDa dung giua chung. VPS co the dang o trang thai dang do: chay 'status' de xem.")
        return 130

    if args.mode != "backup" and not args.dry_run:
        say(f"[KIEM TRA] hoi site that: {base_url}")
        problems = verify_public(base_url)
        for problem in problems:
            say(f"  - {problem}")
        if problems:
            say("[LOI] Site chua tra loi dung. Xem docs/cap_nhat_production.md muc 'Khi loi'.")
            return 1
        say("  Site tra loi dung (trang chu + /api/v1/health).")
    if args.mode == "rollback":
        say("VPS dang o commit cu. Muon quay lai ban moi nhat: python scripts/deploy_vps.py backend")
    say("XONG.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

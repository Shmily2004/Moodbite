"""Chạy TOÀN BỘ MoodBite bằng MỘT lệnh: backend + app người dùng + app quản trị.

    python scripts/run_dev.py                # backend + app người dùng
    python scripts/run_dev.py --admin        # thêm cả app quản trị
    python scripts/run_dev.py --admin-only   # chỉ backend + app quản trị

VÌ SAO CÓ FILE NÀY: trước đây muốn xem giao diện phải mở 3 cửa sổ terminal và nhớ 3 lệnh
khác nhau ở 2 thư mục khác nhau. Thiếu một bước là màn hình trắng, mà KHÔNG có gì nói cho
biết là thiếu bước nào. Đó là lý do thật khiến "frontend đã xong" nhưng mở lên không thấy gì.

Script tự kiểm điều kiện trước khi chạy, và in RÕ địa chỉ để mở.
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

BACKEND_PORT = 8001
# Số cổng thử tiếp nếu cổng mặc định đang bận. 8001 -> 8002 -> ... -> 8005.
SO_CONG_THU = 5


def cong_trong(port: int) -> bool:
    """Cổng này có bind được không.

    VÌ SAO PHẢI KIỂM TRƯỚC: Windows hay để lại "socket ma" — tiến trình đã chết nhưng cổng
    vẫn ở trạng thái LISTENING và không ai nhả. Khi đó uvicorn khởi động rồi CHẾT NGAY với
    lỗi WinError 10048, còn frontend thì vẫn trỏ vào cổng cũ và chỉ báo "không kết nối được
    máy chủ" — người dùng không thể đoán ra nguyên nhân. Lỗi này đã xảy ra thật (2026-08-22).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def tim_cong_backend() -> int:
    """Trả cổng đầu tiên còn trống, bắt đầu từ 8001."""
    for port in range(BACKEND_PORT, BACKEND_PORT + SO_CONG_THU):
        if cong_trong(port):
            return port
    raise SystemExit(
        f"Cả {SO_CONG_THU} cổng {BACKEND_PORT}-{BACKEND_PORT + SO_CONG_THU - 1} đều bận. "
        "Thường là do lần chạy trước chưa tắt hẳn. Đóng các cửa sổ terminal cũ, hoặc "
        "khởi động lại máy rồi thử lại."
    )
CLIENT_PORT = 5173
ADMIN_PORT = 5174


def kiem_dieu_kien(can_admin: bool) -> list[str]:
    """Trả về danh sách vấn đề. Rỗng = chạy được."""
    van_de: list[str] = []

    if not (FRONTEND / "node_modules").exists():
        van_de.append(
            "Chưa cài thư viện frontend.\n"
            "      Sửa: cd frontend  ->  npm install"
        )

    try:
        import fastapi  # noqa: F401
    except ImportError:
        van_de.append(
            "Chưa cài thư viện Python.\n"
            "      Sửa: pip install -r requirements.txt"
        )

    from src.infrastructure.config.settings import Settings

    settings = Settings.from_env()
    if not settings.restaurants_csv.exists():
        van_de.append(
            f"Không tìm thấy dataset: {settings.restaurants_csv}\n"
            "      Sửa: python -m data_pipeline.feature_engineering"
        )

    if can_admin:
        # Không chặn, chỉ cảnh báo: app quản trị vẫn mở được, chỉ là đăng nhập sẽ trả 503.
        thieu = [
            ten
            for ten, gia_tri in [
                ("MOODBITE_ADMIN_USER", settings.admin_username),
                ("MOODBITE_ADMIN_PASSWORD_HASH", settings.admin_password_hash),
                ("MOODBITE_ADMIN_SECRET", settings.admin_token_secret),
            ]
            if not gia_tri
        ]
        if thieu or settings.storage_backend != "sqlite":
            print("!" * 70)
            print("CANH BAO: trang quan tri CHUA duoc cau hinh.")
            print("  Giao dien van mo duoc, nhung dang nhap se tra 503.")
            print("  Xem thieu gi: python scripts/check_permissions.py")
            print("!" * 70)
            print()

    return van_de


def main() -> int:
    parser = argparse.ArgumentParser(description="Chay MoodBite o che do phat trien")
    parser.add_argument("--admin", action="store_true", help="Chay them app quan tri")
    parser.add_argument("--admin-only", action="store_true", help="Chi backend + admin")
    parser.add_argument("--no-open", action="store_true", help="Khong tu mo trinh duyet")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    chay_client = not args.admin_only
    chay_admin = args.admin or args.admin_only

    van_de = kiem_dieu_kien(chay_admin)
    if van_de:
        print("=" * 70)
        print("CHUA CHAY DUOC - can sua truoc:")
        print("=" * 70)
        for i, v in enumerate(van_de, 1):
            print(f"  {i}. {v}")
        return 1

    tien_trinh: list[tuple[str, subprocess.Popen]] = []

    cong_api = tim_cong_backend()
    if cong_api != BACKEND_PORT:
        print(f"[LUU Y] Cong {BACKEND_PORT} dang ban -> dung cong {cong_api} thay the.")
        print("        (Thuong do lan chay truoc chua tat han. Frontend se tu tro dung cong nay.)")

    # Frontend PHAI biet backend nam o cong nao. Truyen qua bien moi truong cua tien trinh
    # con thay vi sua file .env - sua file thi lan sau chay lai van con sai cong.
    moi_truong = dict(os.environ)
    moi_truong["VITE_API_BASE"] = f"http://localhost:{cong_api}/api/v1"

    try:
        print("Dang khoi dong backend...")
        tien_trinh.append((
            "backend",
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn",
                 "src.presentation.api.main:create_app", "--factory",
                 "--port", str(cong_api), "--reload"],
                cwd=ROOT,
            ),
        ))

        # npm trên Windows là npm.cmd -> shell=True cho chắc chạy được ở cả hai nơi.
        if chay_client:
            print("Dang khoi dong app nguoi dung...")
            tien_trinh.append((
                "client",
                subprocess.Popen("npm run dev", cwd=FRONTEND, shell=True, env=moi_truong),
            ))
        if chay_admin:
            print("Dang khoi dong app quan tri...")
            tien_trinh.append((
                "admin",
                subprocess.Popen("npm run dev:admin", cwd=FRONTEND, shell=True, env=moi_truong),
            ))

        # Vite cần vài giây mới sẵn sàng; mở trình duyệt sớm quá sẽ ra trang lỗi.
        time.sleep(4)

        print()
        print("=" * 70)
        print("MOODBITE DANG CHAY")
        print("=" * 70)
        print(f"  Backend  (API)      : http://localhost:{cong_api}/api/v1/health")
        print(f"  Tai lieu API        : http://localhost:{cong_api}/docs")
        if chay_client:
            print(f"  >> APP NGUOI DUNG   : http://localhost:{CLIENT_PORT}")
        if chay_admin:
            print(f"  >> APP QUAN TRI     : http://localhost:{ADMIN_PORT}")
        print("=" * 70)
        print("  Dung lai: bam Ctrl+C")
        print("=" * 70)

        if not args.no_open:
            if chay_client:
                webbrowser.open(f"http://localhost:{CLIENT_PORT}")
            if chay_admin:
                webbrowser.open(f"http://localhost:{ADMIN_PORT}")

        # Bất kỳ tiến trình nào chết thì dừng tất cả - tránh cảnh "frontend chạy nhưng
        # backend chết" mà người dùng không biết.
        while True:
            for ten, p in tien_trinh:
                if p.poll() is not None:
                    print(f"\n[{ten}] da dung (ma thoat {p.returncode}). Dang tat phan con lai...")
                    return 1
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nDang tat...")
        return 0
    finally:
        for _, p in tien_trinh:
            if p.poll() is None:
                p.terminate()
        for _, p in tien_trinh:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        print("Da tat het.")


if __name__ == "__main__":
    sys.exit(main())

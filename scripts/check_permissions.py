"""Kiểm tra QUYỀN của trang quản trị đã cấu hình xong chưa.

    python scripts/check_permissions.py

VÌ SAO CÓ FILE NÀY: trang quản trị cố tình FAIL-CLOSED — thiếu cấu hình thì mọi endpoint
`/api/v1/admin/*` trả 503. Đó là hành vi ĐÚNG, nhưng nhìn từ ngoài rất dễ tưởng là hỏng.
Script này nói rõ thiếu đúng cái gì và phải làm gì tiếp.

Không sửa gì, chỉ đọc và in ra. KHÔNG in secret.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import os  # noqa: E402

from src.domain.entities.user import UserRole  # noqa: E402
from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.repositories.sqlite_user_repository import (  # noqa: E402
    SqliteUserRepository,
)

# Console Windows mặc định là cp1252 và sẽ NỔ khi in chữ tiếng Việt — script
# đang chạy dở bị dừng giữa chừng. Lỗi này đã xảy ra thật với
# "additionalInfo/Bầu không khí" trong `data_report.py`.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


OK, MISSING = "[ DAT  ]", "[THIEU ]"


def main() -> int:
    settings = Settings.from_env()

    print("=" * 70)
    print("KIEM TRA QUYEN QUAN TRI MOODBITE")
    print("=" * 70)

    thieu = []
    print("\n-- Bien moi truong --")
    if settings.admin_token_secret:
        # KHONG in secret, ke ca cat ngan: chi can biet da dat hay chua.
        print(f"  {OK} {'MOODBITE_ADMIN_SECRET':32} {'(da dat)':16} khoa ky token")
    else:
        thieu.append("MOODBITE_ADMIN_SECRET")
        print(f"  {MISSING} {'MOODBITE_ADMIN_SECRET':32} {'(rong)':16} khoa ky token")
    # Tu 2026-09-29 hai bien nay KHONG con tac dung - con sot thi nhac xoa di.
    for cu in ("MOODBITE_ADMIN_USER", "MOODBITE_ADMIN_PASSWORD_HASH"):
        if os.environ.get(cu):
            print(f"  [CANH BAO] {cu} con trong moi truong nhung KHONG con tac dung.")
            print("             Chuyen sang bang users: python scripts/make_admin_user.py --tu-env")

    # Tai khoan quan tri nam trong bang users (role='admin'), khong con o bien moi truong.
    print("\n-- Tai khoan quan tri (bang users) --")
    users = SqliteUserRepository(settings.users_db)
    so_admin = users.count_by_role(UserRole.ADMIN) if users.is_ready else 0
    if so_admin:
        print(f"  {OK} {so_admin} tai khoan co vai admin trong {settings.users_db.name}")
    else:
        thieu.append("tai khoan admin")
        print(f"  {MISSING} Chua co tai khoan nao co vai admin trong {settings.users_db.name}")

    print("\n-- Kho luu tru --")
    ghi_duoc = settings.storage_backend == "sqlite"
    print(f"  {OK if ghi_duoc else MISSING} MOODBITE_STORAGE = {settings.storage_backend!r}"
          f"  ({'ghi duoc' if ghi_duoc else 'CHI DOC - admin khong sua duoc gi'})")

    co_db = settings.restaurants_db.exists()
    print(f"  {OK if co_db else MISSING} CSDL SQLite: {settings.restaurants_db}")

    print(f"\n-- Token quan tri --")
    print(f"  Thoi han: {settings.admin_token_ttl_seconds}s "
          f"({settings.admin_token_ttl_seconds / 3600:.1f} gio)")

    # --- Tai khoan nguoi dung cuoi -------------------------------------------
    # Doc lap hoan toan voi phan admin o tren: mot ben tat khong lam ben kia tat theo.
    print("\n-- Tai khoan nguoi dung cuoi (/api/v1/auth/*) --")
    co_auth = bool(settings.user_token_secret)
    print(f"  {OK if co_auth else MISSING} MOODBITE_AUTH_SECRET"
          f"  ({'da dat' if co_auth else 'rong - /api/v1/auth/* dang tra 503'})")
    print(f"  {OK} Kho tai khoan: {settings.users_db}"
          f"  ({'da co' if settings.users_db.exists() else 'chua co - se tu tao'})")
    print(f"  Thoi han token: {settings.user_token_ttl_seconds}s "
          f"({settings.user_token_ttl_seconds / 3600:.1f} gio)")
    if co_auth and settings.user_token_secret == settings.admin_token_secret:
        # Dung chung khoa ky = mat lop ngan cach cuoi cung giua hai loai quyen.
        print("  [CANH BAO] MOODBITE_AUTH_SECRET TRUNG voi MOODBITE_ADMIN_SECRET.")
        print("             Phai dat hai gia tri KHAC NHAU.")

    print("\n" + "=" * 70)
    if not thieu and ghi_duoc and co_db:
        print("KET QUA: QUYEN DA CAU HINH DAY DU - trang quan tri dung duoc.")
        print("  Chay app admin: cd frontend  ->  npm run dev:admin  (cong 5174)")
        return 0

    print("KET QUA: CHUA CAU HINH XONG - trang quan tri chua dang nhap duoc (dung nhu thiet ke).")
    print("\nCAN LAM:")
    buoc = 1
    if not co_db:
        print(f"  {buoc}. Dung CSDL ghi duoc:")
        print("       python scripts/build_sqlite.py")
        buoc += 1
    if thieu:
        print(f"  {buoc}. Tao tai khoan quan tri + secret (ghi vao .env.local):")
        print("       python scripts/make_admin_user.py        # hoac --tu-env neu co tai khoan cu")
        buoc += 1
    if not ghi_duoc:
        print(f"  {buoc}. Bat kho SQLite (PowerShell):")
        print('       $env:MOODBITE_STORAGE = "sqlite"')
        buoc += 1
    if not co_auth:
        print(f"  {buoc}. Bat tinh nang tai khoan nguoi dung (PowerShell):")
        print('       $env:MOODBITE_AUTH_SECRET = '
              '(python -c "import secrets; print(secrets.token_hex(32))")')
        buoc += 1
    print(f"  {buoc}. Khoi dong lai backend roi chay lai script nay de kiem.")
    print("\nXem them: .env.example")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(main())

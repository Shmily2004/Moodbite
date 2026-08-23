"""Kiểm tra QUYỀN của trang quản trị đã cấu hình xong chưa.

    python scripts/check_permissions.py

VÌ SAO CÓ FILE NÀY: trang quản trị cố tình FAIL-CLOSED — thiếu cấu hình thì mọi endpoint
`/api/v1/admin/*` trả 503. Đó là hành vi ĐÚNG, nhưng nhìn từ ngoài rất dễ tưởng là hỏng.
Script này nói rõ thiếu đúng cái gì và phải làm gì tiếp.

Không sửa gì, chỉ đọc và in ra. In hash mật khẩu ở dạng cắt ngắn, KHÔNG in secret.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.infrastructure.config.settings import Settings  # noqa: E402

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

    checks = [
        ("MOODBITE_ADMIN_USER", settings.admin_username, "ten dang nhap"),
        ("MOODBITE_ADMIN_PASSWORD_HASH", settings.admin_password_hash, "hash mat khau"),
        ("MOODBITE_ADMIN_SECRET", settings.admin_token_secret, "khoa ky token"),
    ]

    thieu = []
    print("\n-- Bien moi truong --")
    for name, value, mo_ta in checks:
        if value:
            # Cat ngan: du de nhan ra da dat dung chua, khong du de lo bi mat.
            hien = value[:10] + "..." if len(value) > 10 else value
            print(f"  {OK} {name:32} {hien:16} {mo_ta}")
        else:
            thieu.append(name)
            print(f"  {MISSING} {name:32} {'(rong)':16} {mo_ta}")

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

    print("KET QUA: CHUA CAU HINH XONG - /api/v1/admin/* dang tra 503 (dung nhu thiet ke).")
    print("\nCAN LAM:")
    buoc = 1
    if not co_db:
        print(f"  {buoc}. Dung CSDL ghi duoc:")
        print("       python scripts/build_sqlite.py")
        buoc += 1
    if thieu:
        print(f"  {buoc}. Sinh tai khoan quan tri (in ra 3 bien can dat):")
        print("       python scripts/make_admin_password.py")
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

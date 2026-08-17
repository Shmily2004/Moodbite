"""Sinh cấu hình đăng nhập cho trang quản trị.

    python scripts/make_admin_password.py

Script hỏi mật khẩu (KHÔNG hiện lên màn hình), rồi in ra 3 biến môi trường cần đặt.
Mật khẩu KHÔNG bao giờ được lưu vào file — chỉ lưu chuỗi hash.
"""
from __future__ import annotations

import getpass
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.infrastructure.auth.admin_auth import hash_password  # noqa: E402

MIN_PASSWORD_LENGTH = 12


def main() -> int:
    print("=" * 68)
    print("TAO TAI KHOAN QUAN TRI MOODBITE")
    print("=" * 68)

    username = input("Ten dang nhap [admin]: ").strip() or "admin"

    password = getpass.getpass("Mat khau (khong hien): ")
    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"\n[LOI] Mat khau phai it nhat {MIN_PASSWORD_LENGTH} ky tu.")
        return 1
    if password != getpass.getpass("Nhap lai mat khau: "):
        print("\n[LOI] Hai lan nhap khong khop.")
        return 1

    password_hash = hash_password(password)
    # 32 byte ngau nhien: du dai de khong the do duoc chu ky HMAC.
    token_secret = secrets.token_urlsafe(32)

    print()
    print("=" * 68)
    print("Dat 3 bien moi truong nay ROI KHOI DONG LAI backend.")
    print("=" * 68)
    print("\n--- PowerShell (Windows) ---")
    print(f'$env:MOODBITE_ADMIN_USER = "{username}"')
    print(f'$env:MOODBITE_ADMIN_PASSWORD_HASH = "{password_hash}"')
    print(f'$env:MOODBITE_ADMIN_SECRET = "{token_secret}"')
    print("\n--- bash / macOS / Linux ---")
    print(f'export MOODBITE_ADMIN_USER="{username}"')
    print(f'export MOODBITE_ADMIN_PASSWORD_HASH="{password_hash}"')
    print(f'export MOODBITE_ADMIN_SECRET="{token_secret}"')
    print()
    print("LUU Y:")
    print("  - KHONG commit 3 gia tri nay len git.")
    print("  - Doi MOODBITE_ADMIN_SECRET se lam moi token dang dung het hieu luc.")
    print("  - Chua dat du 3 bien thi /api/v1/admin/* tra 503 (fail-closed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

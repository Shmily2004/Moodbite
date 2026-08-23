"""Sinh cấu hình đăng nhập cho trang quản trị.

    python scripts/make_admin_password.py                  # hỏi mật khẩu, in ra 3 biến
    python scripts/make_admin_password.py --write-env      # ghi thẳng vào .env.local

Script hỏi mật khẩu (KHÔNG hiện lên màn hình), rồi in ra 3 biến môi trường cần đặt.
Mật khẩu KHÔNG bao giờ được lưu vào file — chỉ lưu chuỗi hash.

`--write-env` thêm 2026-08-23: chép tay ba dòng biến môi trường dài ngoằng vào PowerShell
rất dễ sai, và biến đặt bằng `$env:` chỉ sống trong cửa sổ đang mở — đóng cửa sổ là mất,
lần sau lại thấy 503 mà không hiểu vì sao. Ghi vào `.env.local` (đã nằm trong .gitignore)
thì backend tự đọc mỗi lần khởi động.
"""
from __future__ import annotations

import argparse
import getpass
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.infrastructure.auth.admin_auth import hash_password  # noqa: E402

MIN_PASSWORD_LENGTH = 12


ENV_LOCAL = ROOT / ".env.local"


def ghi_env_local(gia_tri: dict) -> None:
    """Ghi/cập nhật các khoá vào `.env.local`, GIỮ NGUYÊN mọi khoá khác đã có.

    Đọc rồi ghi lại cả file chứ không nối thêm vào cuối: nối thêm sẽ để lại hai dòng
    cùng một khoá, và không ai đoán được dòng nào thắng.
    """
    dong_cu: list[str] = []
    if ENV_LOCAL.exists():
        dong_cu = ENV_LOCAL.read_text(encoding="utf-8").splitlines()

    con_lai = dict(gia_tri)
    dong_moi: list[str] = []
    for dong in dong_cu:
        khoa = dong.split("=", 1)[0].strip()
        if khoa in con_lai:
            dong_moi.append(f"{khoa}={con_lai.pop(khoa)}")
        else:
            dong_moi.append(dong)
    for khoa, gt in con_lai.items():
        dong_moi.append(f"{khoa}={gt}")

    noi_dung = chr(10).join(dong_moi).rstrip(chr(10)) + chr(10)
    ENV_LOCAL.write_text(noi_dung, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--write-env", action="store_true",
        help="Ghi thẳng vào .env.local thay vì chỉ in ra màn hình.",
    )
    args = parser.parse_args()

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

    if args.write_env:
        ghi_env_local(
            {
                "MOODBITE_ADMIN_USER": username,
                "MOODBITE_ADMIN_PASSWORD_HASH": password_hash,
                "MOODBITE_ADMIN_SECRET": token_secret,
                # Trang quản trị PHẢI ghi được; kho CSV cố tình chỉ đọc.
                "MOODBITE_STORAGE": "sqlite",
            }
        )
        print()
        print("=" * 68)
        print(f"Da ghi vao {ENV_LOCAL.name} (file nay nam trong .gitignore).")
        print("Khoi dong lai backend roi chay: python scripts/check_permissions.py")
        print("=" * 68)
        print("  - Mat khau KHONG duoc luu o dau ca - chi luu chuoi hash.")
        print("  - Doi MOODBITE_ADMIN_SECRET se lam moi token dang dung het hieu luc.")
        return 0

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

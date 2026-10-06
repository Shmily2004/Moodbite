"""Tạo / nâng quyền TÀI KHOẢN QUẢN TRỊ trong bảng `users`.

    python scripts/make_admin_user.py            # hỏi tên + mật khẩu (không hiện lên màn hình)
    python scripts/make_admin_user.py --tu-env   # chuyển tài khoản admin CŨ trong .env.local

Từ 2026-09-29 admin là một dòng `role='admin'` trong bảng `users`, KHÔNG còn nằm trong
biến môi trường MOODBITE_ADMIN_USER / MOODBITE_ADMIN_PASSWORD_HASH (chủ dự án duyệt).
Thay cho `scripts/make_admin_password.py` (đã chuyển vào `archive/`).

Cả hai cách đều bảo đảm `.env.local` có MOODBITE_ADMIN_SECRET (sinh ngẫu nhiên nếu chưa
có) và MOODBITE_STORAGE=sqlite - thiếu một trong hai thì trang quản trị vẫn 503.

`--tu-env`: dùng lại ĐÚNG chuỗi băm cũ nên mật khẩu admin KHÔNG đổi. Xong thì xoá hai
biến cũ khỏi `.env.local` để không ai tưởng chúng còn tác dụng.

AN TOÀN: tên đã thuộc về một tài khoản THƯỜNG thì script KHÔNG tự nâng quyền khi chạy
`--tu-env` - nâng quyền nhầm người là lỗi không ai nhìn thấy. Chạy chế độ hỏi-đáp và xác
nhận bằng tay nếu thật sự muốn.
"""
from __future__ import annotations

import argparse
import getpass
import os
import secrets
import sys
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.domain.entities.user import (  # noqa: E402
    MIN_ADMIN_PASSWORD_LENGTH,
    InvalidCredentialsFormat,
    User,
    UserRole,
    validate_password_for_role,
    validate_username,
)
from src.infrastructure.auth.crypto import hash_password  # noqa: E402
from src.infrastructure.config.dotenv import DEFAULT_ENV_FILE  # noqa: E402
from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.repositories.sqlite_user_repository import (  # noqa: E402
    SqliteUserRepository,
)

# `MIN_ADMIN_PASSWORD_LENGTH` (12) nay nằm ở DOMAIN (`domain/entities/user.py`), không còn
# định nghĩa riêng ở đây: trước 2026-10-06 chỉ script này biết con số đó, nên admin vào
# `/auth/change-password` hạ được mật khẩu xuống 8 ký tự. Import lại để giữ tên cũ.
BIEN_CU = ("MOODBITE_ADMIN_USER", "MOODBITE_ADMIN_PASSWORD_HASH")

# Kết quả của `nhap_tu_env` - chuỗi cố định để test và để in thông báo.
DA_TAO = "da_tao"
DA_LA_ADMIN = "da_la_admin"
TRUNG_TEN_NGUOI_THUONG = "trung_ten_nguoi_thuong"
THIEU_BIEN = "thieu_bien"
HASH_HONG = "hash_hong"
TEN_KHONG_HOP_LE = "ten_khong_hop_le"


def tao_admin(repo: SqliteUserRepository, username: str, password_hash: str) -> User:
    """Tạo tài khoản MỚI với vai admin. Tên trùng -> `UsernameAlreadyExists`."""
    return repo.create(
        User(
            user_id="",
            username=validate_username(username),
            password_hash=password_hash,
            role=UserRole.ADMIN,
            display_name="Quản trị viên",
        )
    )


def nhap_tu_env(repo: SqliteUserRepository, env: Mapping[str, str]) -> str:
    """Chuyển tài khoản admin kiểu cũ (biến môi trường) thành một dòng trong `users`."""
    ten = (env.get("MOODBITE_ADMIN_USER") or "").strip()
    bam = (env.get("MOODBITE_ADMIN_PASSWORD_HASH") or "").strip()
    if not ten or not bam:
        return THIEU_BIEN
    if not bam.startswith("pbkdf2_sha256$"):
        # Chép nhầm (thiếu ký tự, dính dấu nháy) thì admin mới sẽ không bao giờ đăng nhập
        # được - báo ngay thay vì tạo ra một tài khoản chết.
        return HASH_HONG
    try:
        # Kiểm tên TRƯỚC mọi thao tác ghi. Bản cũ để `tao_admin` ném lỗi ra tận `main()`
        # -> người dùng thấy traceback thay vì một câu báo lỗi đọc được.
        validate_username(ten)
    except InvalidCredentialsFormat:
        return TEN_KHONG_HOP_LE
    co_san = repo.get_by_username(ten)
    if co_san is not None:
        return DA_LA_ADMIN if co_san.is_admin else TRUNG_TEN_NGUOI_THUONG
    tao_admin(repo, ten, bam)
    return DA_TAO


def cap_nhat_env_local(duong_dan: Path, dat: Mapping[str, str], xoa=()) -> None:
    """Ghi/cập nhật khoá trong `.env.local`, GIỮ NGUYÊN mọi khoá khác; xoá các khoá trong
    `xoa`. Đọc rồi ghi lại cả file: nối thêm vào cuối sẽ để lại hai dòng cùng một khoá."""
    dong_cu = duong_dan.read_text(encoding="utf-8").splitlines() if duong_dan.exists() else []
    con_lai = dict(dat)
    dong_moi = []
    for dong in dong_cu:
        khoa = dong.split("=", 1)[0].strip()
        if khoa in xoa:
            continue
        if khoa in con_lai:
            dong_moi.append(f"{khoa}={con_lai.pop(khoa)}")
        else:
            dong_moi.append(dong)
    dong_moi.extend(f"{k}={v}" for k, v in con_lai.items())
    duong_dan.write_text("\n".join(dong_moi).rstrip("\n") + "\n", encoding="utf-8")


def cau_hinh_can_co(env: Mapping[str, str]) -> dict:
    """Những khoá `.env.local` PHẢI có để trang quản trị chạy. Không đè secret đang dùng:
    đổi secret là đăng xuất mọi admin đang mở trang."""
    can = {"MOODBITE_STORAGE": "sqlite"}
    if not (env.get("MOODBITE_ADMIN_SECRET") or "").strip():
        # 32 byte ngẫu nhiên: đủ dài để không thể dò chữ ký HMAC.
        can["MOODBITE_ADMIN_SECRET"] = secrets.token_urlsafe(32)
    return can


def _hoi_mat_khau() -> str | None:
    mat_khau = getpass.getpass("Mat khau (khong hien): ")
    try:
        # CÙNG luật với `/auth/change-password` và `/auth/reset-password` (domain).
        validate_password_for_role(mat_khau, UserRole.ADMIN)
    except InvalidCredentialsFormat:
        print(
            f"[LOI] Mat khau quan tri phai tu {MIN_ADMIN_PASSWORD_LENGTH} ky tu "
            "(va khong qua 128 ky tu)."
        )
        return None
    if mat_khau != getpass.getpass("Nhap lai mat khau: "):
        print("[LOI] Hai lan nhap khong khop.")
        return None
    return mat_khau


def _che_do_hoi_dap(repo: SqliteUserRepository) -> int:
    ten = input("Ten dang nhap quan tri [admin]: ").strip() or "admin"
    # Kiểm tên NGAY, trước khi hỏi mật khẩu. Bản cũ hỏi mật khẩu (gõ 2 lần) xong mới báo
    # tên sai - bằng một traceback.
    try:
        ten = validate_username(ten)
    except InvalidCredentialsFormat:
        # Câu KHÔNG DẤU, cố ý như mọi dòng `print` của script: console PowerShell 5.1 hay
        # chạy bảng mã cũ, in chữ có dấu (thông điệp của domain) có thể nổ UnicodeEncodeError.
        print(
            "[LOI] Ten dang nhap khong hop le: chi chu a-z khong dau, so, '_', '-', "
            "dai 3-32 ky tu."
        )
        return 1
    co_san = repo.get_by_username(ten)
    if co_san is not None and co_san.is_admin:
        print(f"[OK] '{co_san.username}' da la quan tri vien. Khong doi gi.")
        return 0
    if co_san is not None:
        tra_loi = input(
            f"'{co_san.username}' la tai khoan NGUOI DUNG da co. Nang len quan tri? [y/N]: "
        )
        if tra_loi.strip().lower() != "y":
            print("Da huy.")
            return 1
        repo.set_role(co_san.user_id, UserRole.ADMIN)
        print(f"[OK] Da nang '{co_san.username}' len quan tri. Dang nhap bang mat khau cu.")
        return 0
    mat_khau = _hoi_mat_khau()
    if mat_khau is None:
        return 1
    tao_admin(repo, ten, hash_password(mat_khau))
    print(f"[OK] Da tao tai khoan quan tri '{ten}'.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--tu-env", action="store_true",
        help="Chuyen tai khoan admin cu (MOODBITE_ADMIN_USER/_PASSWORD_HASH) vao bang users.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()  # nạp luôn .env.local vào os.environ
    repo = SqliteUserRepository(settings.users_db)
    if not repo.is_ready:
        print(f"[LOI] Khong mo duoc kho tai khoan: {repo.status()['error']}")
        return 1

    print("=" * 68)
    print("TAI KHOAN QUAN TRI MOODBITE (bang users)")
    print("=" * 68)

    if args.tu_env:
        ket_qua = nhap_tu_env(repo, os.environ)
        thong_bao = {
            DA_TAO: "[OK] Da chuyen tai khoan admin cu vao bang users (mat khau giu nguyen).",
            DA_LA_ADMIN: "[OK] Tai khoan nay da co trong bang users voi vai admin.",
            TRUNG_TEN_NGUOI_THUONG: (
                "[DUNG] Ten nay dang la tai khoan NGUOI DUNG THUONG. Khong tu nang quyen.\n"
                "       Neu dung la ban: chay lai KHONG co --tu-env va xac nhan bang tay."
            ),
            THIEU_BIEN: "[LOI] Khong thay MOODBITE_ADMIN_USER / MOODBITE_ADMIN_PASSWORD_HASH.",
            HASH_HONG: "[LOI] MOODBITE_ADMIN_PASSWORD_HASH khong dung dinh dang pbkdf2_sha256$...",
            TEN_KHONG_HOP_LE: (
                "[LOI] MOODBITE_ADMIN_USER khong hop le: chi chu a-z khong dau, so, '_', '-', "
                "dai 3-32 ky tu. Sua trong .env.local roi chay lai."
            ),
        }[ket_qua]
        print(thong_bao)
        if ket_qua not in (DA_TAO, DA_LA_ADMIN):
            return 1
        cap_nhat_env_local(DEFAULT_ENV_FILE, cau_hinh_can_co(os.environ), xoa=BIEN_CU)
        print(f"Da xoa {', '.join(BIEN_CU)} khoi {DEFAULT_ENV_FILE.name} (khong con tac dung).")
    else:
        ma = _che_do_hoi_dap(repo)
        if ma != 0:
            return ma
        cap_nhat_env_local(DEFAULT_ENV_FILE, cau_hinh_can_co(os.environ))

    print(f"So tai khoan quan tri hien co: {repo.count_by_role(UserRole.ADMIN)}")
    print("Khoi dong lai backend, roi kiem: python scripts/check_permissions.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

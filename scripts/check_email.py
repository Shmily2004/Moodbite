"""Kiểm tra cấu hình gửi thư (tính năng QUÊN MẬT KHẨU) — chạy trước khi thử trên web.

    python scripts/check_email.py                 # chỉ ĐĂNG NHẬP thử, KHÔNG gửi thư
    python scripts/check_email.py --to ban@gmail.com   # gửi thật một lá thư thử

VÌ SAO CẦN SCRIPT NÀY: cách duy nhất còn lại để biết cấu hình đúng chưa là chạy cả backend
lẫn frontend rồi bấm "Quên mật khẩu?" — mà lúc đó lỗi hiện ra chỉ là một dòng 503 chung
chung. Script này nói thẳng SAI CHỖ NÀO: thiếu biến, sai mật khẩu ứng dụng, hay chặn mạng.

MẶC ĐỊNH KHÔNG GỬI THƯ. Đăng nhập SMTP thành công đã đủ chứng minh host/port/tài khoản/mật
khẩu ứng dụng đều đúng; gửi thư thật chỉ cần khi muốn xem lá thư trông thế nào.

⚠️ Script này KHÔNG BAO GIỜ in mật khẩu ra màn hình — log hay bị dán lên nhóm chat.
"""
from __future__ import annotations

import argparse
import smtplib
import ssl
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.notifications.smtp_email_sender import SmtpEmailSender  # noqa: E402


def che(gia_tri: str) -> str:
    """Chỉ cho thấy CÓ hay KHÔNG và dài bao nhiêu — không lộ một ký tự nào của giá trị."""
    return f"đã đặt ({len(gia_tri)} ký tự)" if gia_tri else "CHƯA ĐẶT"


def che_email(dia_chi: str) -> str:
    """Che phần tên của địa chỉ thư, chỉ giữ 2 ký tự đầu và tên miền.

    VÌ SAO CHE CẢ EMAIL (chủ dự án nhắc 2026-08-22): địa chỉ thư cũng là dữ liệu cá nhân.
    Kết quả script này hay được chụp màn hình gửi cho người khác xem giúp, nên mặc định
    phải KHÔNG lộ gì. Vẫn đủ để tự nhận ra mình gõ nhầm tài khoản nào.
    """
    if not dia_chi:
        return "CHƯA ĐẶT"
    if "@" not in dia_chi:
        return f"{dia_chi[:2]}***"
    ten, mien = dia_chi.split("@", 1)
    return f"{ten[:2]}***@{mien}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Kiểm tra cấu hình gửi thư của MoodBite.")
    parser.add_argument(
        "--to",
        help="Gửi THẬT một lá thư thử tới địa chỉ này. Bỏ trống thì chỉ đăng nhập thử.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()

    print("=" * 68)
    print("CẤU HÌNH GỬI THƯ")
    print("=" * 68)
    print(f"  MOODBITE_SMTP_HOST     : {settings.smtp_host or 'CHƯA ĐẶT'}")
    print(f"  MOODBITE_SMTP_PORT     : {settings.smtp_port}")
    print(f"  MOODBITE_SMTP_USER     : {che_email(settings.smtp_username)}")
    print(f"  MOODBITE_SMTP_PASSWORD : {che(settings.smtp_password)}")
    print(
        "  MOODBITE_SMTP_FROM     : "
        + (che_email(settings.smtp_sender) if settings.smtp_sender else "(trống → dùng SMTP_USER)")
    )
    print(f"  MOODBITE_RESET_SECRET  : {che(settings.reset_token_secret)}")
    print(f"  MOODBITE_AUTH_SECRET   : {che(settings.user_token_secret)}")
    print(f"  MOODBITE_APP_URL       : {settings.app_base_url}")
    print()

    if settings.smtp_password and len(settings.smtp_password) != 16:
        print(
            "  ⚠ Mật khẩu ứng dụng của Google luôn dài ĐÚNG 16 ký tự (đã bỏ khoảng trắng)."
            f" Chuỗi hiện tại dài {len(settings.smtp_password)} — có thể bạn đang dán nhầm"
            " mật khẩu Gmail thật."
        )
        print()

    sender = SmtpEmailSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        sender=settings.smtp_sender,
    )
    if not sender.is_configured:
        print("KẾT QUẢ: CHƯA CẤU HÌNH ĐỦ — thiếu host/port/user/password.")
        print("Điền vào `.env.local` (KHÔNG phải `.env.example`), xem hướng dẫn ở đó.")
        return 1

    print(f"Đang thử đăng nhập {settings.smtp_host}:{settings.smtp_port} …")
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(settings.smtp_username, settings.smtp_password)
        print("  ✓ Đăng nhập THÀNH CÔNG — host, cổng, tài khoản và mật khẩu ứng dụng đều đúng.")
    except smtplib.SMTPAuthenticationError:
        print("  ✗ SAI TÀI KHOẢN HOẶC MẬT KHẨU ỨNG DỤNG.")
        print("    - Phải dùng App Password (16 ký tự), KHÔNG phải mật khẩu Gmail.")
        print("    - Tạo tại: https://myaccount.google.com/apppasswords")
        print("    - Phải bật xác minh 2 bước thì trang đó mới hiện ra.")
        return 1
    except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
        print(f"  ✗ KHÔNG KẾT NỐI ĐƯỢC: {exc}")
        print("    Thường là mạng chặn cổng 587, hoặc gõ sai tên máy chủ.")
        return 1

    if not args.to:
        print()
        print("Chưa gửi thư nào (mặc định là vậy).")
        print("Muốn gửi thử thật: python scripts/check_email.py --to email-cua-ban@gmail.com")
        return 0

    print(f"Đang gửi thư thử tới {che_email(args.to)} …")
    try:
        sender.send(
            to=args.to,
            subject="MoodBite — thư thử cấu hình",
            body=chr(10).join(
                [
                    "Nếu bạn đọc được thư này thì cấu hình gửi thư của MoodBite đã chạy.",
                    "",
                    "Thư thật khi quên mật khẩu sẽ kèm một đường dẫn dạng:",
                    f"{settings.app_base_url.rstrip('/')}/dat-lai-mat-khau?token=...",
                    "",
                    "— MoodBite",
                ]
            ),
        )
    except Exception as exc:  # noqa: BLE001 — script chẩn đoán, cần thấy mọi lỗi
        print(f"  ✗ GỬI THẤT BẠI: {exc}")
        return 1

    print("  ✓ Đã gửi. Kiểm tra cả hộp thư rác — thư đầu tiên hay bị lọc.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""GỬI THỬ MỘT LÁ THƯ XÁC MINH THẬT — để tự mắt nhìn thư trông thế nào.

    python scripts/gui_thu_thu.py                     # chỉ IN RA, không gửi đi đâu
    python scripts/gui_thu_thu.py --gui ban@gmail.com # GỬI THẬT vào hộp thư đó

VÌ SAO CÓ SCRIPT NÀY: bộ test chứng minh được `href` không bị bẻ dòng, nhưng KHÔNG chứng
minh được thư hiện ra đẹp hay xấu trong Gmail — chỉ mắt người mới trả lời được. Và cũng
không chứng minh được `MOODBITE_SMTP_*` trên máy này có đúng hay không.

MẶC ĐỊNH LÀ KHÔNG GỬI. Bắn thư đi là việc không thể rút lại, nên phải nói rõ `--gui`
kèm địa chỉ thì mới gửi.

⚠️ Đường dẫn trong thư thử là token GIẢ — bấm vào sẽ báo "đường dẫn không hợp lệ".
Đó là ĐÚNG: script này kiểm HÌNH THỨC lá thư, không phát token thật cho tài khoản nào.
Muốn thử trọn luồng thì đăng ký một tài khoản mới trên web.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.application.emails import thu_co_nut  # noqa: E402
from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.notifications.smtp_email_sender import SmtpEmailSender  # noqa: E402

# Dài đúng cỡ token thật (~220 ký tự) để thấy được nó xuống dòng ra sao.
TOKEN_GIA = (
    "eyJzdWIiOiJVSS1USFUtS0hPTkctUEhBSS1UT0tFTi1USEFUIiwiZW0iOiJ2aS5kdUB2aS5kdS5jb20i"
    "LCJldiI6IjAwMDAwMDAwMDAwMDAwMDAiLCJleHAiOjB9.CHU-KY-GIA-CHI-DE-XEM-HINH-THUC-THU"
)


def soan():
    settings = Settings.from_env()
    lien_ket = f"{settings.app_base_url.rstrip('/')}/verify-email?token={TOKEN_GIA}"
    return thu_co_nut(
        subject="[THỬ] Xác minh email MoodBite",
        tren_nut=[
            "Chào bạn,",
            "",
            "Đây là thư THỬ để xem hình thức. Bấm nút dưới đây sẽ ra trang xác minh, "
            "nhưng báo không hợp lệ vì token trong thư này là giả.",
        ],
        nhan_nut="Xác minh email",
        lien_ket=lien_ket,
        duoi_nut=["Đường dẫn có hiệu lực trong 24 giờ và chỉ dùng được MỘT lần."],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Gui thu thu de xem hinh thuc")
    parser.add_argument("--gui", metavar="EMAIL", help="Dia chi nhan thu. Khong co thi chi in ra.")
    parser.add_argument("--luu-html", metavar="FILE", help="Ghi ban HTML ra file de mo bang trinh duyet")
    args = parser.parse_args()

    thu = soan()

    print("=" * 70)
    print("BẢN CHỮ THUẦN (hộp thư tắt HTML sẽ thấy cái này)")
    print("=" * 70)
    print(thu.text)
    print()

    if args.luu_html:
        Path(args.luu_html).write_text(thu.html, encoding="utf-8")
        print(f"Đã ghi bản HTML ra: {args.luu_html}")
        print("Mở file đó bằng trình duyệt để xem thư hiện ra thế nào.")
        print()

    if not args.gui:
        print("Chưa gửi đi đâu cả. Muốn gửi thật:")
        print("    python scripts/gui_thu_thu.py --gui dia.chi@cua.ban")
        return 0

    settings = Settings.from_env()
    sender = SmtpEmailSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        sender=settings.smtp_sender,
    )
    if not sender.is_configured:
        print("CHƯA CẤU HÌNH MÁY CHỦ THƯ.")
        print("Cần đủ MOODBITE_SMTP_HOST / _PORT / _USER / _PASSWORD trong .env.local")
        print(f"  đang có: host={settings.smtp_host!r} port={settings.smtp_port!r} "
              f"user={settings.smtp_username!r} password={'có' if settings.smtp_password else 'TRỐNG'}")
        return 1

    print(f"Đang gửi tới {args.gui} qua {settings.smtp_host}:{settings.smtp_port} …")
    sender.send(to=args.gui, subject=thu.subject, body=thu.text, html=thu.html)
    print("ĐÃ GỬI. Kiểm tra hộp thư (nhớ xem cả mục Spam / Quảng cáo).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

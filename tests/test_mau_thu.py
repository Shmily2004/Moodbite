"""KHUÔN THƯ — khoá lại đúng lỗi đã xảy ra ngày 2026-08-26.

Lỗi: thư xác minh là CHỮ THUẦN, đường dẫn dài 218 ký tự để trần giữa dòng. Mã hoá
quoted-transfer bẻ dòng ở cột 76 nên phần auto-link của hộp thư chỉ bắt được đoạn đầu →
người dùng bấm vào một đường dẫn CỤT và "không thấy gì hiện lên".

Các test dưới đây kiểm THỨ THẬT ĐI RA KHỎI MÁY, tức là chuỗi MIME sau khi mã hoá, chứ
không phải chuỗi Python trước khi mã hoá — vì chính bước mã hoá mới là chỗ bẻ dòng.
"""
from __future__ import annotations

import re
from email import message_from_string

import pytest

from src.application.emails import thu_co_nut

# Token thật dài cỡ này. Phải vượt 76 ký tự thì mới tái hiện được lỗi bẻ dòng.
LIEN_KET = (
    "http://localhost:5173/verify-email?token=eyJzdWIiOiJ1c3JfMDFKWk1RM1I4WEc0VDVWN1c5"
    "WTJBM0I2QzgiLCJlbSI6Im11bmd2dTk5OUBnbWFpbC5jb20iLCJldiI6IjNmOWEyYzhkNGU3YjFhNWYi"
    "LCJleHAiOjE3NzIwMDAwMDB9.aB3dK9xQ2mP7vL5nR8tY1wZ6cE4uH0jS"
)


@pytest.fixture
def thu():
    return thu_co_nut(
        subject="Xác minh email MoodBite",
        tren_nut=["Chào Ai Đó,", "", "Bấm nút dưới đây."],
        nhan_nut="Xác minh email",
        lien_ket=LIEN_KET,
        duoi_nut=["Hiệu lực 24 giờ."],
    )


def test_lien_ket_dai_phai_nam_gon_trong_mot_thuoc_tinh_href(thu):
    """Đây chính là lỗi đã xảy ra: link bị bẻ làm ba thì bấm vào ra token cụt."""
    assert len(LIEN_KET) > 76, "Link mẫu quá ngắn thì test này không chứng minh được gì"
    assert f'href="{LIEN_KET}"' in thu.html


def test_ban_chu_thuan_van_con_va_van_co_link(thu):
    """Thư chỉ-có-HTML bị chấm là thư rác và hiện ra TRỐNG với người tắt HTML."""
    assert LIEN_KET in thu.text
    assert "Xác minh email" in thu.text


def test_qua_smtp_thi_href_khong_bi_be_dong(tmp_path):
    """Kiểm ĐÚNG chuỗi MIME đi ra dây — chỗ mà bản chữ thuần đã thua.

    Bản chữ thuần bị bẻ dòng (quoted-printable, cột 76) là CHẤP NHẬN ĐƯỢC vì hộp thư nối
    lại được trước khi hiển thị. Thứ KHÔNG được phép hỏng là `href` trong bản HTML, vì đó
    mới là cái người dùng bấm vào.
    """
    from src.infrastructure.notifications.smtp_email_sender import SmtpEmailSender

    da_gui = {}

    class SmtpGia:
        def __init__(self, *a, **k): ...
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self, **k): ...
        def login(self, *a): ...
        def send_message(self, msg): da_gui["raw"] = msg.as_string()

    import src.infrastructure.notifications.smtp_email_sender as mod
    goc = mod.smtplib.SMTP
    mod.smtplib.SMTP = SmtpGia
    try:
        n = thu_co_nut(
            subject="Xác minh email MoodBite",
            tren_nut=["Chào Ai Đó,"],
            nhan_nut="Xác minh email",
            lien_ket=LIEN_KET,
            duoi_nut=["Hiệu lực 24 giờ."],
        )
        SmtpEmailSender(
            host="smtp.test", port=587, username="a@b.c", password="x", sender=""
        ).send(to="ai@do.com", subject=n.subject, body=n.text, html=n.html)
    finally:
        mod.smtplib.SMTP = goc

    # Giải mã lại như hộp thư người nhận làm, rồi tìm phần HTML.
    msg = message_from_string(da_gui["raw"])
    assert msg.is_multipart(), "Phải là multipart/alternative (chữ thuần + HTML)"
    phan_html = [
        p.get_payload(decode=True).decode("utf-8")
        for p in msg.walk()
        if p.get_content_type() == "text/html"
    ]
    assert phan_html, "Thư gửi đi không có phần HTML"

    hrefs = re.findall(r'href="([^"]+)"', phan_html[0])
    assert LIEN_KET in hrefs, f"href bị hỏng sau khi mã hoá MIME: {hrefs}"


def test_khong_bi_chen_the_html_qua_ten_nguoi_dung():
    """Tên hiển thị do NGƯỜI DÙNG tự đặt và bị nhét thẳng vào thư — phải thoát ký tự.

    Không thoát thì một cái tên như `<script>` hay `"><a href=...>` biến lá thư thành
    chỗ chèn đường dẫn giả mạo, mà thư lại là thứ người dùng vốn tin.
    """
    n = thu_co_nut(
        subject="X",
        tren_nut=['Chào <img src=x onerror=alert(1)> "kẻ xấu",'],
        nhan_nut="Bấm",
        lien_ket="http://localhost:5173/verify-email?token=abc",
        duoi_nut=[],
    )
    assert "<img" not in n.html
    assert "&lt;img" in n.html

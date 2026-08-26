"""KHUÔN THƯ — sinh cùng lúc bản chữ thuần và bản HTML từ MỘT nguồn nội dung.

VÌ SAO CÓ FILE NÀY (lỗi thật, chủ dự án báo 2026-08-26)
--------------------------------------------------------
Thư xác minh trước đây là CHỮ THUẦN, đường dẫn để trần giữa dòng:

    Hãy xác nhận ... bằng cách mở đường dẫn dưới đây:
    http://localhost:5173/verify-email?token=eyJzdWIiOiJ1c3Jf...

Đường dẫn đó dài 218 ký tự. Thư chữ thuần mã hoá quoted-printable BẺ DÒNG ở cột 76, nên
trong thư thật nó nằm trên ba dòng nối bằng dấu `=`. Hộp thư đúng chuẩn thì nối lại được,
nhưng phần auto-link của nhiều hộp thư chỉ bắt phần đầu — người dùng bấm vào một đường
dẫn CỤT, tới trang xác minh với token thiếu đuôi, và thấy... gần như không có gì.

Sửa bằng cách gửi kèm bản HTML có NÚT BẤM: `<a href="...">` mang đường dẫn trong thuộc
tính, không phụ thuộc vào việc hộp thư có tự nhận ra chuỗi URL giữa đoạn văn hay không.

⚠️ VẪN GỬI CẢ BẢN CHỮ THUẦN. Xem `EmailSender.send` — thư chỉ-có-HTML bị chấm là thư rác
và hiện ra trống với người tắt HTML.

VÌ SAO CSS VIẾT THẲNG VÀO TỪNG THẺ: hộp thư (Gmail, Outlook) cắt bỏ `<style>` và không
hiểu class. Trong thư, `style=` viết tay là cách duy nhất chắc chắn chạy — đây là ngoại
lệ CÓ CHỦ ĐÍCH so với quy tắc CSS của frontend.

VÌ SAO NẰM Ở `application/` CHỨ KHÔNG PHẢI `infrastructure/`: nội dung thư là NGHIỆP VỤ
(nói gì với người dùng), còn cách chuyển đi mới là hạ tầng. File này thuần Python, không
import framework nào — đúng luật ở CLAUDE.md mục 2.
"""
from __future__ import annotations

import html
from dataclasses import dataclass

# Màu lấy từ `frontend/apps/client/src/app/styles/brand.css` để thư trông cùng một nhà
# với web. Chép giá trị chứ không đọc file: backend không được phụ thuộc vào frontend.
MAU_NHAN = "#E8623C"
MAU_CHU = "#2B2118"
MAU_CHU_NHAT = "#6B5C4D"
MAU_NEN = "#FBF7F2"


@dataclass(frozen=True)
class LaThu:
    """Một lá thư ở cả hai dạng. `html` luôn nói cùng nội dung với `text`."""

    subject: str
    text: str
    html: str


def _doan_html(dong: list[str]) -> str:
    """Mỗi dòng rỗng trong danh sách = hết một đoạn văn."""
    doan: list[list[str]] = [[]]
    for d in dong:
        if d.strip():
            doan[-1].append(html.escape(d))
        elif doan[-1]:
            doan.append([])
    return "".join(
        f'<p style="margin:0 0 14px;font-size:15px;line-height:1.6;color:{MAU_CHU};">'
        f'{" ".join(p)}</p>'
        for p in doan
        if p
    )


def thu_co_nut(
    *,
    subject: str,
    tren_nut: list[str],
    nhan_nut: str,
    lien_ket: str,
    duoi_nut: list[str],
) -> LaThu:
    """Dựng thư "vài dòng → một nút → vài dòng" — khuôn chung của mọi thư trong dự án.

    `tren_nut` / `duoi_nut` là danh sách DÒNG, dòng rỗng ngăn đoạn. Giữ dạng danh sách
    thay vì một chuỗi dài có `\n` vì thư toàn tiếng Việt và còn sửa câu chữ nhiều lần —
    để dạng này thì mỗi dòng nhìn thấy rõ, không ai đếm nhầm ký tự xuống dòng.
    """
    text = chr(10).join(
        [
            *tren_nut,
            "",
            f"{nhan_nut}:",
            lien_ket,
            "",
            *duoi_nut,
        ]
    )

    lk = html.escape(lien_ket, quote=True)
    noi_dung_html = f"""\
<div style="margin:0;padding:24px 12px;background:{MAU_NEN};font-family:-apple-system,\
BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
  <div style="max-width:520px;margin:0 auto;background:#ffffff;border-radius:16px;\
padding:32px 28px;">
    <p style="margin:0 0 24px;font-size:20px;font-weight:700;color:{MAU_NHAN};">MoodBite</p>
    {_doan_html(tren_nut)}
    <p style="margin:24px 0;">
      <a href="{lk}" style="display:inline-block;padding:14px 28px;border-radius:999px;\
background:{MAU_NHAN};color:#ffffff;font-size:16px;font-weight:600;text-decoration:none;">\
{html.escape(nhan_nut)}</a>
    </p>
    {_doan_html(duoi_nut)}
    <p style="margin:24px 0 0;padding-top:16px;border-top:1px solid #EADFD3;\
font-size:12px;line-height:1.6;color:{MAU_CHU_NHAT};">
      Nút không bấm được? Chép đường dẫn này vào trình duyệt:<br>
      <span style="word-break:break-all;">{lk}</span>
    </p>
  </div>
</div>"""

    return LaThu(subject=subject, text=text, html=noi_dung_html)


__all__ = ["LaThu", "thu_co_nut", "MAU_NHAN"]

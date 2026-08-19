"""Khoá lại phép ĐỐI CHIẾU CHÉO giữa các nguồn và quy tắc về TUỔI THẬT của dữ liệu.

Bối cảnh: cột `last_updated` chỉ là NGÀY TA CÀO, không nói gì về việc quán còn tồn tại.
Đo 2026-08-19: nó ghi 97,4% dữ liệu "cập nhật 16-19/08/2026", trong khi thực tế 65% bản
ghi OSM chưa ai sửa trong hơn một năm (cũ nhất: 2010).

`source_updated_at` là ngày NGUỒN cập nhật - thứ nói thật.
"""
import json

import pandas as pd

from scripts.check_websites import NEN_TANG, _ten_mien
from scripts.enrich_freshness import MAX_KHOANG_CACH_KM, _khoang_cach_km


def test_khoang_cach_tinh_dung_o_quy_mo_thanh_pho():
    """Quán cách nhau 0,001 độ vĩ ~ 111m - phải nằm trong ngưỡng ghép."""
    assert _khoang_cach_km(21.030, 105.850, 21.031, 105.850) < MAX_KHOANG_CACH_KM
    # 0,01 độ ~ 1,1km - vượt xa ngưỡng.
    assert _khoang_cach_km(21.030, 105.850, 21.040, 105.850) > MAX_KHOANG_CACH_KM


def test_nguong_ghep_du_chat_de_khong_gop_nham_chi_nhanh():
    """Bài học từ `refresh_check.py`: 73 cặp trùng tên cách nhau tới 22km là CHI NHÁNH
    khác nhau của cùng chuỗi. Ngưỡng phải đủ chặt để không gộp chúng."""
    assert MAX_KHOANG_CACH_KM <= 0.2, "nguong qua rong -> gop nham chi nhanh"


# --- Tách tên miền (dùng cho việc kiểm tra website còn sống) ------------------


def test_bo_www_va_ha_chu_thuong():
    assert _ten_mien("https://WWW.PhoThin.VN/menu") == "phothin.vn"
    assert _ten_mien("phothin.vn") == "phothin.vn"


def test_link_NEN_TANG_bi_nhan_ra_de_bo_qua():
    """facebook.com luôn sống kể cả khi trang của quán đã bị xoá - kiểm tra nó chỉ tốn
    thời gian mà không thu được tin gì về quán."""
    for url in ["https://www.facebook.com/phothin", "https://maps.app.goo.gl/abc",
                "https://shopeefood.vn/ha-noi/pho-thin", "https://www.tiktok.com/@quan"]:
        assert _ten_mien(url) in NEN_TANG, url


def test_ten_mien_RIENG_cua_quan_thi_khong_bi_bo_qua():
    for url in ["https://phothin.vn", "http://nhahangthuco.com"]:
        assert _ten_mien(url) not in NEN_TANG, url


def test_url_rong_hoac_hong_tra_None_chu_khong_no():
    assert _ten_mien(None) is None
    assert _ten_mien("") is None
    assert _ten_mien("   ") is None

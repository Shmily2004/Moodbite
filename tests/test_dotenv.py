"""Test bộ nạp `.env.local`.

Nhỏ nhưng đáng test: đây là chỗ quyết định app đọc được cấu hình hay không, và một lỗi ở
đây biểu hiện ra ngoài thành "tính năng tự nhiên tắt" — kiểu lỗi khó đoán nhất.

Chốt chặn quan trọng nhất: BIẾN ĐÃ CÓ TRONG SHELL PHẢI THẮNG FILE. Trên máy chủ thật biến
do hệ thống triển khai đặt; một file `.env.local` sót lại mà ghi đè được lên nó thì cấu
hình thật bị thay lặng lẽ.
"""
from __future__ import annotations

import os

from src.infrastructure.config.dotenv import nap_env_local


def test_nap_duoc_bien_thuong(tmp_path, monkeypatch):
    f = tmp_path / ".env.local"
    f.write_text("MOODBITE_TEST_A=xin-chao\n", encoding="utf-8")
    monkeypatch.delenv("MOODBITE_TEST_A", raising=False)

    assert nap_env_local(f) == 1
    assert os.environ["MOODBITE_TEST_A"] == "xin-chao"


def test_bien_co_san_trong_shell_THANG_file(tmp_path, monkeypatch):
    f = tmp_path / ".env.local"
    f.write_text("MOODBITE_TEST_B=tu-file\n", encoding="utf-8")
    monkeypatch.setenv("MOODBITE_TEST_B", "tu-shell")

    nap_env_local(f)

    assert os.environ["MOODBITE_TEST_B"] == "tu-shell"


def test_bo_qua_dong_trong_va_dong_ghi_chu(tmp_path, monkeypatch):
    f = tmp_path / ".env.local"
    f.write_text(
        "# ghi chu\n\n   \nMOODBITE_TEST_C=co-gia-tri\n# MOODBITE_TEST_D=bi-comment\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MOODBITE_TEST_C", raising=False)
    monkeypatch.delenv("MOODBITE_TEST_D", raising=False)

    assert nap_env_local(f) == 1
    assert "MOODBITE_TEST_D" not in os.environ


def test_bo_cap_nhay_bao_ngoai(tmp_path, monkeypatch):
    f = tmp_path / ".env.local"
    f.write_text('MOODBITE_TEST_E="co nhay kep"\n', encoding="utf-8")
    monkeypatch.delenv("MOODBITE_TEST_E", raising=False)

    nap_env_local(f)

    assert os.environ["MOODBITE_TEST_E"] == "co nhay kep"


def test_giu_khoang_trang_ben_trong_gia_tri(tmp_path, monkeypatch):
    """Mật khẩu ứng dụng của Google hiện theo nhóm 4 ký tự cách nhau — dán y nguyên phải
    chạy. Nơi dùng nó mới lọc khoảng trắng, không phải bộ nạp này."""
    f = tmp_path / ".env.local"
    f.write_text("MOODBITE_TEST_F=abcd efgh ijkl mnop\n", encoding="utf-8")
    monkeypatch.delenv("MOODBITE_TEST_F", raising=False)

    nap_env_local(f)

    assert os.environ["MOODBITE_TEST_F"] == "abcd efgh ijkl mnop"


def test_khong_co_file_thi_im_lang_tra_0(tmp_path):
    """Chạy bằng biến môi trường của shell là cách dùng hợp lệ — không có gì để cảnh báo."""
    assert nap_env_local(tmp_path / "khong-ton-tai.local") == 0


def test_dong_thieu_dau_bang_bi_bo_qua_chu_khong_no(tmp_path, monkeypatch):
    f = tmp_path / ".env.local"
    f.write_text("DONG RAC KHONG CO DAU BANG\nMOODBITE_TEST_G=ok\n", encoding="utf-8")
    monkeypatch.delenv("MOODBITE_TEST_G", raising=False)

    assert nap_env_local(f) == 1
    assert os.environ["MOODBITE_TEST_G"] == "ok"

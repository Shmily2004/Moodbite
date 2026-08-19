"""Khoá lại việc DỰNG DANH MỤC MÓN từ file seed.

Bug thật 2026-08-19: `load_manual_seed` đọc `description` nhưng quên `image_url`, nên ảnh
chỉ có khi chạy kèm `--enrich` (gọi mạng Wikipedia). Dựng lại danh mục lúc không có mạng
làm ảnh tụt 87,1% -> 0% mà không có gì báo. Nói cách khác: pipeline không dựng lại được
kết quả của chính nó. Đó là thứ phải có test, không phải thứ để nhớ.
"""
import json

from scripts.build_dish_catalog import load_manual_seed


def _viet_seed(tmp_path, entries):
    f = tmp_path / "seed.json"
    f.write_text(json.dumps({"dishes": entries}, ensure_ascii=False), encoding="utf-8")
    return f


def test_giu_lai_MOI_truong_da_lam_giau_khi_khong_co_mang(tmp_path):
    """Mọi thứ tốn công tra Wikipedia mới có được PHẢI đọc lại được từ seed."""
    path = _viet_seed(tmp_path, [{
        "dish_id": "pho-bo",
        "name": "Phở bò",
        "description": "Món nước dùng xương bò.",
        "image_url": "https://upload.wikimedia.org/pho-bo.jpg",
        "source_url": "https://vi.wikipedia.org/wiki/Phở",
        "cuisine": "Việt Nam",
        "match_keywords": ["phở"],
    }])

    dish = load_manual_seed(path)[0]

    assert dish.description == "Món nước dùng xương bò."
    assert dish.image_url == "https://upload.wikimedia.org/pho-bo.jpg"
    assert dish.source_url == "https://vi.wikipedia.org/wiki/Phở"
    assert dish.cuisine == "Việt Nam"


def test_thieu_thi_de_None_chu_khong_dung_chuoi_rong(tmp_path):
    """`None` = chưa tra được. Chuỗi rỗng làm giao diện tưởng "đã tra, không có gì"."""
    path = _viet_seed(tmp_path, [{"name": "Món chưa tra"}])

    dish = load_manual_seed(path)[0]

    assert dish.image_url is None
    assert dish.description is None
    assert dish.cuisine is None

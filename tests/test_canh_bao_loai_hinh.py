"""Cảnh báo "quán này chỉ khớp theo LOẠI HÌNH, không phải theo tên".

VÌ SAO CÓ (đo 2026-09-23 trên dữ liệu thật):
  - Chỉ mục món-quán: 32.118 cặp khớp bằng TÊN quán, 14.353 cặp chỉ khớp bằng
    `categoryName`. Cả hai nằm CÙNG một bậc `MATCH_STRENGTH` nên cạnh tranh ngang nhau
    lúc xếp hạng.
  - Đo trên 120 trang món: 10 trang có quán chỉ khớp loại hình lọt top-20 trong khi vẫn
    còn quán khớp tên (71 quán). Ví dụ trang "Hải sản nướng" xếp "Bánh canh ghẹ Dì Sơn"
    ở hạng 4.
  - Bật bộ lọc "chỉ quán có ghi giá" thì thành áp đảo: trang "Gà rán" còn 62 quán và
    CẢ 62 đều là khớp loại hình.

2026-09-29: khớp loại hình đã xuống bậc thấp hơn khớp tên (CLAUDE.md mục 4 quy tắc 6),
xem `CATEGORY_ONLY_MATCH_STRENGTH`. Cảnh báo vẫn giữ (CLAUDE.md mục 5): khi quán khớp tên
không đủ, phần đuôi danh sách là loại hình và người dùng phải biết điều đó.
"""
from src.domain.services.dish_matching import (
    FIELD_CATEGORY,
    FIELD_NAME,
    MATCHED_BY_NAME,
    DishMatch,
)
from tests.fakes import make_restaurant
from tests.test_dish_api import API, BUN_CHA, SESSION, make_client


def quan(ten, field, **kw):
    r = make_restaurant(ten, lat=21.0285, lng=105.8542, **kw)
    return DishMatch(r, MATCHED_BY_NAME, matched_field=field)


def goi(client, **params):
    params.setdefault("session_id", SESSION)
    return client.get(f"{API}/dishes/bun-cha/restaurants", params=params).json()["data"]


def test_toan_bo_danh_sach_khop_loai_hinh_thi_noi_that_ro():
    """Trường hợp tệ nhất: không quán nào ghi tên món. Phải nói bằng chữ "CẢ"."""
    client = make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [quan("Nhà Hàng Ăn Nhanh A", FIELD_CATEGORY),
                           quan("Quán Vặt B", FIELD_CATEGORY)]},
    )

    data = goi(client)

    assert len(data["results"]) == 2
    canh_bao = " ".join(data["warnings"])
    assert "CẢ 2 quán" in canh_bao
    assert "LOẠI HÌNH" in canh_bao


def test_chi_mot_phan_khop_loai_hinh_thi_dem_dung_so_do():
    client = make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [quan("Bún Chả Hương Liên", FIELD_NAME),
                           quan("Nhà Hàng Ăn Nhanh A", FIELD_CATEGORY)]},
    )

    data = goi(client)

    canh_bao = " ".join(data["warnings"])
    assert "1 quán" in canh_bao
    # Không được dùng chữ "CẢ" khi vẫn còn quán khớp tên - đó là hai tình huống khác nhau.
    assert "CẢ" not in canh_bao


def test_toan_quan_khop_TEN_thi_KHONG_canh_bao_gi():
    """Cảnh báo thừa cũng là một kiểu nói dối: nó làm người dùng nghi ngờ kết quả tốt."""
    client = make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [quan("Bún Chả Hương Liên", FIELD_NAME),
                           quan("Bún Chả Đắc Kim", FIELD_NAME)]},
    )

    data = goi(client)

    assert not any("LOẠI HÌNH" in w for w in data["warnings"])


def test_canh_bao_dem_theo_DANH_SACH_TRA_VE_chu_khong_phai_ca_chi_muc():
    """`limit` cắt danh sách thì con số phải theo phần người dùng THẬT SỰ nhìn thấy."""
    client = make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [quan(f"Quán Ăn Nhanh {i}", FIELD_CATEGORY) for i in range(5)]},
    )

    data = goi(client, limit=2)

    assert len(data["results"]) == 2
    assert "CẢ 2 quán" in " ".join(data["warnings"])


def test_quan_khop_TEN_o_xa_van_dung_tren_quan_khop_LOAI_HINH_o_gan():
    """Sửa 2026-09-29: khớp loại hình xuống bậc thấp hơn khớp tên (CLAUDE.md mục 4 quy
    tắc 6). Trước đó hai quán cùng bậc nên quán loại hình ở gần thắng nhờ khoảng cách."""
    xa = make_restaurant("Bún Chả Hương Liên", lat=21.0485, lng=105.8542)
    gan = DishMatch(
        make_restaurant("Nhà Hàng Ăn Nhanh A", lat=21.0285, lng=105.8542, rating=4.9),
        MATCHED_BY_NAME, matched_field=FIELD_CATEGORY,
    )
    client = make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [gan, DishMatch(xa, MATCHED_BY_NAME)]},
    )

    data = goi(client, latitude=21.0285, longitude=105.8542)

    assert [r["name"] for r in data["results"]] == [
        "Bún Chả Hương Liên", "Nhà Hàng Ăn Nhanh A",
    ]


def test_match_source_tra_ve_van_la_category():
    """Cảnh báo là phần THÊM, không được làm đổi hợp đồng `match_source` sẵn có."""
    client = make_client(
        dishes=[BUN_CHA],
        index={"bun-cha": [quan("Nhà Hàng Ăn Nhanh A", FIELD_CATEGORY)]},
    )

    data = goi(client)

    assert data["results"][0]["match_source"] == "category"

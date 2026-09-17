"""Test đợt nâng cấp khu quản trị 2026-09-16: phân trang · thẻ số · thao tác hàng loạt ·
tab "Đã xử lý" · khối "Hệ thống gợi ý".

Điều đáng khoá ở đây:

  1. Cột "Có quán (số)" của bảng món dùng ĐÚNG chỉ mục của `/dishes/{id}/restaurants`, không
     phải bộ khớp thứ hai.
  2. Phân trang: tổng là tổng KHỚP BỘ LỌC, không phải số dòng của trang.
  3. Ẩn hàng loạt ghi nhật ký TỪNG QUÁN, và báo lại mã không tồn tại thay vì nuốt.
  4. Thống kê tương tác: `None` khi chưa đo được, KHÔNG phải 0; không có CTR.
  5. `/issues/resolved` không bị route `/issues/{key}` nuốt mất.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from src.application.use_cases.get_interaction_stats import GetInteractionStatsUseCase
from src.application.use_cases.list_dishes_admin import (
    GetDishForAdminUseCase,
    ListDishesForAdminUseCase,
)
from src.application.use_cases.manage_issues import LietKeDaXuLyUseCase
from src.domain.entities.dish import Dish
from src.domain.entities.issue_resolution import DanhDauXong
from src.domain.services.dish_matching import (
    MATCHED_BY_DISH_NAME,
    MATCHED_BY_REVIEW,
    DishMatch,
)
from src.domain.services.interaction_stats import BanGhiTuongTac, thong_ke_tuong_tac
from src.infrastructure.repositories.jsonl_interaction_repository import (
    JsonlInteractionRepository,
)
from tests.fakes import FakeDishCatalog, make_restaurant
from tests.test_admin_api import API, auth_header, build_client
from tests.test_sqlite_repository import make_db


# ==========================================================================
# Domain — thống kê tương tác
# ==========================================================================


def test_chua_co_ban_ghi_thi_ty_le_la_None_KHONG_phai_0():
    tk = thong_ke_tuong_tac([], hom_nay=date(2026, 9, 16))

    assert tk.tong == 0
    assert tk.ty_le_tich_cuc is None
    # Khung 7 ngày vẫn ĐỦ ngày để sparkline không nối thẳng hai điểm xa nhau.
    assert len(tk.theo_ngay) == 7
    assert all(d.so_luot == 0 for d in tk.theo_ngay)


def test_thong_ke_dem_dung_phien_tai_khoan_va_theo_ngay():
    ban_ghi = [
        BanGhiTuongTac("view_detail", "2026-09-16T01:00:00+00:00", "s1", None, True),
        BanGhiTuongTac("save", "2026-09-16T02:00:00+00:00", "s1", "u1", True),
        BanGhiTuongTac("explicit_negative", "2026-09-15T02:00:00+00:00", "s2", "u1", False),
        # Bản ghi cũ không có nhãn -> KHÔNG vào mẫu số của tỷ lệ.
        BanGhiTuongTac("view_detail", "2026-09-01T02:00:00+00:00", "s3", None, None),
    ]

    tk = thong_ke_tuong_tac(ban_ghi, hom_nay=date(2026, 9, 16))

    assert tk.tong == 4
    assert tk.ty_le_tich_cuc == pytest.approx(66.7)
    assert tk.so_phien == 3
    assert tk.so_tai_khoan == 1
    assert tk.theo_hanh_dong["view_detail"] == 2
    ngay = {d.ngay: d.so_luot for d in tk.theo_ngay}
    assert ngay["2026-09-16"] == 2 and ngay["2026-09-15"] == 1
    # Ngày 01/09 nằm ngoài 7 ngày -> không vào biểu đồ, nhưng vẫn vào tổng.
    assert "2026-09-01" not in ngay


def test_adapter_jsonl_bo_qua_dong_hong(tmp_path):
    p = tmp_path / "i.jsonl"
    p.write_text(
        '{"action_type": "save", "session_id": "a", "is_positive_signal": true}\n'
        "dong hong {\n"
        '{"session_id": "khong co action"}\n',
        encoding="utf-8",
    )

    ban_ghi = JsonlInteractionRepository(p).read_records()

    assert len(ban_ghi) == 1 and ban_ghi[0].action_type == "save"


def test_kho_khong_doc_duoc_thi_available_false_chu_KHONG_phai_0_luot():
    class KhoCu:
        is_ready = True

    kq = GetInteractionStatsUseCase(KhoCu()).execute()

    assert kq.available is False and kq.thong_ke is None


# ==========================================================================
# Use case — bảng món phân trang + số quán
# ==========================================================================


def _catalog():
    return FakeDishCatalog(
        [
            Dish(name="Bún chả", dish_id="bun-cha", description="Bún ăn với chả nướng"),
            Dish(name="Phở bò", dish_id="pho-bo", image_url="https://x/pho.jpg"),
            Dish(name="Kem bơ", dish_id="kem-bo", is_active=False),
        ]
    )


def test_so_quan_lay_tu_CHINH_chi_muc_mon_quan():
    q = make_restaurant("Bún Chả Hương Liên")
    index = {"bun-cha": [DishMatch(q, MATCHED_BY_DISH_NAME)], "pho-bo": []}

    kq = ListDishesForAdminUseCase(_catalog(), index).execute()

    so = {r.dish_id: r.restaurant_count for r in kq.rows}
    assert so == {"bun-cha": 1, "pho-bo": 0, "kem-bo": 0}


def test_chua_lap_chi_muc_thi_so_quan_la_None_KHONG_phai_0():
    kq = ListDishesForAdminUseCase(_catalog()).execute()

    assert all(r.restaurant_count is None for r in kq.rows)


def test_phan_trang_tong_la_tong_KHOP_khong_phai_so_dong():
    kq = ListDishesForAdminUseCase(_catalog()).execute(page=2, page_size=2)

    assert kq.total == 3 and len(kq.rows) == 1 and kq.page == 2
    assert kq.counts == {
        "all": 3,
        "with_restaurants": 2,
        "without_restaurants": 1,
        "missing_image": 2,
        "missing_description": 2,
    }
    assert kq.dishes_total == 3 and kq.dishes_with_restaurants == 2


def test_quan_cua_mon_khop_manh_truoc_rating_None_xep_sau_nhung_KHONG_bi_coi_la_0():
    manh_chua_rating = make_restaurant("Bún Chả A", rating=None)
    manh_co_rating = make_restaurant("Bún Chả B", rating=4.1)
    yeu_rating_cao = make_restaurant("Nhà Hàng C", rating=4.9)
    index = {
        "bun-cha": [
            DishMatch(yeu_rating_cao, MATCHED_BY_REVIEW),
            DishMatch(manh_chua_rating, MATCHED_BY_DISH_NAME),
            DishMatch(manh_co_rating, MATCHED_BY_DISH_NAME),
        ]
    }
    uc = GetDishForAdminUseCase(_catalog(), index)

    kq = uc.restaurants(uc.execute("bun-cha"))

    assert [m.restaurant.name for m in kq.results] == ["Bún Chả B", "Bún Chả A", "Nhà Hàng C"]
    assert kq.results[1].restaurant.rating is None


# ==========================================================================
# API
# ==========================================================================


@pytest.fixture
def ctx(tmp_path):
    db = make_db(
        tmp_path,
        {"place_id": "pho-1", "name": "Phở Bò Hàng Đồng", "district": "Phường Hoàn Kiếm",
         "source": "overture", "is_active": 1},
        {"place_id": "bun-2", "name": "Bún Chả Hương Liên", "district": "Phường Hai Bà Trưng",
         "source": "openstreetmap", "is_active": 1},
        {"place_id": "manual:3", "name": "Chè Bà Thìn", "district": "Phường Hoàn Kiếm",
         "source": "manual", "is_active": 0},
    )
    client, repo = build_client(db)
    c = client.app.state.container
    quan = repo.get_for_admin("bun-2")
    index = {"bun-cha": [DishMatch(quan, MATCHED_BY_DISH_NAME)], "pho-bo": []}
    catalog = _catalog()
    c.dish_catalog_repository = catalog
    c.list_dishes_for_admin = ListDishesForAdminUseCase(catalog, index)
    c.get_dish_for_admin = GetDishForAdminUseCase(catalog, index)
    # Dựng lại vì `build_client` đã lắp use case này với danh mục món RỖNG.
    c.liet_ke_da_xu_ly = LietKeDaXuLyUseCase(
        restaurant_repository=repo,
        dish_catalog_repository=catalog,
        issue_resolution_repository=c.issue_resolutions,
    )
    return client, c


def test_bang_mon_tra_phan_trang_va_so_tren_nut_loc(ctx):
    client, _ = ctx
    data = client.get(
        f"{API}/admin/dishes?page=1&page_size=2", headers=auth_header(client)
    ).json()["data"]

    assert data["total"] == 3 and data["returned"] == 2
    assert data["page_size"] == 2 and data["counts"]["without_restaurants"] == 1
    bun_cha = next(r for r in data["results"] if r["dish_id"] == "bun-cha")
    assert bun_cha["restaurant_count"] == 1
    assert bun_cha["description"] == "Bún ăn với chả nướng"
    # Không có ngày -> null, KHÔNG được bịa ngày dựng danh mục.
    assert bun_cha["last_updated"] is None


def test_chi_tiet_mon_co_so_quan_va_danh_sach_quan(ctx):
    client, _ = ctx
    h = auth_header(client)

    assert client.get(f"{API}/admin/dishes/bun-cha", headers=h).json()["data"][
        "restaurant_count"
    ] == 1
    data = client.get(f"{API}/admin/dishes/bun-cha/restaurants", headers=h).json()["data"]
    assert data["total"] == 1
    assert data["results"][0]["restaurant_id"] == "bun-2"
    assert data["results"][0]["rating"] is None
    assert data["results"][0]["matched_by"] == MATCHED_BY_DISH_NAME

    assert client.get(f"{API}/admin/dishes/khong-co/restaurants", headers=h).status_code == 404


def test_bang_quan_phan_trang_va_loc(ctx):
    client, _ = ctx
    h = auth_header(client)

    data = client.get(f"{API}/admin/restaurants?page=2&page_size=2", headers=h).json()["data"]
    assert data["total_matched"] == 3 and data["total"] == 1 and data["page"] == 2

    an = client.get(f"{API}/admin/restaurants?status=hidden", headers=h).json()["data"]
    assert [r["restaurant_id"] for r in an["results"]] == ["manual:3"]

    khu = client.get(
        f"{API}/admin/restaurants?district=Phường Hoàn Kiếm&source=manual", headers=h
    ).json()["data"]
    assert khu["total_matched"] == 1


def test_the_so_quan(ctx):
    client, _ = ctx
    data = client.get(f"{API}/admin/restaurants/stats", headers=auth_header(client)).json()[
        "data"
    ]

    assert (data["total"], data["visible"], data["hidden"], data["manual"]) == (3, 2, 1, 1)
    assert data["districts"][0] == {"value": "Phường Hoàn Kiếm", "count": 2}
    assert {s["value"] for s in data["sources"]} == {"overture", "openstreetmap", "manual"}


def test_an_hang_loat_ghi_nhat_ky_TUNG_quan_va_bao_ma_khong_ton_tai(ctx):
    client, _ = ctx
    h = auth_header(client)

    res = client.post(
        f"{API}/admin/restaurants/bulk-visibility",
        json={"restaurant_ids": ["pho-1", "bun-2", "khong-ton-tai"], "is_active": False},
        headers=h,
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert sorted(r["restaurant_id"] for r in data["updated"]) == ["bun-2", "pho-1"]
    assert all(r["is_active"] is False for r in data["updated"])
    assert data["not_found"] == ["khong-ton-tai"]

    nhat_ky = client.get(
        f"{API}/admin/activity?action=hide_restaurant", headers=h
    ).json()["data"]["entries"]
    assert sorted(e["target_id"] for e in nhat_ky) == ["bun-2", "pho-1"]


def test_an_hang_loat_danh_sach_rong_thi_400(ctx):
    client, _ = ctx
    res = client.post(
        f"{API}/admin/restaurants/bulk-visibility",
        json={"restaurant_ids": [], "is_active": False},
        headers=auth_header(client),
    )

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_REQUEST"


def test_nhat_ky_loc_theo_MOT_doi_tuong(ctx):
    client, _ = ctx
    h = auth_header(client)
    client.post(f"{API}/admin/restaurants/pho-1/hide", headers=h)
    client.post(f"{API}/admin/restaurants/bun-2/hide", headers=h)

    data = client.get(
        f"{API}/admin/activity?target_type=restaurant&target_id=pho-1", headers=h
    ).json()["data"]

    assert [e["target_id"] for e in data["entries"]] == ["pho-1"]


def test_tab_da_xu_ly_KHONG_bi_route_issues_key_nuot(ctx):
    client, c = ctx
    c.issue_resolutions.danh_dau(
        DanhDauXong(
            khoa="mon_thieu_anh",
            target_id="bun-cha",
            actor="admin",
            resolved_at=datetime(2026, 9, 16, 1, 0, tzinfo=timezone.utc),
        )
    )
    h = auth_header(client)

    data = client.get(f"{API}/admin/issues/resolved", headers=h).json()["data"]
    assert data["total"] == 1
    assert data["results"][0]["name"] == "Bún chả"
    assert data["results"][0]["resolved_by"] == "admin"

    nhom = client.get(f"{API}/admin/issues", headers=h).json()["data"]["groups"]
    theo_khoa = {g["key"]: g["last_resolved_at"] for g in nhom}
    assert theo_khoa["mon_thieu_anh"].startswith("2026-09-16")
    # Nhóm chưa ai đánh dấu -> null, không đoán.
    assert theo_khoa["dong_tam"] is None


def test_thong_ke_tuong_tac_qua_api_khong_co_CTR(ctx, tmp_path):
    client, c = ctx
    p = tmp_path / "i.jsonl"
    p.write_text(
        '{"action_type": "save", "session_id": "a", "is_positive_signal": true, '
        '"created_at": "2026-09-16T01:00:00+00:00"}\n',
        encoding="utf-8",
    )
    c.interaction_stats = GetInteractionStatsUseCase(
        JsonlInteractionRepository(p), hom_nay=lambda: date(2026, 9, 16)
    )

    data = client.get(
        f"{API}/admin/interactions/stats", headers=auth_header(client)
    ).json()["data"]

    assert data["available"] is True and data["total"] == 1
    assert data["positive_rate"] == 100.0 and data["sessions"] == 1
    assert data["by_action"] == [{"action_type": "save", "count": 1}]
    assert len(data["last_7_days"]) == 7
    assert "ctr" not in data


def test_endpoint_moi_deu_can_token(ctx):
    client, _ = ctx
    for url in (
        "/admin/interactions/stats",
        "/admin/restaurants/stats",
        "/admin/issues/resolved",
        "/admin/dishes/bun-cha/restaurants",
    ):
        assert client.get(f"{API}{url}").status_code == 401, url

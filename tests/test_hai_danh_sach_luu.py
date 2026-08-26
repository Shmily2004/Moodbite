"""HAI DANH SÁCH TÁCH BẠCH: "món yêu thích" (trái tim) và "đã lưu" (dấu trang).

Chủ dự án chốt 2026-08-26. Trước đó chỉ có MỘT danh sách, trái tim vừa mang nghĩa "thích"
vừa mang nghĩa "để dành xem sau" — hai ý định khác nhau bị ép chung một nút.

Cái đáng khoá ở đây KHÔNG phải "lưu được rồi đọc ra được", mà là bốn chỗ dễ làm sai:

  1. một món phải nằm được ở CẢ HAI danh sách cùng lúc (khoá chính phải gộp `list_type`),
  2. bỏ tim KHÔNG được xoá luôn dấu trang của chính món đó,
  3. lọc theo một danh sách không được lẫn mục của danh sách kia,
  4. dữ liệu CŨ (từ hồi một danh sách) phải thành 'favorite', không được mất và không
     được đoán bừa sang 'bookmark'.
"""
from __future__ import annotations

import sqlite3

import pytest

from src.domain.entities.saved_item import (
    InvalidSavedItem,
    SavedItem,
    SavedItemType,
    SavedListType,
    validate_list_type,
)
from src.infrastructure.repositories.sqlite_saved_item_repository import (
    SqliteSavedItemRepository,
)
from tests.test_auth_api import API, build_client, register

MON = {"item_type": "dish", "item_id": "bun-cha", "name": "Bún chả"}


@pytest.fixture
def client(tmp_path):
    c, _ = build_client(tmp_path)
    return c


def token_cua(client):
    return register(client).json()["data"]["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ==========================================================================
# Tầng domain
# ==========================================================================


def test_bo_trong_list_type_thi_mac_dinh_la_trai_tim():
    """Mọi lời gọi viết TRƯỚC ngày tách hai danh sách đều mang nghĩa "thích"."""
    assert validate_list_type(None) is SavedListType.FAVORITE
    assert validate_list_type("") is SavedListType.FAVORITE


def test_list_type_la_thu_khong_ton_tai_thi_bao_loi():
    with pytest.raises(InvalidSavedItem) as loi:
        validate_list_type("thung-rac")
    # Câu lỗi phải NÊU RA giá trị hợp lệ, không chỉ nói "sai".
    assert "favorite" in str(loi.value) and "bookmark" in str(loi.value)


# ==========================================================================
# Tầng kho — nơi khoá chính quyết định mọi thứ
# ==========================================================================


def _them(kho, danh_sach, item_id="bun-cha", ten="Bún chả"):
    return kho.add(
        SavedItem(
            user_id="u1",
            item_type=SavedItemType.DISH,
            item_id=item_id,
            name=ten,
            list_type=danh_sach,
        )
    )


def test_mot_mon_nam_duoc_o_CA_HAI_danh_sach(tmp_path):
    """Thích một món rồi vẫn phải đánh dấu được để hôm nào đi ăn."""
    kho = SqliteSavedItemRepository(tmp_path / "u.db")
    _them(kho, SavedListType.FAVORITE)
    _them(kho, SavedListType.BOOKMARK)

    assert kho.count_for_user("u1") == 2
    assert kho.count_for_user("u1", list_type=SavedListType.FAVORITE) == 1
    assert kho.count_for_user("u1", list_type=SavedListType.BOOKMARK) == 1


def test_bo_tim_KHONG_xoa_dau_trang(tmp_path):
    """Đây là lỗi dễ mắc nhất: quên `list_type` trong câu DELETE."""
    kho = SqliteSavedItemRepository(tmp_path / "u.db")
    _them(kho, SavedListType.FAVORITE)
    _them(kho, SavedListType.BOOKMARK)

    kho.remove("u1", SavedItemType.DISH, "bun-cha", SavedListType.FAVORITE)

    assert kho.count_for_user("u1", list_type=SavedListType.FAVORITE) == 0
    assert kho.count_for_user("u1", list_type=SavedListType.BOOKMARK) == 1


def test_du_lieu_CU_duoc_chuyen_thanh_favorite_va_KHONG_mat(tmp_path):
    """Nâng cấp bảng ba cột khoá -> bốn cột khoá.

    Dữ liệu này là DỮ LIỆU GỐC của người dùng, mất là mất hẳn. Bảng cũ phải dựng bằng
    SQL trần chứ không qua kho — dùng kho thì nó đã là bảng mới rồi, test sẽ xanh giả.
    """
    duong_dan = tmp_path / "u.db"
    with sqlite3.connect(duong_dan) as conn:
        conn.executescript(
            "CREATE TABLE saved_items ("
            " user_id TEXT NOT NULL, item_type TEXT NOT NULL, item_id TEXT NOT NULL,"
            " name TEXT NOT NULL, created_at TEXT NOT NULL,"
            " PRIMARY KEY (user_id, item_type, item_id));"
        )
        conn.execute(
            "INSERT INTO saved_items VALUES "
            "('u1','dish','bun-cha','Bún chả','2026-08-20T10:00:00')"
        )
        conn.execute(
            "INSERT INTO saved_items VALUES "
            "('u1','restaurant','q1','Quán A','2026-08-21T10:00:00')"
        )

    kho = SqliteSavedItemRepository(duong_dan)
    muc = kho.list_for_user("u1")

    assert len(muc) == 2, "Nâng cấp bảng làm MẤT dữ liệu gốc của người dùng"
    assert {m.list_type for m in muc} == {SavedListType.FAVORITE}
    # Tên phải nguyên vẹn — người dùng nhận ra mục đã lưu bằng chính cái tên đó.
    assert {m.name for m in muc} == {"Bún chả", "Quán A"}


def test_nang_cap_chay_hai_lan_khong_hong(tmp_path):
    """Mở app lần thứ hai không được làm gì thêm — nâng cấp phải nhận ra mình đã chạy."""
    duong_dan = tmp_path / "u.db"
    kho = SqliteSavedItemRepository(duong_dan)
    _them(kho, SavedListType.FAVORITE, item_id="d1", ten="Món 1")

    lai = SqliteSavedItemRepository(duong_dan)

    assert lai.count_for_user("u1") == 1


# ==========================================================================
# Tầng HTTP
# ==========================================================================


def test_api_luu_vao_hai_danh_sach_va_loc_rieng_tung_cai(client):
    token = token_cua(client)
    h = auth(token)

    client.post(f"{API}/me/favorites", json=dict(MON, list_type="favorite"), headers=h)
    client.post(f"{API}/me/favorites", json=dict(MON, list_type="bookmark"), headers=h)

    ca_hai = client.get(f"{API}/me/favorites", headers=h).json()["data"]
    chi_tim = client.get(f"{API}/me/favorites?list_type=favorite", headers=h).json()["data"]
    chi_dau = client.get(f"{API}/me/favorites?list_type=bookmark", headers=h).json()["data"]

    # Bỏ trống `list_type` = CẢ HAI, vì giao diện cần biết cùng lúc tim nào bật và dấu
    # trang nào bật, không nên đi mạng hai lượt cho cùng một bảng.
    assert ca_hai["total"] == 2
    assert chi_tim["total"] == 1 and chi_tim["items"][0]["list_type"] == "favorite"
    assert chi_dau["total"] == 1 and chi_dau["items"][0]["list_type"] == "bookmark"


def test_api_khong_khai_list_type_thi_vao_danh_sach_trai_tim(client):
    """Client viết trước ngày tách hai danh sách vẫn phải chạy đúng."""
    token = token_cua(client)

    client.post(f"{API}/me/favorites", json=MON, headers=auth(token))

    data = client.get(
        f"{API}/me/favorites?list_type=favorite", headers=auth(token)
    ).json()["data"]
    assert data["total"] == 1


def test_api_bo_tim_khong_dung_toi_dau_trang(client):
    token = token_cua(client)
    h = auth(token)
    client.post(f"{API}/me/favorites", json=dict(MON, list_type="favorite"), headers=h)
    client.post(f"{API}/me/favorites", json=dict(MON, list_type="bookmark"), headers=h)

    client.delete(f"{API}/me/favorites/dish/bun-cha?list_type=favorite", headers=h)

    con_lai = client.get(f"{API}/me/favorites", headers=h).json()["data"]
    assert con_lai["total"] == 1
    assert con_lai["items"][0]["list_type"] == "bookmark"


def test_api_duong_dan_xoa_CU_van_chay_va_nham_vao_trai_tim(client):
    """Không truyền `list_type` -> bỏ tim. Giữ đường dẫn cũ sống được."""
    token = token_cua(client)
    h = auth(token)
    client.post(f"{API}/me/favorites", json=dict(MON, list_type="favorite"), headers=h)
    client.post(f"{API}/me/favorites", json=dict(MON, list_type="bookmark"), headers=h)

    client.delete(f"{API}/me/favorites/dish/bun-cha", headers=h)

    con_lai = client.get(f"{API}/me/favorites", headers=h).json()["data"]
    assert con_lai["items"][0]["list_type"] == "bookmark"


def test_api_list_type_bay_ba_thi_400_chu_khong_phai_500(client):
    token = token_cua(client)

    res = client.post(
        f"{API}/me/favorites",
        json=dict(MON, list_type="thung-rac"),
        headers=auth(token),
    )

    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_REQUEST"

# ==========================================================================
# Đếm — chỗ đã sai một lần
# ==========================================================================


def test_o_MON_DA_LUU_dem_so_MON_chu_khong_dem_so_dong(tmp_path):
    """Lỗi thật 2026-08-26, sinh ra ngay khi tách hai danh sách.

    Một món vừa được thả tim vừa được đánh dấu nằm ở HAI dòng. Trang tài khoản hỏi
    "tôi đã lưu bao nhiêu MÓN", nên đếm dòng cho ra 2 trong khi người dùng chỉ có 1 món.
    Điểm cấp độ cũng bị thổi gấp đôi cho cùng một hành vi.
    """
    kho = SqliteSavedItemRepository(tmp_path / "u.db")
    _them(kho, SavedListType.FAVORITE)                       # bun-cha, tim
    _them(kho, SavedListType.BOOKMARK)                       # bun-cha, dau trang
    _them(kho, SavedListType.FAVORITE, item_id="pho-bo", ten="Phở bò")

    # Số DÒNG là 3 — đúng, vì đó là ba lượt lưu vào hai danh sách.
    assert kho.count_for_user("u1", SavedItemType.DISH) == 3
    # Số MÓN khác nhau là 2 — đây mới là con số hiện lên ô "Món đã lưu".
    assert kho.count_distinct_items("u1", SavedItemType.DISH) == 2


def test_stats_dung_so_MON_khac_nhau(tmp_path):
    """Chốt chặn ở tầng use case, không chỉ ở tầng kho."""
    from src.application.use_cases.get_user_stats import GetUserStatsUseCase
    from src.domain.services.activity_tally import ActivityTally

    kho = SqliteSavedItemRepository(tmp_path / "u.db")
    _them(kho, SavedListType.FAVORITE)
    _them(kho, SavedListType.BOOKMARK)

    stats = GetUserStatsUseCase(ActivityTally(), kho).execute("u1")

    assert stats.saved_dishes == 1, "Ô 'Món đã lưu' đang đếm dòng thay vì đếm món"
    assert stats.activity.saved_items == 1, "Điểm cấp độ bị thổi gấp đôi"


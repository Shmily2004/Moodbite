"""Test HTTP của `/api/v1/me/*` — quán & món đã lưu · lượt khám phá · cấp độ · huy hiệu.

`test_gamification.py` đã test quy tắc tính điểm ở domain. File này test thứ chỉ hỏng ở
tầng HTTP, và đặc biệt là ĐƯỜNG ĐI SAI:

  - xem/sửa danh sách yêu thích của NGƯỜI KHÁC   -> phải KHÔNG được
  - gọi khi chưa đăng nhập                        -> 401, không phải danh sách rỗng
  - client tự khai `user_id` để cộng điểm cho mình -> phải bị bỏ qua
  - tài khoản mới                                 -> mọi số phải là 0 THẬT
"""
from __future__ import annotations

import pytest

from tests.test_auth_api import API, build_client, register

# Quán duy nhất trong dataset giả của `build_client` (xem `tests/fakes.py`).
QUAN = "id-Quan Pho"

DU_LAU = 5000


@pytest.fixture
def client(tmp_path):
    c, _ = build_client(tmp_path)
    return c


def token_cua(client, username="nguoidung"):
    res = register(client, username=username)
    assert res.status_code == 201, res.text
    return res.json()["data"]["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ==========================================================================
# Chốt chặn: đây là dữ liệu riêng của từng người
# ==========================================================================


def test_chua_dang_nhap_thi_401_chu_khong_phai_danh_sach_rong(client):
    """Trả `[]` sẽ khiến giao diện hiện "bạn chưa lưu gì" cho người đang đăng nhập lỗi."""
    assert client.get(f"{API}/me/favorites").status_code == 401
    assert client.get(f"{API}/me/stats").status_code == 401


def test_KHONG_thay_duoc_muc_da_luu_cua_nguoi_khac(client):
    a = token_cua(client, "nguoi-a")
    b = token_cua(client, "nguoi-b")

    client.post(
        f"{API}/me/favorites",
        json={"item_type": "dish", "item_id": "bun-cha", "name": "Bún chả"},
        headers=auth(a),
    )

    res = client.get(f"{API}/me/favorites", headers=auth(b))
    assert res.status_code == 200
    assert res.json()["data"]["items"] == []


def test_KHONG_xoa_duoc_muc_cua_nguoi_khac(client):
    a = token_cua(client, "nguoi-a")
    b = token_cua(client, "nguoi-b")
    client.post(
        f"{API}/me/favorites",
        json={"item_type": "dish", "item_id": "pho-bo", "name": "Phở bò"},
        headers=auth(a),
    )

    # Không có endpoint nào nhận user_id, nên B chỉ xoá được trong phạm vi của chính B.
    client.delete(f"{API}/me/favorites/dish/pho-bo", headers=auth(b))

    con_lai = client.get(f"{API}/me/favorites", headers=auth(a)).json()["data"]
    assert con_lai["total"] == 1


# ==========================================================================
# Lưu / bỏ lưu
# ==========================================================================


def test_luu_va_doc_lai_duoc(client):
    tk = token_cua(client)
    res = client.post(
        f"{API}/me/favorites",
        json={"item_type": "restaurant", "item_id": "quan-1", "name": "Bún chả Hương Liên"},
        headers=auth(tk),
    )
    assert res.status_code == 201, res.text

    data = client.get(f"{API}/me/favorites", headers=auth(tk)).json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["item_id"] == "quan-1"
    assert data["items"][0]["name"] == "Bún chả Hương Liên"


def test_luu_hai_lan_KHONG_bao_loi_va_khong_nhan_doi(client):
    """Mạng chậm nên người dùng bấm tim hai lần — không đáng nhận một thông báo lỗi."""
    tk = token_cua(client)
    body = {"item_type": "dish", "item_id": "pho-bo", "name": "Phở bò"}

    assert client.post(f"{API}/me/favorites", json=body, headers=auth(tk)).status_code == 201
    assert client.post(f"{API}/me/favorites", json=body, headers=auth(tk)).status_code == 201

    assert client.get(f"{API}/me/favorites", headers=auth(tk)).json()["data"]["total"] == 1


def test_loc_theo_loai(client):
    tk = token_cua(client)
    client.post(f"{API}/me/favorites", headers=auth(tk),
                json={"item_type": "dish", "item_id": "pho-bo", "name": "Phở bò"})
    client.post(f"{API}/me/favorites", headers=auth(tk),
                json={"item_type": "restaurant", "item_id": "q1", "name": "Quán 1"})

    chi_mon = client.get(f"{API}/me/favorites?item_type=dish", headers=auth(tk))
    assert chi_mon.json()["data"]["total"] == 1


def test_loai_khong_hop_le_thi_400_INVALID_REQUEST(client):
    tk = token_cua(client)
    res = client.post(
        f"{API}/me/favorites",
        json={"item_type": "nguoi-dung", "item_id": "x", "name": "X"},
        headers=auth(tk),
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_REQUEST"


def test_bo_luu_thu_von_khong_co_van_tra_200(client):
    """Thao tác này là "đưa về trạng thái mong muốn", kết quả cuối cùng giống hệt nhau."""
    tk = token_cua(client)
    assert client.delete(f"{API}/me/favorites/dish/khong-ton-tai",
                         headers=auth(tk)).status_code == 200


# ==========================================================================
# Số liệu · cấp độ · huy hiệu
# ==========================================================================


def test_tai_khoan_moi_moi_so_deu_la_0_that(client):
    """Bản thiết kế vẽ 27·15·18·5. Đó là minh hoạ, KHÔNG được chép vào code."""
    tk = token_cua(client)
    data = client.get(f"{API}/me/stats", headers=auth(tk)).json()["data"]

    assert data["saved_restaurants"] == 0
    assert data["saved_dishes"] == 0
    assert data["explorations"] == 0
    assert data["points"] == 0
    assert data["level"]["current"]["number"] == 1
    assert all(not b["earned"] for b in data["badges"])


def test_luu_mon_thi_diem_va_so_lieu_tang_that(client):
    tk = token_cua(client)
    client.post(f"{API}/me/favorites", headers=auth(tk),
                json={"item_type": "dish", "item_id": "pho-bo", "name": "Phở bò"})

    data = client.get(f"{API}/me/stats", headers=auth(tk)).json()["data"]
    assert data["saved_dishes"] == 1
    assert data["points"] > 0


def test_xem_chi_tiet_quan_lam_tang_LUOT_KHAM_PHA(client):
    tk = token_cua(client)
    client.post(
        f"{API}/interactions",
        json={
            "session_id": "phien-1",
            "restaurant_id": QUAN,
            "action_type": "view_detail",
            "dwell_time_ms": DU_LAU,
        },
        headers=auth(tk),
    )

    data = client.get(f"{API}/me/stats", headers=auth(tk)).json()["data"]
    assert data["explorations"] == 1


def test_khong_dang_nhap_thi_tuong_tac_van_ghi_duoc(client):
    """Khách vẫn phải ghi được nhật ký — đó là nguồn nhãn huấn luyện và nguồn báo đóng cửa."""
    res = client.post(
        f"{API}/interactions",
        json={
            "session_id": "phien-khach",
            "restaurant_id": QUAN,
            "action_type": "view_detail",
            "dwell_time_ms": DU_LAU,
        },
    )
    assert res.status_code == 201


def test_client_TU_KHAI_user_id_trong_body_thi_bi_BO_QUA(client):
    """Nếu không, ai cũng cộng điểm cho mình (hoặc cho người khác) bằng cách gọi thẳng API."""
    tk = token_cua(client, "nan-nhan")
    ke_gian = token_cua(client, "ke-gian")
    # Kẻ gian gọi bằng token CỦA MÌNH nhưng khai user_id của nạn nhân trong body.
    client.post(
        f"{API}/interactions",
        json={
            "session_id": "phien-x",
            "restaurant_id": QUAN,
            "action_type": "view_detail",
            "dwell_time_ms": DU_LAU,
            "user_id": "nan-nhan",
        },
        headers=auth(ke_gian),
    )

    # Điểm phải rơi vào KẺ GIAN (chủ của token), không phải nạn nhân.
    assert client.get(f"{API}/me/stats", headers=auth(tk)).json()["data"]["explorations"] == 0
    assert (
        client.get(f"{API}/me/stats", headers=auth(ke_gian)).json()["data"]["explorations"]
        == 1
    )


def test_bam_F5_20_lan_van_chi_duoc_tinh_1_luot(client):
    tk = token_cua(client)
    for i in range(20):
        client.post(
            f"{API}/interactions",
            json={
                "session_id": f"phien-{i}",
                "restaurant_id": QUAN,
                "action_type": "view_detail",
                "dwell_time_ms": DU_LAU,
            },
            headers=auth(tk),
        )

    assert client.get(f"{API}/me/stats", headers=auth(tk)).json()["data"]["explorations"] == 1

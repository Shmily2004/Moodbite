"""Khoá HỢP ĐỒNG của một kết quả tìm kiếm — mọi trường khai trong schema phải ra tới client.

BUG THẬT 2026-08-20. Bốn trường sau nằm đủ trong CSV (39.613/40.720 bản ghi có
`source_updated_at`), được repository đọc đúng, được use case gán đúng, và được khai
trong `SearchResultItemSchema`:

    temporarily_closed · source_updated_at · source_datasets · surveyed_at

Nhưng HAI router (`search.py` và `dishes.py`) tự tay dựng dict kết quả và **quên** cả
bốn. Pydantic có giá trị mặc định cho chúng nên response vẫn hợp lệ, không ai thấy lỗi:
API trả `temporarily_closed: null` cho 100% quán trong khi dữ liệu nói khác. Hậu quả
thấy được: giao diện không thể gắn nhãn "đang đóng tạm" dù backend đã cào về, và người
dùng đi tới nơi mới biết quán đang nghỉ.

VÌ SAO TEST CŨ KHÔNG BẮT ĐƯỢC: `test_closed_restaurants.py` dừng ở tầng domain
(`is_visible`) và chỉ GHI CHÚ rằng "phải gắn nhãn cảnh báo ở tầng API" — không có
assert nào ở tầng API. Ghi chú không phải là test.

VÌ SAO KIỂM CẢ HAI ENDPOINT: chúng là hai lối vào của cùng một danh sách quán
(CLAUDE.md mục 5 quy ước 4). Sửa một bên rồi quên bên kia là đúng cái sai đã xảy ra.
"""
import pytest

from tests import test_api, test_dish_api
from tests.fakes import make_restaurant

API = "/api/v1"
SESSION = "3f9a0000-0000-4000-8000-000000000000"

# Trường thuộc lớp "TUỔI THẬT & BẰNG CHỨNG" — thứ trả lời câu "quán này còn đúng không".
# Không có chúng thì giao diện chỉ còn cách im lặng, mà im lặng ở đây bị người dùng đọc
# thành "dữ liệu vừa được kiểm hôm qua".
QUAN_DONG_TAM = dict(
    temporarily_closed=True,
    source_updated_at="2019-04-02T00:00:00Z",
    source_datasets=["meta", "msft"],
    surveyed_at="2024-11-30",
)


def _quan_du_tin_hieu():
    return make_restaurant(
        "Quán Phở Nghỉ Sửa Nhà",
        category="Nhà hàng phở",
        lat=21.0285,
        lng=105.8542,
        **QUAN_DONG_TAM,
    )


def _kiem_du_bon_truong(item: dict) -> None:
    assert item["temporarily_closed"] is True, "cờ đóng tạm bị rơi trên đường ra client"
    assert item["source_updated_at"] == "2019-04-02T00:00:00Z"
    assert item["source_datasets"] == ["meta", "msft"]
    assert item["surveyed_at"] == "2024-11-30"


def test_search_tra_du_tuoi_that_va_co_dong_tam():
    """`POST /search` — lối vào thứ hai (tìm bằng câu tự do)."""
    client = test_api.make_client(restaurants=[_quan_du_tin_hieu()])

    response = client.post(
        f"{API}/search",
        json={"session_id": SESSION, "query_text": "phở", "latitude": 21.03, "longitude": 105.85},
    )

    assert response.status_code == 200
    results = response.json()["data"]["results"]
    assert results, "phải tìm được quán thì mới kiểm được trường của nó"
    _kiem_du_bon_truong(results[0])


def test_dishes_restaurants_tra_du_tuoi_that_va_co_dong_tam():
    """`GET /dishes/{id}/restaurants` — LUỒNG CHÍNH: chọn món trước, tìm quán sau."""
    quan = _quan_du_tin_hieu()
    client = test_dish_api.make_client(index={"pho-bo": [quan], "bun-cha": []})

    response = client.get(
        f"{API}/dishes/pho-bo/restaurants",
        params={"session_id": SESSION, "latitude": 21.03, "longitude": 105.85},
    )

    assert response.status_code == 200
    results = response.json()["data"]["results"]
    assert results, "phải tìm được quán thì mới kiểm được trường của nó"
    _kiem_du_bon_truong(results[0])


@pytest.mark.parametrize("gia_tri", [None, False])
def test_khong_biet_KHAC_biet_chac_dang_mo(gia_tri):
    """Ba trạng thái True/False/**None** phải đi nguyên vẹn qua HTTP.

    Ép `None` thành `False` ở tầng nào cũng là tự nhận đã xác minh 40.000 quán còn mở
    trong khi chưa kiểm quán nào (xem `test_closed_restaurants.py`).
    """
    quan = make_restaurant("Quán chưa rõ trạng thái", temporarily_closed=gia_tri)
    client = test_api.make_client(restaurants=[quan])

    response = client.post(
        f"{API}/search",
        json={"session_id": SESSION, "latitude": 21.03, "longitude": 105.85},
    )

    assert response.json()["data"]["results"][0]["temporarily_closed"] is gia_tri


def test_hai_endpoint_tra_CUNG_bo_truong():
    """Hai lối vào phải khác nhau về THỨ TỰ, không bao giờ khác nhau về TRƯỜNG.

    Đây là chốt chặn để lần sau thêm trường mới không lại rơi đúng một bên.
    """
    quan = _quan_du_tin_hieu()

    tim_kiem = test_api.make_client(restaurants=[quan]).post(
        f"{API}/search",
        json={"session_id": SESSION, "latitude": 21.03, "longitude": 105.85},
    ).json()["data"]["results"][0]

    theo_mon = test_dish_api.make_client(index={"pho-bo": [quan], "bun-cha": []}).get(
        f"{API}/dishes/pho-bo/restaurants",
        params={"session_id": SESSION, "latitude": 21.03, "longitude": 105.85},
    ).json()["data"]["results"][0]

    assert set(tim_kiem) == set(theo_mon)

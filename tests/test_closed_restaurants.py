"""Khoá lại việc XỬ LÝ QUÁN ĐÃ ĐÓNG CỬA.

Bug thật 2026-08-19: `permanentlyClosed` / `temporarilyClosed` do Apify cào về sẵn nhưng
`feature_engineering` cắt mất hai cột, nên 1 quán đóng hẳn + 15 quán đóng tạm vẫn được
gợi ý như quán bình thường. Người dùng đi tới nơi mới biết quán không còn.

BA TRẠNG THÁI, đừng rút xuống hai: True / False / None. 96,5% dataset (OSM + Overture)
không có trường này -> `None`. Ép `None` thành `False` là tự nhận đã xác minh 40.000 quán
còn mở trong khi chưa kiểm quán nào.
"""
from src.domain.services.search_ranking import rank_restaurants
from src.domain.value_objects.location import Location
from tests.fakes import make_restaurant

HANOI = Location(lat=21.03, lng=105.85)


def _ten_ket_qua(quans):
    return [r.restaurant.name for r in rank_restaurants(restaurants=quans, origin=HANOI, limit=10)]


# --- is_visible: gộp hai lý do ẩn khác nhau ----------------------------------


def test_quan_dong_han_KHONG_duoc_hien():
    quan = make_restaurant("Bún Ốc Hương Xưa", permanently_closed=True)
    assert quan.is_visible is False
    assert _ten_ket_qua([quan]) == []


def test_quan_dong_TAM_VAN_duoc_hien():
    """Nghỉ Tết hay sửa nhà vài tuần thì quán vẫn có thật và sẽ mở lại. Giấu đi thì người
    dùng tưởng quán biến mất luôn - nhưng phải gắn nhãn cảnh báo ở tầng API."""
    quan = make_restaurant("Of Him. Coffee", temporarily_closed=True)
    assert quan.is_visible is True
    assert _ten_ket_qua([quan]) == ["Of Him. Coffee"]


def test_khong_biet_trang_thai_thi_VAN_hien():
    """Quán OSM/Overture không có trường này. `None` KHÔNG được coi như đã đóng - làm thế
    là xoá 96,5% dataset."""
    quan = make_restaurant("Quán từ Overture")
    assert quan.permanently_closed is None
    assert quan.is_visible is True
    assert _ten_ket_qua([quan]) == ["Quán từ Overture"]


def test_admin_an_quan_van_hoat_dong_nhu_cu():
    """`is_visible` gộp thêm lý do mới nhưng KHÔNG được làm hỏng soft-delete sẵn có."""
    quan = make_restaurant("Quán bị admin ẩn", is_active=False)
    assert quan.is_visible is False
    assert _ten_ket_qua([quan]) == []


def test_hai_ly_do_an_van_phan_biet_duoc_nhau():
    """Admin phải biết quán biến mất vì MÌNH ẩn hay vì quán đã đóng - hai chuyện xử lý
    khác hẳn nhau, nên không được gộp thành một cờ duy nhất."""
    admin_an = make_restaurant("A", is_active=False)
    da_dong = make_restaurant("B", permanently_closed=True)

    assert admin_an.is_active is False and admin_an.permanently_closed is None
    assert da_dong.is_active is True and da_dong.permanently_closed is True


def test_chi_loai_quan_dong_han_trong_danh_sach_lon():
    quans = [
        make_restaurant("Đang mở"),
        make_restaurant("Đóng hẳn", permanently_closed=True),
        make_restaurant("Đóng tạm", temporarily_closed=True),
    ]
    ten = _ten_ket_qua(quans)
    assert "Đóng hẳn" not in ten
    assert {"Đang mở", "Đóng tạm"} <= set(ten)

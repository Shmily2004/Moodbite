"""Khoá lại phép SO SÁNH dữ liệu cào lại với dữ liệu đang dùng.

`so_sanh` là hàm THUẦN: nhận hai bộ, trả báo cáo. Không gọi mạng, không đọc file - nên
test được đầy đủ mà không phụ thuộc Overpass có sống hay không.
"""
from scripts.refresh_check import so_sanh
from tests.fakes import make_restaurant


def _cu(*cap):
    return {pid: make_restaurant(ten, place_id=pid) for pid, ten in cap}


def _moi(*cap):
    """`cap` = (place_id, tên) hoặc (place_id, tên, lat, lng)."""
    out = {}
    for item in cap:
        pid, ten = item[0], item[1]
        lat, lng = (item[2], item[3]) if len(item) > 3 else (21.03, 105.85)
        out[pid] = {"placeId": pid, "title": ten, "categoryName": "Nhà hàng",
                    "lat": lat, "lng": lng}
    return out


def test_phat_hien_quan_moi():
    bao_cao = so_sanh(_cu(("a", "Phở Thìn")), _moi(("a", "Phở Thìn"), ("b", "Bún Chả Mới")))

    assert [q["ten"] for q in bao_cao["quan_moi"]] == ["Bún Chả Mới"]
    assert bao_cao["quan_bien_mat"] == []


def test_phat_hien_quan_bien_mat():
    bao_cao = so_sanh(_cu(("a", "Phở Thìn"), ("b", "Quán Cũ")), _moi(("a", "Phở Thìn")))

    assert [q["ten"] for q in bao_cao["quan_bien_mat"]] == ["Quán Cũ"]


def test_phat_hien_doi_ten():
    bao_cao = so_sanh(_cu(("a", "Quán Ăn Bình Dân")), _moi(("a", "Nhà Hàng Sang Trọng")))

    assert bao_cao["quan_doi_ten"] == [
        {"place_id": "a", "ten_cu": "Quán Ăn Bình Dân", "ten_moi": "Nhà Hàng Sang Trọng"}
    ]


def test_chuan_hoa_CHINH_TA_khong_bi_coi_la_doi_ten():
    """Người vẽ bản đồ sửa "Pho Thin" thành "Phở Thìn" là thêm dấu, không phải quán đổi
    tên. Báo cả những thứ đó thì báo cáo đầy nhiễu và không ai đọc nữa."""
    bao_cao = so_sanh(_cu(("a", "Pho Thin")), _moi(("a", "Phở Thìn")))

    assert bao_cao["quan_doi_ten"] == []
    assert bao_cao["van_giu_nguyen"] == 1


def test_trung_TEN_nhung_O_XA_thi_van_la_hai_quan_khac_nhau():
    """"Phở Thìn" có nhiều hàng thật. Chỉ dựa vào tên mà gộp là giấu mất một quán -
    nên phải cùng tên VÀ ở gần nhau mới coi là một quán bị vẽ lại."""
    # 21.03 -> 21.10 cách khoảng 7,8km, xa hơn hẳn ngưỡng 150m.
    bao_cao = so_sanh(_cu(("a", "Phở Thìn")), _moi(("b", "Phở Thìn", 21.10, 105.85)))

    assert len(bao_cao["quan_moi"]) == 1
    assert len(bao_cao["quan_bien_mat"]) == 1
    assert bao_cao["quan_doi_id"] == []


def test_khong_doi_gi_thi_bao_cao_rong():
    bao_cao = so_sanh(_cu(("a", "Phở Thìn"), ("b", "Bún Chả")),
                      _moi(("a", "Phở Thìn"), ("b", "Bún Chả")))

    assert bao_cao["quan_moi"] == []
    assert bao_cao["quan_bien_mat"] == []
    assert bao_cao["quan_doi_ten"] == []
    assert bao_cao["van_giu_nguyen"] == 2


def test_quan_chi_DOI_ID_khong_bi_bao_la_bien_mat():
    """Người vẽ bản đồ xoá node cũ rồi vẽ lại thành đường bao toà nhà -> ID mới, tâm lệch
    vài chục mét. Nhìn từ ngoài giống hệt "đóng cửa + mở mới" nhưng thực ra không đổi gì.
    """
    bao_cao = so_sanh(_cu(("node-1", "Starbucks")), _moi(("way-9", "Starbucks")))

    assert bao_cao["quan_bien_mat"] == []
    assert bao_cao["quan_moi"] == []
    assert bao_cao["quan_doi_id"] == [
        {"place_id_cu": "node-1", "ten": "Starbucks", "place_id_moi": "way-9"}
    ]


def test_quan_bien_mat_that_su_van_duoc_bao():
    """Tách nhiễu ra không được phép nuốt luôn tín hiệu thật."""
    bao_cao = so_sanh(_cu(("a", "Quán Đóng Cửa Thật")), _moi(("b", "Quán Khác Hẳn")))

    assert [q["ten"] for q in bao_cao["quan_bien_mat"]] == ["Quán Đóng Cửa Thật"]
    assert [q["ten"] for q in bao_cao["quan_moi"]] == ["Quán Khác Hẳn"]
    assert bao_cao["quan_doi_id"] == []

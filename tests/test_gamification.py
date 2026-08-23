"""Test ĐIỂM · CẤP ĐỘ · HUY HIỆU và bộ đếm hoạt động.

Thuần domain — không import fastapi, không đụng CSDL. Nếu một ngày phải import chúng để
test được mấy quy tắc này thì tức là quy tắc đã nằm sai tầng (CLAUDE.md mục 2).

Trọng tâm là những chỗ SAI THÌ NGUY:
  - đếm số lần bấm thay vì đếm thứ khác nhau  -> cày cấp bằng F5
  - khách chưa đăng nhập bị gộp chung một rổ  -> điểm của người này chảy sang người khác
  - thanh tiến độ tính trên tổng điểm         -> người mới nhìn thấy thanh trống mãi
"""
from __future__ import annotations

from src.domain.entities.interaction import ActionType
from src.domain.services.activity_tally import ActivityTally
from src.domain.services.gamification import (
    BADGES,
    DIEM_BAO_DONG_CUA,
    DIEM_LUU,
    DIEM_XEM_QUAN,
    LEVELS,
    UserActivity,
    tinh_cap_do,
    tinh_huy_hieu,
)

DU_LAU = 5000  # ms — trên ngưỡng MIN_POSITIVE_DWELL_MS


# ==========================================================================
# Bảng điểm
# ==========================================================================


def test_tai_khoan_moi_co_dung_0_diem_va_cap_1():
    """Không có hoạt động nào thì mọi số phải là 0 THẬT, không phải số minh hoạ."""
    tien_do = tinh_cap_do(UserActivity().points)

    assert UserActivity().points == 0
    assert tien_do.level.number == 1
    assert tien_do.ratio == 0.0


def test_diem_cong_dung_theo_bang():
    hoat_dong = UserActivity(viewed_restaurants=3, saved_items=2, closure_reports=1)

    assert hoat_dong.points == 3 * DIEM_XEM_QUAN + 2 * DIEM_LUU + DIEM_BAO_DONG_CUA


def test_bao_dong_cua_dang_gia_hon_xem_quan():
    """Đóng góp cho cộng đồng phải hơn tiêu thụ — nguyên tắc 3 của bảng điểm."""
    assert DIEM_BAO_DONG_CUA > DIEM_LUU > DIEM_XEM_QUAN


# ==========================================================================
# Cấp độ
# ==========================================================================


def test_moc_cap_do_tang_dan_va_bat_dau_tu_0():
    assert LEVELS[0].min_points == 0
    moc = [c.min_points for c in LEVELS]
    assert moc == sorted(moc) and len(set(moc)) == len(moc)


def test_dung_moc_thi_len_cap():
    """Đúng bằng ngưỡng đã là cấp mới, không phải hơn ngưỡng."""
    assert tinh_cap_do(LEVELS[1].min_points).level.number == 2
    assert tinh_cap_do(LEVELS[1].min_points - 1).level.number == 1


def test_thanh_tien_do_tinh_TRONG_khoang_hai_cap():
    """Nửa đường từ cấp 1 sang cấp 2 phải là 0.5, không phải điểm/tổng-điểm-tối-đa."""
    giua = (LEVELS[0].min_points + LEVELS[1].min_points) // 2
    tien_do = tinh_cap_do(giua)

    assert tien_do.level.number == 1
    assert abs(tien_do.ratio - 0.5) < 0.05


def test_cap_cao_nhat_khong_con_cap_ke_tiep():
    tien_do = tinh_cap_do(LEVELS[-1].min_points + 10_000)

    assert tien_do.next_level is None
    assert tien_do.points_to_next is None
    assert tien_do.ratio == 1.0  # thanh đầy, không chia cho 0


def test_diem_am_khong_lam_no():
    """Dữ liệu hỏng không được làm sập trang tài khoản."""
    assert tinh_cap_do(-50).level.number == 1


# ==========================================================================
# Huy hiệu
# ==========================================================================


def test_tra_ve_TOAN_BO_huy_hieu_ke_ca_cai_chua_dat():
    """Huy hiệu mờ kèm tiến độ mới cho người dùng biết phải làm gì tiếp."""
    ket_qua = tinh_huy_hieu(UserActivity())

    assert len(ket_qua) == len(BADGES)
    assert all(not b.earned for b in ket_qua)


def test_dat_huy_hieu_khi_du_nguong():
    explorer = next(b for b in BADGES if b.badge_id == "explorer")
    ket_qua = tinh_huy_hieu(UserActivity(viewed_restaurants=explorer.target))

    assert next(b for b in ket_qua if b.rule.badge_id == "explorer").earned


def test_moi_huy_hieu_deu_tro_toi_mot_truong_CO_THAT():
    """Chống lỗi gõ nhầm tên trường: `getattr` sai tên sẽ im lặng trả 0 mãi mãi."""
    for rule in BADGES:
        assert hasattr(UserActivity(), rule.field_name), rule.badge_id
        assert rule.target >= 1


# ==========================================================================
# Bộ đếm hoạt động — chỗ dễ cày điểm nhất
# ==========================================================================


def test_xem_mot_quan_20_lan_van_chi_tinh_1():
    """Không có luật này thì cấp độ chỉ đo được ai bấm F5 nhiều hơn."""
    tally = ActivityTally()
    for _ in range(20):
        tally.record("u1", ActionType.VIEW_DETAIL, "quan-a", "2026-08-22", DU_LAU)

    assert tally.snapshot("u1").viewed_restaurants == 1


def test_xem_luot_qua_roi_thoat_KHONG_tinh_la_kham_pha():
    tally = ActivityTally()
    tally.record("u1", ActionType.VIEW_DETAIL, "quan-a", "2026-08-22", dwell_time_ms=200)

    assert tally.snapshot("u1").explorations == 0


def test_khach_chua_dang_nhap_bi_bo_qua_hoan_toan():
    """`user_id` rỗng không được gom vào một rổ chung — sẽ thành điểm của người khác."""
    tally = ActivityTally()
    tally.record(None, ActionType.VIEW_DETAIL, "quan-a", "2026-08-22", DU_LAU)
    tally.record("", ActionType.VIEW_DETAIL, "quan-b", "2026-08-22", DU_LAU)

    assert tally.tracked_users == 0


def test_hoat_dong_cua_hai_nguoi_KHONG_lan_sang_nhau():
    tally = ActivityTally()
    tally.record("u1", ActionType.VIEW_DETAIL, "quan-a", "2026-08-22", DU_LAU)
    tally.record("u2", ActionType.VIEW_DETAIL, "quan-b", "2026-08-22", DU_LAU)

    assert tally.snapshot("u1").viewed_restaurants == 1
    assert tally.snapshot("u2").viewed_restaurants == 1
    assert tally.snapshot("u1").points == tally.snapshot("u2").points


def test_dem_so_NGAY_khac_nhau_chu_khong_phai_so_luot():
    tally = ActivityTally()
    for _ in range(5):
        tally.record("u1", ActionType.GET_DIRECTIONS, "quan-a", "2026-08-20")
    tally.record("u1", ActionType.GET_DIRECTIONS, "quan-b", "2026-08-21")

    assert tally.snapshot("u1").active_days == 2


def test_luot_SAVE_khong_tinh_o_tally():
    """Số mục đã lưu lấy từ bảng `saved_items` — nguồn sự thật của "đang lưu".

    Nếu đếm cả ở đây thì lưu rồi bỏ lưu vẫn còn điểm, tức là cày điểm được bằng cách bấm
    tim rồi bỏ tim liên tục.
    """
    tally = ActivityTally()
    tally.record("u1", ActionType.SAVE, "quan-a", "2026-08-22")

    assert tally.snapshot("u1", saved_items=0).points == 0


def test_snapshot_nhan_so_muc_da_luu_tu_ben_ngoai():
    tally = ActivityTally()

    assert tally.snapshot("u1", saved_items=3).points == 3 * DIEM_LUU

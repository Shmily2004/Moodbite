"""Mọi hành động nhật ký đều phải có NHÃN tiếng Việt.

VÌ SAO CÓ TEST NÀY: thiếu nhãn thì `AuditEntry.nhan` lặng lẽ trả về mã kỹ thuật
(`update_dish`) và màn "Nhật ký hoạt động" hiện nguyên mã cho người quản trị. Lỗi này đã
xảy ra thật: `UPDATE_DISH` được thêm từ trước nhưng quên nhãn, không test nào bắt được.
"""
from src.domain.entities.audit_log import NHAN_HANH_DONG, AuditAction


def test_moi_hanh_dong_co_nhan_tieng_viet():
    thieu = [a.value for a in AuditAction if a not in NHAN_HANH_DONG]
    assert thieu == [], f"Thiếu nhãn cho: {thieu}"


def test_nhan_khong_rong_va_khong_trung_ma_ky_thuat():
    for hanh_dong, nhan in NHAN_HANH_DONG.items():
        assert nhan.strip(), hanh_dong
        assert nhan != hanh_dong.value, f"Nhãn của {hanh_dong.value} vẫn là mã kỹ thuật"

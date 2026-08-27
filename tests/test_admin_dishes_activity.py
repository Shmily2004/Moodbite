"""Ba màn quản trị mới (2026-08-26): danh mục MÓN · NHẬT KÝ hoạt động · thông tin HỆ THỐNG.

Cái đáng khoá ở đây:

  1. Màn MÓN của admin phải thấy ĐÚNG những thứ người dùng KHÔNG được thấy — món chưa có
     quán (557) và danh mục ("Bún"). Lọc nhầm là admin mất khả năng tìm món đang thiếu.
  2. NHẬT KÝ phải ghi được ai-làm-gì, và ghi nhật ký hỏng TUYỆT ĐỐI không được làm hỏng
     chính thao tác nó đang ghi.
  3. Màn HỆ THỐNG tuyệt đối KHÔNG lộ secret. Trang quản trị chạy trong trình duyệt.
"""
from __future__ import annotations

import json

import pytest

from src.domain.entities.audit_log import (
    AuditAction,
    AuditEntry,
    InvalidAuditEntry,
    tom_tat_thay_doi,
    validate_audit_entry,
)
from src.application.use_cases.manage_audit_log import GhiNhatKyUseCase
from src.infrastructure.repositories.sqlite_audit_log_repository import (
    SqliteAuditLogRepository,
)
from tests.test_admin_api import API, auth_header, build_client, db  # noqa: F401


@pytest.fixture
def client(db):  # noqa: F811
    c, _ = build_client(db)
    return c


# ==========================================================================
# Nhật ký — tầng domain
# ==========================================================================


def test_tom_tat_chi_neu_truong_THUC_SU_doi():
    """Bản ghi quán có hơn 30 trường; liệt kê hết thì dòng nào cũng giống dòng nào."""
    cau = tom_tat_thay_doi(
        {"name": "Phở Thìn", "phone": None, "website": "https://a.vn"},
        {"name": "Phở Thìn 13 Lò Đúc", "phone": None, "website": "https://a.vn"},
    )

    assert "name" in cau
    assert "phone" not in cau, "Đang nêu cả trường không đổi"
    assert "website" not in cau


def test_tom_tat_hien_None_thanh_trong_chu_khong_phai_chu_None():
    """Người đọc nhật ký là người, không phải lập trình viên đọc repr Python."""
    cau = tom_tat_thay_doi({"phone": None}, {"phone": "024-1234"})

    assert "(trống)" in cau
    assert "None" not in cau


def test_khong_co_gi_doi_van_ghi_mot_cau_co_nghia():
    """Gửi đúng y giá trị đang có cũng là thao tác có thật — không để dòng trống nghĩa."""
    assert tom_tat_thay_doi({"name": "A"}, {"name": "A"}) == "Không có trường nào thay đổi"


def test_thieu_actor_thi_bao_loi():
    """Không biết ai làm thì ghi lại vô nghĩa."""
    with pytest.raises(InvalidAuditEntry):
        validate_audit_entry("", "hide_restaurant", "restaurant", "r1", "x")


def test_action_la_thu_khong_ton_tai_thi_bao_loi():
    with pytest.raises(InvalidAuditEntry) as loi:
        validate_audit_entry("admin", "xoa_sach_du_lieu", "restaurant", "r1", "x")
    assert "hide_restaurant" in str(loi.value), "Câu lỗi phải nêu giá trị hợp lệ"


# ==========================================================================
# Nhật ký — tầng kho + use case
# ==========================================================================


def test_nhat_ky_moi_nhat_dung_dau(tmp_path):
    kho = SqliteAuditLogRepository(tmp_path / "u.db")
    for i in range(3):
        kho.add(
            AuditEntry(
                actor="admin",
                action=AuditAction.HIDE_RESTAURANT,
                target_type="restaurant",
                target_id=f"r{i}",
                summary=f"lần {i}",
            )
        )

    gan_nhat = kho.list_recent(limit=10)

    assert [e.target_id for e in gan_nhat] == ["r2", "r1", "r0"]


def test_loc_theo_hanh_dong(tmp_path):
    kho = SqliteAuditLogRepository(tmp_path / "u.db")
    kho.add(AuditEntry("admin", AuditAction.HIDE_RESTAURANT, "restaurant", "r1", "ẩn"))
    kho.add(AuditEntry("admin", AuditAction.CREATE_RESTAURANT, "restaurant", "r2", "thêm"))

    assert len(kho.list_recent(action="hide_restaurant")) == 1


def test_GHI_NHAT_KY_HONG_KHONG_LAM_HONG_THAO_TAC():
    """Chốt chặn quan trọng nhất của cả tính năng nhật ký.

    Nếu ghi nhật ký ném lỗi ra ngoài thì: quán ĐÃ bị ẩn trong CSDL -> ghi nhật ký hỏng
    -> trả 500 -> admin thấy "thất bại" nên bấm lại -> "quán đã ẩn rồi" -> bối rối hoàn
    toàn. Thao tác chính đã xong và không rút lại được.
    """

    class KhoNo:
        is_ready = True

        def add(self, entry):
            raise RuntimeError("ổ đĩa đầy")

    ket_qua = GhiNhatKyUseCase(KhoNo()).ghi(
        actor="admin",
        action="hide_restaurant",
        target_type="restaurant",
        target_id="r1",
        summary="x",
    )

    assert ket_qua is False, "Phải trả False chứ KHÔNG được ném lỗi ra ngoài"


def test_khong_co_kho_nhat_ky_thi_ghi_im_lang_bo_qua():
    assert (
        GhiNhatKyUseCase(None).ghi(
            actor="admin",
            action="hide_restaurant",
            target_type="restaurant",
            target_id="r1",
            summary="x",
        )
        is False
    )


# ==========================================================================
# Nhật ký — tầng HTTP, đi qua thao tác thật
# ==========================================================================


def test_an_quan_thi_CO_dong_nhat_ky(client):
    h = auth_header(client)
    truoc = client.get(f"{API}/admin/activity", headers=h).json()["data"]["total"]

    client.post(f"{API}/admin/restaurants/pho-1/hide", headers=h)

    data = client.get(f"{API}/admin/activity", headers=h).json()["data"]
    assert data["total"] == truoc + 1
    dong = data["entries"][0]
    assert dong["action"] == "hide_restaurant"
    assert dong["actor"], "Không ghi lại ai làm"
    assert "Phở Bò Hàng Đồng" in dong["summary"]


def test_sua_quan_thi_nhat_ky_noi_ro_CU_ROI_MOI(client):
    h = auth_header(client)

    client.patch(f"{API}/admin/restaurants/pho-1", headers=h, json={"phone": "024-999"})

    dong = client.get(f"{API}/admin/activity", headers=h).json()["data"]["entries"][0]
    assert dong["action"] == "update_restaurant"
    assert "phone" in dong["summary"]
    assert "024-999" in dong["summary"]


def test_nhat_ky_can_token(client):
    assert client.get(f"{API}/admin/activity").status_code == 401


# ==========================================================================
# Danh mục món cho quản trị
# ==========================================================================


def test_mon_can_token(client):
    assert client.get(f"{API}/admin/dishes").status_code == 401


def test_tra_ve_ca_TONG_lan_SO_DONG(client):
    """Thiếu `total` thì giao diện hiện "50 món" trong khi bộ lọc khớp 557."""
    data = client.get(f"{API}/admin/dishes?limit=1", headers=auth_header(client)).json()["data"]

    assert "total" in data and "returned" in data
    assert data["returned"] <= data["total"]


def test_moi_dong_mon_deu_khai_co_quan_hay_khong(client):
    """`is_active` là thứ admin dựa vào để tìm món chưa khớp được quán nào."""
    data = client.get(f"{API}/admin/dishes", headers=auth_header(client)).json()["data"]

    for x in data["results"]:
        assert isinstance(x["is_active"], bool)
        assert isinstance(x["is_category"], bool)
        assert isinstance(x["has_description"], bool)


# ==========================================================================
# Thông tin hệ thống
# ==========================================================================


def test_he_thong_can_token(client):
    assert client.get(f"{API}/admin/system").status_code == 401


def test_he_thong_TUYET_DOI_KHONG_LO_SECRET(client):
    """Trang quản trị chạy trong trình duyệt — mọi thứ gửi ra đây coi như đã lộ.

    Test này đỏ nghĩa là ai đó vừa thêm một trường tiện-cho-gỡ-lỗi mà không nghĩ tới
    chuyện nó đi thẳng ra trình duyệt.
    """
    data = client.get(f"{API}/admin/system", headers=auth_header(client)).json()["data"]

    raw = json.dumps(data).lower()
    for cam in ("password", "secret", "_hash", "smtp_pass", "bearer"):
        assert cam not in raw, f"Đang lộ '{cam}' ra trang quản trị"


def test_he_thong_bao_trang_thai_tung_kho(client):
    data = client.get(f"{API}/admin/system", headers=auth_header(client)).json()["data"]

    assert data["services"], "Không báo kho nào"
    for s in data["services"]:
        assert isinstance(s["ready"], bool)
        assert s["label"]

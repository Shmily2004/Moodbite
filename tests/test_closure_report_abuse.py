"""Chống LẠM DỤNG nút "quán này đã đóng cửa" + cho admin GỠ được lượt báo.

BUG THẬT (rà soát 2026-10-06), tái hiện được:
  1. `POST /interactions` không cần đăng nhập, không giới hạn tần suất, và bộ đếm đếm theo
     `session_id` — chuỗi do CLIENT tự đặt. 3 lượt `report_closed` với 3 session_id bịa
     là ẩn được BẤT KỲ quán nào khỏi MỌI luồng, cho MỌI người dùng.
  2. Admin không gỡ được: `ClosureReportTally` không có hàm xoá, nút "khôi phục" của admin
     chỉ đặt `is_active=1`, và lượt báo được phát lại từ `interactions.jsonl` mỗi lần khởi
     động -> quán bị ẩn VĨNH VIỄN.
  3. Comment ở `closure_reports.py` ghi "admin bỏ ẩn lại được" — sai sự thật.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from src.application.use_cases.log_interaction import (
    LogInteractionCommand,
    LogInteractionUseCase,
)
from src.application.use_cases.manage_closure_reports import (
    ClearClosureReportsUseCase,
    ListClosureReportsUseCase,
)
from src.domain.services.closure_reports import (
    MIN_REPORTS_TO_HIDE,
    ClosureReportTally,
    reporter_key_from_ip,
    tally_from_events,
)
from src.infrastructure.repositories.jsonl_interaction_repository import (
    JsonlInteractionRepository,
)
from src.presentation.api.main import create_app
from tests.fakes import FakeRestaurantRepo, make_restaurant
from tests.test_api import SESSION, _container

API = "/api/v1"
QUAN = "id-Quan Pho"   # place_id của quán mặc định trong `tests.test_api._container`


# --- Miền: bộ đếm có thể XOÁ -----------------------------------------------------------


def test_xoa_luot_bao_thi_quan_hien_lai_va_dem_lai_tu_dau():
    tally = ClosureReportTally()
    for i in range(MIN_REPORTS_TO_HIDE):
        tally.record("q1", f"ip:{i}")
    assert tally.is_reported_closed("q1")

    assert tally.clear("q1") == MIN_REPORTS_TO_HIDE

    assert tally.is_reported_closed("q1") is False
    assert tally.report_count("q1") == 0
    # Người cũ báo lại thì tính lại từ đầu — xoá là "bắt đầu lại", không phải "miễn nhiễm".
    tally.record("q1", "ip:0")
    assert tally.report_count("q1") == 1


def test_xoa_quan_chua_ai_bao_tra_0_khong_no():
    assert ClosureReportTally().clear("q-khong-co") == 0


def test_khoa_nguoi_bao_KHONG_chua_IP_tho():
    """Nhật ký tương tác là dữ liệu huấn luyện, không được chứa IP gốc."""
    khoa = reporter_key_from_ip("203.0.113.7", salt="muoi")
    assert "203.0.113.7" not in khoa
    assert khoa == reporter_key_from_ip("203.0.113.7", salt="muoi")
    assert khoa != reporter_key_from_ip("203.0.113.8", salt="muoi")


# --- Use case ghi tương tác: đếm theo NGƯỜI BÁO do server xác định -----------------------


def _use_case(tmp_path):
    quan = make_restaurant("Quan Pho", place_id=QUAN)
    log = JsonlInteractionRepository(tmp_path / "interactions.jsonl")
    tally = ClosureReportTally()
    uc = LogInteractionUseCase(log, FakeRestaurantRepo([quan]), closure_tally=tally)
    return uc, tally, log


def _bao(uc, session, reporter_key):
    uc.execute(LogInteractionCommand(
        session_id=session, restaurant_id=QUAN, action_type="report_closed",
        reporter_key=reporter_key,
    ))


def test_doi_session_id_KHONG_tang_so_nguoi_bao(tmp_path):
    uc, tally, _ = _use_case(tmp_path)
    for i in range(MIN_REPORTS_TO_HIDE + 2):
        _bao(uc, f"phien-bia-{i}", reporter_key="ip:cung-mot-may")
    assert tally.report_count(QUAN) == 1
    assert tally.is_reported_closed(QUAN) is False


def test_nguoi_bao_KHAC_NHAU_thi_moi_du_nguong(tmp_path):
    uc, tally, _ = _use_case(tmp_path)
    for i in range(MIN_REPORTS_TO_HIDE):
        _bao(uc, "cung-phien", reporter_key=f"ip:may-{i}")
    assert tally.is_reported_closed(QUAN) is True


def test_khong_co_khoa_nguoi_bao_thi_ghi_nhat_ky_nhung_KHONG_dem(tmp_path):
    """Lời gọi không đi qua HTTP (script, test cũ) không có cách nào xác minh người báo."""
    uc, tally, log = _use_case(tmp_path)
    _bao(uc, "s", reporter_key=None)
    assert tally.report_count(QUAN) == 0
    assert log.count() == 1


def test_nhat_ky_ghi_khoa_nguoi_bao_de_phat_lai_luc_khoi_dong(tmp_path):
    uc, _, log = _use_case(tmp_path)
    for i in range(MIN_REPORTS_TO_HIDE):
        _bao(uc, "s", reporter_key=f"ip:{i}")

    tally_moi = tally_from_events(log.replay_closure_events())

    assert tally_moi.is_reported_closed(QUAN) is True


# --- Phát lại nhật ký: bản ghi cũ + sự kiện xoá -----------------------------------------


def _ghi(path, *recs):
    with open(path, "a", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_ban_ghi_CU_khong_co_khoa_nguoi_bao_KHONG_duoc_tinh(tmp_path):
    """Quyết định 2026-10-06: lượt báo cũ chỉ có session_id (client tự đặt, không xác minh
    được) -> giữ trong nhật ký nhưng KHÔNG dùng để ẩn quán nữa."""
    path = tmp_path / "interactions.jsonl"
    _ghi(path, *[
        {"action_type": "report_closed", "restaurant_id": "q1", "session_id": f"s{i}"}
        for i in range(5)
    ])
    tally = tally_from_events(JsonlInteractionRepository(path).replay_closure_events())
    assert tally.is_reported_closed("q1") is False


def test_su_kien_XOA_duoc_phat_lai_dung_thu_tu(tmp_path):
    path = tmp_path / "interactions.jsonl"
    bao = lambda k: {"action_type": "report_closed", "restaurant_id": "q1",  # noqa: E731
                     "session_id": "s", "reporter_key": k}
    repo = JsonlInteractionRepository(path)
    _ghi(path, bao("ip:a"), bao("ip:b"), bao("ip:c"))
    repo.append_closure_reports_cleared("q1", actor="admin")
    _ghi(path, bao("ip:d"))

    tally = tally_from_events(repo.replay_closure_events())

    # Ba lượt TRƯỚC lần xoá không còn tính; chỉ còn lượt sau.
    assert tally.report_count("q1") == 1
    assert tally.is_reported_closed("q1") is False


def test_su_kien_xoa_KHONG_lam_ban_thong_ke_tuong_tac(tmp_path):
    repo = JsonlInteractionRepository(tmp_path / "interactions.jsonl")
    repo.append_closure_reports_cleared("q1", actor="admin")
    assert repo.read_records() == []
    assert repo.replay_user_activity() == []


# --- HTTP: người báo xác định bằng IP, không phải session_id ------------------------------


def _client_bao_dong_cua(tmp_path):
    c = _container()
    log = JsonlInteractionRepository(tmp_path / "interactions.jsonl")
    c.interaction_repository = log
    c.log_interaction = LogInteractionUseCase(
        log, c.restaurant_repository, closure_tally=c.closure_tally
    )
    return TestClient(create_app(container=c), raise_server_exceptions=False), c, log


def test_HTTP_ba_session_id_bia_tu_MOT_may_KHONG_an_duoc_quan(tmp_path):
    client, c, _ = _client_bao_dong_cua(tmp_path)
    for i in range(MIN_REPORTS_TO_HIDE):
        res = client.post(f"{API}/interactions", json={
            "session_id": f"bia-{i}", "restaurant_id": QUAN,
            "action_type": "report_closed",
        })
        assert res.status_code == 201, res.text

    assert c.closure_tally.report_count(QUAN) == 1
    ids = [r["restaurant_id"] for r in client.post(
        f"{API}/search", json={"session_id": SESSION}
    ).json()["data"]["results"]]
    assert QUAN in ids


def test_HTTP_nhat_ky_co_khoa_nguoi_bao_nhung_khong_co_IP(tmp_path):
    client, _, log = _client_bao_dong_cua(tmp_path)
    client.post(f"{API}/interactions", json={
        "session_id": "s", "restaurant_id": QUAN, "action_type": "report_closed",
    })
    dong = log.path.read_text(encoding="utf-8")
    rec = json.loads(dong.splitlines()[-1])
    assert rec["reporter_key"]
    assert "testclient" not in dong     # host mà TestClient dùng làm "IP"


def test_HTTP_tuong_tac_thuong_KHONG_ghi_khoa_nguoi_bao(tmp_path):
    """Chỉ lượt báo đóng cửa mới cần; ghi cho mọi tương tác là thu thập dữ liệu thừa."""
    client, _, log = _client_bao_dong_cua(tmp_path)
    client.post(f"{API}/interactions", json={
        "session_id": "s", "restaurant_id": QUAN, "action_type": "view_detail",
        "dwell_time_ms": 5000,
    })
    rec = json.loads(log.path.read_text(encoding="utf-8").splitlines()[-1])
    assert "reporter_key" not in rec


# --- Use case quản trị -------------------------------------------------------------------


def test_use_case_xoa_ghi_nhat_ky_TRUOC_roi_moi_xoa_bo_dem(tmp_path):
    uc, tally, log = _use_case(tmp_path)
    for i in range(MIN_REPORTS_TO_HIDE):
        _bao(uc, "s", f"ip:{i}")
    restaurants = FakeRestaurantRepo([make_restaurant("Quan Pho", place_id=QUAN)])
    clear = ClearClosureReportsUseCase(tally=tally, log=log, restaurants=restaurants)

    kq = clear.execute(QUAN, actor="admin")

    assert kq.cleared_reports == MIN_REPORTS_TO_HIDE
    assert tally.is_reported_closed(QUAN) is False
    # Khởi động lại (phát lại nhật ký) vẫn giữ trạng thái đã xoá.
    assert tally_from_events(log.replay_closure_events()).is_reported_closed(QUAN) is False


def test_use_case_xoa_quan_khong_ton_tai_va_khong_co_luot_bao_thi_404(tmp_path):
    from src.application.use_cases.log_interaction import RestaurantNotFoundError

    _, tally, log = _use_case(tmp_path)
    clear = ClearClosureReportsUseCase(
        tally=tally, log=log, restaurants=FakeRestaurantRepo([])
    )
    with pytest.raises(RestaurantNotFoundError):
        clear.execute("khong-co", actor="admin")


def test_use_case_xoa_duoc_ca_quan_da_bien_khoi_du_lieu_neu_con_luot_bao(tmp_path):
    """Quán bị xoá khỏi dataset nhưng vẫn còn lượt báo treo trong bộ đếm -> admin vẫn
    phải dọn được, nếu không danh sách "đang bị báo" có dòng không bao giờ xoá nổi."""
    _, tally, log = _use_case(tmp_path)
    tally.record("ma-cu", "ip:x")
    clear = ClearClosureReportsUseCase(
        tally=tally, log=log, restaurants=FakeRestaurantRepo([])
    )
    assert clear.execute("ma-cu", actor="admin").cleared_reports == 1


def test_liet_ke_quan_dang_bi_bao(tmp_path):
    _, tally, _ = _use_case(tmp_path)
    for i in range(MIN_REPORTS_TO_HIDE):
        tally.record(QUAN, f"ip:{i}")
    tally.record("q-le", "ip:z")
    restaurants = FakeRestaurantRepo([make_restaurant("Quan Pho", place_id=QUAN)])

    rows = ListClosureReportsUseCase(tally=tally, restaurants=restaurants).execute()

    assert [(r.restaurant_id, r.report_count, r.is_hidden) for r in rows] == [
        (QUAN, MIN_REPORTS_TO_HIDE, True),
        ("q-le", 1, False),
    ]
    assert rows[0].name == "Quan Pho"
    # Quán không còn trong dữ liệu: tên là None (chưa biết), KHÔNG bịa.
    assert rows[1].name is None


# --- HTTP quản trị -----------------------------------------------------------------------


@pytest.fixture
def admin_client(tmp_path):
    from src.application.use_cases.manage_closure_reports import (
        ClearClosureReportsUseCase as Clear,
        ListClosureReportsUseCase as List_,
    )
    from tests.test_admin_api import build_client
    from tests.test_sqlite_repository import make_db

    db = make_db(tmp_path, {"place_id": "pho-1", "name": "Phở Bò Hàng Đồng"})
    client, repo = build_client(db)
    c = client.app.state.container
    log = JsonlInteractionRepository(tmp_path / "interactions.jsonl")
    tally = c.closure_tally
    c.interaction_repository = log
    c.log_interaction = LogInteractionUseCase(log, repo, closure_tally=tally)
    c.list_closure_reports = List_(tally=tally, restaurants=repo, admin_restaurants=repo)
    c.clear_closure_reports = Clear(
        tally=tally, log=log, restaurants=repo, admin_restaurants=repo,
        audit=c.ghi_nhat_ky,
    )
    return client, c, log


def test_HTTP_admin_xoa_luot_bao_can_dang_nhap(admin_client):
    client, _, _ = admin_client
    assert client.get(f"{API}/admin/closure-reports").status_code == 401
    res = client.post(f"{API}/admin/restaurants/pho-1/closure-reports/clear")
    assert res.status_code == 401


def test_HTTP_admin_xem_va_xoa_luot_bao(admin_client):
    from tests.test_admin_api import auth_header

    client, c, log = admin_client
    for i in range(MIN_REPORTS_TO_HIDE):
        c.closure_tally.record("pho-1", f"ip:{i}")
    h = auth_header(client)

    ds = client.get(f"{API}/admin/closure-reports", headers=h)
    assert ds.status_code == 200, ds.text
    data = ds.json()["data"]
    assert data["threshold"] == MIN_REPORTS_TO_HIDE
    assert data["items"] == [{
        "restaurant_id": "pho-1", "name": "Phở Bò Hàng Đồng",
        "report_count": MIN_REPORTS_TO_HIDE, "is_hidden": True,
    }]

    res = client.post(f"{API}/admin/restaurants/pho-1/closure-reports/clear", headers=h)
    assert res.status_code == 200, res.text
    assert res.json()["data"] == {
        "restaurant_id": "pho-1", "cleared_reports": MIN_REPORTS_TO_HIDE,
        "is_hidden": False,
    }
    assert c.closure_tally.is_reported_closed("pho-1") is False
    # Bền qua khởi động lại.
    assert tally_from_events(log.replay_closure_events()).is_reported_closed("pho-1") is False
    # Có dấu vết trong nhật ký hoạt động quản trị.
    hang = client.get(f"{API}/admin/activity", headers=h).json()["data"]["entries"]
    assert any(
        e["action"] == "clear_closure_reports" and e["target_id"] == "pho-1" for e in hang
    )


def test_HTTP_admin_xoa_quan_khong_ton_tai_404(admin_client):
    from tests.test_admin_api import auth_header

    client, _, _ = admin_client
    res = client.post(
        f"{API}/admin/restaurants/khong-co/closure-reports/clear",
        headers=auth_header(client),
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESTAURANT_NOT_FOUND"

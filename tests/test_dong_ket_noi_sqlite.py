"""Mọi kết nối SQLite phải được ĐÓNG sau mỗi lần gọi repository (phát hiện 2026-10-02).

`with sqlite3.connect(...) as conn:` chỉ commit/rollback, KHÔNG đóng kết nối - hiểu lầm
rất phổ biến về thư viện chuẩn. Hậu quả đo được: pytest in ~30.000 ResourceWarning
"unclosed database", và trên Windows file .db bị giữ handle tới lúc bộ gom rác chạy (chặn
xoá/thay file CSDL, làm hỏng ngẫu nhiên việc dọn thư mục tạm).
"""
import sqlite3

import pytest

from src.domain.entities.user import User
from src.infrastructure.repositories.sqlite_audit_log_repository import (
    SqliteAuditLogRepository,
)
from src.infrastructure.repositories.sqlite_issue_resolution_repository import (
    SqliteIssueResolutionRepository,
)
from src.infrastructure.repositories.sqlite_quality_snapshot_repository import (
    SqliteQualitySnapshotRepository,
)
from src.infrastructure.repositories.sqlite_restaurant_repository import (
    SqliteRestaurantRepository,
)
from src.infrastructure.repositories.sqlite_saved_item_repository import (
    SqliteSavedItemRepository,
)
from src.infrastructure.repositories.sqlite_user_repository import SqliteUserRepository
from tests.test_sqlite_repository import make_db


@pytest.fixture
def ket_noi_da_mo(monkeypatch):
    """Ghi lại MỌI kết nối được mở trong lúc test chạy."""
    goc = sqlite3.connect
    da_mo = []

    def theo_doi(*a, **k):
        conn = goc(*a, **k)
        da_mo.append(conn)
        return conn

    monkeypatch.setattr(sqlite3, "connect", theo_doi)
    return da_mo


def _con_mo(conn) -> bool:
    try:
        conn.execute("SELECT 1")
        return True
    except sqlite3.ProgrammingError:
        return False


def test_kho_tai_khoan_dong_het_ket_noi(tmp_path, ket_noi_da_mo):
    repo = SqliteUserRepository(tmp_path / "u.db")
    u = repo.create(User(user_id="", username="dongketnoi", password_hash="h"))
    repo.get_by_id(u.user_id)
    repo.get_by_username("dongketnoi")
    repo.revoke_tokens(u.user_id)
    repo.update_password(u.user_id, "h2")
    repo.count()

    assert ket_noi_da_mo, "không theo dõi được kết nối nào - test vô nghĩa"
    assert not [c for c in ket_noi_da_mo if _con_mo(c)]


def test_cac_kho_khac_cung_dong_het(tmp_path, ket_noi_da_mo):
    db = tmp_path / "users.db"
    SqliteSavedItemRepository(db).count_for_user("u")
    SqliteAuditLogRepository(db)
    SqliteIssueResolutionRepository(db)
    SqliteQualitySnapshotRepository(db)

    assert ket_noi_da_mo
    assert not [c for c in ket_noi_da_mo if _con_mo(c)]


def test_kho_quan_dong_het_ket_noi(tmp_path, ket_noi_da_mo):
    db = make_db(tmp_path, {"place_id": "p1", "name": "Phở Thìn", "is_active": 1})
    repo = SqliteRestaurantRepository(db)
    repo.list_all()

    assert ket_noi_da_mo
    assert not [c for c in ket_noi_da_mo if _con_mo(c)]

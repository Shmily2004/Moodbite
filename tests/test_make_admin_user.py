"""Khoá `scripts/make_admin_user.py` - đường chuyển admin từ biến môi trường sang bảng users.

Chỗ dễ sai nhất: tự NÂNG QUYỀN nhầm một tài khoản thường chỉ vì trùng tên, và làm hỏng
`.env.local` của chủ dự án (mất các khoá khác, đè secret đang dùng).
"""
import importlib.util
from pathlib import Path

from src.domain.entities.user import User, UserRole
from src.infrastructure.auth.admin_auth import AdminAuthService
from src.infrastructure.auth.crypto import hash_password
from src.infrastructure.repositories.sqlite_user_repository import SqliteUserRepository

_SPEC = importlib.util.spec_from_file_location(
    "make_admin_user", Path(__file__).resolve().parent.parent / "scripts" / "make_admin_user.py"
)
script = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(script)

MAT_KHAU = "mat-khau-admin-rat-dai"
BAM = hash_password(MAT_KHAU)


def test_tu_env_tao_admin_va_dang_nhap_duoc_bang_MAT_KHAU_CU(tmp_path):
    repo = SqliteUserRepository(tmp_path / "u.db")

    ket_qua = script.nhap_tu_env(
        repo, {"MOODBITE_ADMIN_USER": "Admin", "MOODBITE_ADMIN_PASSWORD_HASH": BAM}
    )

    assert ket_qua == script.DA_TAO
    token = AdminAuthService(repo, "secret").login("admin", MAT_KHAU)
    assert AdminAuthService(repo, "secret").verify(token) == "admin"


def test_tu_env_KHONG_tu_nang_quyen_tai_khoan_thuong_trung_ten(tmp_path):
    repo = SqliteUserRepository(tmp_path / "u.db")
    repo.create(User(user_id="", username="admin", password_hash=hash_password("khac-han-nhe")))

    ket_qua = script.nhap_tu_env(
        repo, {"MOODBITE_ADMIN_USER": "admin", "MOODBITE_ADMIN_PASSWORD_HASH": BAM}
    )

    assert ket_qua == script.TRUNG_TEN_NGUOI_THUONG
    assert repo.get_by_username("admin").role == UserRole.USER


def test_tu_env_chay_hai_lan_khong_tao_trung(tmp_path):
    repo = SqliteUserRepository(tmp_path / "u.db")
    env = {"MOODBITE_ADMIN_USER": "admin", "MOODBITE_ADMIN_PASSWORD_HASH": BAM}

    script.nhap_tu_env(repo, env)

    assert script.nhap_tu_env(repo, env) == script.DA_LA_ADMIN
    assert repo.count_by_role(UserRole.ADMIN) == 1


def test_tu_env_hash_hong_hoac_thieu_bien_thi_KHONG_tao_gi(tmp_path):
    repo = SqliteUserRepository(tmp_path / "u.db")

    assert script.nhap_tu_env(repo, {}) == script.THIEU_BIEN
    assert script.nhap_tu_env(
        repo, {"MOODBITE_ADMIN_USER": "admin", "MOODBITE_ADMIN_PASSWORD_HASH": "'pbkdf2..."}
    ) == script.HASH_HONG
    assert repo.count() == 0


def test_env_local_giu_khoa_khac_xoa_bien_cu_va_KHONG_de_secret_dang_dung(tmp_path):
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "MOODBITE_AUTH_SECRET=giu-nguyen\n"
        "MOODBITE_ADMIN_USER=admin\n"
        "MOODBITE_ADMIN_PASSWORD_HASH=pbkdf2_sha256$x\n"
        "MOODBITE_ADMIN_SECRET=secret-dang-dung\n",
        encoding="utf-8",
    )

    script.cap_nhat_env_local(
        env_file,
        script.cau_hinh_can_co({"MOODBITE_ADMIN_SECRET": "secret-dang-dung"}),
        xoa=script.BIEN_CU,
    )

    noi_dung = env_file.read_text(encoding="utf-8")
    assert "MOODBITE_AUTH_SECRET=giu-nguyen" in noi_dung
    assert "MOODBITE_ADMIN_SECRET=secret-dang-dung" in noi_dung
    assert "MOODBITE_STORAGE=sqlite" in noi_dung
    assert "MOODBITE_ADMIN_USER" not in noi_dung
    assert "MOODBITE_ADMIN_PASSWORD_HASH" not in noi_dung


def test_chua_co_secret_thi_sinh_moi():
    assert len(script.cau_hinh_can_co({})["MOODBITE_ADMIN_SECRET"]) >= 32


def test_ha_quyen_bang_set_role_thu_hoi_token_quan_tri(tmp_path):
    repo = SqliteUserRepository(tmp_path / "u.db")
    admin = script.tao_admin(repo, "admin", BAM)
    auth = AdminAuthService(repo, "secret")
    token = auth.login("admin", MAT_KHAU)

    repo.set_role(admin.user_id, UserRole.USER)

    import pytest
    from src.application.errors import InvalidCredentialsError

    with pytest.raises(InvalidCredentialsError):
        auth.verify(token)

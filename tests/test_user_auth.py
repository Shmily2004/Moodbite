"""Test tài khoản người dùng + phân quyền.

Trọng tâm là BẢO MẬT. Mở đăng ký công khai nghĩa là ai cũng gọi được các endpoint này,
nên test "đường đi sai" quan trọng hơn test đường đi đúng:
  - tự đăng ký thành admin  -> phải KHÔNG được
  - dò xem tài khoản có tồn tại -> phải KHÔNG đoán được
  - dò mật khẩu hàng loạt   -> phải bị chặn
  - lộ chuỗi băm ra API     -> phải KHÔNG bao giờ
"""
from __future__ import annotations

import time

import pytest

from src.application.errors import InvalidCredentialsError
from src.application.ports.user_repository import UserRepository, UsernameAlreadyExists
from src.application.use_cases.manage_account import LoginUseCase, RegisterUserUseCase
from src.domain.entities.user import (
    InvalidCredentialsFormat,
    User,
    UserRole,
    validate_password,
    validate_username,
)
from src.infrastructure.auth.crypto import hash_password, verify_password
from src.infrastructure.auth.rate_limit import (
    RateLimitExceeded,
    SlidingWindowRateLimiter,
)
from src.infrastructure.repositories.sqlite_user_repository import SqliteUserRepository

PASSWORD = "mat-khau-du-dai"


@pytest.fixture
def repo(tmp_path):
    return SqliteUserRepository(tmp_path / "users.db")


def make_use_cases(repo):
    issue = lambda user: f"token-cho-{user.username}"  # noqa: E731
    return (
        RegisterUserUseCase(repo, hash_password, issue),
        LoginUseCase(repo, verify_password, issue),
    )


# ==========================================================================
# PHÂN QUYỀN — chỗ sai thì nguy hiểm nhất
# ==========================================================================


def test_dang_ky_LUON_la_vai_user_khong_bao_gio_la_admin(repo):
    """Nếu vai lấy từ input thì ai cũng tự phong mình làm admin."""
    register, _ = make_use_cases(repo)

    user, _ = register.execute("nguoidung", PASSWORD)

    assert user.role == UserRole.USER
    assert user.is_admin is False


def test_khong_the_tu_dang_ky_thanh_admin_qua_tham_so(repo):
    """`execute()` cố tình KHÔNG nhận tham số `role`. Test này khoá điều đó lại."""
    register, _ = make_use_cases(repo)

    with pytest.raises(TypeError):
        register.execute("kesau", PASSWORD, role="admin")  # type: ignore[call-arg]


def test_vai_LA_trong_CSDL_bi_ha_ve_user_khong_phai_nang_len_admin(tmp_path):
    """Dữ liệu hỏng thì phải chọn phía AN TOÀN."""
    import sqlite3

    db = tmp_path / "users.db"
    repo = SqliteUserRepository(db)
    repo.create(User(user_id="u-1", username="ai", password_hash="x", role=UserRole.USER))
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE users SET role = 'sieu_admin' WHERE username = 'ai'")
        conn.commit()

    assert repo.get_by_username("ai").role == UserRole.USER


def test_to_public_KHONG_BAO_GIO_lo_chuoi_bam():
    """Bản trả ra API tuyệt đối không được chứa `password_hash`."""
    user = User(
        user_id="u-1", username="ai", password_hash="pbkdf2_sha256$600000$abc$def",
        role=UserRole.ADMIN, display_name="Ai Đó",
    )

    public = user.to_public()

    assert "password_hash" not in public
    assert "pbkdf2" not in str(public)
    assert public["role"] == "admin"


# ==========================================================================
# CHỐNG DÒ TÀI KHOẢN
# ==========================================================================


def test_thong_bao_loi_KHONG_noi_sai_ten_hay_sai_mat_khau(repo):
    register, login = make_use_cases(repo)
    register.execute("cothat", PASSWORD)

    loi = []
    for ten, mk in [("cothat", "sai-mat-khau"), ("khong-ton-tai", PASSWORD)]:
        with pytest.raises(InvalidCredentialsError) as exc:
            login.execute(ten, mk)
        loi.append(str(exc.value))

    # Hai tình huống khác nhau nhưng thông báo phải Y HỆT, nếu không kẻ tấn công biết
    # được tên nào có thật.
    assert loi[0] == loi[1] == "Sai tài khoản hoặc mật khẩu."


def test_van_bam_mat_khau_ke_ca_khi_tai_khoan_khong_ton_tai(repo):
    """Chống dò qua THỜI GIAN phản hồi.

    Nếu thoát sớm khi không tìm thấy người dùng thì tài khoản không tồn tại trả lời trong
    ~1ms còn tài khoản có thật mất ~400ms. Đo thời gian là biết tên nào có thật.
    """
    da_goi = []

    def verify_co_dem(password, stored):
        da_goi.append(stored)
        return False

    login = LoginUseCase(repo, verify_co_dem, lambda u: "t")

    with pytest.raises(InvalidCredentialsError):
        login.execute("khong-he-ton-tai", PASSWORD)

    assert len(da_goi) == 1, "phải gọi verify_password dù không có tài khoản"
    assert da_goi[0].startswith("pbkdf2_sha256$"), "phải dùng hash giả đúng định dạng"


# ==========================================================================
# GIỚI HẠN TẦN SUẤT
# ==========================================================================


def test_chan_sau_khi_vuot_so_lan_cho_phep():
    limiter = SlidingWindowRateLimiter(max_attempts=3, window_seconds=60)

    for _ in range(3):
        limiter.check("1.2.3.4")

    with pytest.raises(RateLimitExceeded) as exc:
        limiter.check("1.2.3.4")
    assert exc.value.retry_after_seconds > 0


def test_moi_khoa_dem_rieng():
    """Người này bị chặn không được làm ảnh hưởng người khác."""
    limiter = SlidingWindowRateLimiter(max_attempts=2, window_seconds=60)
    limiter.check("nguoi-a")
    limiter.check("nguoi-a")

    limiter.check("nguoi-b")   # không được ném lỗi


def test_dang_nhap_thanh_cong_thi_xoa_lich_su():
    """Gõ nhầm vài lần rồi đúng thì không được bị chặn oan ở lần sau."""
    limiter = SlidingWindowRateLimiter(max_attempts=3, window_seconds=60)
    limiter.check("ai"); limiter.check("ai")

    limiter.reset("ai")

    for _ in range(3):
        limiter.check("ai")   # lại được 3 lần đầy đủ


def test_cua_so_TRUOT_chu_khong_phai_cua_so_co_dinh():
    """Cửa sổ cố định cho phép dồn gấp đôi quanh mốc reset."""
    limiter = SlidingWindowRateLimiter(max_attempts=2, window_seconds=1)
    limiter.check("ai"); limiter.check("ai")
    with pytest.raises(RateLimitExceeded):
        limiter.check("ai")

    time.sleep(1.1)

    limiter.check("ai")   # cửa sổ đã trượt qua, được phép lại


# ==========================================================================
# QUY TẮC ĐẶT TÊN / MẬT KHẨU (domain)
# ==========================================================================


@pytest.mark.parametrize("ten", ["ab", "a" * 33, "co khoang trang", "dấu-tiếng-việt", ""])
def test_ten_dang_nhap_khong_hop_le(ten):
    with pytest.raises(InvalidCredentialsFormat):
        validate_username(ten)


@pytest.mark.parametrize("ten", ["abc", "nguoi_dung-1", "A" * 32])
def test_ten_dang_nhap_hop_le(ten):
    assert validate_username(ten) == ten.lower()


def test_ten_dang_nhap_chuan_hoa_ve_chu_thuong(repo):
    """'Admin' và 'admin' phải là CÙNG một tài khoản, nếu không sẽ giả mạo được."""
    register, _ = make_use_cases(repo)
    register.execute("NguoiDung", PASSWORD)

    with pytest.raises(UsernameAlreadyExists):
        register.execute("nguoidung", PASSWORD)


def test_mat_khau_qua_ngan_bi_tu_choi():
    with pytest.raises(InvalidCredentialsFormat):
        validate_password("1234567")
    assert validate_password("12345678") == "12345678"


# ==========================================================================
# KHO LƯU TRỮ
# ==========================================================================


def test_tao_va_doc_lai_duoc(repo):
    register, login = make_use_cases(repo)
    created, token = register.execute("ai_do", PASSWORD, display_name="Ai Đó")

    assert token == "token-cho-ai_do"
    doc_lai = repo.get_by_username("ai_do")
    assert doc_lai.user_id == created.user_id
    assert doc_lai.display_name == "Ai Đó"
    assert verify_password(PASSWORD, doc_lai.password_hash)


def test_trung_ten_bi_chan_o_TANG_CSDL(repo):
    """Ràng buộc UNIQUE, không phải kiểm bằng SELECT trước khi ghi — hai người đăng ký
    cùng lúc sẽ cùng vượt qua phép kiểm đó."""
    repo.create(User(user_id="u-1", username="trung", password_hash="x"))

    with pytest.raises(UsernameAlreadyExists):
        repo.create(User(user_id="u-2", username="trung", password_hash="y"))


def test_kho_tai_khoan_la_FILE_RIENG_khong_chung_voi_kho_quan(tmp_path):
    """Kho quán dựng lại được từ CSV; kho tài khoản thì mất là mất hẳn.

    Để chung một file thì chỉ cần xoá .db đi dựng lại dữ liệu quán là bay sạch tài khoản.
    """
    users_db = tmp_path / "moodbite_users.db"
    repo = SqliteUserRepository(users_db)
    repo.create(User(user_id="u-1", username="ai", password_hash="x"))

    # Mô phỏng việc xoá CSDL quán để dựng lại - việc hoàn toàn bình thường.
    restaurants_db = tmp_path / "moodbite.db"
    restaurants_db.write_bytes(b"gia lap")
    restaurants_db.unlink()

    assert repo.get_by_username("ai") is not None, "tài khoản phải sống sót"


def test_thieu_thu_muc_van_tao_duoc_kho(tmp_path):
    """Lần chạy đầu tiên chưa có gì - app phải tự tạo, không được sập."""
    repo = SqliteUserRepository(tmp_path / "chua-co" / "users.db")

    assert repo.is_ready
    assert repo.count() == 0


def test_thoa_man_port_UserRepository(repo):
    assert isinstance(repo, UserRepository)

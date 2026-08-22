"""Test tính năng QUÊN MẬT KHẨU — `/auth/forgot-password` và `/auth/reset-password`.

Trọng tâm là những chỗ SAI THÌ NGUY HIỂM, không phải đường đi thuận lợi:

  - dò xem email/tên nào đã đăng ký      -> phải KHÔNG đoán được qua câu trả lời
  - dùng lại đường dẫn trong thư lần hai -> phải BỊ TỪ CHỐI
  - token của tài khoản A đổi mật khẩu B -> phải KHÔNG được
  - token đăng nhập đem đi đổi mật khẩu  -> phải KHÔNG được (hai secret khác nhau)
  - thư gửi đi có lộ mật khẩu không      -> phải KHÔNG bao giờ

Không có test nào gửi thư thật: `FakeEmailSender` giữ thư trong bộ nhớ (xem `tests/fakes.py`).
"""
from __future__ import annotations

import pytest

from src.application.errors import InvalidCredentialsError
from src.infrastructure.auth.crypto import hash_password, verify_password
from src.infrastructure.auth.password_reset import PasswordResetTokenService
from tests.fakes import FakeEmailSender
from tests.test_auth_api import API, PASSWORD, build_client, login, register

MAT_KHAU_MOI = "mat-khau-moi-day-du-123"
EMAIL = "nguoidung@vidu.com"


@pytest.fixture
def setup(tmp_path):
    """Client + hộp thư giả + kho tài khoản, đã có sẵn một tài khoản CÓ email."""
    emails = FakeEmailSender()
    client, users = build_client(tmp_path, emails=emails)
    assert register(client, email=EMAIL).status_code == 201
    return client, emails, users


def quen(client, identifier):
    return client.post(f"{API}/auth/forgot-password", json={"identifier": identifier})


def dat_lai(client, token, new_password=MAT_KHAU_MOI):
    return client.post(
        f"{API}/auth/reset-password",
        json={"token": token, "new_password": new_password},
    )


def token_trong_thu(emails) -> str:
    """Bóc token từ đường dẫn trong lá thư gần nhất — đúng như người dùng bấm vào link."""
    body = emails.da_gui[-1]["body"]
    dong = next(d for d in body.splitlines() if "/dat-lai-mat-khau?token=" in d)
    return dong.split("token=", 1)[1].strip()


# ==========================================================================
# ĐƯỜNG ĐI ĐÚNG
# ==========================================================================


def test_quen_mat_khau_gui_thu_va_doi_duoc_mat_khau(setup):
    client, emails, _ = setup

    assert quen(client, EMAIL).status_code == 200
    assert len(emails.da_gui) == 1
    assert emails.da_gui[0]["to"] == EMAIL

    assert dat_lai(client, token_trong_thu(emails)).status_code == 200

    # Mật khẩu CŨ hết dùng được, mật khẩu MỚI vào được.
    assert login(client, password=PASSWORD).status_code == 401
    assert login(client, password=MAT_KHAU_MOI).status_code == 200


def test_tim_duoc_ca_khi_go_TEN_DANG_NHAP_thay_vi_email(setup):
    """Người dùng thường không nhớ mình đăng ký bằng email nào."""
    client, emails, _ = setup
    assert quen(client, "nguoidung").status_code == 200
    assert len(emails.da_gui) == 1


def test_thu_KHONG_chua_mat_khau_va_co_han_su_dung(setup):
    client, emails, _ = setup
    quen(client, EMAIL)
    body = emails.da_gui[0]["body"]

    assert PASSWORD not in body           # không bao giờ gửi mật khẩu qua thư
    assert "pbkdf2" not in body           # cũng không gửi chuỗi băm
    assert "/dat-lai-mat-khau?token=" in body
    assert "phút" in body                 # nói rõ đường dẫn sống bao lâu


# ==========================================================================
# CHỐNG DÒ TÀI KHOẢN
# ==========================================================================


def test_email_khong_ton_tai_van_tra_ve_Y_HET_email_co_that(setup):
    """Khác nhau một chữ trong câu trả lời là đủ để dò xem ai đã đăng ký."""
    client, emails, _ = setup

    co_that = quen(client, EMAIL)
    khong_co = quen(client, "khongtontai@vidu.com")

    assert co_that.status_code == khong_co.status_code == 200
    assert co_that.json() == khong_co.json()
    # Nhưng thư thì chỉ gửi cho tài khoản có thật.
    assert len(emails.da_gui) == 1


def test_tai_khoan_KHONG_khai_email_cung_tra_ve_cau_giong_het(tmp_path):
    emails = FakeEmailSender()
    client, _ = build_client(tmp_path, emails=emails)
    register(client, username="khongemail")     # đăng ký không kèm email

    res = quen(client, "khongemail")

    assert res.status_code == 200
    assert emails.da_gui == []                  # không có gì để gửi


# ==========================================================================
# TOKEN — chỉ dùng một lần, đúng người, đúng cửa
# ==========================================================================


def test_dung_lai_duong_dan_lan_hai_bi_tu_choi(setup):
    """Chốt chặn 'một lần dùng' — không cần bảng token nào, xem `password_reset.py`."""
    client, emails, _ = setup
    quen(client, EMAIL)
    token = token_trong_thu(emails)

    assert dat_lai(client, token).status_code == 200
    lan_hai = dat_lai(client, token, "mat-khau-khac-nua-456")

    assert lan_hai.status_code == 401
    assert "đã được dùng" in lan_hai.json()["error"]["message"]
    # Và mật khẩu vẫn là cái đặt ở lần đầu.
    assert login(client, password=MAT_KHAU_MOI).status_code == 200


def test_token_DANG_NHAP_khong_dung_duoc_de_doi_mat_khau(setup):
    """Hai secret khác nhau: token phiên đăng nhập phải vô nghĩa ở cửa đặt lại."""
    client, emails, _ = setup
    token_dang_nhap = login(client).json()["data"]["token"]

    res = dat_lai(client, token_dang_nhap)

    assert res.status_code == 401


def test_token_bi_sua_mot_ky_tu_bi_tu_choi(setup):
    client, emails, _ = setup
    quen(client, EMAIL)
    token = token_trong_thu(emails)

    # Đổi ký tự cuối của chữ ký.
    hong = token[:-1] + ("A" if token[-1] != "A" else "B")

    assert dat_lai(client, hong).status_code == 401


def test_mat_khau_moi_qua_ngan_bi_tu_choi_400_va_KHONG_doi(setup):
    client, emails, _ = setup
    quen(client, EMAIL)
    token = token_trong_thu(emails)

    res = dat_lai(client, token, "ngan")

    assert res.status_code == 400
    assert login(client, password=PASSWORD).status_code == 200   # vẫn mật khẩu cũ


def test_token_cua_nguoi_nay_khong_doi_duoc_mat_khau_nguoi_kia(tmp_path):
    emails = FakeEmailSender()
    client, users = build_client(tmp_path, emails=emails)
    register(client, username="nguoi-a", email="a@vidu.com")
    register(client, username="nguoi-b", email="b@vidu.com")

    quen(client, "a@vidu.com")
    token_cua_a = token_trong_thu(emails)

    dat_lai(client, token_cua_a)

    # B hoàn toàn không bị ảnh hưởng.
    assert login(client, username="nguoi-b", password=PASSWORD).status_code == 200


# ==========================================================================
# CHƯA CẤU HÌNH -> 503 KÈM CÁCH KHẮC PHỤC, KHÔNG PHẢI IM LẶNG
# ==========================================================================


def test_chua_dat_secret_thi_tra_503_kem_huong_dan(tmp_path):
    client, _ = build_client(tmp_path, reset_secret="")

    res = quen(client, EMAIL)

    assert res.status_code == 503
    assert res.json()["error"]["code"] == "DATA_NOT_READY"
    assert "MOODBITE_RESET_SECRET" in res.json()["error"]["message"]


def test_may_chu_thu_hong_thi_bao_loi_chu_khong_im_lang(tmp_path):
    """Giấu lỗi gửi thư = người dùng ngồi đợi mãi một lá thư không bao giờ tới."""
    from src.application.ports.email_sender import EmailSendFailed

    emails = FakeEmailSender(loi=EmailSendFailed("SMTP tu choi"))
    client, _ = build_client(tmp_path, emails=emails)
    register(client, email=EMAIL)

    res = quen(client, EMAIL)

    assert res.status_code == 503


def test_gioi_han_tan_suat_chat_hon_dang_nhap(tmp_path):
    """Mỗi lần gọi là một lá thư thật -> phải chặn, nếu không là kênh spam miễn phí."""
    emails = FakeEmailSender()
    client, _ = build_client(tmp_path, emails=emails, forgot_limit=2)
    register(client, email=EMAIL)

    assert quen(client, EMAIL).status_code == 200
    assert quen(client, EMAIL).status_code == 200
    lan_ba = quen(client, EMAIL)

    assert lan_ba.status_code == 429
    assert lan_ba.json()["error"]["code"] == "RATE_LIMITED"


# ==========================================================================
# TẦNG DƯỚI — service token, test riêng cho nhanh và rõ nguyên nhân
# ==========================================================================


def test_service_token_het_han_thi_tu_choi():
    from src.domain.entities.user import User

    service = PasswordResetTokenService("secret-test", token_ttl_seconds=-1)
    user = User(user_id="u1", username="a", password_hash=hash_password(PASSWORD))

    with pytest.raises(InvalidCredentialsError):
        service.subject_of(service.issue(user))


def test_service_van_tay_doi_theo_mat_khau():
    """Nền tảng của chốt 'một lần dùng': đổi mật khẩu là vân tay lệch."""
    from src.domain.entities.user import User

    service = PasswordResetTokenService("secret-test")
    hash_cu = hash_password(PASSWORD)
    user = User(user_id="u1", username="a", password_hash=hash_cu)
    token = service.issue(user)

    service.ensure_unused(token, hash_cu)          # chưa đổi -> qua

    hash_moi = hash_password(MAT_KHAU_MOI)
    assert not verify_password(PASSWORD, hash_moi)
    with pytest.raises(InvalidCredentialsError):
        service.ensure_unused(token, hash_moi)     # đã đổi -> chết

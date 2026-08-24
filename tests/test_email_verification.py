"""Xác minh email — khoá hành vi của cả ba tầng.

Vì sao có file riêng thay vì nhét vào `test_auth_api.py`: file đó đã dài và nói về đăng
ký/đăng nhập/quên mật khẩu. Xác minh email là một luồng độc lập, và cái đáng khoá nhất ở
đây không phải "đường thẳng chạy được" mà là BỐN CÁCH LÀM SAI:

  1. bấm lại đường dẫn cũ sau khi đã xác minh,
  2. đổi email rồi bấm đường dẫn cũ  -> tuyệt đối không được đóng dấu cho địa chỉ mới,
  3. token bị sửa chữ ký,
  4. máy chủ thư hỏng lúc đăng ký    -> KHÔNG được làm hỏng việc tạo tài khoản.
"""
from __future__ import annotations

import pytest

from src.application.errors import InvalidCredentialsError
from src.domain.entities.user import User
from src.infrastructure.auth.email_verification import EmailVerificationTokenService
from tests.fakes import FakeEmailSender
from tests.test_auth_api import API, build_client, register

SECRET_XM = "secret-xac-minh-dung-cho-test"


def _lay_token_trong_thu(emails) -> str:
    """Bóc token ra khỏi lá thư cuối cùng — đúng cách người dùng bấm vào đường dẫn."""
    body = emails.da_gui[-1]["body"]
    dong = [d for d in body.splitlines() if "verify-email?token=" in d]
    assert dong, f"Thư không có đường dẫn xác minh:\n{body}"
    return dong[0].split("token=")[1].strip()


# --- Luồng chính -----------------------------------------------------------------


def test_dang_ky_co_email_thi_tu_gui_thu_xac_minh(tmp_path):
    client, _ = build_client(tmp_path)
    register(client, email="ai.do@vi.du.com")
    assert len(client.app.state.container.emails.da_gui) == 1
    assert "Xác minh email" in client.app.state.container.emails.da_gui[0]["subject"]


def test_dang_ky_khong_email_thi_khong_gui_thu(tmp_path):
    client, _ = build_client(tmp_path)
    register(client)
    assert client.app.state.container.emails.da_gui == []


def test_xac_minh_thanh_cong_thi_email_verified_thanh_true(tmp_path):
    client, _ = build_client(tmp_path)
    register(client, email="ai.do@vi.du.com")
    token = _lay_token_trong_thu(client.app.state.container.emails)

    res = client.post(f"{API}/auth/verify-email/confirm", json={"token": token})

    assert res.status_code == 200
    assert res.json()["data"]["email_verified"] is True


def test_moi_dang_ky_thi_chua_xac_minh(tmp_path):
    """Mặc định PHẢI là chưa xác minh — đóng dấu sẵn là nói dối về địa chỉ chưa ai kiểm."""
    client, _ = build_client(tmp_path)
    res = register(client, email="ai.do@vi.du.com")
    token = res.json()["data"]["token"]

    me = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me.json()["data"]["email_verified"] is False


# --- Bốn cách làm sai ------------------------------------------------------------


def test_bam_lai_duong_dan_cu_thi_bi_tu_choi(tmp_path):
    """Chốt chặn chỉ-dùng-một-lần: xác minh xong thì vân tay đổi, token cũ chết."""
    client, _ = build_client(tmp_path)
    register(client, email="ai.do@vi.du.com")
    token = _lay_token_trong_thu(client.app.state.container.emails)
    client.post(f"{API}/auth/verify-email/confirm", json={"token": token})

    lan_hai = client.post(f"{API}/auth/verify-email/confirm", json={"token": token})

    assert lan_hai.status_code == 401


def test_doi_email_roi_bam_link_cu_khong_dong_dau_cho_dia_chi_moi(tmp_path):
    """Ca NGUY HIỂM NHẤT của luồng này.

    Khai `a@x.com`, nhận thư, chưa bấm. Đổi sang `b@y.com`. Rồi mới bấm link cũ.
    Nếu lọt thì `b@y.com` được đóng dấu "đã xác minh" mà chưa ai chứng minh nó có thật —
    tức là con dấu này vô nghĩa. Xem `infrastructure/auth/email_verification.py`.
    """
    users_repo = build_client(tmp_path)
    client, users = users_repo
    register(client, email="dia.chi.cu@vi.du.com")
    token = _lay_token_trong_thu(client.app.state.container.emails)

    # Đổi email thẳng dưới CSDL — đây là mô phỏng trạng thái, không phải luồng người dùng.
    import sqlite3

    with sqlite3.connect(tmp_path / "users.db") as conn:
        conn.execute("UPDATE users SET email = ?", ("dia.chi.moi@vi.du.com",))
        conn.commit()

    res = client.post(f"{API}/auth/verify-email/confirm", json={"token": token})

    assert res.status_code == 401
    nguoi = users.get_by_email("dia.chi.moi@vi.du.com")
    assert nguoi is not None and nguoi.email_verified is False


def test_token_bi_sua_thi_bi_tu_choi(tmp_path):
    client, _ = build_client(tmp_path)
    register(client, email="ai.do@vi.du.com")
    token = _lay_token_trong_thu(client.app.state.container.emails)

    res = client.post(
        f"{API}/auth/verify-email/confirm", json={"token": token[:-4] + "0000"}
    )

    assert res.status_code == 401


def test_smtp_hong_luc_dang_ky_van_tao_duoc_tai_khoan(tmp_path):
    """Tài khoản đã ghi vào CSDL rồi; ném lỗi ra lúc này là người dùng mất tên đăng ký."""
    # `FakeEmailSender` đã có sẵn cách giả lập máy chủ thư hỏng — dùng lại thay vì tự
    # viết một lớp giả thứ hai chỉ để ném lỗi.
    client, users = build_client(
        tmp_path, emails=FakeEmailSender(loi=RuntimeError("SMTP chet"))
    )

    res = register(client, email="ai.do@vi.du.com")

    assert res.status_code == 201
    assert users.get_by_username("nguoidung") is not None


# --- Gửi lại thư -----------------------------------------------------------------


def test_da_xac_minh_roi_thi_khong_gui_them_thu(tmp_path):
    client, _ = build_client(tmp_path)
    res = register(client, email="ai.do@vi.du.com")
    headers = {"Authorization": f"Bearer {res.json()['data']['token']}"}
    token = _lay_token_trong_thu(client.app.state.container.emails)
    client.post(f"{API}/auth/verify-email/confirm", json={"token": token})
    so_thu = len(client.app.state.container.emails.da_gui)

    lai = client.post(f"{API}/auth/verify-email/request", headers=headers)

    assert lai.status_code == 200
    assert len(client.app.state.container.emails.da_gui) == so_thu  # không gửi thêm


def test_chua_khai_email_thi_bao_ro_va_khong_gui(tmp_path):
    client, _ = build_client(tmp_path)
    res = register(client)
    headers = {"Authorization": f"Bearer {res.json()['data']['token']}"}

    lai = client.post(f"{API}/auth/verify-email/request", headers=headers)

    assert lai.status_code == 200
    assert "chưa khai email" in lai.json()["data"]["message"]
    assert client.app.state.container.emails.da_gui == []


def test_chua_dang_nhap_thi_khong_xin_gui_lai_duoc(tmp_path):
    client, _ = build_client(tmp_path)

    assert client.post(f"{API}/auth/verify-email/request").status_code == 401


# --- Tầng infrastructure ---------------------------------------------------------


def _nguoi(email="ai.do@vi.du.com", da_xac_minh=False) -> User:
    return User(
        user_id="u-1",
        username="nguoidung",
        password_hash="bam",
        email=email,
        email_verified=da_xac_minh,
    )


def test_khong_co_secret_thi_khong_phat_token():
    """FAIL-CLOSED: thiếu cấu hình thì tắt hẳn, không phát token ký bằng khoá rỗng."""
    from src.application.errors import AuthNotConfiguredError

    with pytest.raises(AuthNotConfiguredError):
        EmailVerificationTokenService("").issue(_nguoi())


def test_khong_co_email_thi_khong_phat_token():
    with pytest.raises(InvalidCredentialsError):
        EmailVerificationTokenService(SECRET_XM).issue(_nguoi(email=None))


def test_token_xac_minh_khong_mo_duoc_bang_secret_khac():
    """Đây là lý do secret xác minh phải TÁCH khỏi secret đăng nhập."""
    token = EmailVerificationTokenService(SECRET_XM).issue(_nguoi())

    with pytest.raises(InvalidCredentialsError):
        EmailVerificationTokenService("secret-hoan-toan-khac").read(token)


def test_token_het_han_thi_bi_tu_choi():
    token = EmailVerificationTokenService(SECRET_XM, token_ttl_seconds=-1).issue(_nguoi())

    with pytest.raises(InvalidCredentialsError):
        EmailVerificationTokenService(SECRET_XM).read(token)

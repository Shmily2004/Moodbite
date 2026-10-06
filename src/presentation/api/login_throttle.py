"""Giới hạn tần suất cho MỘT lượt đăng nhập — dùng chung cho `/auth/login` và `/admin/login`.

VÌ SAO TÁCH RA FILE RIÊNG (2026-10-06, sau rà soát bảo mật): trước đó mỗi router tự gọi
`limiter.check(ip)` rồi `limiter.reset(ip)` khi đăng nhập đúng. Hai lỗ thật đã tái hiện:

  1. Reset theo IP TRẦN: kẻ tấn công đoán một lần mật khẩu nạn nhân, đăng nhập ĐÚNG vào
     tài khoản của chính mình để xoá bộ đếm, lặp lại -> 20 lần đoán, 0 lần bị chặn.
  2. Admin là tài khoản trong bảng `users` nên đăng nhập được qua `/auth/login`, nơi chỉ
     có bộ đếm người dùng (5/5 phút) -> lách bộ đếm chặt (5/15 phút) của `/admin/login`.

BỐN BỘ ĐẾM, mỗi bộ chặn một kiểu tấn công khác nhau (ngưỡng ở `rate_limit.py`):

| Bộ đếm                      | Khoá        | Chặn                               | Đăng nhập đúng   |
|-----------------------------|-------------|------------------------------------|------------------|
| `login_ip_rate_limiter`     | IP          | rải nhiều tên từ một IP             | trả lại 1 lượt   |
| `login_account_rate_limiter`| tên         | đổi IP liên tục nhắm một tài khoản  | xoá (của tên đó) |
| `login_rate_limiter`        | IP + tên    | đoán dồn một tài khoản thường       | xoá (của cặp đó) |
| `admin_login_rate_limiter`  | IP + tên    | như trên, cho tài khoản QUẢN TRỊ    | xoá (của cặp đó) |

Không bộ nào bị xoá bởi đăng nhập đúng của MỘT TÀI KHOẢN KHÁC — đó chính là lỗ số 1.

Thuộc tầng presentation vì khoá đếm là địa chỉ IP (khái niệm HTTP). Quyết định "tài khoản
đích có phải admin không" lấy từ chính lần tra tài khoản của use case (`before_verify`),
không tra thêm lần nào.

⚠️ RÒ RỈ NHỎ CHẤP NHẬN ĐƯỢC: ai đoán sai 5 lần liền một tên thì thấy `Retry-After` của
admin (15 phút) khác của người thường (5 phút), tức là đoán được tên đó là admin. Họ đã
phải biết đúng tên và bị chặn rồi mới thấy; đổi lại là admin không còn bị đoán mật khẩu
không giới hạn. Đánh đổi có chủ đích.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Request

from src.domain.entities.user import User
from src.presentation.api.dependencies import Container, client_key


class LoginThrottle:
    """Gom các bộ đếm của MỘT request đăng nhập. Dùng:

        throttle = LoginThrottle(container, request, payload.username)
        ... use_case.execute(..., before_verify=throttle.before_verify)
        throttle.on_success()
    """

    def __init__(
        self,
        container: Container,
        request: Request,
        username: str,
        *,
        admin_endpoint: bool = False,
    ) -> None:
        self._c = container
        self._ip = client_key(request)
        # Chuẩn hoá giống `LoginUseCase`/`get_by_username`: "Admin" và "admin " là CÙNG
        # một tài khoản thì phải là cùng một bộ đếm, nếu không đổi hoa/thường là lách được.
        self._name = (username or "").strip().lower()
        self._pair = f"{self._ip}|{self._name}"
        self._admin = admin_endpoint

    def before_verify(self, user: Optional[User]) -> None:
        """Ghi nhận một lần thử. Ném `RateLimitExceeded` (-> 429) nếu vượt bất kỳ bộ nào.

        Gọi SAU khi tra tài khoản (một câu SELECT, rẻ) và TRƯỚC khi băm mật khẩu (~0,4s).
        """
        self._c.login_ip_rate_limiter.check(self._ip)
        self._c.login_account_rate_limiter.check(self._name)
        if user is not None and user.is_admin:
            self._admin = True
        self._pair_limiter().check(self._pair)

    def on_success(self) -> None:
        self._c.login_ip_rate_limiter.refund(self._ip)
        self._c.login_account_rate_limiter.reset(self._name)
        self._pair_limiter().reset(self._pair)

    def _pair_limiter(self):
        return (
            self._c.admin_login_rate_limiter if self._admin else self._c.login_rate_limiter
        )


__all__ = ["LoginThrottle"]

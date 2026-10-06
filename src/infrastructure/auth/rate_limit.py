"""Giới hạn tần suất — chặn dò mật khẩu và bơm tài khoản rác.

VÌ SAO BẮT BUỘC (không còn là "nên có"): khi chỉ có 1 tài khoản admin, PBKDF2 600k vòng
đã làm mỗi lần thử tốn ~0.4s nên dò mật khẩu rất chậm. Nhưng mở đăng ký công khai thì:

  - dò mật khẩu hàng loạt trên NHIỀU tài khoản cùng lúc
  - bot tạo tài khoản vô hạn
  - mỗi lần thử tốn 0.4s CPU của server -> chính PBKDF2 thành công cụ làm nghẽn server

⚠️ GIỚI HẠN CỦA CÁCH LÀM NÀY — phải biết trước khi tin vào nó:
  1. Lưu trong BỘ NHỚ tiến trình -> khởi động lại là mất, và chạy nhiều tiến trình
     (gunicorn nhiều worker) thì mỗi worker đếm riêng.
  2. Chặn theo khoá do lời gọi truyền vào (IP hoặc tên đăng nhập). Kẻ tấn công đổi IP
     liên tục thì lách được.
  Đủ cho đồ án và cho deploy một tiến trình. Cần chắc chắn hơn thì phải dùng Redis hoặc
  chặn ở tầng reverse proxy - đó là quyết định hạ tầng, không phải việc của file này.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

# Lỗi định nghĩa ở `application/errors.py` chứ không phải ở đây, để `presentation` bắt
# được nó mà không phải import `infrastructure` (CLAUDE.md mục 2). Re-export để chỗ nào
# quan tâm tới giới hạn tần suất thì import ngay tại file này, khỏi phải nhớ nó nằm đâu.
from src.application.errors import RateLimitExceeded


class SlidingWindowRateLimiter:
    """Cho tối đa `max_attempts` lần trong `window_seconds` giây, tính theo từng khoá.

    Dùng cửa sổ TRƯỢT chứ không phải cửa sổ cố định: cửa sổ cố định cho phép dồn gấp đôi
    số lần ngay quanh mốc reset (5 lần cuối phút này + 5 lần đầu phút sau).
    """

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        # FastAPI chạy nhiều request song song -> phải khoá, nếu không hai request cùng
        # lúc có thể cùng đọc thấy "còn chỗ" rồi cùng được cho qua.
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        """Ghi nhận một lần thử. Ném `RateLimitExceeded` nếu vượt."""
        now = time.time()
        with self._lock:
            hits = self._hits[key]
            # Bỏ các lần đã ra khỏi cửa sổ.
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()

            if len(hits) >= self.max_attempts:
                cho = int(self.window_seconds - (now - hits[0])) + 1
                raise RateLimitExceeded(cho)

            hits.append(now)

            # Dọn khoá rỗng để bộ nhớ không phình vô hạn khi bị rải nhiều khoá khác nhau.
            if len(self._hits) > 10_000:
                self._prune(now)

    def reset(self, key: str) -> None:
        """Xoá lịch sử của một khoá — gọi sau khi đăng nhập THÀNH CÔNG.

        ⚠️ CHỈ reset khoá gắn với ĐÚNG tài khoản vừa đăng nhập (`IP|tên`, hoặc `tên`).
        Trước 2026-10-06 `/auth/login` reset khoá theo IP TRẦN: kẻ tấn công đoán một lần
        mật khẩu nạn nhân, rồi đăng nhập đúng vào tài khoản CỦA CHÍNH MÌNH để xoá bộ đếm,
        lặp lại vô hạn — đã tái hiện 20 lần đoán, 0 lần 429. Khoá dùng chung nhiều tài
        khoản thì dùng `refund`, không bao giờ `reset`.
        """
        with self._lock:
            self._hits.pop(key, None)

    def refund(self, key: str) -> None:
        """Trả lại MỘT lượt (lượt vừa đếm) — dùng cho khoá DÙNG CHUNG nhiều tài khoản (IP).

        Đăng nhập thành công không nên ăn vào hạn mức của cả IP (nhiều người sau cùng một
        NAT), nhưng cũng KHÔNG được xoá các lần thử sai trước đó — xem `reset`. Trả đúng
        một lượt thì các lần sai vẫn nằm nguyên trong cửa sổ.
        """
        with self._lock:
            hits = self._hits.get(key)
            if hits:
                hits.pop()

    def _prune(self, now: float) -> None:
        for k in [k for k, v in self._hits.items()
                  if not v or now - v[-1] > self.window_seconds]:
            self._hits.pop(k, None)


# Ngưỡng mặc định. Đăng nhập chặt hơn đăng ký vì đó là đường dò mật khẩu.
# 5 lần/5 phút cho MỘT CẶP (IP, tên đăng nhập): đủ rộng cho người gõ nhầm vài lần, đủ hẹp
# để dò mật khẩu là vô vọng. Khoá theo CẶP từ 2026-10-06 - xem `reset`.
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300

# Theo IP, gộp MỌI tên đăng nhập — chặn kiểu "rải": mỗi tên thử vài mật khẩu phổ biến,
# không cặp (IP, tên) nào chạm ngưỡng. Rộng gấp 4 cặp vì nhiều người thật có thể ngồi sau
# cùng một IP (wifi quán, ký túc xá). Đăng nhập ĐÚNG được trả lại lượt (`refund`), nên
# người dùng thật hầu như không chạm ngưỡng này.
LOGIN_IP_MAX_ATTEMPTS = 20
LOGIN_IP_WINDOW_SECONDS = 300

# Theo TÊN ĐĂNG NHẬP, gộp MỌI IP — chặn kẻ đổi IP liên tục (mạng botnet, proxy xoay vòng)
# để né hai bộ đếm trên.
#
# ⚠️ ĐÁNH ĐỔI PHẢI BIẾT: đếm theo tên thì AI CŨNG khoá tạm được tài khoản người khác bằng
# cách cố tình gõ sai (tấn công từ chối dịch vụ nhắm một người). Vì vậy ngưỡng để CAO
# (20 lần/15 phút — gấp 4 ngưỡng của một cặp) và chỉ khoá 15 phút: người dùng thật gõ sai
# 20 lần liền là chuyện không có, còn kẻ phá phải duy trì 20 lần mỗi 15 phút cho MỖI nạn
# nhân. Chủ tài khoản đăng nhập đúng thì bộ đếm của tên đó được xoá.
LOGIN_ACCOUNT_MAX_ATTEMPTS = 20
LOGIN_ACCOUNT_WINDOW_SECONDS = 900

# 3 tài khoản/giờ cho mỗi IP: người thật hầu như không tạo quá 1.
REGISTER_MAX_ATTEMPTS = 3
REGISTER_WINDOW_SECONDS = 3600

# QUÊN MẬT KHẨU: 3 lần/giờ. Chặt hơn cả đăng nhập vì mỗi lần gọi là một LÁ THƯ THẬT bay
# đi: hạn mức SMTP miễn phí của Gmail chỉ ~500 thư/ngày, và người nhận bị dội thư liên tục
# thì tài khoản gửi rất dễ bị đánh dấu spam. Người quên thật cũng chỉ cần bấm 1-2 lần.
FORGOT_PASSWORD_MAX_ATTEMPTS = 3
FORGOT_PASSWORD_WINDOW_SECONDS = 3600

# Đăng nhập QUẢN TRỊ — CHẶT HƠN đăng nhập thường. Thêm 2026-08-24 sau khi rà soát bảo mật.
#
# ⚠️ TRƯỚC ĐÓ `/admin/login` KHÔNG hề có giới hạn nào, trong khi `/auth/login` của người
# dùng thường thì có. Đó là bất đối xứng đúng chiều nguy hiểm nhất: chỉ có MỘT tài khoản
# quản trị, nó sửa/ẩn được mọi quán, và đây là cánh cửa duy nhất vào đó.
#
# Còn một lý do thứ hai không liên quan tới đoán mật khẩu: mỗi lần thử đều chạy PBKDF2
# 600.000 vòng, tốn ~0,4 giây CPU. Không chặn thì một người gửi liên tục là đủ chiếm hết
# CPU của máy chủ — endpoint này công khai, ai cũng gọi được.
#
# 5 lần/15 phút: người quản trị biết mật khẩu của mình, gõ nhầm quá 5 lần là chuyện hiếm.
#
# Áp cho CẢ `/auth/login` khi tài khoản đích là admin (từ 2026-10-06). Admin là dòng
# `role='admin'` trong bảng `users` nên `/auth/login` cũng đăng nhập được; trước đó đường
# này chỉ chịu bộ đếm người dùng (5 lần/5 phút) -> lách được ngưỡng chặt của quản trị.
# Khoá là cặp (IP, tên) giống hệt ở `/admin/login`, nên hai cửa DÙNG CHUNG một bộ đếm.
ADMIN_LOGIN_MAX_ATTEMPTS = 5
ADMIN_LOGIN_WINDOW_SECONDS = 900


__all__ = [
    "SlidingWindowRateLimiter",
    "RateLimitExceeded",
    "ADMIN_LOGIN_MAX_ATTEMPTS",
    "ADMIN_LOGIN_WINDOW_SECONDS",
    "LOGIN_MAX_ATTEMPTS",
    "LOGIN_WINDOW_SECONDS",
    "LOGIN_IP_MAX_ATTEMPTS",
    "LOGIN_IP_WINDOW_SECONDS",
    "LOGIN_ACCOUNT_MAX_ATTEMPTS",
    "LOGIN_ACCOUNT_WINDOW_SECONDS",
    "REGISTER_MAX_ATTEMPTS",
    "REGISTER_WINDOW_SECONDS",
    "FORGOT_PASSWORD_MAX_ATTEMPTS",
    "FORGOT_PASSWORD_WINDOW_SECONDS",
]

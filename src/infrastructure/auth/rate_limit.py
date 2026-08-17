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


class RateLimitExceeded(Exception):
    """Vượt giới hạn -> HTTP 429. Kèm số giây phải chờ."""

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Bạn thao tác quá nhanh. Thử lại sau {retry_after_seconds} giây."
        )


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

        Nếu không reset thì người gõ nhầm vài lần rồi đăng nhập đúng vẫn bị tính, lát sau
        đăng nhập lại là bị chặn oan.
        """
        with self._lock:
            self._hits.pop(key, None)

    def _prune(self, now: float) -> None:
        for k in [k for k, v in self._hits.items()
                  if not v or now - v[-1] > self.window_seconds]:
            self._hits.pop(k, None)


# Ngưỡng mặc định. Đăng nhập chặt hơn đăng ký vì đó là đường dò mật khẩu.
# 5 lần/5 phút: đủ rộng cho người gõ nhầm vài lần, đủ hẹp để dò mật khẩu là vô vọng.
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300

# 3 tài khoản/giờ cho mỗi IP: người thật hầu như không tạo quá 1.
REGISTER_MAX_ATTEMPTS = 3
REGISTER_WINDOW_SECONDS = 3600


__all__ = [
    "SlidingWindowRateLimiter",
    "RateLimitExceeded",
    "LOGIN_MAX_ATTEMPTS",
    "LOGIN_WINDOW_SECONDS",
    "REGISTER_MAX_ATTEMPTS",
    "REGISTER_WINDOW_SECONDS",
]

"""Băm mật khẩu và ký token — NƠI DUY NHẤT của dự án làm hai việc này.

VÌ SAO TÁCH RA: trước đây chỉ có admin nên hai hàm này nằm trong `admin_auth.py`. Nay
người dùng cũng đăng nhập, nếu chép sang chỗ khác thì sẽ có HAI cách băm mật khẩu — sửa
số vòng lặp ở một chỗ mà quên chỗ kia là sinh ra tài khoản không đăng nhập được. Đây đúng
kiểu lỗi "hai nguồn sự thật" mà dự án đã trả giá để học.

Dùng `hmac`, `hashlib`, `secrets` của thư viện chuẩn — không thêm thư viện nào.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional

# 600k vòng PBKDF2-SHA256: mức OWASP khuyến nghị cho SHA-256 (2023).
# ⚠️ Đủ chậm để dò mật khẩu tốn kém (~0.4s/lần), nhưng khi có NHIỀU người đăng nhập cùng
# lúc thì đây là chi phí CPU thật. Nếu sau này thấy nghẽn, giảm số vòng là ĐỔI HỢP ĐỒNG:
# mọi hash cũ vẫn đọc được (số vòng lưu ngay trong chuỗi), nhưng phải băm lại khi đăng nhập.
PBKDF2_ITERATIONS = 600_000
_HASH_PREFIX = "pbkdf2_sha256"


def hash_password(password: str, *, salt: Optional[bytes] = None) -> str:
    """Sinh chuỗi băm dạng `pbkdf2_sha256$<vòng>$<salt hex>$<hash hex>`.

    Salt ngẫu nhiên mỗi lần: hai người đặt cùng mật khẩu vẫn ra hai chuỗi khác nhau,
    nên không thể tra bảng dựng sẵn.
    """
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"{_HASH_PREFIX}${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """So khớp mật khẩu. Chuỗi băm sai định dạng -> False, KHÔNG ném lỗi.

    Số vòng lặp đọc TỪ CHÍNH chuỗi băm, không dùng hằng số hiện tại — nhờ vậy đổi
    `PBKDF2_ITERATIONS` không làm hỏng các tài khoản đã tạo trước đó.
    """
    try:
        prefix, iterations, salt_hex, digest_hex = stored.split("$")
        if prefix != _HASH_PREFIX:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError, AttributeError):
        return False
    # compare_digest: so sánh thời gian hằng định, không rò rỉ qua thời gian phản hồi.
    return hmac.compare_digest(digest.hex(), digest_hex)


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign_token(payload: Dict[str, Any], secret: bytes, ttl_seconds: int) -> str:
    """Tạo token `<payload>.<chữ ký>`.

    Định dạng GIỐNG JWT nhưng KHÔNG phải JWT: không có header `alg`, nên miễn nhiễm lỗ
    hổng "alg: none" kinh điển. Thuật toán cố định cứng trong code, client không chọn được.
    """
    body = dict(payload)
    body["exp"] = int(time.time()) + ttl_seconds
    encoded = _b64encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    return f"{encoded}.{_sign(encoded, secret)}"


def _sign(body: str, secret: bytes) -> str:
    return _b64encode(hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest())


class TokenInvalid(Exception):
    """Token hỏng, bị sửa, hoặc hết hạn."""


def verify_token(token: str, secret: bytes) -> Dict[str, Any]:
    """Trả payload nếu token hợp lệ, ngược lại ném `TokenInvalid`."""
    try:
        body, signature = (token or "").split(".")
    except ValueError:
        raise TokenInvalid("Token không hợp lệ.")

    # Kiểm CHỮ KÝ TRƯỚC khi đọc nội dung: chưa xác thực thì payload là dữ liệu do kẻ tấn
    # công kiểm soát, không được tin.
    if not hmac.compare_digest(signature, _sign(body, secret)):
        raise TokenInvalid("Token không hợp lệ.")

    try:
        payload = json.loads(_b64decode(body))
    except (ValueError, TypeError):
        raise TokenInvalid("Token không hợp lệ.")

    if int(payload.get("exp", 0)) < time.time():
        raise TokenInvalid("Token đã hết hạn, hãy đăng nhập lại.")
    return payload


__all__ = [
    "hash_password",
    "verify_password",
    "sign_token",
    "verify_token",
    "TokenInvalid",
    "PBKDF2_ITERATIONS",
]

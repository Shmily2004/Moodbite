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
from typing import Any, Dict, List, Optional

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


# --- MỤC ĐÍCH CỦA TOKEN (`typ`) --------------------------------------------------
#
# Thêm 2026-10-06 sau rà soát bảo mật. TRƯỚC ĐÓ bốn loại token (đăng nhập, đặt lại mật
# khẩu, xác minh email, quản trị) chỉ khác nhau ở SECRET. Nhưng secret đặt lại/xác minh
# mặc định LUI VỀ secret đăng nhập (`dependencies.py`), và `UserTokenService` chỉ đòi có
# `sub` -> token đặt lại mật khẩu trong hộp thư dùng được làm token ĐĂNG NHẬP 24 giờ. Đã
# tái hiện thật. Tách secret là lớp bảo vệ thứ hai; `typ` là lớp thứ nhất, không phụ thuộc
# cấu hình của người triển khai.
PURPOSE_LOGIN = "login"
PURPOSE_RESET = "reset"
PURPOSE_VERIFY = "verify"
PURPOSE_ADMIN = "admin"
_PURPOSES = frozenset({PURPOSE_LOGIN, PURPOSE_RESET, PURPOSE_VERIFY, PURPOSE_ADMIN})


def _legacy_purpose(payload: Dict[str, Any]) -> str:
    """Suy mục đích của token CŨ (phát trước khi có `typ`) từ trường đặc trưng của nó.

    VÌ SAO KHÔNG BẮT MỌI NGƯỜI ĐĂNG NHẬP LẠI: token đăng nhập sống 24 giờ, thư xác minh
    cũng 24 giờ. Từ chối hết token cũ = đăng xuất mọi người và giết mọi lá thư vừa gửi,
    trong khi mỗi loại token cũ vốn ĐÃ có một trường riêng không loại nào khác có:
        `role`=admin -> quản trị · `pw` -> đặt lại · `ev` -> xác minh · không có gì -> đăng nhập
    Suy theo cách đó thì token cũ chỉ dùng được ĐÚNG việc của nó — lỗ hổng vẫn bịt kín.
    Mọi token cũ tự hết hạn sau tối đa 24 giờ; sau đó nhánh này chỉ còn là đường chết.
    """
    if payload.get("role") == "admin":
        return PURPOSE_ADMIN
    if "pw" in payload:
        return PURPOSE_RESET
    if "ev" in payload or "em" in payload:
        return PURPOSE_VERIFY
    return PURPOSE_LOGIN


def sign_token(
    payload: Dict[str, Any], secret: bytes, ttl_seconds: int, *, purpose: Optional[str]
) -> str:
    """Tạo token `<payload>.<chữ ký>`, mang `typ` = `purpose`.

    `purpose` là tham số BẮT BUỘC (keyword) để không chỗ phát token nào quên được nó.
    `None` chỉ dành cho test dựng token kiểu cũ.

    Định dạng GIỐNG JWT nhưng KHÔNG phải JWT: không có header `alg`, nên miễn nhiễm lỗ
    hổng "alg: none" kinh điển. Thuật toán cố định cứng trong code, client không chọn được.
    """
    body = dict(payload)
    if purpose is not None:
        if purpose not in _PURPOSES:
            raise ValueError(f"purpose không hợp lệ: {purpose!r}")  # lỗi lập trình -> 500
        body["typ"] = purpose
    body["exp"] = int(time.time()) + ttl_seconds
    encoded = _b64encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    return f"{encoded}.{_sign(encoded, secret)}"


def _sign(body: str, secret: bytes) -> str:
    return _b64encode(hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest())


class TokenInvalid(Exception):
    """Token hỏng, bị sửa, sai mục đích, hoặc hết hạn."""


def verify_token(token: str, secret: bytes, *, purpose: str) -> Dict[str, Any]:
    """Trả payload nếu token hợp lệ VÀ đúng mục đích, ngược lại ném `TokenInvalid`."""
    token = token if isinstance(token, str) else ""
    # Chặn ký tự ngoài ASCII TRƯỚC mọi thứ khác. Token thật chỉ gồm base64url và dấu chấm.
    # Không chặn ở đây thì: `body.encode("ascii")` ném UnicodeEncodeError (là ValueError ->
    # từng thành 400 kèm thông điệp codec nội bộ), còn `hmac.compare_digest` với chuỗi
    # non-ASCII ném TypeError -> 500. Cả hai đã tái hiện thật (2026-10-06).
    if not token.isascii():
        raise TokenInvalid("Token không hợp lệ.")
    try:
        body, signature = token.split(".")
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
    if not isinstance(payload, dict):
        raise TokenInvalid("Token không hợp lệ.")

    # Kiểm MỤC ĐÍCH trước hạn dùng: token sai loại thì hết hạn hay chưa cũng vô nghĩa.
    typ = payload.get("typ")
    if (typ if typ is not None else _legacy_purpose(payload)) != purpose:
        raise TokenInvalid("Token không hợp lệ.")

    try:
        het_han = int(payload.get("exp", 0))
    except (TypeError, ValueError):
        raise TokenInvalid("Token không hợp lệ.")
    if het_han < time.time():
        raise TokenInvalid("Token đã hết hạn, hãy đăng nhập lại.")
    return payload


def shared_secret_groups(secrets_by_name: Dict[str, str]) -> List[List[str]]:
    """Nhóm các biến môi trường đang dùng CÙNG một giá trị secret (bỏ qua giá trị rỗng).

    Cho cảnh báo lúc khởi động. Trùng secret không còn mở được lỗ nhầm loại token (đã có
    `typ`), nhưng vẫn là cấu hình yếu: lộ một secret = lộ cả bốn loại token.
    """
    theo_gia_tri: Dict[str, List[str]] = {}
    for ten, gia_tri in secrets_by_name.items():
        if gia_tri:
            theo_gia_tri.setdefault(gia_tri, []).append(ten)
    return [sorted(ten) for ten in theo_gia_tri.values() if len(ten) > 1]


__all__ = [
    "hash_password",
    "verify_password",
    "sign_token",
    "verify_token",
    "TokenInvalid",
    "PBKDF2_ITERATIONS",
    "PURPOSE_LOGIN",
    "PURPOSE_RESET",
    "PURPOSE_VERIFY",
    "PURPOSE_ADMIN",
    "shared_secret_groups",
]

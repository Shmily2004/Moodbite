"""Router tài khoản người dùng — `/api/v1/auth/*`.

MỎNG theo đúng CLAUDE.md mục 3: nhận HTTP, gọi use case, trả envelope. Quy tắc đặt tên
và mật khẩu nằm ở `domain/entities/user.py`; băm và ký token nằm ở `infrastructure/auth/`.

BA CHỐT CHẶN, độc lập nhau:
  1. Chưa đặt MOODBITE_AUTH_SECRET -> 503 kèm hướng dẫn. Fail-closed.
  2. Giới hạn tần suất theo IP trên cả `/register` lẫn `/login`.
  3. Vai LUÔN là `user`. Router KHÔNG nhận `role` từ client - xem `RegisterUserUseCase`.

VÌ SAO CHƯA CÓ `/logout`: token ký bằng HMAC là STATELESS, server không giữ danh sách
token đang sống nên không có gì để xoá. Một endpoint chỉ trả 200 rồi không làm gì là ảo
giác an toàn — tệ hơn là không có. Đăng xuất hiện tại = client xoá token của mình, và
thiệt hại khi token bị lộ bị chặn trên bởi thời hạn 24 giờ. Thu hồi thật cần thêm cột
`token_version` vào bảng `users`; đó là ĐỔI DATA MODEL nên phải chốt trước —
xem `docs/API_DECISIONS_PENDING.md`.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from src.domain.entities.user import User
from src.presentation.api.dependencies import (
    Container,
    client_key,
    get_container,
    get_current_user,
)
from src.presentation.api.envelope import success
from src.presentation.api.schemas import (
    AuthResponse,
    LoginRequest,
    MeResponse,
    RegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_payload(user: User, token: str, ttl_seconds: int) -> dict:
    """Hình dạng response dùng chung cho cả đăng ký và đăng nhập.

    Đăng ký trả luôn token để người dùng không phải đăng nhập lại ngay sau đó — một bước
    thừa mà ai cũng bỏ qua được.

    `to_public()` là nơi DUY NHẤT quyết định trường nào được lộ ra; router không tự dựng
    dict, nếu không thì thêm trường vào entity sẽ có ngày lộ cả `password_hash`.
    """
    return {
        "user": user.to_public(),
        "token": token,
        "token_type": "bearer",
        "expires_in": ttl_seconds,
    }


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(
    payload: RegisterRequest,
    request: Request,
    container: Container = Depends(get_container),
):
    """Tạo tài khoản mới. Vai luôn là `user`.

    201 CREATED chứ không phải 200: có tài nguyên mới được tạo ra.
    Tên đã có người dùng -> 409 USERNAME_TAKEN. Sai định dạng -> 400 INVALID_REQUEST.
    """
    container.user_tokens.ensure_configured()
    # Đếm TRƯỚC khi băm mật khẩu: băm tốn ~0.4s CPU, để sau thì kẻ tấn công vẫn ép được
    # server làm việc nặng dù request rốt cuộc bị từ chối.
    container.register_rate_limiter.check(client_key(request))

    user, token = container.register_user.execute(
        payload.username, payload.password, payload.display_name
    )
    return success(
        _auth_payload(user, token, container.user_tokens.token_ttl_seconds),
        status_code=201,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    container: Container = Depends(get_container),
):
    """Đổi tài khoản/mật khẩu lấy token.

    Sai tên HAY sai mật khẩu đều trả CÙNG MỘT câu 401 — không nói cái nào sai, nếu không
    thì đây thành công cụ dò xem tên nào đã tồn tại.
    """
    container.user_tokens.ensure_configured()
    key = client_key(request)
    container.login_rate_limiter.check(key)

    user, token = container.login_user.execute(payload.username, payload.password)

    # Đăng nhập ĐÚNG thì xoá lịch sử đếm: người gõ nhầm vài lần rồi vào được không đáng
    # bị chặn oan ở lần đăng nhập sau.
    container.login_rate_limiter.reset(key)
    return success(_auth_payload(user, token, container.user_tokens.token_ttl_seconds))


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    """Thông tin tài khoản đang đăng nhập, kèm VAI hiện tại.

    Frontend gọi endpoint này lúc mở app để biết token còn sống không và được vào những
    đâu. Vai đọc từ CSDL chứ không lấy trong token, nên admin vừa bị hạ quyền sẽ thấy
    ngay ở lần gọi kế tiếp.
    """
    return success(user.to_public())

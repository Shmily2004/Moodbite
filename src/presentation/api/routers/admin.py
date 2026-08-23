"""Router quản trị — `/api/v1/admin/*`.

MỎNG theo đúng CLAUDE.md mục 3: chỉ nhận HTTP, gọi use case, trả envelope. Không có
quy tắc nghiệp vụ ở đây (quy tắc "sửa được trường nào" nằm ở
`domain/value_objects/restaurant_edit.py`).

BẢO MẬT — hai chốt chặn độc lập:
  1. `Depends(require_admin)` gắn ở CẤP ROUTER cho mọi endpoint dưới đây, trừ `/login`.
     Đặt ở router thay vì từng hàm để thêm endpoint mới KHÔNG THỂ quên xác thực.
  2. Chưa cấu hình đủ biến môi trường -> `AdminAuthService` ném AdminNotConfiguredError
     -> 503. Fail-closed, không bao giờ mặc định cho qua.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, Query

from src.application.errors import DataNotReadyError
from src.presentation.api.dependencies import Container, get_container, require_admin
from src.presentation.api.envelope import success
from src.presentation.api.schemas import (
    AdminCreateRestaurantRequest,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminRestaurantListResponse,
    AdminRestaurantResponse,
    AdminRestaurantSummary,
    AdminUpdateRestaurantRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])

# Router riêng cho /login: đây là endpoint DUY NHẤT không yêu cầu token, vì nó chính là
# nơi phát token ra.
public_router = APIRouter(prefix="/admin", tags=["admin"])


def _require_writable(container: Container):
    """Kho hiện tại có ghi được không. CSV thì không."""
    if container.admin_restaurants is None:
        raise DataNotReadyError(
            "kho lưu trữ hiện tại không ghi được",
            "Dựng CSDL bằng `python scripts/build_sqlite.py` rồi chạy lại backend với "
            "MOODBITE_STORAGE=sqlite",
        )


def _to_summary(restaurant) -> AdminRestaurantSummary:
    return AdminRestaurantSummary(
        restaurant_id=restaurant.place_id,
        name=restaurant.name,
        category=restaurant.category,
        cuisine=restaurant.cuisine,
        address=restaurant.address,
        district=restaurant.district,
        # `price` là CHUỖI khoảng giá, không phải số - xem CLAUDE.md mục 4 quy tắc 2.
        price=restaurant.price,
        phone=restaurant.phone,
        website=restaurant.website,
        # `None` giữ nguyên None: "chưa có đánh giá" khác hẳn "0 sao".
        rating=restaurant.rating,
        reviews_count=restaurant.reviews_count,
        is_active=restaurant.is_active,
        source=restaurant.source,
    )


@public_router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest, container: Container = Depends(get_container)):
    """Đổi tài khoản/mật khẩu lấy token ngắn hạn.

    Sai thông tin -> 401 UNAUTHORIZED. Chưa cấu hình admin -> 503 kèm hướng dẫn.
    """
    token = container.admin_auth.login(payload.username, payload.password)
    return success(
        {
            "token": token,
            "token_type": "bearer",
            "expires_in": container.admin_auth.token_ttl_seconds,
        }
    )


@router.get("/restaurants", response_model=AdminRestaurantListResponse)
def list_restaurants(
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
    q: Optional[str] = Query(None, description="Lọc theo tên, địa chỉ hoặc placeId"),
    limit: int = Query(50, ge=1, le=200),
    include_hidden: bool = Query(True, description="Có kèm quán đã ẩn hay không"),
):
    """Danh sách quán cho trang quản trị.

    MẶC ĐỊNH có cả quán đã ẩn — khác với `/search` của người dùng cuối. Không có nó thì
    ẩn xong sẽ không còn cách nào tìm lại để bỏ ẩn.
    """
    _require_writable(container)
    results = container.list_restaurants_for_admin.execute(
        query=q, limit=limit, include_hidden=include_hidden
    )
    return success(
        {
            "total": len(results),
            "results": [_to_summary(r).model_dump() for r in results],
        }
    )


@router.post("/restaurants", response_model=AdminRestaurantResponse, status_code=201)
def create_restaurant(
    payload: AdminCreateRestaurantRequest = Body(...),
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
):
    """Thêm một quán hoàn toàn mới.

    201 CREATED chứ không phải 200: có tài nguyên mới được tạo ra.
    `place_id` do SERVER sinh với tiền tố `manual:` — nhìn mã là biết quán này do người
    gõ vào chứ không phải từ Google/OSM/Overture. Client KHÔNG được tự đặt mã.

    Toạ độ ngoài Hà Nội -> 400 (phạm vi dự án chốt 2026-08-19).
    """
    _require_writable(container)
    created = container.create_restaurant.execute(payload.model_dump(exclude_unset=True))
    return success(_to_summary(created).model_dump(), status_code=201)


@router.patch("/restaurants/{restaurant_id}", response_model=AdminRestaurantResponse)
def update_restaurant(
    restaurant_id: str,
    payload: AdminUpdateRestaurantRequest = Body(...),
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
):
    """Sửa các trường mô tả của một quán.

    `exclude_unset=True`: chỉ gửi trường nào thì sửa trường đó. Nhờ vậy client phân biệt
    được "không đụng tới trường này" với "xoá giá trị của trường này" (gửi `null`).
    """
    _require_writable(container)
    changes = payload.model_dump(exclude_unset=True)
    updated = container.update_restaurant.execute(restaurant_id, changes)
    return success(_to_summary(updated).model_dump())


@router.post("/restaurants/{restaurant_id}/hide", response_model=AdminRestaurantResponse)
def hide_restaurant(
    restaurant_id: str,
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
):
    """Ẩn quán (soft-delete). Dữ liệu KHÔNG bị xoá, chỉ biến mất khỏi luồng người dùng."""
    _require_writable(container)
    updated = container.set_restaurant_visibility.execute(restaurant_id, is_active=False)
    return success(_to_summary(updated).model_dump())


@router.post("/restaurants/{restaurant_id}/restore", response_model=AdminRestaurantResponse)
def restore_restaurant(
    restaurant_id: str,
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
):
    """Bỏ ẩn quán đã ẩn."""
    _require_writable(container)
    updated = container.set_restaurant_visibility.execute(restaurant_id, is_active=True)
    return success(_to_summary(updated).model_dump())

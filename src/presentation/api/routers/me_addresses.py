"""Router "Địa chỉ của tôi" — `/api/v1/me/addresses/*`.

Bắt buộc đăng nhập, không nhận `user_id` từ client; địa chỉ của người khác trả 404.
KHÔNG có endpoint geocoding: toạ độ do client gửi (vị trí trình duyệt hoặc bấm bản đồ),
`address_text` lưu nguyên văn — xem `domain/entities/user_address.py`.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.application.use_cases.manage_addresses import (
    CreateAddressCommand,
    UpdateAddressCommand,
)
from src.domain.entities.user import User
from src.presentation.api.dependencies import Container, get_container, get_current_user
from src.presentation.api.envelope import success
from src.presentation.api.schemas import MessageResponse
from src.presentation.api.schemas_me_places import (
    ME_PLACES_ERROR_RESPONSES,
    AddressesResponse,
    CreateAddressRequest,
    UpdateAddressRequest,
    UserAddressResponse,
)

router = APIRouter(prefix="/me/addresses", tags=["me"])


@router.get("", response_model=AddressesResponse, responses=ME_PLACES_ERROR_RESPONSES)
def list_addresses(
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """Địa chỉ đã lưu. Địa chỉ MẶC ĐỊNH đứng đầu (nếu có)."""
    ds = container.list_addresses.execute(user.user_id)
    return success({"addresses": [a.to_public() for a in ds], "total": len(ds)})


@router.post(
    "", response_model=UserAddressResponse, status_code=201,
    responses=ME_PLACES_ERROR_RESPONSES,
)
def create_address(
    body: CreateAddressRequest,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """Toạ độ ngoài Hà Nội -> 400 kèm câu giải thích (MoodBite chỉ có dữ liệu Hà Nội)."""
    dc = container.create_address.execute(
        CreateAddressCommand(
            user_id=user.user_id,
            label=body.label,
            lat=body.latitude,
            lng=body.longitude,
            address_text=body.address_text,
            is_default=body.is_default,
        )
    )
    return success(dc.to_public(), status_code=201)


@router.patch(
    "/{address_id}", response_model=UserAddressResponse,
    responses=ME_PLACES_ERROR_RESPONSES,
)
def update_address(
    address_id: str,
    body: UpdateAddressRequest,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """Đổi nhãn / mô tả / cờ mặc định. Đặt `is_default: true` thì địa chỉ mặc định cũ tự
    thôi làm mặc định (cùng một giao dịch)."""
    dc = container.update_address.execute(
        UpdateAddressCommand(
            user_id=user.user_id,
            address_id=address_id,
            label=body.label,
            address_text=body.address_text,
            # `model_fields_set` phân biệt "không gửi" với "gửi null": chỉ gửi null mới là
            # XOÁ mô tả. Thiếu phân biệt này thì mọi lần đổi nhãn đều lặng lẽ xoá mô tả.
            address_text_provided="address_text" in body.model_fields_set,
            is_default=body.is_default,
        )
    )
    return success(dc.to_public())


@router.delete(
    "/{address_id}", response_model=MessageResponse,
    responses=ME_PLACES_ERROR_RESPONSES,
)
def delete_address(
    address_id: str,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    container.delete_address.execute(user.user_id, address_id)
    return success({"message": "Đã xoá địa chỉ."})

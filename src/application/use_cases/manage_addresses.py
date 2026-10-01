"""USE CASE: "Địa chỉ của tôi" — liệt kê · thêm · sửa (nhãn/mô tả/mặc định) · xoá.

Chỉ ĐIỀU PHỐI: luật nhãn, toạ độ trong Hà Nội, số địa chỉ tối đa, địa chỉ đầu tiên tự
thành mặc định — tất cả ở `domain/entities/user_address.py`. Bất biến "không quá một địa
chỉ mặc định" do kho giữ trong một giao dịch (xem port).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable, List, Optional

from src.application.errors import ApplicationError, DataNotReadyError
from src.application.ports.user_address_repository import UserAddressRepository
from src.domain.entities.user_address import (
    UserAddress,
    ensure_can_add_address,
    resolve_default_flag,
    validate_address_coordinates,
    validate_address_label,
    validate_address_text,
)


class AddressesNotAvailable(DataNotReadyError):
    def __init__(self) -> None:
        super().__init__(
            "kho 'địa chỉ của tôi' không mở được",
            "Kiểm tra quyền ghi ở đường dẫn MOODBITE_USERS_DB.",
        )


class AddressNotFoundError(ApplicationError):
    """Không có địa chỉ này TRONG PHẠM VI người đang đăng nhập -> 404.

    Cùng một lỗi cho "không tồn tại" và "của người khác" — xem `CollectionNotFoundError`.
    """

    def __init__(self, address_id: str) -> None:
        super().__init__(f"Không tìm thấy địa chỉ '{address_id}'.")
        self.address_id = address_id


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass(frozen=True)
class CreateAddressCommand:
    user_id: str
    label: str
    lat: float
    lng: float
    address_text: Optional[str] = None
    # `None` = người dùng không nói gì -> domain quyết (địa chỉ đầu tiên thành mặc định).
    is_default: Optional[bool] = None


@dataclass(frozen=True)
class UpdateAddressCommand:
    user_id: str
    address_id: str
    label: Optional[str] = None
    # `address_text_provided=False` = client không gửi trường này -> giữ nguyên.
    # `True` + chuỗi rỗng/None = XOÁ mô tả. Tách cờ vì JSON `null` và "không gửi" là hai
    # ý định khác nhau mà `Optional[str]` một mình không phân biệt được.
    address_text: Optional[str] = None
    address_text_provided: bool = False
    is_default: Optional[bool] = None


class _AddressUseCase:
    def __init__(
        self,
        addresses: UserAddressRepository,
        new_id: Callable[[], str] = _new_id,
    ) -> None:
        self._repo = addresses
        self._new_id = new_id

    def _ensure_ready(self) -> None:
        if not self._repo.is_ready:
            raise AddressesNotAvailable()


class ListAddressesUseCase(_AddressUseCase):
    def execute(self, user_id: str) -> List[UserAddress]:
        self._ensure_ready()
        return self._repo.list_for_user(user_id)


class CreateAddressUseCase(_AddressUseCase):
    def execute(self, command: CreateAddressCommand) -> UserAddress:
        self._ensure_ready()
        nhan = validate_address_label(command.label)
        mo_ta = validate_address_text(command.address_text)
        lat, lng = validate_address_coordinates(command.lat, command.lng)
        so_hien_co = self._repo.count_for_user(command.user_id)
        ensure_can_add_address(so_hien_co)
        return self._repo.create(
            UserAddress(
                address_id=self._new_id(),
                user_id=command.user_id,
                label=nhan,
                address_text=mo_ta,
                lat=lat,
                lng=lng,
                is_default=resolve_default_flag(command.is_default, so_hien_co),
            )
        )


class UpdateAddressUseCase(_AddressUseCase):
    def execute(self, command: UpdateAddressCommand) -> UserAddress:
        self._ensure_ready()
        nhan = validate_address_label(command.label) if command.label is not None else None
        mo_ta: Optional[str] = None
        xoa_mo_ta = False
        if command.address_text_provided:
            mo_ta = validate_address_text(command.address_text)
            xoa_mo_ta = mo_ta is None
        sau = self._repo.update(
            command.user_id,
            command.address_id,
            label=nhan,
            address_text=mo_ta,
            clear_address_text=xoa_mo_ta,
            is_default=command.is_default,
        )
        if sau is None:
            raise AddressNotFoundError(command.address_id)
        return sau


class DeleteAddressUseCase(_AddressUseCase):
    def execute(self, user_id: str, address_id: str) -> None:
        """Xoá địa chỉ mặc định thì người dùng KHÔNG còn mặc định nào — cố ý không tự đôn
        địa chỉ khác lên: chọn hộ "Công ty" làm điểm dự phòng là quyết định thay người dùng."""
        self._ensure_ready()
        if not self._repo.delete(user_id, address_id):
            raise AddressNotFoundError(address_id)


__all__ = [
    "AddressesNotAvailable",
    "AddressNotFoundError",
    "CreateAddressCommand",
    "UpdateAddressCommand",
    "ListAddressesUseCase",
    "CreateAddressUseCase",
    "UpdateAddressUseCase",
    "DeleteAddressUseCase",
]

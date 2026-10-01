"""Schema HTTP cho "Bộ sưu tập của tôi" và "Địa chỉ của tôi" (`/me/collections`,
`/me/addresses`) — chủ dự án duyệt 2026-09-29.

VÌ SAO FILE RIÊNG, KHÔNG THÊM VÀO `schemas.py`: file đó đã ~1.200 dòng (CLAUDE.md mục 6:
file > ~300 dòng là tín hiệu cần tách). Hai tính năng này tự đứng được, không dùng chung
kiểu nào với phần còn lại ngoài envelope lỗi.

Tên trường `snake_case`, mọi response bọc trong `{"data": …}` — CLAUDE.md mục 5.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.presentation.api.schemas import ERROR_RESPONSES, ErrorEnvelope

# Hai endpoint nhóm này KHÁC `ERROR_RESPONSES` chung ở hai chỗ: có 401 (bắt buộc đăng
# nhập), và 404 mang mã riêng chứ không phải RESTAURANT_NOT_FOUND.
ME_PLACES_ERROR_RESPONSES = {
    **ERROR_RESPONSES,
    401: {"model": ErrorEnvelope, "description": "UNAUTHORIZED"},
    404: {
        "model": ErrorEnvelope,
        "description": "COLLECTION_NOT_FOUND | ADDRESS_NOT_FOUND",
    },
}


# --- Bộ sưu tập --------------------------------------------------------------


class CollectionItemSchema(BaseModel):
    item_type: str = Field(..., description="restaurant | dish")
    item_id: str
    name: str = Field(..., description="Tên chụp lại lúc thêm vào bộ.")
    added_at: Optional[str] = None


class CollectionSchema(BaseModel):
    collection_id: str
    name: str
    created_at: Optional[str] = None
    item_count: int
    items: List[CollectionItemSchema]


class CollectionsData(BaseModel):
    collections: List[CollectionSchema]
    total: int


class CollectionsResponse(BaseModel):
    data: CollectionsData


class CollectionResponse(BaseModel):
    data: CollectionSchema


class CollectionNameRequest(BaseModel):
    # KHÔNG đặt max_length ở đây: luật độ dài nằm ở domain (`validate_collection_name`)
    # và trả câu lỗi tiếng Việt rõ ràng. Chép luật sang schema là hai nơi giữ một con số.
    name: str = Field(..., description="Tên bộ sưu tập, 1–60 ký tự.")


class AddCollectionItemRequest(BaseModel):
    item_type: str = Field(..., description="restaurant | dish")
    item_id: str
    name: str = Field(..., description="Tên để hiển thị, chụp lại lúc thêm.")


# --- Địa chỉ -----------------------------------------------------------------


class UserAddressSchema(BaseModel):
    address_id: str
    label: str
    address_text: Optional[str] = Field(
        None, description="Chữ người dùng tự gõ. null = không có — KHÔNG phải geocoding."
    )
    lat: float
    lng: float
    is_default: bool
    created_at: Optional[str] = None


class AddressesData(BaseModel):
    addresses: List[UserAddressSchema]
    total: int


class AddressesResponse(BaseModel):
    data: AddressesData


class UserAddressResponse(BaseModel):
    data: UserAddressSchema


class CreateAddressRequest(BaseModel):
    label: str = Field(..., description="Nhãn ngắn: Nhà, Công ty… (1–40 ký tự).")
    address_text: Optional[str] = Field(None, description="Mô tả tự do, tối đa 200 ký tự.")
    lat: float = Field(..., description="Vĩ độ — phải nằm trong Hà Nội.")
    lng: float = Field(..., description="Kinh độ — phải nằm trong Hà Nội.")
    is_default: Optional[bool] = Field(
        None,
        description="Bỏ trống: địa chỉ ĐẦU TIÊN tự thành mặc định, các địa chỉ sau thì không.",
    )


class UpdateAddressRequest(BaseModel):
    """Chỉ gửi trường muốn đổi. Gửi `address_text: null` hoặc "" = XOÁ mô tả."""

    label: Optional[str] = None
    address_text: Optional[str] = None
    is_default: Optional[bool] = None


__all__ = [
    "ME_PLACES_ERROR_RESPONSES",
    "CollectionItemSchema",
    "CollectionSchema",
    "CollectionsData",
    "CollectionsResponse",
    "CollectionResponse",
    "CollectionNameRequest",
    "AddCollectionItemRequest",
    "UserAddressSchema",
    "AddressesData",
    "AddressesResponse",
    "UserAddressResponse",
    "CreateAddressRequest",
    "UpdateAddressRequest",
]

"""Router "Bộ sưu tập của tôi" — `/api/v1/me/collections/*`.

VÌ SAO TÁCH KHỎI `me.py`: `me.py` lo yêu thích + số liệu + cấp độ. Bộ sưu tập là một
tính năng riêng (6 endpoint), dồn vào đó thì file vượt xa ngưỡng ~300 dòng.

Giống `me.py`: MỌI endpoint bắt buộc đăng nhập, KHÔNG nhận `user_id` từ client. Mã bộ sưu
tập của người khác trả 404 y như mã không tồn tại — xem `CollectionNotFoundError`.
Router MỎNG: không có luật nghiệp vụ nào ở đây.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.application.use_cases.manage_collections import AddCollectionItemCommand
from src.domain.entities.user import User
from src.presentation.api.dependencies import Container, get_container, get_current_user
from src.presentation.api.envelope import success
from src.presentation.api.schemas import MessageResponse
from src.presentation.api.schemas_me_places import (
    ME_PLACES_ERROR_RESPONSES,
    AddCollectionItemRequest,
    CollectionNameRequest,
    CollectionResponse,
    CollectionsResponse,
)

router = APIRouter(prefix="/me/collections", tags=["me"])


@router.get("", response_model=CollectionsResponse, responses=ME_PLACES_ERROR_RESPONSES)
def list_collections(
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """Mọi bộ sưu tập của chính chủ, KÈM mục bên trong và số mục. Bộ mới nhất đứng đầu.

    Trả luôn mục trong một lượt: số bộ bị chặn ở 50 và số mục mỗi bộ ở 200, nên gọi thêm
    một request cho từng bộ chỉ tốn lượt mạng mà không tiết kiệm được gì đáng kể.
    """
    bo = container.list_collections.execute(user.user_id)
    return success({"collections": [b.to_public() for b in bo], "total": len(bo)})


@router.post(
    "", response_model=CollectionResponse, status_code=201,
    responses=ME_PLACES_ERROR_RESPONSES,
)
def create_collection(
    body: CollectionNameRequest,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    bo = container.create_collection.execute(user.user_id, body.name)
    return success(bo.to_public(), status_code=201)


@router.patch(
    "/{collection_id}", response_model=CollectionResponse,
    responses=ME_PLACES_ERROR_RESPONSES,
)
def rename_collection(
    collection_id: str,
    body: CollectionNameRequest,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    bo = container.rename_collection.execute(user.user_id, collection_id, body.name)
    return success(bo.to_public())


@router.delete(
    "/{collection_id}", response_model=MessageResponse,
    responses=ME_PLACES_ERROR_RESPONSES,
)
def delete_collection(
    collection_id: str,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """Xoá bộ và MỌI mục trong bộ. Các mục vẫn còn nguyên ở "Yêu thích"/"Đã lưu" nếu có —
    bộ sưu tập chỉ là một cách nhóm, không sở hữu dữ liệu đã lưu."""
    container.delete_collection.execute(user.user_id, collection_id)
    return success({"message": "Đã xoá bộ sưu tập."})


@router.post(
    "/{collection_id}/items", response_model=CollectionResponse,
    responses=ME_PLACES_ERROR_RESPONSES,
)
def add_collection_item(
    collection_id: str,
    body: AddCollectionItemRequest,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """Thêm một quán/món vào bộ. IDEMPOTENT: thêm lại thứ đã có chỉ cập nhật tên.

    Trả 200 (không phải 201) kèm CẢ BỘ sau khi thêm: thao tác này không tạo ra tài nguyên
    có địa chỉ riêng, và client cần số mục mới để cập nhật giao diện.
    """
    bo = container.add_collection_item.execute(
        AddCollectionItemCommand(
            user_id=user.user_id,
            collection_id=collection_id,
            item_type=body.item_type,
            item_id=body.item_id,
            name=body.name,
        )
    )
    return success(bo.to_public())


@router.delete(
    "/{collection_id}/items/{item_type}/{item_id}", response_model=MessageResponse,
    responses=ME_PLACES_ERROR_RESPONSES,
)
def remove_collection_item(
    collection_id: str,
    item_type: str,
    item_id: str,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    da_bo = container.remove_collection_item.execute(
        user.user_id, collection_id, item_type, item_id
    )
    return success(
        {"message": "Đã bỏ khỏi bộ sưu tập." if da_bo else "Mục này vốn không có trong bộ."}
    )

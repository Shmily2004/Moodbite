"""USE CASE: "Bộ sưu tập của tôi" — tạo · đổi tên · xoá · thêm/bỏ mục.

Chỉ ĐIỀU PHỐI: luật "tên hợp lệ", "tối đa bao nhiêu bộ/mục" nằm ở
`domain/entities/collection.py`; việc giới hạn trong phạm vi chủ tài khoản do kho lo
(xem port). Ở đây chỉ nối hai thứ đó lại và đổi "không thấy" thành lỗi 404.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable, List

from src.application.errors import ApplicationError, DataNotReadyError
from src.application.ports.collection_repository import CollectionRepository
from src.domain.entities.collection import (
    Collection,
    CollectionItem,
    ensure_can_add_item,
    ensure_can_create_collection,
    validate_collection_name,
)
from src.domain.entities.saved_item import validate_saved_item


class CollectionsNotAvailable(DataNotReadyError):
    """Kho bộ sưu tập không mở được -> 503 kèm cách khắc phục."""

    def __init__(self) -> None:
        super().__init__(
            "kho 'bộ sưu tập' không mở được",
            "Kiểm tra quyền ghi ở đường dẫn MOODBITE_USERS_DB.",
        )


class CollectionNotFoundError(ApplicationError):
    """Không có bộ sưu tập này TRONG PHẠM VI người đang đăng nhập -> 404.

    Cố ý dùng cùng một lỗi cho "không tồn tại" và "của người khác": tách ra thì kẻ dò chỉ
    cần đếm 403 và 404 là biết mã nào có thật.
    """

    def __init__(self, collection_id: str) -> None:
        super().__init__(f"Không tìm thấy bộ sưu tập '{collection_id}'.")
        self.collection_id = collection_id


def _new_id() -> str:
    # uuid4 chứ không dùng số tăng dần: số tăng dần để lộ tổng số bộ sưu tập của cả hệ
    # thống và dễ đoán mã của người khác.
    return uuid.uuid4().hex


class _CollectionUseCase:
    def __init__(
        self,
        collections: CollectionRepository,
        new_id: Callable[[], str] = _new_id,
    ) -> None:
        self._repo = collections
        self._new_id = new_id

    def _ensure_ready(self) -> None:
        if not self._repo.is_ready:
            raise CollectionsNotAvailable()

    def _require(self, user_id: str, collection_id: str) -> Collection:
        found = self._repo.get(user_id, collection_id)
        if found is None:
            raise CollectionNotFoundError(collection_id)
        return found


class ListCollectionsUseCase(_CollectionUseCase):
    def execute(self, user_id: str) -> List[Collection]:
        self._ensure_ready()
        return self._repo.list_for_user(user_id)


class CreateCollectionUseCase(_CollectionUseCase):
    def execute(self, user_id: str, name: str) -> Collection:
        self._ensure_ready()
        ten = validate_collection_name(name)
        ensure_can_create_collection(self._repo.count_for_user(user_id))
        return self._repo.create(
            Collection(collection_id=self._new_id(), user_id=user_id, name=ten)
        )


class RenameCollectionUseCase(_CollectionUseCase):
    def execute(self, user_id: str, collection_id: str, name: str) -> Collection:
        self._ensure_ready()
        ten = validate_collection_name(name)
        if not self._repo.rename(user_id, collection_id, ten):
            raise CollectionNotFoundError(collection_id)
        return self._require(user_id, collection_id)


class DeleteCollectionUseCase(_CollectionUseCase):
    def execute(self, user_id: str, collection_id: str) -> None:
        """404 nếu không có — KHÁC bỏ lưu yêu thích (luôn 200).

        Bỏ lưu là "đưa về trạng thái mong muốn" với một mục mà client đã biết. Còn xoá bộ
        sưu tập theo mã: mã sai nghĩa là client đang giữ dữ liệu cũ hoặc đoán mã — cả hai
        đều đáng để client biết.
        """
        self._ensure_ready()
        if not self._repo.delete(user_id, collection_id):
            raise CollectionNotFoundError(collection_id)


@dataclass(frozen=True)
class AddCollectionItemCommand:
    user_id: str
    collection_id: str
    item_type: str
    item_id: str
    name: str


class AddCollectionItemUseCase(_CollectionUseCase):
    def execute(self, command: AddCollectionItemCommand) -> Collection:
        self._ensure_ready()
        # Dùng lại ĐÚNG luật kiểm của "đã lưu": một mục trong bộ sưu tập cũng phải có loại
        # hợp lệ, có mã và có tên để hiển thị.
        loai, ma, ten = validate_saved_item(command.item_type, command.item_id, command.name)
        bo = self._require(command.user_id, command.collection_id)
        da_co = any(i.item_type == loai and i.item_id == ma for i in bo.items)
        ensure_can_add_item(len(bo.items), da_co)
        self._repo.add_item(
            command.user_id,
            command.collection_id,
            CollectionItem(item_type=loai, item_id=ma, name=ten),
        )
        return self._require(command.user_id, command.collection_id)


class RemoveCollectionItemUseCase(_CollectionUseCase):
    def execute(
        self, user_id: str, collection_id: str, item_type: str, item_id: str
    ) -> bool:
        """Bộ không có -> 404. Mục không có trong bộ -> vẫn thành công (trả False).

        Hai tình huống khác nhau thật: bộ sai mã là lỗi của client; còn bỏ một mục vốn đã
        không nằm trong bộ thì kết quả cuối cùng đúng như người dùng muốn — cùng quy ước
        với `DELETE /me/favorites`.
        """
        self._ensure_ready()
        loai, ma, _ = validate_saved_item(item_type, item_id, "-")
        self._require(user_id, collection_id)
        return self._repo.remove_item(user_id, collection_id, loai, ma)


__all__ = [
    "CollectionsNotAvailable",
    "CollectionNotFoundError",
    "ListCollectionsUseCase",
    "CreateCollectionUseCase",
    "RenameCollectionUseCase",
    "DeleteCollectionUseCase",
    "AddCollectionItemCommand",
    "AddCollectionItemUseCase",
    "RemoveCollectionItemUseCase",
]

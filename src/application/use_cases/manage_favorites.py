"""USE CASE: lưu / bỏ lưu / liệt kê "quán & món yêu thích".

Chỉ ĐIỀU PHỐI: kiểm dữ liệu bằng hàm ở domain, rồi gọi kho. Không có quy tắc nghiệp vụ
nào nằm ở đây — luật "một mục lưu trông thế nào" ở `domain/entities/saved_item.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.application.errors import ApplicationError, DataNotReadyError
from src.application.ports.saved_item_repository import SavedItemRepository
from src.domain.entities.saved_item import (
    SavedItem,
    SavedItemType,
    validate_saved_item,
)


class FavoritesNotAvailable(DataNotReadyError):
    """Kho yêu thích không mở được -> 503 kèm cách khắc phục."""

    def __init__(self) -> None:
        super().__init__(
            "kho 'quán & món đã lưu' không mở được",
            "Kiểm tra quyền ghi ở đường dẫn MOODBITE_USERS_DB.",
        )


@dataclass(frozen=True)
class SaveFavoriteCommand:
    user_id: str
    item_type: str
    item_id: str
    name: str


class SaveFavoriteUseCase:
    def __init__(self, saved_items: SavedItemRepository) -> None:
        self._saved = saved_items

    def execute(self, command: SaveFavoriteCommand) -> SavedItem:
        if not self._saved.is_ready:
            raise FavoritesNotAvailable()
        loai, ma, ten = validate_saved_item(
            command.item_type, command.item_id, command.name
        )
        return self._saved.add(
            SavedItem(
                user_id=command.user_id, item_type=loai, item_id=ma, name=ten
            )
        )


class RemoveFavoriteUseCase:
    def __init__(self, saved_items: SavedItemRepository) -> None:
        self._saved = saved_items

    def execute(self, user_id: str, item_type: str, item_id: str) -> bool:
        if not self._saved.is_ready:
            raise FavoritesNotAvailable()
        # Dùng lại đúng hàm kiểm của domain. Tên rỗng ở đây là hợp lệ về mặt nghiệp vụ
        # (bỏ lưu không cần tên), nên truyền một chỗ giữ chỗ rồi bỏ đi.
        loai, ma, _ = validate_saved_item(item_type, item_id, "-")
        return self._saved.remove(user_id, loai, ma)


class ListFavoritesUseCase:
    def __init__(self, saved_items: SavedItemRepository) -> None:
        self._saved = saved_items

    def execute(
        self, user_id: str, item_type: Optional[str] = None
    ) -> List[SavedItem]:
        if not self._saved.is_ready:
            raise FavoritesNotAvailable()
        loai: Optional[SavedItemType] = None
        if item_type:
            loai, _, _ = validate_saved_item(item_type, "-", "-")
        return self._saved.list_for_user(user_id, loai)


__all__ = [
    "SaveFavoriteCommand",
    "SaveFavoriteUseCase",
    "RemoveFavoriteUseCase",
    "ListFavoritesUseCase",
    "FavoritesNotAvailable",
]

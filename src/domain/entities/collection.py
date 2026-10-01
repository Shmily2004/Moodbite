"""BỘ SƯU TẬP của người dùng: một NHÓM quán/món do chính họ đặt tên. Thuần Python.

KHÁC "đã lưu" (`saved_item.py`) Ở ĐÂU
------------------------------------
"Yêu thích" và "Đã lưu" là hai danh sách CỐ ĐỊNH do hệ thống đặt tên — người dùng chỉ bật
/tắt. Bộ sưu tập thì người dùng TỰ ĐẶT TÊN và tự tạo bao nhiêu nhóm tuỳ ý ("Hẹn hò cuối
tuần", "Quán gần công ty"). Chủ dự án duyệt 2026-09-29 theo `frontend/design/profile.png`.

VÌ SAO KHÔNG NHÉT VÀO BẢNG `saved_items` bằng một `list_type` mới: `list_type` là một
TẬP ĐÓNG (enum), còn tên bộ sưu tập là DỮ LIỆU người dùng gõ. Để tên bộ sưu tập làm khoá
trong `saved_items` thì đổi tên một bộ = cập nhật hàng loạt dòng, và hai bộ trùng tên sẽ
dính vào nhau. Một bảng `collections` có mã riêng tránh được cả hai.

Mục trong bộ sưu tập DÙNG LẠI `SavedItemType` (restaurant | dish) — cùng một khái niệm
"cái gì được lưu", không định nghĩa lần thứ hai.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from src.domain.entities.saved_item import SavedItemType


class InvalidCollection(ValueError):
    """Dữ liệu bộ sưu tập không hợp lệ hoặc vượt giới hạn -> HTTP 400."""


# Tên hiện trên một dòng của thanh bên và trên nút chọn "Thêm vào bộ sưu tập". 60 ký tự đủ
# cho "Quán bún chả ngon quanh Hoàn Kiếm để dẫn bạn nước ngoài đi ăn" mà không vỡ bố cục.
MAX_COLLECTION_NAME_LENGTH = 60

# Chặn trên số bộ sưu tập một người được tạo. KHÔNG phải để "bán gói trả phí" mà vì hai lý
# do có thật: (1) ô chọn "Thêm vào bộ sưu tập" là một <select> — quá vài chục lựa chọn thì
# không còn dùng được; (2) một script gọi POST liên tục không làm phình CSDL vô hạn.
# 50 thừa xa cho một người dùng thật (bản thiết kế minh hoạ 5).
MAX_COLLECTIONS_PER_USER = 50

# Chặn trên số mục trong MỘT bộ. Dataset chỉ có ~4.200 quán ở Hà Nội; một bộ 200 mục đã là
# cả một bản đồ ẩm thực. Mục đích giống trên: chặn lạm dụng, không chặn người dùng thật.
MAX_ITEMS_PER_COLLECTION = 200


@dataclass(frozen=True)
class CollectionItem:
    item_type: SavedItemType
    item_id: str
    # Tên chụp lại LÚC THÊM, cùng lý do với `SavedItem.name`: hiện được danh sách ngay mà
    # không phải tra lại tên từng quán.
    name: str
    added_at: Optional[datetime] = None

    def to_public(self) -> dict:
        return {
            "item_type": self.item_type.value,
            "item_id": self.item_id,
            "name": self.name,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }


@dataclass(frozen=True)
class Collection:
    collection_id: str
    user_id: str
    name: str
    created_at: Optional[datetime] = None
    items: List[CollectionItem] = field(default_factory=list)

    def to_public(self) -> dict:
        # KHÔNG trả `user_id`: mọi endpoint đã tự giới hạn trong phạm vi chủ tài khoản,
        # đưa id ra chỉ thêm một thứ để lộ mà client không dùng tới.
        return {
            "collection_id": self.collection_id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "item_count": len(self.items),
            "items": [i.to_public() for i in self.items],
        }


def validate_collection_name(name: Optional[str]) -> str:
    """Tên bộ sưu tập: bỏ khoảng trắng hai đầu, 1..60 ký tự.

    Dài quá thì BÁO LỖI chứ không tự cắt (khác `validate_saved_item`): tên quán là dữ liệu
    ta chụp lại, cắt đi không ai để ý; tên bộ sưu tập là thứ người dùng vừa GÕ, cắt lặng lẽ
    thì họ sẽ thấy tên mình bị đổi mà không hiểu vì sao.
    """
    ten = " ".join((name or "").split())  # gộp khoảng trắng lặp, tránh "Hẹn    hò"
    if not ten:
        raise InvalidCollection("Tên bộ sưu tập không được để trống.")
    if len(ten) > MAX_COLLECTION_NAME_LENGTH:
        raise InvalidCollection(
            f"Tên bộ sưu tập tối đa {MAX_COLLECTION_NAME_LENGTH} ký tự "
            f"(đang có {len(ten)})."
        )
    return ten


def ensure_can_create_collection(current_count: int) -> None:
    """Còn được tạo thêm bộ sưu tập không. Ném `InvalidCollection` nếu đã đủ."""
    if current_count >= MAX_COLLECTIONS_PER_USER:
        raise InvalidCollection(
            f"Bạn đã có {MAX_COLLECTIONS_PER_USER} bộ sưu tập — mức tối đa. "
            "Hãy xoá bớt một bộ rồi tạo mới."
        )


def ensure_can_add_item(current_item_count: int, already_in_collection: bool) -> None:
    """Còn thêm được mục vào bộ này không.

    Mục ĐÃ CÓ trong bộ thì luôn cho qua: thêm lại là thao tác idempotent (chỉ cập nhật tên),
    không làm bộ to thêm. Chặn nó ở giới hạn sẽ khiến bộ đầy không đồng bộ lại được tên.
    """
    if already_in_collection:
        return
    if current_item_count >= MAX_ITEMS_PER_COLLECTION:
        raise InvalidCollection(
            f"Bộ sưu tập này đã có {MAX_ITEMS_PER_COLLECTION} mục — mức tối đa."
        )


__all__ = [
    "Collection",
    "CollectionItem",
    "InvalidCollection",
    "MAX_COLLECTION_NAME_LENGTH",
    "MAX_COLLECTIONS_PER_USER",
    "MAX_ITEMS_PER_COLLECTION",
    "validate_collection_name",
    "ensure_can_create_collection",
    "ensure_can_add_item",
]

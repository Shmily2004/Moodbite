"""Mục người dùng đã LƯU: một quán hoặc một món. Thuần Python.

VÌ SAO LƯU Ở SERVER MÀ KHÔNG PHẢI localStorage NHƯ TRƯỚC
--------------------------------------------------------
Bản đầu để ở trình duyệt vì backend chưa có gì. Nhược điểm thật, không phải giả định:
đổi máy là mất, xoá dữ liệu trình duyệt là mất, và quan trọng nhất — không đếm được để
tính cấp độ. Chủ dự án chốt 2026-08-22 làm "Quán yêu thích" nên phải có bảng thật.

Khách CHƯA đăng nhập vẫn dùng bản localStorage (xem `features/save-dish`): không có tài
khoản thì không có chỗ nào ở server để gắn dữ liệu vào.

VÌ SAO MỘT BẢNG CHO CẢ QUÁN LẪN MÓN, KHÔNG PHẢI HAI
---------------------------------------------------
Hai bảng `saved_restaurants` và `saved_dishes` sẽ có ĐÚNG cùng các cột và đúng cùng các
câu truy vấn, chỉ khác cái tên. Gộp lại thành một bảng với cột `item_type` giữ cho mọi
thao tác (lưu, bỏ lưu, đếm) chỉ có một bản cài đặt. Thêm loại thứ ba (bộ sưu tập chẳng
hạn) sau này là thêm một giá trị enum, không phải thêm một bảng và một adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class SavedItemType(str, Enum):
    RESTAURANT = "restaurant"
    DISH = "dish"


class InvalidSavedItem(ValueError):
    """Dữ liệu mục lưu không hợp lệ -> HTTP 400."""


# Chặn trên độ dài tên. Không phải để "bảo mật" mà để một request cố tình gửi 10MB tên
# quán không làm phình CSDL. 200 ký tự thừa cho mọi tên quán có thật.
MAX_SAVED_NAME_LENGTH = 200


@dataclass(frozen=True)
class SavedItem:
    user_id: str
    item_type: SavedItemType
    item_id: str
    # Tên chụp lại LÚC LƯU, cố ý sao chép chứ không tra lại mỗi lần hiển thị.
    # Lý do: danh sách "đã lưu" phải hiện được ngay mà không phải gọi thêm 15 request tra
    # tên từng quán. Đổi lại, quán đổi tên thì bản lưu vẫn giữ tên cũ — chấp nhận được,
    # và còn đúng hơn về mặt "đây là thứ tôi đã lưu lúc đó".
    name: str
    created_at: Optional[datetime] = None

    def to_public(self) -> dict:
        return {
            "item_type": self.item_type.value,
            "item_id": self.item_id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def validate_saved_item(item_type: str, item_id: str, name: str) -> tuple:
    """Kiểm và chuẩn hoá dữ liệu một mục lưu. Trả `(SavedItemType, item_id, name)`.

    Đặt ở domain vì đây là quy tắc nghiệp vụ: "một mục lưu phải có loại hợp lệ, có mã, và
    có tên để hiển thị". Mai kia có lệnh CLI nhập hàng loạt thì vẫn phải theo đúng luật này.
    """
    try:
        loai = SavedItemType(item_type)
    except ValueError:
        hop_le = [t.value for t in SavedItemType]
        raise InvalidSavedItem(f"item_type '{item_type}' không hợp lệ. Hợp lệ: {hop_le}")

    ma = (item_id or "").strip()
    if not ma:
        raise InvalidSavedItem("Thiếu item_id.")

    ten = (name or "").strip()
    if not ten:
        raise InvalidSavedItem("Thiếu name — danh sách đã lưu cần tên để hiển thị.")
    if len(ten) > MAX_SAVED_NAME_LENGTH:
        ten = ten[:MAX_SAVED_NAME_LENGTH]

    return loai, ma, ten


__all__ = [
    "SavedItem",
    "SavedItemType",
    "InvalidSavedItem",
    "validate_saved_item",
    "MAX_SAVED_NAME_LENGTH",
]

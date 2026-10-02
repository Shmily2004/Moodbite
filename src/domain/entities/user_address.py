"""ĐỊA CHỈ CỦA TÔI: những chỗ người dùng hay ăn quanh đó (Nhà, Công ty…). Thuần Python.

VÌ SAO CẦN: vị trí hiện lấy từ trình duyệt. Người dùng từ chối chia sẻ vị trí (hoặc máy
tính bàn không định vị được) thì app rơi về trung tâm Hà Nội — gợi ý quán cách nhà họ
10km. Một địa chỉ MẶC ĐỊNH đã lưu là điểm dự phòng tốt hơn hẳn trung tâm thành phố.

⚠️ KHÔNG CÓ GEOCODING. Toạ độ chỉ đến từ hai nguồn người dùng tự làm: bấm "Dùng vị trí
hiện tại" (trình duyệt) hoặc bấm lên bản đồ Leaflet. `address_text` là chữ người dùng tự
gõ, lưu NGUYÊN VĂN — hệ thống không đoán, không chuẩn hoá, không tra ngược từ toạ độ.
Lý do: Google Geocoding cần thẻ thanh toán; Nominatim cấm dùng cho ứng dụng tra liên tục
theo điều khoản sử dụng. Xem CLAUDE.md mục "Ràng buộc chi phí".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.value_objects.location import HANOI_BBOX, trong_ha_noi


class InvalidUserAddress(ValueError):
    """Dữ liệu địa chỉ không hợp lệ hoặc vượt giới hạn -> HTTP 400."""


# Nhãn hiện trên chip "Đang dùng: Nhà" ở thanh bộ lọc — phải ngắn. 40 ký tự đủ cho
# "Nhà bố mẹ ở Long Biên" nhưng không đủ để biến nhãn thành một đoạn văn.
MAX_ADDRESS_LABEL_LENGTH = 40

# Chữ mô tả tự do (số nhà, ngõ, ghi chú). 200 ký tự như `MAX_SAVED_NAME_LENGTH`: đủ cho
# địa chỉ Việt Nam dài nhất, chặn request cố tình gửi hàng MB.
MAX_ADDRESS_TEXT_LENGTH = 200

# Người dùng thật có 2–4 chỗ hay ăn (nhà, công ty, nhà người yêu, chỗ học). 10 là thừa,
# và danh sách vẫn gọn trong một màn hình. Chặn để một script không làm phình CSDL.
MAX_ADDRESSES_PER_USER = 10


@dataclass(frozen=True)
class UserAddress:
    address_id: str
    user_id: str
    label: str
    # `None` = người dùng không gõ gì. KHÔNG thay bằng chuỗi rỗng hay chữ tự sinh.
    address_text: Optional[str]
    lat: float
    lng: float
    is_default: bool = False
    created_at: Optional[datetime] = None

    def to_public(self) -> dict:
        return {
            "address_id": self.address_id,
            "label": self.label,
            "address_text": self.address_text,
            # Tên trường CHUNG của cả API (`/search`, `/dishes`...), xem test khoá ở
            # tests/test_user_addresses.py. Bên trong entity vẫn là `lat`/`lng` cho gọn.
            "latitude": self.lat,
            "longitude": self.lng,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def validate_address_label(label: Optional[str]) -> str:
    nhan = " ".join((label or "").split())
    if not nhan:
        raise InvalidUserAddress("Nhãn địa chỉ không được để trống (ví dụ: Nhà, Công ty).")
    if len(nhan) > MAX_ADDRESS_LABEL_LENGTH:
        raise InvalidUserAddress(
            f"Nhãn địa chỉ tối đa {MAX_ADDRESS_LABEL_LENGTH} ký tự (đang có {len(nhan)})."
        )
    return nhan


def validate_address_text(text: Optional[str]) -> Optional[str]:
    """Chữ mô tả: bỏ trống -> `None` (chưa có dữ liệu), KHÔNG phải chuỗi rỗng.

    Giữ nguyên nội dung người dùng gõ, chỉ bỏ khoảng trắng hai đầu.
    """
    if text is None:
        return None
    gon = text.strip()
    if not gon:
        return None
    if len(gon) > MAX_ADDRESS_TEXT_LENGTH:
        raise InvalidUserAddress(
            f"Mô tả địa chỉ tối đa {MAX_ADDRESS_TEXT_LENGTH} ký tự (đang có {len(gon)})."
        )
    return gon


def validate_address_coordinates(lat: float, lng: float) -> tuple:
    """Toạ độ phải nằm trong Hà Nội — phạm vi sản phẩm chốt 2026-08-19.

    Ngoài Hà Nội thì từ chối chứ không lưu: dataset không có quán nào ở đó, lưu vào rồi
    làm điểm dự phòng sẽ cho ra trang "không tìm thấy quán nào" mà người dùng không hiểu
    vì sao. Báo ngay lúc lưu thì họ biết nguyên nhân.
    """
    try:
        vi_do = float(lat)
        kinh_do = float(lng)
    except (TypeError, ValueError):
        raise InvalidUserAddress("Toạ độ lat/lng phải là số.")
    # NaN lọt qua mọi phép so sánh `<=` dưới dạng False -> tự bị loại ở `trong_ha_noi`.
    if not trong_ha_noi(vi_do, kinh_do):
        nam, tay, bac, dong = HANOI_BBOX
        raise InvalidUserAddress(
            "Địa chỉ phải nằm trong Hà Nội — MoodBite hiện chỉ có dữ liệu quán ở Hà Nội. "
            f"Toạ độ nhận được: ({vi_do}, {kinh_do}); "
            f"khung hợp lệ: vĩ độ {nam}–{bac}, kinh độ {tay}–{dong}."
        )
    return vi_do, kinh_do


def ensure_can_add_address(current_count: int) -> None:
    if current_count >= MAX_ADDRESSES_PER_USER:
        raise InvalidUserAddress(
            f"Bạn đã lưu {MAX_ADDRESSES_PER_USER} địa chỉ — mức tối đa. "
            "Hãy xoá bớt một địa chỉ rồi thêm mới."
        )


def resolve_default_flag(requested: Optional[bool], current_count: int) -> bool:
    """Địa chỉ mới có thành mặc định không.

    Người dùng nói rõ thì theo người dùng. Không nói gì thì địa chỉ ĐẦU TIÊN tự thành mặc
    định: lưu một địa chỉ duy nhất mà vẫn không có điểm dự phòng là bắt người dùng làm
    thêm một bước không ai nghĩ tới. Từ địa chỉ thứ hai trở đi thì KHÔNG tự đổi mặc định
    — lặng lẽ chuyển điểm dự phòng từ "Nhà" sang "Công ty" là đổi hành vi sau lưng họ.
    """
    if requested is not None:
        return bool(requested)
    return current_count == 0


__all__ = [
    "UserAddress",
    "InvalidUserAddress",
    "MAX_ADDRESS_LABEL_LENGTH",
    "MAX_ADDRESS_TEXT_LENGTH",
    "MAX_ADDRESSES_PER_USER",
    "validate_address_label",
    "validate_address_text",
    "validate_address_coordinates",
    "ensure_can_add_address",
    "resolve_default_flag",
]

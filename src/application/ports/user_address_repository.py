"""PORT: hợp đồng lưu "Địa chỉ của tôi".

⚠️ Hai bất biến adapter PHẢI giữ, không được giao cho use case tự lo:

  1. Mọi truy vấn giới hạn trong `user_id`. Địa chỉ của người khác = không tồn tại.
  2. Mỗi người có KHÔNG HOẶC MỘT địa chỉ mặc định. Đặt một địa chỉ làm mặc định thì bỏ
     cờ ở mọi địa chỉ khác của người đó TRONG CÙNG MỘT GIAO DỊCH — làm hai bước rời thì
     hai tab bấm cùng lúc sẽ để lại hai địa chỉ mặc định, và điểm dự phòng vị trí trở
     thành ngẫu nhiên.
"""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from src.domain.entities.user_address import UserAddress


@runtime_checkable
class UserAddressRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        ...

    def list_for_user(self, user_id: str) -> List[UserAddress]:
        """Mặc định đứng đầu, rồi tới địa chỉ cũ nhất (thứ tự người dùng đã thêm)."""
        ...

    def get(self, user_id: str, address_id: str) -> Optional[UserAddress]:
        ...

    def count_for_user(self, user_id: str) -> int:
        ...

    def create(self, address: UserAddress) -> UserAddress:
        """Lưu mới. `is_default=True` thì bỏ cờ mặc định của các địa chỉ khác (cùng giao dịch)."""
        ...

    def update(
        self,
        user_id: str,
        address_id: str,
        *,
        label: Optional[str] = None,
        address_text: Optional[str] = None,
        clear_address_text: bool = False,
        is_default: Optional[bool] = None,
    ) -> Optional[UserAddress]:
        """Sửa những trường được truyền. `None` = giữ nguyên.

        `clear_address_text=True` để XOÁ mô tả (khác "không đổi"): hai ý định này đều biểu
        diễn bằng `None` nếu chỉ có một tham số, nên phải có cờ riêng.
        Trả bản sau khi sửa, hoặc `None` nếu không có địa chỉ đó trong phạm vi người dùng.
        """
        ...

    def delete(self, user_id: str, address_id: str) -> bool:
        ...


__all__ = ["UserAddressRepository"]

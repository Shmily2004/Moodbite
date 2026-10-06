"""PORT: chỉ mục MÓN -> QUÁN mà luồng "chọn món trước" đọc.

Hai dạng đều hợp lệ:
  - một `Mapping[dish_id, list[DishMatch]]` thường (test, hoặc kho chỉ đọc);
  - một nguồn TỰ LÀM MỚI có `snapshot()` (bản thật: `LiveDishRestaurantIndex`), vì kho
    quán đổi được lúc chạy — admin ẩn/sửa/thêm quán (bug chỉ mục cũ, 2026-10-06).

`current_index()` gom hai dạng về một: use case gọi nó MỘT LẦN đầu mỗi request, để mọi
lần tra trong cùng request nhìn cùng một phiên bản dữ liệu (không lẫn nửa cũ nửa mới nếu
admin ghi đúng lúc đó).
"""
from __future__ import annotations

from typing import Mapping, Optional, Protocol, Sequence, runtime_checkable


@runtime_checkable
class RefreshingDishIndex(Protocol):
    @property
    def is_ready(self) -> bool:
        ...

    def snapshot(self) -> Mapping[str, Sequence]:
        ...


def current_index(source: Optional[object]) -> Mapping[str, Sequence]:
    """Chỉ mục dùng cho request hiện tại. `None` -> rỗng."""
    if source is None:
        return {}
    snapshot = getattr(source, "snapshot", None)
    return snapshot() if callable(snapshot) else source  # type: ignore[return-value]


def index_is_ready(source: Optional[object]) -> bool:
    """Nguồn tự làm mới biết mình sẵn sàng chưa; `dict` thường thì coi là sẵn sàng."""
    if source is None:
        return False
    return bool(getattr(source, "is_ready", True))


__all__ = ["RefreshingDishIndex", "current_index", "index_is_ready"]

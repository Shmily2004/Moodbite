"""ADAPTER: chỉ mục MÓN -> QUÁN luôn khớp với dữ liệu quán HIỆN TẠI.

BUG THẬT mà file này sửa (rà soát 2026-10-06)
----------------------------------------------
Trước đây `dependencies.py` dựng chỉ mục MỘT LẦN lúc khởi động bằng một `dict` thường.
Admin ẩn/sửa/thêm quán -> kho quán nạp lại -> nhưng `dict` kia vẫn giữ các đối tượng
`Restaurant` CŨ. Tái hiện được: `repo.set_active("p1", False)` xong thì
`repo.list_all() == []` mà `/dishes/{id}/restaurants` vẫn trả p1; quán mới thêm không bao
giờ hiện; tên/giá vừa sửa vẫn là bản cũ — tới tận lần khởi động lại.

CÁCH LÀM
--------
Kho quán có `data_version` tăng sau mỗi lần nạp lại. Chỉ mục nhớ nó được dựng từ phiên bản
nào; mỗi lần được hỏi thì so hai số (O(1)) và chỉ dựng lại khi KHÁC.

CHI PHÍ ĐÃ ĐO (2026-10-06, 298 món x 52.871 quán): dựng một lần mất ~3,9 giây.
  - KHÔNG dựng lại ở mỗi request — đó là 3,9 giây cho mỗi lần bấm.
  - Dựng lại ĐÚNG MỘT LẦN cho mỗi lần dữ liệu đổi, và cố gắng làm việc đó NGOÀI request
    của người dùng: kho quán báo "vừa nạp lại" (`add_reload_listener`) thì chỉ mục khởi
    động một thread nền dựng ngay. Request người dùng tới trong lúc đang dựng sẽ CHỜ bản
    mới (tối đa ~4 giây) thay vì nhận bản cũ: thà chậm một lần còn hơn dẫn người dùng tới
    quán admin vừa ẩn vì đã đóng cửa.

KHÔNG phải singleton cấp module: được tạo trong `build_container` và sống trên Container
(CLAUDE.md mục 6).

Kho nào không có `data_version` (bản CSV — chỉ đọc, không bao giờ đổi lúc chạy) thì coi
như phiên bản 0 mãi mãi: dựng đúng một lần như trước.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

from src.domain.services.dish_matching import build_dish_restaurant_index

logger = logging.getLogger("moodbite.dish_index")

_EMPTY: Dict[str, List] = {}


class LiveDishRestaurantIndex(Mapping):
    """`Mapping[dish_id, list[DishMatch]]` tự làm mới theo `data_version` của kho quán.

    Là một `Mapping` để use case nào đang nhận `dict` (kể cả bản giả trong test) vẫn nhận
    được nó mà không đổi gì. Use case nên gọi `snapshot()` MỘT LẦN đầu mỗi request để mọi
    lần tra trong request đó cùng nhìn một phiên bản.
    """

    def __init__(
        self,
        catalog: object,
        restaurants: object,
        background_refresh: bool = True,
    ) -> None:
        self._catalog = catalog
        self._restaurants = restaurants
        # (phiên bản dữ liệu quán đã dùng để dựng, chỉ mục). MỘT thuộc tính, gán MỘT lần
        # -> người đọc không bao giờ thấy chỉ mục mới đi kèm số phiên bản cũ hay ngược lại.
        self._built: Optional[Tuple[int, Mapping[str, Sequence]]] = None
        self._lock = threading.Lock()
        self._last_build_seconds: Optional[float] = None
        self._last_error: Optional[str] = None
        if background_refresh:
            subscribe = getattr(restaurants, "add_reload_listener", None)
            if callable(subscribe):
                subscribe(self._refresh_in_background)

    # -- Trạng thái ---------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        """Cả danh mục món LẪN kho quán đều đã nạp được. Thiếu một trong hai thì chỉ mục
        rỗng là vô nghĩa — use case phải trả 503, không phải "0 quán"."""
        return bool(
            getattr(self._catalog, "is_ready", False)
            and getattr(self._restaurants, "is_ready", False)
        )

    def status(self) -> dict:
        built = self._built
        return {
            "ready": self.is_ready,
            "built_from_data_version": built[0] if built else None,
            "data_version": self._data_version(),
            "last_build_seconds": self._last_build_seconds,
            "error": self._last_error,
        }

    # -- Đọc ---------------------------------------------------------------------

    def snapshot(self) -> Mapping[str, Sequence]:
        """Chỉ mục ứng với dữ liệu quán HIỆN TẠI. Dựng lại nếu dữ liệu đã đổi.

        Chưa sẵn sàng -> `{}` (use case tự kiểm `is_ready` để trả 503 trước khi tới đây).
        """
        if not self.is_ready:
            return _EMPTY
        version = self._data_version()
        built = self._built
        if built is not None and built[0] == version:
            return built[1]
        return self._rebuild()

    def _rebuild(self) -> Mapping[str, Sequence]:
        with self._lock:
            # Kiểm lại SAU khi có khoá: thread nền (hoặc request khác) có thể vừa dựng
            # xong đúng phiên bản này trong lúc ta chờ — không dựng lần hai.
            version = self._data_version()
            built = self._built
            if built is not None and built[0] == version:
                return built[1]
            # Đọc phiên bản TRƯỚC `list_all()`: nếu dữ liệu đổi tiếp trong lúc dựng, chỉ
            # mục này mang số cũ và lần hỏi sau sẽ dựng lại — thừa một lần dựng, không
            # bao giờ thiếu.
            bat_dau = time.perf_counter()
            try:
                index = build_dish_restaurant_index(
                    self._catalog.list_dishes(), self._restaurants.list_all()
                )
            except Exception as exc:  # noqa: BLE001 - ghi lại rồi ném tiếp, không nuốt
                self._last_error = f"Dựng chỉ mục món-quán thất bại: {exc}"
                logger.exception("Dựng chỉ mục món-quán thất bại")
                raise
            self._built = (version, index)
            self._last_build_seconds = round(time.perf_counter() - bat_dau, 3)
            self._last_error = None
            logger.info(
                "Dựng chỉ mục món-quán (dữ liệu phiên bản %s) mất %.2f giây.",
                version, self._last_build_seconds,
            )
            return index

    def _refresh_in_background(self) -> None:
        """Gọi từ luồng của request GHI (admin) -> chỉ khởi động thread rồi trả về ngay."""
        threading.Thread(
            target=self._refresh_quietly, name="dish-index-rebuild", daemon=True
        ).start()

    def _refresh_quietly(self) -> None:
        try:
            self.snapshot()
        except Exception:  # noqa: BLE001 - đã ghi log trong `_rebuild`; request sau thử lại
            pass

    def _data_version(self) -> int:
        return int(getattr(self._restaurants, "data_version", 0) or 0)

    # -- Giao diện Mapping ---------------------------------------------------------

    def __getitem__(self, dish_id: str) -> Sequence:
        return self.snapshot()[dish_id]

    def __iter__(self) -> Iterator[str]:
        return iter(self.snapshot())

    def __len__(self) -> int:
        return len(self.snapshot())


__all__ = ["LiveDishRestaurantIndex"]

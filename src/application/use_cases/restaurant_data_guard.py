"""Chốt chặn DÙNG CHUNG: dataset quán chưa nạp được -> 503 DATA_NOT_READY kèm lệnh cần chạy.

VÌ SAO TÁCH RA (bug thật, rà soát 2026-10-06): luồng món (`/dishes/suggest`,
`/dishes/{id}`, `/dishes/{id}/restaurants`) chỉ kiểm DANH MỤC MÓN. Thiếu dataset quán thì
chỉ mục món-quán rỗng, và API trả 200 kèm "Chưa có quán nào khớp món" / "285 món chưa tìm
được quán" — đổ lỗi cho dữ liệu món trong khi thực ra CHƯA NẠP ĐƯỢC QUÁN NÀO. Ba use case
cùng cần một câu trả lời, nên câu đó chỉ được viết ở MỘT chỗ.

Lệnh khắc phục viết thành từng lệnh RIÊNG, KHÔNG nối bằng `&&`: máy chủ dự án chạy Windows
PowerShell 5.1, nơi `&&` là lỗi cú pháp (CLAUDE.md mục 1 — lỗi đã từng xảy ra).
"""
from __future__ import annotations

from typing import Optional

from src.application.errors import DataNotReadyError

# Thứ tự pipeline BẮT BUỘC (CLAUDE.md mục 4c): clustering phải chạy CUỐI.
HOW_TO_BUILD_RESTAURANT_DATA = (
    "chạy lần lượt từng lệnh: "
    "python -m data_pipeline.merge_and_prepare_raw ; "
    "python -m data_pipeline.data_cleaning ; "
    "python -m data_pipeline.feature_engineering ; "
    "python -m data_pipeline.clustering ; "
    "nếu dùng MOODBITE_STORAGE=sqlite thì thêm python scripts/build_sqlite.py ; "
    "rồi khởi động lại backend"
)


def require_restaurant_data(restaurants: Optional[object]) -> None:
    """Ném `DataNotReadyError` (-> 503) nếu kho quán chưa sẵn sàng.

    `None` = use case được dựng không kèm kho quán (bộ test cũ chỉ quan tâm tới món) ->
    không kiểm, giữ hành vi cũ.
    """
    if restaurants is None or getattr(restaurants, "is_ready", True):
        return
    ly_do = getattr(restaurants, "load_error", None)
    raise DataNotReadyError(
        f"dataset quán ăn ({ly_do})" if ly_do else "dataset quán ăn",
        HOW_TO_BUILD_RESTAURANT_DATA,
    )


__all__ = ["HOW_TO_BUILD_RESTAURANT_DATA", "require_restaurant_data"]

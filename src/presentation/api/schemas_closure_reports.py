"""Schema HTTP cho trang quản trị "Quán bị người dùng báo đóng cửa" (thêm 2026-10-06).

File riêng, không thêm vào `schemas.py` (đã > 1.000 dòng — CLAUDE.md mục 6), cùng lý do
với `schemas_me_places.py`. Tên trường `snake_case`, bọc `{"data": …}` — CLAUDE.md mục 5.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.presentation.api.schemas import ERROR_RESPONSES, ErrorEnvelope

CLOSURE_ADMIN_ERROR_RESPONSES = {
    **ERROR_RESPONSES,
    401: {"model": ErrorEnvelope, "description": "UNAUTHORIZED"},
    403: {"model": ErrorEnvelope, "description": "FORBIDDEN"},
}


class ClosureReportItem(BaseModel):
    restaurant_id: str
    name: Optional[str] = Field(
        None, description="`null` = quán không còn trong dữ liệu. KHÔNG bịa tên."
    )
    report_count: int = Field(..., description="Số NGƯỜI BÁO khác nhau (theo IP đã băm).")
    is_hidden: bool = Field(
        ..., description="Đủ ngưỡng -> đang bị ẩn khỏi MỌI luồng người dùng."
    )


class ClosureReportListData(BaseModel):
    threshold: int = Field(..., description="Số người báo cần để ẩn quán.")
    items: List[ClosureReportItem]


class ClosureReportListResponse(BaseModel):
    data: ClosureReportListData


class ClearedClosureReportsData(BaseModel):
    restaurant_id: str
    cleared_reports: int = Field(..., description="Số người báo vừa bị gỡ.")
    is_hidden: bool


class ClearedClosureReportsResponse(BaseModel):
    data: ClearedClosureReportsData

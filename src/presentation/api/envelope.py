"""Response envelope theo đặc tả API mục 1.5.

    Thành công:  {"data": {...}}
    Lỗi:         {"error": {"code": "...", "message": "...", "details": {...}}}

Lý do (trích đặc tả): client xử lý nhất quán bằng MỘT điều kiện duy nhất (có `error`
hay không) thay vì phải suy đoán qua HTTP status.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    """Bảng mã lỗi dùng chung - đặc tả API mục 1.6."""

    INVALID_REQUEST = "INVALID_REQUEST"
    RESTAURANT_NOT_FOUND = "RESTAURANT_NOT_FOUND"
    SEARCH_RESULT_ITEM_NOT_FOUND = "SEARCH_RESULT_ITEM_NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    DATA_NOT_READY = "DATA_NOT_READY"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def success(data: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"data": data})


def error(
    code: ErrorCode,
    message: str,
    status_code: int,
    details: Optional[dict] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code.value,
                "message": message,
                "details": details or {},
            }
        },
    )

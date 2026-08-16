"""Ánh xạ lỗi nghiệp vụ -> HTTP status + mã lỗi theo đặc tả API mục 1.6.

MỘT nơi duy nhất, thay vì try/except ở mọi router.

Cách cũ bọc `except Exception` quanh từng route rồi trả 400 khiến MỌI lỗi - kể cả lỗi lập
trình như AttributeError - đều hiện thành "400 Bad Request", che mất bug thật.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.application.errors import DataNotReadyError
from src.application.use_cases.log_interaction import (
    InvalidInteractionError,
    RestaurantNotFoundError,
)
from src.domain.value_objects.mood import UnsupportedMoodError
from src.presentation.api.envelope import ErrorCode, error

logger = logging.getLogger("moodbite")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _request_invalid(request: Request, exc: RequestValidationError):
        # Thiếu trường bắt buộc / sai kiểu -> INVALID_REQUEST theo đặc tả, không phải 422 trần.
        return error(
            ErrorCode.INVALID_REQUEST,
            "Request không hợp lệ.",
            status_code=400,
            details={"fields": exc.errors()},
        )

    @app.exception_handler(UnsupportedMoodError)
    async def _unsupported_mood(request: Request, exc: UnsupportedMoodError):
        return error(ErrorCode.INVALID_REQUEST, str(exc), status_code=400)

    @app.exception_handler(InvalidInteractionError)
    async def _invalid_interaction(request: Request, exc: InvalidInteractionError):
        return error(ErrorCode.INVALID_REQUEST, str(exc), status_code=400)

    @app.exception_handler(RestaurantNotFoundError)
    async def _restaurant_not_found(request: Request, exc: RestaurantNotFoundError):
        return error(
            ErrorCode.RESTAURANT_NOT_FOUND,
            str(exc),
            status_code=404,
            details={"restaurant_id": exc.restaurant_id},
        )

    @app.exception_handler(DataNotReadyError)
    async def _data_not_ready(request: Request, exc: DataNotReadyError):
        # Không phải lỗi client: server thiếu dữ liệu, cần chạy data_pipeline.
        return error(ErrorCode.DATA_NOT_READY, str(exc), status_code=503)

    @app.exception_handler(ResponseValidationError)
    async def _response_invalid(request: Request, exc: ResponseValidationError):
        # Response không khớp schema = BUG CỦA SERVER, không phải lỗi client.
        logger.error("Response không khớp schema tại %s: %s", request.url.path, exc)
        return error(
            ErrorCode.INTERNAL_ERROR,
            "Response không khớp schema API.",
            status_code=500,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception(request: Request, exc: StarletteHTTPException):
        # Bọc cả 404 định tuyến vào envelope để client chỉ phải xử lý một dạng response.
        code = (
            ErrorCode.RESTAURANT_NOT_FOUND
            if exc.status_code == 404 and "/restaurants/" in request.url.path
            else ErrorCode.INVALID_REQUEST
            if exc.status_code < 500
            else ErrorCode.INTERNAL_ERROR
        )
        return error(code, str(exc.detail), status_code=exc.status_code)

    @app.exception_handler(ValueError)
    async def _value_error(request: Request, exc: ValueError):
        return error(ErrorCode.INVALID_REQUEST, str(exc), status_code=400)

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception):
        # Lỗi ngoài dự kiến = bug. Ghi FULL traceback vào log để còn sửa được,
        # nhưng không trả traceback cho client.
        logger.exception("Lỗi không mong đợi tại %s %s", request.method, request.url.path)
        return error(
            ErrorCode.INTERNAL_ERROR,
            "Internal server error. Xem log server để biết chi tiết.",
            status_code=500,
        )

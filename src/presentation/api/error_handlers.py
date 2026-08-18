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

from src.application.errors import (
    AdminNotConfiguredError,
    AuthNotConfiguredError,
    DataNotReadyError,
    InvalidCredentialsError,
    PermissionDeniedError,
    RateLimitExceeded,
)
from src.application.ports.user_repository import UsernameAlreadyExists
from src.application.use_cases.find_restaurants_for_dish import DishNotFoundError
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

    @app.exception_handler(DishNotFoundError)
    async def _dish_not_found(request: Request, exc: DishNotFoundError):
        return error(
            ErrorCode.DISH_NOT_FOUND,
            str(exc),
            status_code=404,
            details={"dish_id": exc.dish_id},
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

    @app.exception_handler(InvalidCredentialsError)
    async def _unauthorized(request: Request, exc: InvalidCredentialsError):
        # 401 chứ KHÔNG phải 403: client chưa chứng minh được mình là ai.
        return error(ErrorCode.UNAUTHORIZED, str(exc), status_code=401)

    @app.exception_handler(PermissionDeniedError)
    async def _forbidden(request: Request, exc: PermissionDeniedError):
        # 403 chứ KHÔNG phải 401: token tốt, người này chỉ không đủ quyền. Trả nhầm 401
        # khiến client đá người dùng về màn hình đăng nhập, đăng nhập lại vẫn hỏng.
        return error(ErrorCode.FORBIDDEN, str(exc), status_code=403)

    @app.exception_handler(UsernameAlreadyExists)
    async def _username_taken(request: Request, exc: UsernameAlreadyExists):
        # 409 CONFLICT: request hợp lệ về cú pháp, chỉ xung đột với trạng thái hiện có.
        # Đây là chỗ DUY NHẤT được phép tiết lộ "tên này đã có người dùng" — không tránh
        # được, vì người đăng ký buộc phải biết để đổi tên khác. Bù lại, luồng ĐĂNG NHẬP
        # tuyệt đối không lộ điều đó (xem `LoginUseCase`).
        return error(
            ErrorCode.USERNAME_TAKEN,
            "Tên đăng nhập này đã có người dùng. Hãy chọn tên khác.",
            status_code=409,
        )

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limited(request: Request, exc: RateLimitExceeded):
        return error(
            ErrorCode.RATE_LIMITED,
            str(exc),
            status_code=429,
            details={"retry_after_seconds": exc.retry_after_seconds},
            # Header chuẩn HTTP: client và proxy hiểu được mà không cần đọc body.
            headers={"Retry-After": str(exc.retry_after_seconds)},
        )

    @app.exception_handler(AdminNotConfiguredError)
    async def _admin_not_configured(request: Request, exc: AdminNotConfiguredError):
        # Chưa cấu hình admin -> 503 kèm CÁCH KHẮC PHỤC, đúng quy ước DATA_NOT_READY.
        return error(ErrorCode.DATA_NOT_READY, str(exc), status_code=503)

    @app.exception_handler(AuthNotConfiguredError)
    async def _auth_not_configured(request: Request, exc: AuthNotConfiguredError):
        # Chưa cấu hình xác thực người dùng. Cùng quy ước với admin ở trên; đăng ký riêng
        # vì thông báo khác nhau (biến môi trường khác nhau).
        return error(ErrorCode.DATA_NOT_READY, str(exc), status_code=503)

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

"""Điểm khởi tạo FastAPI app.

Dùng app factory (`create_app`) thay vì tạo app ở cấp module, để test dựng được app
sạch với cấu hình riêng mà không đụng biến toàn cục.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config.settings import Settings
from src.presentation.api.dependencies import build_container
from src.presentation.api.error_handlers import register_error_handlers
from src.presentation.api.routers import admin, interactions, meta, restaurants, search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("moodbite")

# Tiền tố version tường minh ngay từ đầu (đặc tả API mục 1.2): khi công thức xếp hạng
# hoặc response schema đổi ở giai đoạn sau, client cũ không vỡ.
API_PREFIX = "/api/v1"


def create_app(
    settings: Optional[Settings] = None, container: Optional[object] = None
) -> FastAPI:
    """Dựng app.

    `container` cho phép TIÊM sẵn bộ phụ thuộc thay vì tự lắp. Chỉ dùng trong test:
    `build_container()` đọc cả dataset (4938 quán) và dựng chỉ mục TF-IDF, mất ~1.5s.
    Test dựng app hàng chục lần rồi ghi đè container ngay sau đó, nên nếu không có
    tham số này thì mỗi test phải trả 1.5s cho công việc bị vứt đi.
    """
    settings = settings or Settings.from_env()

    app = FastAPI(
        title="MoodBite API",
        description=(
            "Gợi ý nhà hàng theo ngữ cảnh: câu tìm kiếm tự do + vị trí + thời điểm.\n\n"
            "Mọi response bọc trong `data` (thành công) hoặc `error` (lỗi).\n"
            "Xem GET /api/v1/health để biết nguồn dữ liệu nào đã sẵn sàng."
        ),
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Lắp dependency MỘT LẦN lúc khởi động - không đọc lại file ở mỗi request.
    app.state.container = container if container is not None else build_container(settings)

    register_error_handlers(app)

    app.include_router(search.router, prefix=API_PREFIX)
    app.include_router(restaurants.router, prefix=API_PREFIX)
    app.include_router(interactions.router, prefix=API_PREFIX)
    app.include_router(meta.router, prefix=API_PREFIX)
    # Quản trị: `public_router` chỉ có /login (nơi phát token), `router` yêu cầu token.
    app.include_router(admin.public_router, prefix=API_PREFIX)
    app.include_router(admin.router, prefix=API_PREFIX)

    # /health không prefix để hạ tầng (Railway/Heroku) probe được theo mặc định.
    # Chỉ health, không nhân bản cả router meta.
    app.add_api_route("/health", meta.health, methods=["GET"], tags=["meta"])

    # Tính năng floorplan -> 3D đã chuyển vào `archive/spatial-3d/` (2026-08-17).
    # Nó kéo theo torch + ultralytics + transformers + opencv (~2GB) mà CI phải cài ở
    # MỌI lần chạy, trong khi tính năng đã tạm dừng và tắt mặc định. Cách khôi phục ghi
    # ở `archive/spatial-3d/README.md`.

    health = app.state.container.health()
    logger.info(
        "MoodBite khởi động: %s quán, %s quán có chi tiết, %s rule món ăn.",
        health["restaurants"].get("count", "?"),
        health["restaurant_details"].get("count", "?"),
        health["dish_knowledge"].get("rules", "?"),
    )
    # In rõ nguồn nào hỏng NGAY lúc khởi động, thay vì để tới lúc gọi API mới biết.
    for name, info in health.items():
        if info.get("error"):
            logger.warning("Nguồn '%s' chưa sẵn sàng: %s", name, info["error"])

    return app

# CỐ Ý không tạo `app = create_app()` ở cấp module: làm vậy thì mỗi lần import file này
# (kể cả trong test) đều nạp toàn bộ 4170 quán. Server tạo app ở app.py.

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
from src.presentation.api.routers import interactions, meta, restaurants, search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("moodbite")

# Tiền tố version tường minh ngay từ đầu (đặc tả API mục 1.2): khi công thức xếp hạng
# hoặc response schema đổi ở giai đoạn sau, client cũ không vỡ.
API_PREFIX = "/api/v1"


def create_app(settings: Optional[Settings] = None) -> FastAPI:
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
    app.state.container = build_container(settings)

    register_error_handlers(app)

    app.include_router(search.router, prefix=API_PREFIX)
    app.include_router(restaurants.router, prefix=API_PREFIX)
    app.include_router(interactions.router, prefix=API_PREFIX)
    app.include_router(meta.router, prefix=API_PREFIX)

    # /health không prefix để hạ tầng (Railway/Heroku) probe được theo mặc định.
    # Chỉ health, không nhân bản cả router meta.
    app.add_api_route("/health", meta.health, methods=["GET"], tags=["meta"])

    if settings.enable_spatial_features:
        # Tính năng floorplan -> 3D đang TẠM DỪNG (xem docs/architecture_decisions.md).
        # Chỉ bật khi MOODBITE_ENABLE_SPATIAL=1 để không bắt mọi lần khởi động phải nạp
        # torch/ultralytics (nặng và hay lỗi môi trường).
        from src.presentation.api.routers import spatial

        app.include_router(spatial.router, prefix=API_PREFIX)
        logger.info("Đã bật tính năng spatial (floorplan/depth) - đang ở trạng thái thử nghiệm.")

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

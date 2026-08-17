"""DI container: nơi DUY NHẤT lắp adapter thật vào use case.

Đây là chỗ trả lời câu hỏi "cái gì nối với cái gì". Muốn đổi CSV sang PostgreSQL thì
sửa đúng file này, không đụng vào use case hay router.

Container được tạo MỘT LẦN lúc khởi động và gắn vào app.state. Router lấy ra qua
Depends(...) chứ không tự khởi tạo gì.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Request

from src.application.ports.admin_restaurant_repository import AdminRestaurantRepository
from src.application.use_cases.get_restaurant_details import GetRestaurantDetailsUseCase
from src.application.use_cases.log_interaction import LogInteractionUseCase
from src.application.use_cases.manage_restaurants import (
    ListRestaurantsForAdminUseCase,
    SetRestaurantVisibilityUseCase,
    UpdateRestaurantUseCase,
)
from src.application.use_cases.search_restaurants import SearchRestaurantsUseCase
from src.application.errors import InvalidCredentialsError
from src.infrastructure.auth.admin_auth import AdminAuthService
from src.infrastructure.adapters.ml_rule_predictor import MlRulePredictor
from src.infrastructure.adapters.open_meteo_context_provider import (
    ClockOnlyContextProvider,
    OpenMeteoContextProvider,
)
from src.infrastructure.config.settings import Settings
from src.infrastructure.repositories.csv_restaurant_repository import (
    CsvRestaurantRepository,
)
from src.infrastructure.repositories.json_dish_knowledge_repository import (
    JsonDishKnowledgeRepository,
)
from src.infrastructure.repositories.json_restaurant_details_repository import (
    JsonRestaurantDetailsRepository,
)
from src.infrastructure.adapters.tfidf_semantic_search import TfidfSemanticSearch
from src.infrastructure.repositories.jsonl_interaction_repository import (
    JsonlInteractionRepository,
)
from src.infrastructure.repositories.sqlite_restaurant_repository import (
    SqliteRestaurantRepository,
)


def _status_of(adapter: object) -> dict:
    """Trạng thái 1 adapter. Adapter nào chưa có `status()` (VD bản giả trong test) thì
    suy ra tối thiểu từ `is_ready`, để /health không bao giờ làm sập app."""
    status = getattr(adapter, "status", None)
    if callable(status):
        return status()
    return {"ready": bool(getattr(adapter, "is_ready", False))}


@dataclass
class Container:
    settings: Optional[Settings]
    restaurant_repository: object
    details_repository: object
    dish_knowledge_repository: object
    interaction_repository: object
    rule_predictor: object
    context_provider: object
    semantic_search: object
    search_restaurants: SearchRestaurantsUseCase
    get_restaurant_details: GetRestaurantDetailsUseCase
    log_interaction: LogInteractionUseCase
    # --- Quản trị ------------------------------------------------------------
    # `None` khi kho lưu trữ không ghi được (CSV). Router admin phải kiểm và trả 503,
    # KHÔNG được để nổ AttributeError.
    admin_auth: AdminAuthService
    admin_restaurants: Optional[object]
    list_restaurants_for_admin: Optional[ListRestaurantsForAdminUseCase]
    update_restaurant: Optional[UpdateRestaurantUseCase]
    set_restaurant_visibility: Optional[SetRestaurantVisibilityUseCase]

    def health(self) -> dict:
        """Trạng thái từng nguồn dữ liệu, kèm LÝ DO khi chưa sẵn sàng.

        Mỗi adapter TỰ mô tả mình qua `status()`. Container không đọc thuộc tính riêng của
        adapter cụ thể, nhờ vậy thay adapter (CSV -> PostgreSQL) không phải sửa hàm này.
        """
        return {
            "restaurants": _status_of(self.restaurant_repository),
            "restaurant_details": _status_of(self.details_repository),
            "dish_knowledge": _status_of(self.dish_knowledge_repository),
            "interactions": _status_of(self.interaction_repository),
            "ml_rule_predictor": _status_of(self.rule_predictor),
            "context_provider": _status_of(self.context_provider),
            "semantic_search": _status_of(self.semantic_search),
            "admin_auth": _status_of(self.admin_auth),
            "admin_storage": {
                "ready": self.admin_restaurants is not None,
                "error": None
                if self.admin_restaurants is not None
                else "kho hiện tại không ghi được - cần MOODBITE_STORAGE=sqlite",
            },
        }


def build_container(settings: Optional[Settings] = None) -> Container:
    """Lắp toàn bộ app. Thiếu file dữ liệu KHÔNG làm sập - repository ghi nhận lỗi và
    endpoint liên quan trả 503 kèm hướng dẫn, các endpoint khác vẫn chạy."""
    settings = settings or Settings.from_env()

    details_repository = JsonRestaurantDetailsRepository(
        settings.restaurant_details_json
    )
    # Ghép review từ file chi tiết vào dataset chính để tìm kiếm bằng câu tự do khớp được
    # nội dung review. Việc ghép 2 nguồn là trách nhiệm của composition root, không phải
    # của repository - mỗi repository chỉ đọc đúng một nguồn.
    review_texts = details_repository.review_texts() if details_repository.is_ready else {}

    # ĐÂY là toàn bộ chi phí của việc đổi kho lưu trữ: một câu if ở composition root.
    # Use case, domain và router không biết dữ liệu đến từ CSV hay SQLite - cả hai
    # adapter đều triển khai cùng port `RestaurantRepository`.
    #
    # SQLite đã lưu sẵn `review_text` (do `scripts/build_sqlite.py` ghép lúc dựng CSDL),
    # nên không cần truyền `review_texts` vào nữa.
    if settings.storage_backend == "sqlite":
        restaurant_repository = SqliteRestaurantRepository(settings.restaurants_db)
    else:
        restaurant_repository = CsvRestaurantRepository(
            settings.restaurants_csv, review_texts=review_texts
        )
    dish_knowledge_repository = JsonDishKnowledgeRepository(
        settings.dish_knowledge_json
    )
    interaction_repository = JsonlInteractionRepository(settings.interactions_path)
    rule_predictor = MlRulePredictor(
        settings.dish_model_path, mode=settings.dish_adapter_mode
    )
    context_provider = (
        OpenMeteoContextProvider(enable_weather=True)
        if settings.enable_weather
        else ClockOnlyContextProvider()
    )
    # Chỉ mục ngữ nghĩa dựng MỘT LẦN lúc khởi động từ dữ liệu đã nạp - không dựng lại
    # ở mỗi request (dựng mất ~1 giây cho 5000 quán).
    semantic_search = TfidfSemanticSearch(
        restaurant_repository.list_all() if restaurant_repository.is_ready else []
    )

    admin_auth = AdminAuthService(
        username=settings.admin_username,
        password_hash=settings.admin_password_hash,
        token_secret=settings.admin_token_secret,
        token_ttl_seconds=settings.admin_token_ttl_seconds,
    )
    # Chỉ SQLite mới ghi được. Bản CSV cố tình KHÔNG triển khai port ghi, nên phép kiểm
    # dưới đây tự động đúng khi thêm adapter mới - không phải nhớ sửa thêm chỗ nào.
    admin_restaurants = (
        restaurant_repository
        if isinstance(restaurant_repository, AdminRestaurantRepository)
        else None
    )

    return Container(
        settings=settings,
        admin_auth=admin_auth,
        admin_restaurants=admin_restaurants,
        list_restaurants_for_admin=(
            ListRestaurantsForAdminUseCase(admin_restaurants) if admin_restaurants else None
        ),
        update_restaurant=(
            UpdateRestaurantUseCase(admin_restaurants) if admin_restaurants else None
        ),
        set_restaurant_visibility=(
            SetRestaurantVisibilityUseCase(admin_restaurants) if admin_restaurants else None
        ),
        restaurant_repository=restaurant_repository,
        details_repository=details_repository,
        dish_knowledge_repository=dish_knowledge_repository,
        interaction_repository=interaction_repository,
        rule_predictor=rule_predictor,
        context_provider=context_provider,
        semantic_search=semantic_search,
        search_restaurants=SearchRestaurantsUseCase(
            restaurants=restaurant_repository,
            dish_knowledge=dish_knowledge_repository,
            context_provider=context_provider,
            rule_predictor=rule_predictor,
            semantic_search=semantic_search,
        ),
        get_restaurant_details=GetRestaurantDetailsUseCase(
            details_repository, restaurant_repository
        ),
        log_interaction=LogInteractionUseCase(
            interactions=interaction_repository,
            restaurants=restaurant_repository,
        ),
    )


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_search_restaurants(
    container: Container = Depends(get_container),
) -> SearchRestaurantsUseCase:
    return container.search_restaurants


def get_restaurant_details_use_case(
    container: Container = Depends(get_container),
) -> GetRestaurantDetailsUseCase:
    return container.get_restaurant_details


def get_log_interaction(
    container: Container = Depends(get_container),
) -> LogInteractionUseCase:
    return container.log_interaction


def require_admin(
    request: Request,
    container: Container = Depends(get_container),
) -> str:
    """Chốt chặn xác thực cho MỌI endpoint /api/v1/admin/* trừ /login.

    Đặt ở đây (composition root) chứ không ở router, để router giữ đúng vai trò "mỏng".
    Ném `InvalidCredentialsError` -> `error_handlers.py` đổi thành 401 UNAUTHORIZED.
    """
    # Kiểm CẤU HÌNH trước khi kiểm token. Ngược lại thì lúc chưa bật admin, mọi request
    # đều nhận 401 "sai xác thực" — sai sự thật và gây lạc hướng khi chẩn đoán: không có
    # token nào chạy được cả, vấn đề nằm ở việc chưa đặt biến môi trường. Phải là 503
    # kèm hướng dẫn.
    container.admin_auth.ensure_configured()

    header = request.headers.get("Authorization", "")
    # `partition` chịu được cả chuỗi rỗng lẫn thiếu dấu cách, không cần try/except.
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise InvalidCredentialsError(
            "Thiếu header 'Authorization: Bearer <token>'. Gọi POST /api/v1/admin/login trước."
        )
    return container.admin_auth.verify(token.strip())

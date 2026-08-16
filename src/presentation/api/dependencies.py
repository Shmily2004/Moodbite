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

from src.application.use_cases.get_restaurant_details import GetRestaurantDetailsUseCase
from src.application.use_cases.log_interaction import LogInteractionUseCase
from src.application.use_cases.search_restaurants import SearchRestaurantsUseCase
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
from src.infrastructure.repositories.jsonl_interaction_repository import (
    JsonlInteractionRepository,
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
    search_restaurants: SearchRestaurantsUseCase
    get_restaurant_details: GetRestaurantDetailsUseCase
    log_interaction: LogInteractionUseCase

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

    return Container(
        settings=settings,
        restaurant_repository=restaurant_repository,
        details_repository=details_repository,
        dish_knowledge_repository=dish_knowledge_repository,
        interaction_repository=interaction_repository,
        rule_predictor=rule_predictor,
        context_provider=context_provider,
        search_restaurants=SearchRestaurantsUseCase(
            restaurants=restaurant_repository,
            dish_knowledge=dish_knowledge_repository,
            context_provider=context_provider,
            rule_predictor=rule_predictor,
        ),
        get_restaurant_details=GetRestaurantDetailsUseCase(details_repository),
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

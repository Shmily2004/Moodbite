"""Demo nhanh: gọi thẳng use case tìm kiếm, không cần chạy server.

Dùng để kiểm chứng luồng nghiệp vụ hoạt động với dữ liệu THẬT.

Chạy:
    python scripts/run_suggest_demo.py                      # không có câu tìm kiếm
    python scripts/run_suggest_demo.py "quán lẩu ấm cúng"   # tìm bằng câu tự do
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.application.use_cases.search_restaurants import (  # noqa: E402
    SearchQuery,
    SearchRestaurantsUseCase,
)
from src.infrastructure.adapters.open_meteo_context_provider import (  # noqa: E402
    ClockOnlyContextProvider,
)
from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.repositories.csv_restaurant_repository import (  # noqa: E402
    CsvRestaurantRepository,
)
from src.infrastructure.repositories.json_dish_knowledge_repository import (  # noqa: E402
    JsonDishKnowledgeRepository,
)
from src.infrastructure.repositories.json_restaurant_details_repository import (  # noqa: E402
    JsonRestaurantDetailsRepository,
)

DEMO_SESSION = "00000000-0000-4000-8000-000000000000"


def main() -> int:
    query_text = sys.argv[1] if len(sys.argv) > 1 else None
    settings = Settings.from_env()

    details = JsonRestaurantDetailsRepository(settings.restaurant_details_json)
    restaurants = CsvRestaurantRepository(
        settings.restaurants_csv,
        review_texts=details.review_texts() if details.is_ready else {},
    )
    knowledge = JsonDishKnowledgeRepository(settings.dish_knowledge_json)

    if not restaurants.is_ready:
        print(f"Chua co du lieu: {restaurants.load_error}")
        print("Chay truoc: python -m data_pipeline.feature_engineering")
        return 1

    print(f"Da nap {len(restaurants.list_all())} quan, "
          f"{len(knowledge.list_rules())} rule mon an.")
    print(f"Tim kiem: {query_text!r}\n")

    use_case = SearchRestaurantsUseCase(
        restaurants=restaurants,
        dish_knowledge=knowledge,
        # Chi dung gio, khong goi mang - de demo chay duoc offline.
        context_provider=ClockOnlyContextProvider(),
    )
    result = use_case.execute(
        SearchQuery(session_id=DEMO_SESSION, query_text=query_text, limit=5)
    )

    print(f"Ngu canh: {' | '.join(result.context) or '(khong co)'}")
    print(f"Tra ve {len(result.results)} quan:\n")
    for item in result.results:
        dish = item.suggested_dish
        print(f"  #{item.rank_position} {item.name[:46]}")
        print(f"      diem {item.predicted_score:.3f} | {item.distance_m} m "
              f"| khop theo: {item.match_source}")
        if dish:
            print(f"      mon goi y: {dish.name} ({dish.confidence})")

    for warning in result.warnings:
        print(f"\n  ! {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

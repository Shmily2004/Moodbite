import sys
from pathlib import Path

# Ensure project root on sys.path when running this script directly
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.application.services.dish_recommendation_service import DishRecommendationService
from src.application.services.recommendation_service import RecommendationService
from src.infrastructure.repositories.csv_restaurant_repository import CSVRestaurantRepository


print('Calling DishRecommendationService.suggest("happy")...')
repo = CSVRestaurantRepository("data_pipeline/data_cleaned/dataset_moodbite_features.csv")
recommender = RecommendationService(repository=repo)
service = DishRecommendationService(base_service=recommender)
results = service.suggest('happy', top_k_restaurants_per_dish=2)
print('Returned', len(results), 'dishes')
for r in results[:3]:
    print(r['dish_name'], 'confidence=', r.get('dish_confidence'), 'restaurants=', len(r.get('restaurants', [])))

import sys
from pathlib import Path

# Ensure project root on sys.path when running this script directly
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.application.services.dish_recommendation_service import dish_recommendation_service


print('Calling DishRecommendationService.suggest("happy")...')
results = dish_recommendation_service.suggest('happy', top_k_restaurants_per_dish=2)
print('Returned', len(results), 'dishes')
for r in results[:3]:
    print(r['dish_name'], 'confidence=', r.get('dish_confidence'), 'restaurants=', len(r.get('restaurants', [])))

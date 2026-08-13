import pandas as pd
from src.application.services.dish_recommendation_service import DishRecommendationService
from src.application.services.recommendation_service import RecommendationService
from src.config import di


class FakeBaseService:
    def __init__(self):
        # create a tiny restaurants DataFrame with required columns
        data = [
            {
                'title': 'Phở Test',
                'placeId': 'p1',
                'location/lat': 21.03,
                'location/lng': 105.84,
                'totalScore': 4.5,
                'categoryName': 'Nhà hàng phở',
                'cuisine': 'vietnamese',
                'address': 'Address 1',
                'fresh_healthy_score': 0.1,
                'comfort_cozy_score': 0.0,
                'spicy_hot_score': 0.0,
                'cheap_budget_score': 0.0,
                'quick_fast_score': 0.0,
            },
            {
                'title': 'Generic Place',
                'placeId': 'p2',
                'location/lat': 21.04,
                'location/lng': 105.85,
                'totalScore': 3.8,
                'categoryName': 'Nhà hàng',
                'cuisine': None,
                'address': 'Address 2',
                'fresh_healthy_score': 0.0,
                'comfort_cozy_score': 0.0,
                'spicy_hot_score': 0.0,
                'cheap_budget_score': 0.0,
                'quick_fast_score': 0.0,
            },
        ]
        self.restaurants = pd.DataFrame(data)
        self.is_ready = True


def test_service_uses_ml_prediction(monkeypatch):
    # monkeypatch DI to return 'pho' when category contains 'phở'
    def stub_predict(cat, cuisine=None):
        if cat and 'phở' in cat.lower():
            return 'pho'
        return None

    monkeypatch.setattr(di, 'predict_rule_id', stub_predict)

    service = DishRecommendationService(base_service=FakeBaseService())
    res = service.suggest('happy', top_k_restaurants_per_dish=2)
    assert isinstance(res, list)
    # ensure dishes returned (from KB rules matching 'phở')
    assert len(res) > 0
    # check dish_confidence is string and can be 'ml' or rule confidence
    for d in res:
        assert 'dish_confidence' in d


def test_service_fallback_to_kb(monkeypatch):
    # force DI to return None (no ML), so KB matching used
    monkeypatch.setattr(di, 'predict_rule_id', lambda c, cu=None: None)

    service = DishRecommendationService(base_service=FakeBaseService())
    res = service.suggest('happy', top_k_restaurants_per_dish=2)
    assert isinstance(res, list)
    assert len(res) > 0
    for d in res:
        assert d['dish_confidence'] in ('specific', 'generic_fallback', 'unknown')

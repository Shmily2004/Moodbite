"""Khóa lại 3 bug đã sửa của /api/recommend, để lần refactor sau không âm thầm làm hỏng."""
import pandas as pd
import pytest

from src.application.services.recommendation_service import (
    MOOD_PROFILES,
    MOOD_TO_SCORE_COLUMN,
    RecommendationService,
)

MOOD_SCORE_COLUMNS = {
    'comfort_cozy_score', 'spicy_hot_score', 'fresh_healthy_score',
    'cheap_budget_score', 'quick_fast_score',
}


def _row(title, lat, lng, rating=4.0, **scores):
    base = {
        'title': title,
        'placeId': f'id-{title}',
        'location/lat': lat,
        'location/lng': lng,
        'totalScore': rating,
        'categoryName': 'Nhà hàng',
        'cuisine': None,
        'address': f'{title} address',
        'price': None,
        'reviewsCount': None,
    }
    base.update({c: 0.0 for c in MOOD_SCORE_COLUMNS})
    base.update(scores)
    return base


def _service(rows):
    svc = RecommendationService.__new__(RecommendationService)
    svc.dataset_path = 'in-memory'
    svc.restaurants = pd.DataFrame(rows)
    svc.is_ready = True
    return svc


# Hoàn Kiếm là điểm mặc định của API.
HOAN_KIEM = (21.0285, 105.8542)


def test_sad_and_relaxed_do_not_return_identical_lists():
    """Trước đây cả 2 mood cùng trỏ vào comfort_cozy_score nên trả kết quả GIỐNG HỆT nhau -
    người dùng đổi mood mà danh sách không đổi."""
    rows = [
        # Quán rẻ + ấm cúng -> hợp 'sad'.
        _row('Quan Re', 21.03, 105.85, comfort_cozy_score=0.8, cheap_budget_score=0.9),
        # Quán ấm cúng nhưng đắt và không phải đồ ăn nhanh -> hợp 'relaxed'.
        _row('Cafe San Vuon', 21.03, 105.85, comfort_cozy_score=0.8, cheap_budget_score=0.0),
    ]
    svc = _service(rows)
    sad = [r['name'] for r in svc.recommend('sad', *HOAN_KIEM, top_k=2)]
    relaxed = [r['name'] for r in svc.recommend('relaxed', *HOAN_KIEM, top_k=2)]

    assert sad != relaxed
    assert sad[0] == 'Quan Re'
    assert relaxed[0] == 'Cafe San Vuon'


def test_every_mood_score_column_is_used_by_some_mood():
    """cheap_budget_score và quick_fast_score từng được pipeline tính ra nhưng không mood
    nào dùng tới - 2/5 feature chết."""
    used = {col for weights in MOOD_PROFILES.values() for col in weights}
    assert used == MOOD_SCORE_COLUMNS


def test_far_restaurant_is_excluded_by_default_radius():
    """Quán cách 36km vẫn lọt top-5 của người dùng ở Hoàn Kiếm, vì khoảng cách chỉ là tiêu
    chí phụ thứ ba nên gần như không bao giờ tới lượt."""
    rows = [
        _row('Xa Tit Tap', 20.90, 105.57, comfort_cozy_score=1.0),   # ~31km
        _row('Gan Nha', 21.03, 105.85, comfort_cozy_score=0.2),      # ~1km
    ]
    svc = _service(rows)

    names = [r['name'] for r in svc.recommend('sad', *HOAN_KIEM, top_k=5)]
    assert names == ['Gan Nha'], 'quán ngoài bán kính mặc định phải bị loại'

    # Tắt lọc thì quán xa quay lại và thắng nhờ mood-score cao hơn.
    names = [r['name'] for r in svc.recommend('sad', *HOAN_KIEM, top_k=5, max_distance_km=None)]
    assert names[0] == 'Xa Tit Tap'


def test_radius_filter_is_skipped_when_it_would_empty_the_results():
    """Thà gợi ý quán xa còn hơn trả về danh sách rỗng."""
    rows = [_row('Chi Co Quan Nay', 20.90, 105.57, comfort_cozy_score=1.0)]
    svc = _service(rows)
    out = svc.recommend('sad', *HOAN_KIEM, top_k=5, max_distance_km=1.0)
    assert [r['name'] for r in out] == ['Chi Co Quan Nay']


def test_missing_price_and_rating_stay_null_not_zero():
    """Quán từ OSM không có giá/rating - phải là null, KHÔNG được fillna(0) thành '0 sao'."""
    rows = [_row('Quan OSM', 21.03, 105.85, comfort_cozy_score=0.5)]
    rows[0]['totalScore'] = None
    svc = _service(rows)
    out = svc.recommend('sad', *HOAN_KIEM, top_k=1)[0]
    assert out['price'] is None
    assert out['rating'] is None


def test_primary_column_mapping_still_exposed_for_dish_service():
    """dish_recommendation_service.py import MOOD_TO_SCORE_COLUMN và cần đúng 1 tên cột."""
    assert set(MOOD_TO_SCORE_COLUMN) == set(MOOD_PROFILES)
    for mood, col in MOOD_TO_SCORE_COLUMN.items():
        assert col in MOOD_SCORE_COLUMNS
        assert col == max(MOOD_PROFILES[mood], key=MOOD_PROFILES[mood].get)


def test_unknown_mood_raises():
    svc = _service([_row('X', 21.03, 105.85)])
    with pytest.raises(ValueError):
        svc.recommend('hungry', *HOAN_KIEM)

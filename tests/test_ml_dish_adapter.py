from src.infrastructure.adapters import ml_dish_adapter as adapter


def test_predict_and_fetch():
    # basic smoke test: should return a list of dishes and a confidence string
    dishes, confidence = adapter.dishes_for_input('Cà phê', 'coffee')
    assert isinstance(dishes, list)
    assert isinstance(confidence, str)
    # dishes should contain at least one entry when KB/model available
    assert len(dishes) >= 1


def test_predict_unknown_fallback():
    # gibberish category should fallback to KB unmatched behavior (still returns list)
    dishes, confidence = adapter.dishes_for_input('Some random unknown category 123', None)
    assert isinstance(dishes, list)
    assert isinstance(confidence, str)
    assert len(dishes) >= 1

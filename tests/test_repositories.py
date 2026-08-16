"""Test tầng infrastructure: đọc file thật -> entity, và xử lý file thiếu/hỏng.

Cụ thể khoá lại: thiếu file KHÔNG được làm sập app, chỉ được báo degraded.
"""
import json

import pandas as pd
import pytest

from src.infrastructure.adapters.ml_rule_predictor import MlRulePredictor
from src.infrastructure.repositories.csv_restaurant_repository import (
    CsvRestaurantRepository,
)
from src.infrastructure.repositories.json_dish_knowledge_repository import (
    JsonDishKnowledgeRepository,
)
from src.infrastructure.repositories.json_restaurant_details_repository import (
    JsonRestaurantDetailsRepository,
)


def write_csv(tmp_path, rows):
    path = tmp_path / "features.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


BASE_ROW = {
    "placeId": "p1",
    "title": "Quán A",
    "categoryName": "Nhà hàng phở",
    "cuisine": "vietnamese",
    "address": "1 Đinh Tiên Hoàng",
    "price": "100-200\xa0N\xa0₫",
    "totalScore": 4.5,
    "reviewsCount": 12,
    "location/lat": 21.03,
    "location/lng": 105.85,
    "comfort_cozy_score": 0.8,
    "spicy_hot_score": 0.0,
    "fresh_healthy_score": 0.0,
    "cheap_budget_score": 0.0,
    "quick_fast_score": 0.0,
}


def test_csv_repo_maps_row_to_entity(tmp_path):
    repo = CsvRestaurantRepository(write_csv(tmp_path, [BASE_ROW]))
    assert repo.is_ready
    r = repo.list_all()[0]
    assert r.name == "Quán A"
    assert r.place_id == "p1"
    assert r.location.lat == 21.03
    assert r.rating == 4.5
    assert r.reviews_count == 12
    assert r.mood_score("comfort_cozy_score") == 0.8


def test_csv_repo_normalizes_nbsp_in_price(tmp_path):
    """Giá từ Google Maps dùng non-breaking space, phải chuẩn hoá để frontend hiển thị đúng."""
    repo = CsvRestaurantRepository(write_csv(tmp_path, [BASE_ROW]))
    assert repo.list_all()[0].price == "100-200 N ₫"


def test_csv_repo_keeps_missing_values_as_none(tmp_path):
    row = BASE_ROW | {"price": None, "totalScore": None, "reviewsCount": None}
    repo = CsvRestaurantRepository(write_csv(tmp_path, [row]))
    r = repo.list_all()[0]
    assert r.price is None and r.rating is None and r.reviews_count is None


def test_csv_repo_skips_rows_without_coordinates(tmp_path):
    """Quán thiếu toạ độ không thể xếp hạng - phải bỏ qua thay vì nổ giữa vòng lặp."""
    bad = BASE_ROW | {"placeId": "p2", "location/lat": None}
    repo = CsvRestaurantRepository(write_csv(tmp_path, [BASE_ROW, bad]))
    assert [r.place_id for r in repo.list_all()] == ["p1"]


def test_csv_repo_missing_file_is_degraded_not_crash(tmp_path):
    repo = CsvRestaurantRepository(tmp_path / "khong-ton-tai.csv")
    assert repo.is_ready is False
    assert "Không tìm thấy" in repo.load_error
    assert repo.list_all() == []


def test_csv_repo_missing_required_columns_reports_clearly(tmp_path):
    path = tmp_path / "broken.csv"
    pd.DataFrame([{"placeId": "p1"}]).to_csv(path, index=False)
    repo = CsvRestaurantRepository(path)
    assert repo.is_ready is False
    assert "thiếu cột bắt buộc" in repo.load_error


def test_csv_repo_lookup_by_place_id(tmp_path):
    repo = CsvRestaurantRepository(write_csv(tmp_path, [BASE_ROW]))
    assert repo.get_by_place_id("p1").name == "Quán A"
    assert repo.get_by_place_id("nope") is None


def test_details_repo_reads_and_degrades(tmp_path):
    path = tmp_path / "details.json"
    path.write_text(json.dumps({"p1": {"title": "Quán A"}}), encoding="utf-8")
    repo = JsonRestaurantDetailsRepository(path)
    assert repo.is_ready and repo.count == 1
    assert repo.get("p1")["title"] == "Quán A"
    assert repo.get("missing") is None

    missing = JsonRestaurantDetailsRepository(tmp_path / "nope.json")
    assert missing.is_ready is False
    assert missing.get("p1") is None


def test_dish_knowledge_repo_preserves_rule_order(tmp_path):
    """Rule cụ thể phải đứng trước rule chung, nếu không rule chung nuốt mất rule cụ thể."""
    path = tmp_path / "kb.json"
    path.write_text(
        json.dumps(
            {
                "rules": [
                    {"id": "pho", "confidence": "specific", "match_category": ["phở"],
                     "dishes": [{"name": "Phở bò", "mood_keywords": ["comfort"]}]},
                    {"id": "generic", "confidence": "generic_fallback",
                     "match_category": ["nhà hàng"],
                     "dishes": [{"name": "Cơm rang", "mood_keywords": ["comfort"]}]},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    repo = JsonDishKnowledgeRepository(path)
    assert [r.id for r in repo.list_rules()] == ["pho", "generic"]
    # "Nhà hàng phở" khớp CẢ HAI rule -> phải chọn rule cụ thể đứng trước.
    assert repo.match_rule_for_category("Nhà hàng phở").id == "pho"
    assert repo.match_rule_for_category("Nhà hàng").id == "generic"
    assert repo.match_rule_for_category(None) is None


def test_ml_predictor_without_model_is_unavailable(tmp_path):
    """Không có model là trạng thái MẶC ĐỊNH bình thường, không phải lỗi."""
    predictor = MlRulePredictor(tmp_path / "khong-co.joblib")
    assert predictor.is_available is False
    assert predictor.predict_rule_id("Nhà hàng phở") is None
    assert "Không có model" in predictor.reason


def test_ml_predictor_kb_mode_skips_model_entirely(tmp_path):
    predictor = MlRulePredictor(tmp_path / "any.joblib", mode="kb")
    assert predictor.is_available is False
    assert "DISH_ADAPTER=kb" in predictor.reason

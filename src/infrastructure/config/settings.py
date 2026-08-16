"""Cấu hình chạy được đọc từ biến môi trường. MỘT nơi duy nhất định nghĩa đường dẫn file.

Trước đây đường dẫn CSV bị hardcode ở 3 chỗ khác nhau (service, startup, repository) nên
đổi 1 chỗ là hỏng 2 chỗ còn lại.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Gốc repo = thư mục chứa src/ (file này ở src/infrastructure/config/settings.py).
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _path_from_env(env_key: str, default_relative: str) -> Path:
    raw = os.getenv(env_key)
    if raw:
        return Path(raw)
    return PROJECT_ROOT / default_relative


@dataclass(frozen=True)
class Settings:
    restaurants_csv: Path
    restaurant_details_json: Path
    dish_knowledge_json: Path
    dish_model_path: Path
    # Nơi ghi sự kiện tương tác (nguồn nhãn cho mô hình xếp hạng sau này).
    interactions_path: Path
    # 'auto' = dùng ML nếu có, không thì khớp từ khoá | 'kb' = ép chỉ dùng từ khoá
    # | 'ml' = chỉ dùng ML.
    dish_adapter_mode: str
    cors_allow_origins: tuple[str, ...]
    # Gọi API thời tiết (Open-Meteo, miễn phí, không cần key). Tắt trong test/CI để
    # không phụ thuộc mạng.
    enable_weather: bool
    # Các tính năng 3D/floorplan đang TẠM DỪNG (xem docs/architecture_decisions.md).
    # Để bật lại: MOODBITE_ENABLE_SPATIAL=1
    enable_spatial_features: bool

    @staticmethod
    def from_env() -> "Settings":
        origins = os.getenv("MOODBITE_CORS_ORIGINS", "*")
        return Settings(
            restaurants_csv=_path_from_env(
                "MOODBITE_RESTAURANTS_CSV",
                "data_pipeline/data_cleaned/dataset_moodbite_features.csv",
            ),
            restaurant_details_json=_path_from_env(
                "MOODBITE_RESTAURANT_DETAILS_JSON",
                "data_pipeline/data_cleaned/restaurant_details.json",
            ),
            dish_knowledge_json=_path_from_env(
                "MOODBITE_DISH_KNOWLEDGE_JSON",
                "data_pipeline/dish_knowledge_base.json",
            ),
            dish_model_path=_path_from_env(
                "MOODBITE_DISH_MODEL", "models/dish_rule_classifier.joblib"
            ),
            interactions_path=_path_from_env(
                "MOODBITE_INTERACTIONS", "data_pipeline/data_cleaned/interactions.jsonl"
            ),
            dish_adapter_mode=os.getenv("DISH_ADAPTER", "auto").strip().lower(),
            cors_allow_origins=tuple(
                o.strip() for o in origins.split(",") if o.strip()
            ),
            # Mặc định TẮT: bật thời tiết làm mọi lượt tìm kiếm phụ thuộc mạng.
            # Bật bằng MOODBITE_ENABLE_WEATHER=1 khi chạy thật.
            enable_weather=os.getenv("MOODBITE_ENABLE_WEATHER", "") == "1",
            enable_spatial_features=os.getenv("MOODBITE_ENABLE_SPATIAL", "") == "1",
        )

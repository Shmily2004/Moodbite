"""ADAPTER: đọc tri thức món ăn từ dish_knowledge_base.json -> entity DishRule/Dish.

Nội dung món ăn sửa ở file JSON, KHÔNG hardcode danh sách món trong code.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from src.domain.entities.dish import CONFIDENCE_UNKNOWN, Dish, DishRule


class JsonDishKnowledgeRepository:
    """Triển khai DishKnowledgeRepository từ file JSON."""

    def __init__(self, json_path: Path | str, eager: bool = True) -> None:
        self.json_path = Path(json_path)
        self._rules: Optional[List[DishRule]] = None
        self._load_error: Optional[str] = None
        if eager:
            self._ensure_loaded()

    @property
    def is_ready(self) -> bool:
        self._ensure_loaded()
        return self._rules is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def status(self) -> dict:
        return {
            "ready": self.is_ready,
            "source": str(self.json_path),
            "rules": len(self._rules or []),
            "error": self._load_error,
        }

    def list_rules(self) -> List[DishRule]:
        """Giữ NGUYÊN thứ tự trong JSON: rule cụ thể ("phở") đứng trước rule chung
        ("nhà hàng"), nếu không rule chung sẽ nuốt mất rule cụ thể."""
        self._ensure_loaded()
        return list(self._rules or [])

    def match_rule_for_category(self, category_name: Optional[str]) -> Optional[DishRule]:
        for rule in self.list_rules():
            if rule.matches_category(category_name):
                return rule
        return None

    def _ensure_loaded(self) -> None:
        if self._rules is not None or self._load_error is not None:
            return
        if not self.json_path.exists():
            self._load_error = f"Không tìm thấy knowledge base: {self.json_path}"
            return
        try:
            with open(self.json_path, encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            self._load_error = f"Không đọc được {self.json_path}: {exc}"
            return

        self._rules = [self._to_rule(r) for r in raw.get("rules", [])]

    @staticmethod
    def _to_rule(raw: dict) -> DishRule:
        return DishRule(
            id=str(raw.get("id", "")),
            confidence=raw.get("confidence", CONFIDENCE_UNKNOWN),
            match_category=list(raw.get("match_category", [])),
            match_cuisine=list(raw.get("match_cuisine", [])),
            dishes=[
                Dish(
                    name=d.get("name", ""),
                    cuisine=d.get("cuisine"),
                    spice_level=d.get("spice_level"),
                    temperature=d.get("temperature"),
                    portion_size=d.get("portion_size"),
                    mood_keywords=list(d.get("mood_keywords", [])),
                )
                for d in raw.get("dishes", [])
            ],
        )

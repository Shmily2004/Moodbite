"""ADAPTER: đọc danh mục món từ `dish_catalog.json` -> entity `Dish`.

File này do `scripts/build_dish_catalog.py` sinh ra. Thiếu file KHÔNG được làm sập app:
repository ghi nhận lỗi, `/health` báo `ready: false` kèm lý do, và endpoint món trả 503
kèm đúng lệnh cần chạy (CLAUDE.md mục 4 quy tắc 3).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.domain.entities.dish import Dish

logger = logging.getLogger("moodbite.repository")


class JsonDishCatalogRepository:
    """Triển khai `DishCatalogRepository` từ file JSON."""

    def __init__(self, json_path: Path | str, eager: bool = True) -> None:
        self.json_path = Path(json_path)
        self._dishes: Optional[List[Dish]] = None
        self._by_id: Dict[str, Dish] = {}
        self._load_error: Optional[str] = None
        if eager:
            self._ensure_loaded()

    @property
    def is_ready(self) -> bool:
        self._ensure_loaded()
        return self._dishes is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def status(self) -> dict:
        return {
            "ready": self.is_ready,
            "source": str(self.json_path),
            "dishes": len(self._dishes or []),
            "error": self._load_error,
        }

    def list_dishes(self) -> List[Dish]:
        self._ensure_loaded()
        return list(self._dishes or [])

    def get_dish(self, dish_id: str) -> Optional[Dish]:
        self._ensure_loaded()
        return self._by_id.get(dish_id)

    def _ensure_loaded(self) -> None:
        if self._dishes is not None or self._load_error is not None:
            return
        if not self.json_path.exists():
            self._load_error = (
                f"Không tìm thấy danh mục món: {self.json_path}. "
                "Chạy: python scripts/build_dish_catalog.py"
            )
            return
        try:
            raw = json.loads(self.json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._load_error = f"Không đọc được {self.json_path}: {exc}"
            return

        dishes = [
            self._to_dish(entry)
            for entry in raw.get("dishes", [])
            # Món bị admin ẩn không bao giờ lộ ra ngoài - cùng quy ước soft-delete với quán.
            if entry.get("is_active", True)
        ]
        self._dishes = dishes
        self._by_id = {d.identifier: d for d in dishes}
        logger.info("Đã nạp %d món từ %s", len(dishes), self.json_path.name)

    @staticmethod
    def _to_dish(raw: dict) -> Dish:
        """JSON -> entity.

        `None` giữ nguyên `None`, KHÔNG đổi thành 0 hay chuỗi rỗng: `spice_level=None`
        nghĩa là chưa biết cay tới đâu, khác hẳn `spice_level=0` (không cay).
        """
        name = raw.get("name", "")
        return Dish(
            name=name,
            dish_id=raw.get("dish_id") or None,
            cuisine=raw.get("cuisine"),
            spice_level=raw.get("spice_level"),
            temperature=raw.get("temperature"),
            cooking_method=raw.get("cooking_method"),
            meal_times=list(raw.get("meal_times") or []),
            portion_size=raw.get("portion_size"),
            mood_keywords=list(raw.get("mood_keywords") or []),
            ingredients=list(raw.get("ingredients") or []),
            description=raw.get("description"),
            image_url=raw.get("image_url"),
            match_keywords=list(raw.get("match_keywords") or []),
            source=raw.get("source"),
            source_url=raw.get("source_url"),
            last_updated=raw.get("last_updated"),
            data_confidence=raw.get("data_confidence"),
        )

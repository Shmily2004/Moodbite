"""ADAPTER: đọc chi tiết quán từ restaurant_details.json (do feature_engineering sinh ra)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


class JsonRestaurantDetailsRepository:
    """Triển khai RestaurantDetailsRepository từ file JSON."""

    def __init__(self, json_path: Path | str, eager: bool = True) -> None:
        self.json_path = Path(json_path)
        self._details: Optional[Dict[str, dict]] = None
        self._load_error: Optional[str] = None
        if eager:
            self._ensure_loaded()

    @property
    def is_ready(self) -> bool:
        self._ensure_loaded()
        return self._details is not None

    @property
    def count(self) -> int:
        self._ensure_loaded()
        return len(self._details or {})

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def review_texts(self) -> Dict[str, str]:
        """{place_id: toàn bộ review gộp thành 1 chuỗi} - phục vụ tìm kiếm bằng câu tự do.

        Chỉ ~8.4% quán có review, nên đây là nguồn tín hiệu THƯA. Quán không có review
        vẫn tìm được qua tên và loại hình (xem domain/services/text_relevance.py).
        """
        self._ensure_loaded()
        if not self._details:
            return {}
        texts: Dict[str, str] = {}
        for place_id, detail in self._details.items():
            reviews = detail.get("reviews") or []
            joined = " ".join(
                str(r.get("text")) for r in reviews if isinstance(r, dict) and r.get("text")
            )
            if joined.strip():
                texts[str(place_id)] = joined
        return texts

    def thumbnail_urls(self) -> Dict[str, str]:
        """{place_id: URL ảnh ĐẦU TIÊN} - để card kết quả tìm kiếm có ảnh.

        CHỈ lấy 1 ảnh, không lấy cả bộ: danh sách kết quả chỉ hiển thị 1 ảnh nhỏ, kéo
        cả 6.5 ảnh/quán vào response chỉ làm nặng JSON mà không dùng tới. Xem đủ ảnh
        thì gọi GET /restaurants/{id}.

        ĐỘ PHỦ THẤP: chỉ 1064/4938 quán (21.5%) có ảnh. Giao diện BẮT BUỘC phải xử lý
        đẹp trường hợp không có ảnh - đó là trường hợp PHỔ BIẾN (78.5%), không phải lỗi.
        """
        self._ensure_loaded()
        if not self._details:
            return {}
        thumbnails: Dict[str, str] = {}
        for place_id, detail in self._details.items():
            images = detail.get("imageUrls") or []
            if images and isinstance(images, list):
                first = images[0]
                if isinstance(first, str) and first.strip():
                    thumbnails[str(place_id)] = first.strip()
        return thumbnails

    def status(self) -> dict:
        return {
            "ready": self.is_ready,
            "source": str(self.json_path),
            "count": self.count,
            "error": self._load_error,
        }

    def get(self, place_id: str) -> Optional[dict]:
        """None = quán chưa có dữ liệu chi tiết. Đây là trường hợp BÌNH THƯỜNG:
        phần lớn quán đến từ OpenStreetMap vốn không có giá/review/ảnh."""
        self._ensure_loaded()
        if self._details is None:
            return None
        return self._details.get(str(place_id))

    def _ensure_loaded(self) -> None:
        if self._details is not None or self._load_error is not None:
            return
        if not self.json_path.exists():
            self._load_error = f"Không tìm thấy file chi tiết: {self.json_path}"
            return
        try:
            with open(self.json_path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            self._load_error = f"Không đọc được {self.json_path}: {exc}"
            return
        if not isinstance(data, dict):
            self._load_error = (
                f"{self.json_path} phải là object dạng {{placeId: chi tiết}}, "
                f"nhận được {type(data).__name__}"
            )
            return
        self._details = data

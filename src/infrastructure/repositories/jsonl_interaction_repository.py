"""ADAPTER: ghi sự kiện tương tác vào file JSONL (mỗi dòng 1 JSON).

Vì sao JSONL mà không phải CSV hay DB:
  - Ghi THÊM vào cuối file là thao tác an toàn, không phải đọc-sửa-ghi lại cả file.
  - Mỗi dòng độc lập: file hỏng giữa chừng vẫn đọc được các dòng trước đó.
  - pandas đọc trực tiếp bằng `pd.read_json(path, lines=True)` khi cần huấn luyện.

Khi chuyển sang PostgreSQL: viết PostgresInteractionRepository triển khai cùng port,
đổi một dòng trong dependencies.py. Use case không đổi.
"""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.domain.entities.interaction import InteractionEvent

logger = logging.getLogger("moodbite.interactions")


class JsonlInteractionRepository:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._error: Optional[str] = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._error = f"Không tạo được thư mục {self.path.parent}: {exc}"

    @property
    def is_ready(self) -> bool:
        return self._error is None

    @property
    def load_error(self) -> Optional[str]:
        return self._error

    def append(self, event: InteractionEvent) -> str:
        event_id = str(uuid.uuid4())
        record = {
            "interaction_event_id": event_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "session_id": event.session_id,
            "search_query_id": event.search_query_id,
            "restaurant_id": event.restaurant_id,
            "action_type": event.action_type.value,
            "dwell_time_ms": event.dwell_time_ms,
            "rank_position": event.rank_position,
            # Tính sẵn ở server để dữ liệu huấn luyện sau này có nhãn nhất quán.
            "is_positive_signal": event.is_positive_signal,
        }
        line = json.dumps(record, ensure_ascii=False)

        # Khoá vì uvicorn có thể xử lý nhiều request song song; hai lượt ghi cùng lúc
        # có thể xen kẽ nhau và tạo ra dòng JSON hỏng.
        with self._lock:
            try:
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
            except OSError as exc:
                self._error = f"Không ghi được {self.path}: {exc}"
                logger.error("Ghi tương tác thất bại: %s", exc)
                raise

        return event_id

    def count(self) -> int:
        if not self.path.exists():
            return 0
        try:
            with open(self.path, encoding="utf-8") as fh:
                return sum(1 for line in fh if line.strip())
        except OSError:
            return 0

    def status(self) -> dict:
        return {
            "ready": self.is_ready,
            "source": str(self.path),
            "count": self.count(),
            "error": self._error,
        }

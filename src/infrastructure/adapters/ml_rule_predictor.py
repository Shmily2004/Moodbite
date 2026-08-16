"""ADAPTER: đoán rule_id món ăn bằng model ML (tuỳ chọn).

BỐI CẢNH QUAN TRỌNG: model demo cũ đã bị GỠ BỎ vì rò rỉ nhãn - nó học `rule_id` từ
`categoryName` trong khi `categoryName` chính là input, nên đạt 98.56% một cách vô nghĩa.
KHÔNG được coi con số đó là bằng chứng có model ML thật.

Hiện tại mặc định KHÔNG có model -> is_available = False -> hệ thống dùng khớp từ khoá.
Đây là trạng thái ĐÚNG và đủ dùng, không phải lỗi cần sửa gấp.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


class MlRulePredictor:
    """Triển khai RulePredictor. Không có model -> is_available=False, bỏ qua ML."""

    def __init__(self, model_path: Path | str, mode: str = "auto") -> None:
        self.model_path = Path(model_path)
        self.mode = (mode or "auto").strip().lower()
        self._model = None
        self._reason: Optional[str] = None
        if self.mode == "kb":
            self._reason = "DISH_ADAPTER=kb - ép dùng khớp từ khoá, bỏ qua ML"
        else:
            self._load()

    @property
    def is_available(self) -> bool:
        return self._model is not None

    @property
    def reason(self) -> Optional[str]:
        """Vì sao không dùng được ML - hiện ở /health để khỏi phải đoán."""
        return self._reason

    def status(self) -> dict:
        return {"available": self.is_available, "reason": self._reason}

    def predict_rule_id(
        self, category: Optional[str], cuisine: Optional[str] = None
    ) -> Optional[str]:
        if self._model is None:
            return None
        text = category or ""
        if cuisine:
            text = f"{text} {cuisine}"
        try:
            return str(self._model.predict([str(text)])[0])
        except Exception:
            # Model hỏng giữa chừng không được làm sập request - fallback về từ khoá.
            return None

    def _load(self) -> None:
        if not self.model_path.exists():
            self._reason = (
                f"Không có model tại {self.model_path} - dùng khớp từ khoá "
                "(đây là trạng thái mặc định bình thường)"
            )
            return
        try:
            import joblib

            self._model = joblib.load(self.model_path)
        except Exception as exc:
            self._reason = f"Không nạp được model {self.model_path}: {exc}"
            self._model = None

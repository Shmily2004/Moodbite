"""
Đọc và match data_pipeline/dish_knowledge_base.json — nguồn tri thức món ăn DÙNG CHUNG
với tầng TypeScript (src/infrastructure/adapters/DishKnowledgeBase.ts). Sửa nội dung
món ăn thì sửa ở file JSON đó, không hardcode lại danh sách món ở đây hay bên TS.
"""
import json
from pathlib import Path
from typing import Optional

_DEFAULT_KB_PATH = Path("data_pipeline/dish_knowledge_base.json")

_kb_cache: Optional[dict] = None


def load_knowledge_base(path: Path = _DEFAULT_KB_PATH) -> dict:
    global _kb_cache
    if _kb_cache is None:
        with open(path, "r", encoding="utf-8") as f:
            _kb_cache = json.load(f)
    return _kb_cache


def match_rule_for_category(category_name: Optional[str], kb: Optional[dict] = None) -> Optional[dict]:
    """
    Trả về rule đầu tiên khớp categoryName (thứ tự trong JSON quyết định độ ưu tiên -
    rule cụ thể như "phở" phải đứng trước rule chung chung như "nhà hàng" trong file
    JSON để không bị rule chung nuốt mất trước). Trả về None nếu không khớp gì
    (dùng unmatched_fallback ở tầng gọi).
    """
    if kb is None:
        kb = load_knowledge_base()
    if not category_name or not isinstance(category_name, str):
        return None

    normalized = category_name.strip().lower()
    for rule in kb["rules"]:
        for keyword in rule.get("match_category", []):
            if keyword.lower() in normalized:
                return rule
    return None


def dishes_for_category(category_name: Optional[str], kb: Optional[dict] = None) -> tuple[list[dict], str]:
    """
    Trả về (danh sách món ăn, confidence) cho 1 categoryName.
    confidence: "specific" | "generic_fallback" | "unknown"
    Khi "unknown", danh sách món trả về là 1 món giả có tên = categoryName gốc, giữ
    hành vi cũ để không loại quán khỏi kết quả, nhưng tầng gọi cần tự hiển thị khác đi
    khi thấy confidence="unknown" (VD: ghi "loại hình: X" thay vì "món: X").
    """
    if kb is None:
        kb = load_knowledge_base()

    rule = match_rule_for_category(category_name, kb)
    if rule is not None:
        return rule["dishes"], rule["confidence"]

    fallback_name = category_name if isinstance(category_name, str) and category_name.strip() else "Món ăn"
    return (
        [{"name": fallback_name, "cuisine": None, "spice_level": None, "temperature": None,
          "portion_size": None, "mood_keywords": []}],
        kb["unmatched_fallback"]["confidence"],
    )

"""ML-backed adapter: predict a KB rule_id from category/cuisine using trained model
and return dishes from the shared knowledge base. Falls back to rule-based KB when
model is unavailable or prediction not found.
"""
from pathlib import Path
import sys
from typing import Dict, List, Tuple, Optional

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import joblib
from data_pipeline.dish_knowledge import load_knowledge_base, dishes_for_category

MODEL_PATH = Path(ROOT) / 'models' / 'dish_rule_classifier.joblib'


def _load_model():
    if MODEL_PATH.exists():
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return None
    return None


_MODEL = _load_model()


def predict_rule_id(category: Optional[str], cuisine: Optional[str] = None) -> Optional[str]:
    """Predict rule id (KB id) from category and optional cuisine using ML model.
    Returns None if model missing or prediction fails.
    """
    if _MODEL is None:
        return None
    text = (category or '')
    if cuisine:
        text = f"{text} {cuisine}"
    try:
        pred = _MODEL.predict([str(text)])[0]
        return str(pred)
    except Exception:
        return None


def dishes_for_input(category: Optional[str], cuisine: Optional[str] = None) -> Tuple[List[Dict], str]:
    """Return (dishes, confidence)
    - If model predicts a rule and it's present in KB -> return that rule's dishes with confidence 'ml'
    - Otherwise fallback to rule-based `dishes_for_category` (returns confidence from KB)
    """
    kb = load_knowledge_base()
    predicted = predict_rule_id(category, cuisine)
    if predicted:
        for rule in kb.get('rules', []):
            if rule.get('id') == predicted:
                return rule.get('dishes', []), 'ml'

    # fallback: use existing KB matching by category
    return dishes_for_category(category, kb)


__all__ = ['predict_rule_id', 'dishes_for_input']

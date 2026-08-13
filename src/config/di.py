"""Simple DI/config for selecting dish adapter at runtime.

Environment variable `DISH_ADAPTER` controls behavior:
 - 'ml'   : use ML adapter predict_rule_id if available (may return None if model missing)
 - 'kb'   : force KB-only (predict_rule_id returns None)
 - 'auto' : prefer ML if available, else fallback to KB (default)

This module exposes `predict_rule_id(category, cuisine)` which returns a rule id
string or None.
"""
import os
from typing import Callable, Optional


def _load_ml_predictor() -> Optional[Callable[[Optional[str], Optional[str]], Optional[str]]]:
    try:
        from src.infrastructure.adapters.ml_dish_adapter import predict_rule_id as ml_predict

        return ml_predict
    except Exception:
        return None


_ML_PREDICTOR = _load_ml_predictor()


def predict_rule_id(category: Optional[str], cuisine: Optional[str] = None) -> Optional[str]:
    mode = os.getenv('DISH_ADAPTER', 'auto').lower()
    if mode == 'kb':
        return None
    if mode == 'ml':
        if _ML_PREDICTOR:
            try:
                return _ML_PREDICTOR(category, cuisine)
            except Exception:
                return None
        return None
    # auto
    if _ML_PREDICTOR:
        try:
            return _ML_PREDICTOR(category, cuisine)
        except Exception:
            return None
    return None


__all__ = ['predict_rule_id']

"""Demo using trained model to predict rule_id from categoryName and fetch dishes from KB."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import joblib
from data_pipeline.dish_knowledge import load_knowledge_base

MODEL_PATH = Path('models/dish_rule_classifier.joblib')
KB_PATH = Path('data_pipeline/dish_knowledge_base.json')

if not MODEL_PATH.exists():
    print('Model not found. Run scripts/train_dish_classifier.py first.')
    raise SystemExit(1)

model = joblib.load(MODEL_PATH)
kb = load_knowledge_base(KB_PATH)

examples = [
    'Phở bò',
    'Quán lẩu & nướng',
    'Cà phê, coffee shop',
    'Nhà hàng hải sản',
    'Pizza place',
]

for cat in examples:
    pred = model.predict([cat])[0]
    print('Category:', cat)
    print('Predicted rule id:', pred)
    rule = next((r for r in kb['rules'] if r['id'] == pred), None)
    if rule:
        print('Example dishes:', [d['name'] for d in rule['dishes']])
    else:
        print('No rule found; fallback applies')
    print('---')

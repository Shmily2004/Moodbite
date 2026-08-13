"""Train a simple classifier that predicts dish rule id from categoryName and cuisine.
This is a lightweight demo to validate a training loop for dish-suggestion.
"""
from pathlib import Path
import json
import pandas as pd
import joblib
import sys

# Ensure project root is on sys.path so imports like `data_pipeline` work when
# running the script directly.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

from data_pipeline.dish_knowledge import load_knowledge_base, match_rule_for_category

KB_PATH = Path('data_pipeline/dish_knowledge_base.json')
CSV_PATH = Path('data_pipeline/data_cleaned/dataset_moodbite_features.csv')
MODEL_DIR = Path('models')
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / 'dish_rule_classifier.joblib'

if not CSV_PATH.exists():
    print('dataset_moodbite_features.csv not found. Run feature_engineering first.')
    raise SystemExit(1)

kb = load_knowledge_base(KB_PATH)

df = pd.read_csv(CSV_PATH)
# Prepare text input: categoryName + ' ' + cuisine

def get_rule_id(cat):
    r = match_rule_for_category(cat, kb)
    return r['id'] if r else 'unknown'

# Fill NaNs
df = df.fillna('')
texts = (df.get('categoryName', '') + ' ' + df.get('cuisine', '')).astype(str)
labels = df['categoryName'].apply(lambda c: get_rule_id(c))

# Filter labels that appear at least twice to avoid singleton classes (optional)
label_counts = labels.value_counts()
valid_labels = set(label_counts[label_counts >= 2].index)
mask = labels.isin(valid_labels)
texts = texts[mask]
labels = labels[mask]

if len(labels) < 10:
    print('Not enough labeled samples to train. Exiting.')
    raise SystemExit(1)

X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42, stratify=labels)

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1,2), max_features=5000)),
    ('clf', LogisticRegression(max_iter=1000))
])

pipeline.fit(X_train, y_train)

pred = pipeline.predict(X_test)
acc = accuracy_score(y_test, pred)
print('Test accuracy:', acc)
print(classification_report(y_test, pred))

joblib.dump(pipeline, MODEL_PATH)
print('Saved model to', MODEL_PATH)

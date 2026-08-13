from pathlib import Path
import pandas as pd

p = Path('data_pipeline/data_cleaned/dataset_moodbite_features.csv')
if not p.exists():
    print('MISSING:', p)
    raise SystemExit(1)

df = pd.read_csv(p)
# detect mood columns: prefer columns starting with 'mood_', else any column ending with '_score'
mood_cols = [c for c in df.columns if c.startswith('mood_')]
if not mood_cols:
    mood_cols = [c for c in df.columns if c.endswith('_score') or 'mood' in c.lower()]

if not mood_cols:
    print('No mood columns detected')
    raise SystemExit(1)

# convert to numeric where possible
for c in mood_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

has_mood = (df[mood_cols].max(axis=1) > 0)

pct = 100.0 * has_mood.sum() / len(df) if len(df) > 0 else 0.0

print(f'Total records: {len(df)}')
print(f'Mood columns detected ({len(mood_cols)}): {mood_cols}')
print(f'Records with any mood-score > 0: {pct:.2f}%')

print('\nTop 5 samples (title, placeId, mood scores):')
print(df[[col for col in ['title','placeId'] if col in df.columns] + mood_cols].head(5).to_string(index=False))

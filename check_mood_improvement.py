import pandas as pd

df = pd.read_csv('data_pipeline/data_cleaned/dataset_moodbite_features.csv')
print(f'Tong record: {len(df)}')
print()

mood_cols = [col for col in df.columns if col.startswith('mood_')]
print(f'So mood fields: {len(mood_cols)}')
print()

df['has_any_mood'] = df[mood_cols].max(axis=1) > 0
pct_with_mood = (df['has_any_mood'].sum() / len(df)) * 100
pct_no_mood = 100 - pct_with_mood

print(f'Record voi >= 1 mood > 0: {df["has_any_mood"].sum()}/{len(df)} ({pct_with_mood:.1f}%)')
print(f'Record voi TAT CA mood = 0: {(~df["has_any_mood"]).sum()}/{len(df)} ({pct_no_mood:.1f}%)')
print()

print('--- Top 5 samples ---')
sample_cols = ['title', 'categoryName', 'totalScore'] + mood_cols[:3]
print(df[sample_cols].head())

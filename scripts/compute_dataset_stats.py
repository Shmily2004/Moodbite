import pandas as pd

def main():
    f = 'data_pipeline/data_cleaned/dataset_moodbite_features.csv'
    df = pd.read_csv(f)
    print('FILE:', f)
    print('ROWS:', len(df))
    mood_cols = [c for c in df.columns if c.endswith('_score')]
    print('MOOD_COLS:', mood_cols)
    if mood_cols:
        has_any = int(df[mood_cols].gt(0).any(axis=1).sum())
        pct = has_any / len(df) * 100
        print('ROWS_WITH_MOOD_GT0:', has_any)
        print('PCT_WITH_MOOD_GT0:{:.2f}%'.format(pct))

if __name__ == '__main__':
    main()

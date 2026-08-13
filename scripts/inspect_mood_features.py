import csv
from pathlib import Path

p = Path('data_pipeline/data_cleaned/dataset_moodbite_features.csv')
if not p.exists():
    print('MISSING')
    raise SystemExit(1)

with p.open(newline='', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    # mood columns: those that end with _score
    mood_idxs = [i for i,h in enumerate(header) if h.lower().endswith('_score')]
    mood_names = [header[i] for i in mood_idxs]
    total = 0
    positive = 0
    samples = []
    for row in reader:
        total += 1
        has = False
        for i in mood_idxs:
            try:
                if float(row[i]) > 0:
                    has = True
                    break
            except:
                pass
        if has:
            positive += 1
        if len(samples) < 5:
            sample = {header[j]: row[j] for j in range(len(header)) if j in mood_idxs or header[j] in ('title','placeId')}
            samples.append(sample)

print('TOTAL', total)
print('MOOD_COLS', len(mood_idxs))
print('MOOD_NAMES', ','.join(mood_names))
print('POSITIVE', positive)
print('POSITIVE_PCT', round(100*positive/total,2) if total>0 else 0)
print('SAMPLES')
for s in samples:
    print(s)

import pandas as pd
import numpy as np
from pathlib import Path

def extract_features():
    """
    MoodBite Feature Engineering Pipeline
    Refactored from 02_feature_engineering.ipynb
    """
    cleaned_file = Path('data_pipeline/data_cleaned/dataset_moodbite_clean.csv')
    
    if not cleaned_file.exists():
        print(f"Warning: {cleaned_file} not found. Skipping feature extraction demo.")
        return

    # 1. Đọc file dữ liệu sạch từ bước trước
    df = pd.read_csv(cleaned_file)

    # Lấy TẤT CẢ chữ trong mỗi dòng ghép lại thành 1 đoạn văn bản lớn.
    df['all_text'] = df.apply(lambda row: ' '.join(row.values.astype(str)).lower(), axis=1)

    # 2. Xây dựng Bộ từ điển Cảm xúc (Mood Lexicon)
    mood_dictionaries = {
        'comfort_cozy': ['chill', 'thư giãn', 'yên tĩnh', 'thoải mái', 'ấm cúng', 'tâm tình', 'nhẹ nhàng', 'view đẹp'],
        'spicy_hot': ['cay', 'nóng', 'tê', 'đậm đà', 'xuýt xoa', 'sa tế', 'ớt'],
        'fresh_healthy': ['tươi', 'thanh mát', 'sạch', 'healthy', 'rau', 'healthy', 'ngọt tự nhiên'],
        'cheap_budget': ['rẻ', 'bình dân', 'sinh viên', 'hợp lý', 'phải chăng', 'vỉa hè'],
        'quick_fast': ['nhanh', 'vội', 'tiện', 'lấy luôn', 'không phải đợi', 'ăn liền']
    }

    # 3. Hàm tính điểm Cảm xúc (Scoring Function)
    def calculate_mood_score(text, keywords):
        score = 0
        for word in keywords:
            score += text.count(word)
        return score

    # 4. Áp dụng chấm điểm cho từng quán
    for mood, keywords in mood_dictionaries.items():
        df[f'{mood}_score'] = df['all_text'].apply(lambda x: calculate_mood_score(x, keywords))

    # 5. Chuẩn hóa dữ liệu (Normalization)
    mood_columns = [f'{mood}_score' for mood in mood_dictionaries.keys()]
    for col in mood_columns:
        max_val = df[col].max()
        if max_val > 0:
            df[col] = df[col] / max_val

    # 6. Lọc lại các cột cần thiết
    columns_to_keep = ['title', 'location/lat', 'location/lng', 'totalScore'] + mood_columns
    final_cols = [c for c in columns_to_keep if c in df.columns]
    df_features = df[final_cols]

    # 7. Lưu bộ dữ liệu vàng này lại
    output_file = Path('data_pipeline/data_cleaned/dataset_moodbite_features.csv')
    df_features.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"Đã trích xuất đặc trưng xong! Lưu tại {output_file}")

if __name__ == "__main__":
    extract_features()

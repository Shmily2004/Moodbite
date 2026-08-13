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
    #
    # LƯU Ý QUAN TRỌNG: bộ từ khóa gốc (chill, thư giãn, xuýt xoa, ...) được thiết kế để đọc
    # từ text review/description của khách hàng. Nhưng dữ liệu cào được từ Google Maps/OSM
    # KHÔNG có trường description/review (hầu hết đều null) — chỉ có categoryName dạng
    # "Nhà hàng lẩu", "Quán cà phê", ... Nếu chỉ dùng bộ từ khóa gốc, mood score sẽ ra 0
    # cho gần như toàn bộ dataset vì không có từ nào khớp.
    #
    # Vì vậy bổ sung thêm nhóm từ khóa suy luận từ LOẠI HÌNH quán ăn (categoryName) —
    # đây là suy luận heuristic (VD: quán lẩu/nướng thường cay-nóng), không chính xác
    # 100% như đọc được review thật, nhưng vẫn tốt hơn nhiều so với toàn bộ ra 0.
    # Khi dự án có dữ liệu review thật (vd Apify actor có field 'reviews'), nên ưu tiên
    # dùng lại bộ từ khóa gốc trên chính text đó.
    mood_dictionaries = {
        'comfort_cozy': [
            'chill', 'thư giãn', 'yên tĩnh', 'thoải mái', 'ấm cúng', 'tâm tình', 'nhẹ nhàng', 'view đẹp',
            'cà phê', 'coffee', 'trà', 'gia đình', 'ấm bụng',
            # Từ khóa cuisine (field 'cuisine' cào từ OSM, tiếng Anh) - tín hiệu thật
            # nhưng trước đây bị bỏ qua vì bộ từ điển chỉ có tiếng Việt.
            'japanese', 'korean', 'cake',
        ],
        'spicy_hot': [
            'cay', 'nóng', 'tê', 'đậm đà', 'xuýt xoa', 'sa tế', 'ớt',
            'lẩu', 'nướng', 'cà ri', 'curry',
            'pho', 'cha_ca', 'thai', 'chinese',
        ],
        'fresh_healthy': [
            'tươi', 'thanh mát', 'sạch', 'healthy', 'rau', 'ngọt tự nhiên',
            'chay', 'hải sản', 'salad', 'organic', 'hữu cơ',
            'seafood', 'vietnamese',
        ],
        'cheap_budget': [
            'rẻ', 'bình dân', 'sinh viên', 'hợp lý', 'phải chăng', 'vỉa hè',
            'quán ăn nhỏ', 'ăn nhanh',
            'banh_mi', 'street',
        ],
        'quick_fast': [
            'nhanh', 'vội', 'tiện', 'lấy luôn', 'không phải đợi', 'ăn liền',
            'ăn nhanh', 'fast food', 'giao đồ ăn', 'mang về', 'lưu động',
            'pizza', 'burger',
        ]
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
    # Giữ lại categoryName/address (trước đây bị loại) vì tầng ứng dụng (TypeScript) cần
    # categoryName để suy luận loại món và address để hiển thị cho người dùng.
    # Giữ lại 'cuisine' (trước đây bị loại ở chính bước này) - đây là field đã cào được
    # từ OSM (data_pipeline/scrape_osm_hanoi.py + scrapers/enhanced_osm_query.py) nhưng
    # chưa từng được dùng, dù all_text ở bước 1 đã ghép nó vào lúc tính mood_score. Giữ
    # lại cột này để tầng dish-knowledge-base (Python + TS) có thể dùng cuisine làm tín
    # hiệu match chính xác hơn categoryName một mình.
    columns_to_keep = ['title', 'placeId', 'location/lat', 'location/lng', 'totalScore', 'categoryName', 'cuisine', 'address'] + mood_columns
    final_cols = [c for c in columns_to_keep if c in df.columns]
    df_features = df[final_cols]

    # 7. Lưu bộ dữ liệu vàng này lại
    output_file = Path('data_pipeline/data_cleaned/dataset_moodbite_features.csv')
    df_features.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"Đã trích xuất đặc trưng xong! Lưu tại {output_file}")

if __name__ == "__main__":
    extract_features()
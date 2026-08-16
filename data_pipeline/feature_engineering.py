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
        'comfort_cozy': [
            'chill', 'thư giãn', 'yên tĩnh', 'thoải mái', 'ấm cúng', 'tâm tình', 'nhẹ nhàng', 'view đẹp',
            'cà phê', 'coffee', 'trà', 'gia đình', 'ấm bụng',
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
    #
    # ENRICHMENT_COLUMNS: giá / đánh giá / ảnh / giờ mở cửa. Những cột này Apify ĐÃ cào về
    # và nằm sẵn trong merged_places.csv, nhưng trước đây bị bước này cắt bỏ nên toàn bộ
    # app không hề biết tới - phải cào lại từ đầu mới có, dù dữ liệu vốn đã nằm trên đĩa.
    # Chỉ quán từ Apify mới có (quán từ OSM không có giá/đánh giá) -> để trống là ĐÚNG,
    # không fillna(0), nhất quán với quy ước sẵn có của totalScore.
    enrichment_columns = [
        'price',                        # VD: "100-200 N ₫"
        'reviewsCount',
        'reviewsDistribution/oneStar', 'reviewsDistribution/twoStar',
        'reviewsDistribution/threeStar', 'reviewsDistribution/fourStar',
        'reviewsDistribution/fiveStar',
        'imagesCount',
        'openingHours',
        'website', 'url',               # deep-link ra menu (Google Maps không có menu)
        # Thuộc tính có cấu trúc của Google - mô tả KHÔNG GIAN quán. Đây là dữ liệu thật
        # do Google gắn nhãn (VD "Ấm cúng", "Thông thường", "Cao cấp"), chính xác hơn hẳn
        # so với đoán mood bằng cách dò từ khóa trong categoryName.
        'additionalInfo/Bầu không khí',   # không gian: Ấm cúng / Cao cấp / Thông thường
        'additionalInfo/Tiện nghi',       # tiện nghi
        'additionalInfo/Lựa chọn ăn uống',
        'additionalInfo/Khách hàng',      # phù hợp nhóm / gia đình / đi một mình
        'additionalInfo/Nổi tiếng về',
    ]
    # PROVENANCE_COLUMNS: mỗi bản ghi phải trả lời được "ở đâu ra, đáng tin tới đâu,
    # cập nhật lúc nào". Trước đây dataset trộn lẫn Google + OSM mà KHÔNG có cách nào
    # phân biệt, nên không thể đánh giá chất lượng dữ liệu hay ưu tiên nguồn tốt hơn.
    provenance_columns = [
        'source', 'source_url', 'last_updated', 'data_confidence',
    ]

    # DISCOVERY_COLUMNS: các trường phục vụ tìm kiếm / lọc / hiển thị mà bản cào mới
    # (data_pipeline/sources/osm_overpass.py) đã lấy về nhưng trước đây bị bước này cắt bỏ.
    discovery_columns = [
        'district', 'district_confidence',   # quận/huyện - suy từ toạ độ
        'phone', 'street',
        'aliases',                            # tên gọi khác -> tăng khả năng khớp tìm kiếm
        'amenities',                          # outdoor_seating, air_conditioning, wifi...
        'dietary',                            # vegetarian / vegan / halal
        'delivery', 'takeaway',
        'dishes',                             # gợi ý món từ tag cuisine của OSM
        'menu',
        # Cụm trải nghiệm do data_pipeline/clustering.py sinh ra (Lớp 1 của đề án).
        # PHẢI có ở đây, nếu không mỗi lần chạy lại feature_engineering sẽ xoá mất cụm
        # và phải chạy lại clustering. Thứ tự đúng:
        #   merge -> cleaning -> feature_engineering -> clustering
        'experience_cluster_id', 'experience_cluster_label',
    ]

    columns_to_keep = (
        ['title', 'placeId', 'location/lat', 'location/lng', 'totalScore',
         'categoryName', 'cuisine', 'address']
        + mood_columns + enrichment_columns + provenance_columns + discovery_columns
    )
    final_cols = [c for c in columns_to_keep if c in df.columns]
    df_features = df[final_cols]
    
    # 7. Lưu bộ dữ liệu vừa xử lý lại
    output_file = Path('data_pipeline/data_cleaned/dataset_moodbite_features.csv')
    df_features.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"Đã trích xuất đặc trưng xong! Lưu tại {output_file}")

    # 8. Tách phần "nặng" (review đầy đủ + danh sách ảnh) ra file riêng, đánh khóa theo
    #    placeId. Lý do: gộp chung vào CSV đặc trưng làm file phình từ 0.7MB lên 12MB
    #    (riêng cột reviews đã chiếm 87%), trong khi RecommendationService.recommend()
    #    gọi df.copy() ở MỖI request -> copy 12MB mỗi lần gọi API là quá phí.
    #    Xếp hạng chỉ cần cột nhẹ; review/ảnh chỉ cần khi người dùng bấm xem chi tiết 1 quán.
    _write_details(df)


# Giới hạn để file chi tiết không phình vô hạn. Apify trả về HÀNG TRĂM review/quán, mỗi
# review kèm ~24 field (ảnh người đánh giá, url, id...) mà UI không bao giờ dùng. Giữ
# nguyên thì 450 quán đã nặng 11.5MB -> cào đủ 4170 quán sẽ vượt giới hạn 100MB/file của
# GitHub. Cắt còn 10 review mới nhất và 5 field thực sự cần.
MAX_REVIEWS_PER_PLACE = 10
MAX_IMAGES_PER_PLACE = 12
REVIEW_FIELDS = ('name', 'text', 'stars', 'publishedAtDate', 'likesCount')


def _parse_cell(value):
    """Cột trong CSV là chuỗi Python-literal (["a", "b"] / [{...}]), không phải JSON hợp lệ
    (dùng nháy đơn), nên json.loads sẽ hỏng -> dùng ast.literal_eval."""
    import ast

    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    if isinstance(value, (list, dict)):
        return value
    try:
        return ast.literal_eval(str(value))
    except (ValueError, SyntaxError):
        return None


def _write_details(df):
    import json

    scalar_columns = [c for c in ('title', 'menu', 'price', 'website', 'url', 'openingHours',
                                  'additionalInfo/Bầu không khí') if c in df.columns]

    details = {}
    for _, row in df.iterrows():
        place_id = row.get('placeId')
        if pd.isna(place_id):
            continue

        reviews = _parse_cell(row.get('reviews')) or []
        trimmed = [
            {k: r.get(k) for k in REVIEW_FIELDS}
            for r in reviews[:MAX_REVIEWS_PER_PLACE]
            if isinstance(r, dict)
        ]
        images = (_parse_cell(row.get('imageUrls')) or [])[:MAX_IMAGES_PER_PLACE]

        record = {c: (None if pd.isna(row[c]) else row[c]) for c in scalar_columns}
        record['reviews'] = trimmed
        record['imageUrls'] = images

        # Chỉ giữ quán thực sự có dữ liệu chi tiết (quán OSM không có gì để hiện).
        if trimmed or images or record.get('price') is not None:
            details[str(place_id)] = record

    output_file = Path('data_pipeline/data_cleaned/restaurant_details.json')
    with open(output_file, 'w', encoding='utf-8') as fh:
        json.dump(details, fh, ensure_ascii=False)

    print(f"Đã lưu chi tiết {len(details)} quán (review/ảnh/giá) tại {output_file}")

if __name__ == "__main__":
    extract_features()
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Dùng lại phép so khớp chữ tiếng Việt của domain thay vì tự viết bản thứ hai.
# CLAUDE.md mục 4 quy tắc 5 nói thẳng: "dùng domain/value_objects/text.py, đừng tự viết
# lại". Bản cũ ở đây dùng `text.count(tu_khoa)` - so CHUỖI CON, nên "rẻ" đếm luôn trong
# "trẻ em", "trà" đếm trong "trách". Đã có tiền lệ import như thế này ở
# `merge_and_prepare_raw.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.domain.value_objects.text import PhraseLookup  # noqa: E402

# TỪ ĐIỂN CẢM XÚC. Đưa ra ngoài hàm để đo được bằng script mà không phải chạy cả pipeline.
MOOD_LEXICON = {
    'comfort_cozy': [
        'chill', 'thư giãn', 'yên tĩnh', 'thoải mái', 'ấm cúng', 'tâm tình', 'nhẹ nhàng',
        'view đẹp', 'cà phê', 'coffee', 'trà', 'gia đình', 'ấm bụng',
        'japanese', 'korean', 'cake',
    ],
    'spicy_hot': [
        'cay', 'nóng', 'tê', 'đậm đà', 'xuýt xoa', 'sa tế', 'ớt',
        'lẩu', 'nướng', 'cà ri', 'curry',
        # "phở" CÓ DẤU: từ khoá không dấu "pho" sẽ khớp cả "Phố" lẫn "Tào Phớ" vì luật
        # so khớp cố tình bao dung khi một vế không có dấu (xem `tokens_match`).
        'phở', 'cha_ca', 'thai', 'chinese',
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
    ],
}

# Số từ khoá RIÊNG BIỆT để một quán đạt điểm 0.5 ở một chiều cảm xúc.
#
# CHỌN BẰNG SỐ ĐO, không bằng cảm tính (CLAUDE.md mục 4c). Đo trên mẫu 2.000 quán ngẫu
# nhiên ngày 2026-08-19, phân phối số từ khoá khớp (0 / 1 / 2 / >=3 từ):
#
#     comfort_cozy    61,9%  23,8%  12,7%   1,7%   (nhiều nhất - ai cũng nhắc "cà phê")
#     spicy_hot       83,7%  13,1%   2,1%   1,1%
#     fresh_healthy   92,0%   6,2%   0,9%   0,9%
#     cheap_budget    93,2%   5,3%   0,6%   0,9%
#     quick_fast      93,3%   1,9%   4,1%   0,7%
#
# Trường hợp có bằng chứng thì PHỔ BIẾN NHẤT là đúng 1 từ khoá. Vậy K phải đủ nhỏ để 1 từ
# đã tách khỏi nhóm 0 từ, nhưng không lớn tới mức 1 từ đã là "rất hợp":
#     K=1 -> 1 từ = 0,50 (một chữ "cà phê" mà thành nửa điểm là quá mạnh)
#     K=2 -> 1 từ = 0,33 · 2 từ = 0,50 · 4 từ = 0,67   <- chọn cái này
#     K=3 -> 1 từ = 0,25 (gần như không tách khỏi 0)
# Từ thứ năm trở đi gần như không thêm gì - đúng thực tế: nhắc "ấm cúng" 1 lần hay 5 lần
# thì quán vẫn chỉ là ấm cúng.
MOOD_SATURATION = 2


def mood_scores_for_text(text):
    """{tên_chiều: điểm [0,1]} cho MỘT quán. Hàm thuần - test và đo được độc lập.

    HAI THỨ ĐÃ SỬA SO VỚI BẢN CŨ, cả hai đều làm hỏng thứ hạng trên dữ liệu thật:

    1. ĐẾM SỐ TỪ KHOÁ RIÊNG BIỆT, không đếm số lần xuất hiện. Bản cũ cộng dồn
       `text.count(tu_khoa)`, nên quán có review (trung bình ~670 ký tự/review, tối đa 10
       review) luôn cộng được điểm cao hơn quán chỉ có tên + loại hình. Kết quả là điểm
       mood đo LƯỢNG CHỮ CÀO ĐƯỢC chứ không đo tính chất của quán.

    2. BỎ CHUẨN HOÁ THEO GIÁ TRỊ LỚN NHẤT TOÀN BỘ (`df[col] / df[col].max()`).
       Cách đó buộc điểm của một quán phụ thuộc vào quán "ồn ào" nhất trong dataset: chỉ
       cần thêm một quán có nhiều review là điểm của 40.719 quán còn lại tụt xuống. Đo
       được hậu quả ngày 2026-08-19: chỉ 460/40.720 quán (1,1%) có điểm > 0,1, trung vị
       bằng 0 - trong khi mood là trọng số NẶNG NHẤT của bảng xếp hạng (W_MOOD = 0,26).
       Đường cong bão hoà n/(n+K) cho điểm nằm gọn trong [0,1] mà không cần biết gì về
       các quán khác, nên thêm dữ liệu mới không làm xáo trộn điểm của dữ liệu cũ.
    """
    lookup = PhraseLookup(text)
    return {
        mood: (lambda n: n / (n + MOOD_SATURATION))(lookup.count_present(keywords))
        for mood, keywords in MOOD_LEXICON.items()
    }


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
    # Gộp toàn bộ chữ của một dòng thành một đoạn để dò từ khoá cảm xúc.
    df['all_text'] = df.apply(lambda row: ' '.join(row.values.astype(str)).lower(), axis=1)

    # 2-4. Chấm điểm cảm xúc. Từ điển + công thức nằm ở đầu file (`MOOD_LEXICON`,
    # `mood_scores_for_text`) để đo và test được mà không phải chạy cả pipeline.
    #
    # KHÔNG còn bước "chuẩn hoá theo max" ở đây: `mood_scores_for_text` đã trả về [0,1]
    # cho từng quán một cách độc lập. Xem docstring của nó để biết vì sao bước cũ có hại.
    diem = df['all_text'].apply(mood_scores_for_text)
    for mood in MOOD_LEXICON:
        df[f'{mood}_score'] = diem.apply(lambda d, m=mood: d[m])

    mood_columns = [f'{mood}_score' for mood in MOOD_LEXICON]

    # Báo cáo ngay tại chỗ: không có số đo thì không được nói "dữ liệu đã cải thiện"
    # (CLAUDE.md mục 4b).
    khong_bang_chung = (df[mood_columns].sum(axis=1) == 0).mean()
    print(f"  Diem mood: {100*(1-khong_bang_chung):.1f}% quan co it nhat 1 tu khoa khop")
    for col in mood_columns:
        print(f"    {col:22s} trung vi={df[col].median():.3f}  >0.3: {100*(df[col]>0.3).mean():.1f}%")


    # 6. Lọc lại các cột cần thiết
    #
    # ENRICHMENT_COLUMNS: giá / đánh giá / ảnh / giờ mở cửa. Những cột này Apify ĐÃ cào về
    # và nằm sẵn trong merged_places.csv, nhưng trước đây bị bước này cắt bỏ nên toàn bộ
    # app không hề biết tới - phải cào lại từ đầu mới có, dù dữ liệu vốn đã nằm trên đĩa.
    # Chỉ quán từ Apify mới có (quán từ OSM không có giá/đánh giá) -> để trống là ĐÚNG,
    # không fillna(0), nhất quán với quy ước sẵn có của totalScore.
    enrichment_columns = [
        # TRẠNG THÁI CÒN MỞ HAY ĐÃ ĐÓNG. Apify cào về sẵn từ Google nhưng bước này từng
        # cắt mất, nên app vẫn gợi ý quán đã đóng cửa như quán bình thường. Đo 2026-08-19:
        # 1 quán đóng hẳn + 15 quán đóng tạm vẫn nằm trong kết quả tìm kiếm.
        # `None` = KHÔNG BIẾT (quán từ OSM/Overture không có trường này), khác hẳn `False`
        # = biết chắc đang mở. Đừng fillna(False) - xem CLAUDE.md mục 4 quy tắc 1.
        'permanentlyClosed',
        'temporarilyClosed',
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
        # TUỔI THẬT + BẰNG CHỨNG XÁC NHẬN. Phải nằm trong danh sách GIỮ LẠI, nếu không
        # lần chạy pipeline sau sẽ xoá sạch - đúng bài học `ENRICHMENT_COLUMNS` ở trên,
        # dự án đã mất một lần rồi.
        #
        # KHÁC `last_updated`: cột kia là ngày TA CÀO, mấy cột này là ngày NGUỒN cập nhật
        # và ngày người ta đi xác minh tận nơi. Xem `data_pipeline/sources/base.py`.
        'source_updated_at',    # ngày nguồn sửa bản ghi lần cuối
        'source_datasets',      # nền tảng nào cùng ghi nhận (meta, Microsoft, Foursquare...)
        'source_confidence',    # điểm tin cậy do nguồn chấm [0,1]
        'surveyed_at',          # ngày có người đi xác minh TẬN NƠI (OSM check_date)
        'socials',              # link Facebook/Instagram do Meta đóng góp hợp pháp
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
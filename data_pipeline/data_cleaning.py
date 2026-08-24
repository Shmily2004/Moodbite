import os
import re
import pandas as pd
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# --- LÀM SẠCH TÊN QUÁN (thêm 2026-08-24) ------------------------------------
#
# Số điện thoại dính vào tên là chuyện rất hay gặp trong dữ liệu POI:
#     "Lò Quay Vịt Huy Hải 0973663726"   ->  "Lò Quay Vịt Huy Hải"
#     "Bảo Long Audio-0983293453"        ->  "Bảo Long Audio"
# Đo 2026-08-24: 149/53.462 tên có chuỗi >=9 chữ số liên tiếp.
#
# CHỈ bắt chuỗi >=9 chữ số, KHÔNG bắt số ngắn: "Bún Chả 141" thì 141 là SỐ NHÀ, và
# "Cơm Tấm 68" thì 68 là tên quán. Số điện thoại Việt Nam có 10 chữ số nên ngưỡng 9 vừa
# đủ rộng để bắt cả số cũ 9 chữ số, vừa đủ hẹp để không đụng số nhà.
SO_DIEN_THOAI = re.compile(r"[\s\-–—:.]*\(?\+?\d[\d.\-\s]{7,}\d\)?\s*$")

# Ký tự phân cách còn sót lại sau khi cắt số điện thoại ("Bảo Long Audio-" -> "Bảo Long Audio").
DUOI_THUA = re.compile(r"[\s\-–—:.,|/]+$")


def _lam_sach_ten(ten) -> str:
    """Chuẩn hoá một tên quán. Trả chuỗi rỗng nếu tên không dùng được.

    ⚠️ KHÔNG loại theo ĐỘ DÀI. Đó là cái bẫy đã suýt mắc: trong dữ liệu thật có các quán
    Hàn Quốc ở Mỹ Đình tên đúng hai ký tự — '삼원', '청담', '고궁', '연경', '인연'. Luật
    "tên <= 2 ký tự là rác" sẽ xoá sạch chúng, mà chúng hoàn toàn hợp lệ.
    Luật an toàn hơn: chỉ loại tên KHÔNG CÓ LẤY MỘT CHỮ CÁI NÀO ('345', '1900', '1989').
    """
    if not isinstance(ten, str):
        return ""
    sach = SO_DIEN_THOAI.sub("", ten)
    sach = DUOI_THUA.sub("", sach)
    # Gộp mọi khoảng trắng lặp về một dấu cách (đo được 196 tên dính lỗi này).
    sach = re.sub(r"\s+", " ", sach).strip()
    # Không còn chữ cái nào -> không hiển thị được, cũng không khớp món được.
    if not any(c.isalpha() for c in sach):
        return ""
    return sach


def clean_data(raw_file: str = None):
    """
    MoodBite Data Cleaning Pipeline
    - Handles missing values
    - Removes duplicates
    - Filters invalid records
    """
    BASE_DIR = Path.cwd()
    RAW_DIR = BASE_DIR / 'data_pipeline' / 'data_raw'
    CLEANED_DIR = BASE_DIR / 'data_pipeline' / 'data_cleaned'

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    if raw_file is None:
        csv_files = list(RAW_DIR.glob('*.csv'))
        if not csv_files:
            logger.warning(f"No CSV files found in {RAW_DIR}")
            return
        raw_path = csv_files[0]
    else:
        raw_path = Path(raw_file)

    logger.info(f'Cleaning data from: {raw_path}')
    
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        logger.error(f"Failed to read {raw_path}: {e}")
        return

    initial_count = len(df)
    
    # 1. Remove duplicates
    df = df.drop_duplicates()
    logger.info(f"Removed {initial_count - len(df)} duplicate records.")

    # 2. Handle missing essential values
    essential_cols = ['title', 'location/lat', 'location/lng']
    available_essential = [col for col in essential_cols if col in df.columns]
    
    if available_essential:
        before_drop = len(df)
        df = df.dropna(subset=available_essential)
        logger.info(f"Dropped {before_drop - len(df)} records with missing essential fields: {available_essential}")

    # 3. Fill non-essential missing values
    # LƯU Ý: totalScore KHÔNG được fillna(0) - quán không có rating (VD: toàn bộ quán
    # từ OpenStreetMap, không có hệ thống rating sao như Google Maps) sẽ trông giống
    # "bị đánh giá 0 sao" nếu điền 0, trong khi thực ra nghĩa là "không có dữ liệu".
    # Để trống (NaN) - tầng ứng dụng (`csv_restaurant_repository.py`) đã xử lý đúng giá
    # trị rỗng thành `rating: None` thay vì giả định là số 0.
    # (Comment cũ trỏ tới `CsvRestaurantRepository.ts` - file đó thuộc backend TypeScript
    #  đã chuyển vào `archive/` từ lâu. Sửa 2026-08-24.)

    if 'categoryName' in df.columns:
        df['categoryName'] = df['categoryName'].fillna('Unknown')

    # 3b. Làm sạch TÊN quán — xem `_lam_sach_ten`.
    if 'title' in df.columns:
        truoc = df['title'].fillna('')
        sach = truoc.map(_lam_sach_ten)
        so_sua = int((sach != truoc.map(lambda x: x if isinstance(x, str) else '')).sum())
        so_bo = int((sach == '').sum())
        df = df.assign(title=sach)
        df = df[df['title'] != '']
        logger.info(
            "Làm sạch tên: sửa %d tên (số điện thoại dính vào tên, khoảng trắng thừa), "
            "bỏ %d bản ghi không còn chữ cái nào",
            so_sua - so_bo, so_bo,
        )

    # 4. Save cleaned data
    output_path = CLEANED_DIR / 'dataset_moodbite_clean.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"Cleaned data saved to {output_path}")

if __name__ == "__main__":
    clean_data()
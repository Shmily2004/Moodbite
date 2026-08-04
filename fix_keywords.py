#!/usr/bin/env python3
"""
Script sửa encoding từ khóa trong filter_restaurants.py
Sửa 2 lỗi:
  1. Xóa UTF-8 BOM nếu có
  2. Fix tất cả từ khóa Tiếng Việt bị double-encoded

Cách sử dụng trên Windows:
  python fix_keywords.py data_pipeline/filter_restaurants.py
"""

import sys
import re
from pathlib import Path

restaurant_keywords = [
    "nhà hàng",
    "nhà hàng hải sản",
    "nhà hàng gia đình",
    "nhà hàng món lẩu",
    "quán ăn",
    "quán",
    "quán cafe",
    "cafe",
    "coffee",
    "restaurant",
    "food",
    "eatery",
    "bar",
    "pub",
    "tea house",
    "bubble tea",
    "fast food",
    "buffet",
    "seafood",
    "phở",
    "bún",
    "miến",
    "bánh",
    "cà phê",
    "trà sữa",
]

excluded_keywords = [
    "khách sạn",
    "hotel",
    "resort",
    "cửa hàng",
    "siêu thị",
    "market",
    "grocery",
    "supermarket",
    "chăn nuôi",
    "pet",
    "farm",
    "motel",
    "homestay",
    "hostel",
    "apartment",
    "phòng trọ",
    "nhà nghỉ",
    "spa",
    "salon",
    "beauty",
    "clinic",
    "hospital",
    "pharmacy",
    "bakery",
    "tiệm bánh",
    "lò bánh",
    "bookstore",
    "stationery",
    "car wash",
    "garage",
    "repair",
    "school",
    "university",
    "người cung cấp thực phẩm",
    "nhà cung cấp thực phẩm",
    "cung cấp thực phẩm",
    "công ty",
    "công ty tnnh",
    "công ty tnhh",
    "chi nhánh",
    "viettel",
    "telecom",
    "company",
    "corp",
    "inc",
    "llc",
    "limited",
    "joint stock",
    "investment",
    "trading",
    "commercial",
]

def fix_file(file_path):
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ File không tồn tại: {file_path}")
        return False
    
    # Đọc file
    with open(file_path, 'rb') as f:
        content_bytes = f.read()
    
    # Xóa UTF-8 BOM nếu có
    has_bom = False
    if content_bytes.startswith(b'\xef\xbb\xbf'):
        content_bytes = content_bytes[3:]
        has_bom = True
    
    content = content_bytes.decode('utf-8')
    
    # Tạo từ khóa mới
    rest_kw_str = "RESTAURANT_KEYWORDS = [\n"
    for kw in restaurant_keywords:
        rest_kw_str += f'    "{kw}",\n'
    rest_kw_str += "]\n"
    
    excl_kw_str = "EXCLUDED_KEYWORDS = [\n"
    for kw in excluded_keywords:
        excl_kw_str += f'    "{kw}",\n'
    excl_kw_str += "]\n"
    
    # Replace từ khóa cũ
    pattern = r'RESTAURANT_KEYWORDS = \[.*?\n\]\n'
    content = re.sub(pattern, rest_kw_str, content, flags=re.DOTALL)
    
    pattern = r'EXCLUDED_KEYWORDS = \[.*?\n\]\n'
    content = re.sub(pattern, excl_kw_str, content, flags=re.DOTALL)
    
    # Lưu file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")
    if has_bom:
        print(f"   ✓ Removed UTF-8 BOM")
    print(f"   ✓ Fixed {len(restaurant_keywords)} restaurant keywords")
    print(f"   ✓ Fixed {len(excluded_keywords)} excluded keywords")
    return True

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "data_pipeline/filter_restaurants.py"
    
    if fix_file(file_path):
        print("\n✨ Done! Giờ chạy test:")
        print("   python -m unittest tests.test_filter_restaurants -v")
        sys.exit(0)
    else:
        sys.exit(1)

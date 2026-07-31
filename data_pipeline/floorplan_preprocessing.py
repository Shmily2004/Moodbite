import cv2
import numpy as np
from pathlib import Path

def preprocess_floorplan(image_path: str, output_path: str):
    """
    Tiền xử lý bản vẽ mặt bằng: Grayscale, Denoising, Thresholding.
    """
    # 1. Đọc ảnh
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image at {image_path}")
        return

    # 2. Chuyển sang ảnh xám
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Khử nhiễu (Denoising)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # 4. Tăng cường độ tương phản (Adaptive Thresholding)
    # Giúp làm nổi bật các đường nét tường và cửa
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # 5. Khử nhiễu đốm nhỏ (Morphological Operations)
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # 6. Lưu kết quả
    cv2.imwrite(output_path, processed)
    print(f"Processed image saved to {output_path}")

if __name__ == "__main__":
    # Demo code
    RAW_SAMPLE = "data_pipeline/data_raw/sample_floorplan.jpg"
    PROCESSED_SAMPLE = "data_pipeline/data_cleaned/sample_floorplan_preprocessed.png"
    
    # Tạo thư mục nếu chưa có
    Path("data_pipeline/data_cleaned").mkdir(parents=True, exist_ok=True)
    
    # Chạy tiền xử lý nếu có file mẫu (ở đây chỉ là skeleton)
    if Path(RAW_SAMPLE).exists():
        preprocess_floorplan(RAW_SAMPLE, PROCESSED_SAMPLE)
    else:
        print("Raw sample not found. Skipping preprocessing demo.")

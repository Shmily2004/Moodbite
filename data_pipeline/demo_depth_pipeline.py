"""
MoodBite - Script test nhanh pipeline depth-estimation với vài ảnh mẫu tự chọn.

Dùng để KIỂM CHỨNG pipeline (depth map + point cloud) hoạt động đúng với ảnh chụp thật
TRƯỚC KHI cào ảnh hàng loạt từ Apify (đang chỉ dùng):
1. Tự chọn vài ảnh chụp không gian quán ăn (điện thoại của bạn, hoặc tự lưu vài
   ảnh từ Google Maps - không cần script scrape gì cả).
2. Bỏ các ảnh đó vào thư mục test_images/ (tạo thư mục này ở gốc project nếu chưa có).
3. Chạy:
    python -m pip install transformers torch pillow numpy matplotlib --break-system-packages
    python -m data_pipeline.test_depth_pipeline

Kết quả: với mỗi ảnh trong test_images/, script tạo ra 1 ảnh so sánh (gốc | depth map |
point cloud nhìn từ trên xuống) lưu vào test_images_output/, để bạn xem trực quan mà
không cần công cụ 3D chuyên dụng.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # không cần hiển thị màn hình, chỉ lưu file
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.application.services.depth_estimation_service import depth_estimation_service

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

INPUT_DIR = Path("test_images")
OUTPUT_DIR = Path("test_images_output")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def process_one_image(image_path: Path) -> bool:
    """Xử lý một ảnh: tính depth map + point cloud, vẽ 3-panel."""
    logger.info(f"Đang xử lý: {image_path.name}")

    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        logger.error(f"  Lỗi khi đọc ảnh: {e}")
        return False

    try:
        depth_array = depth_estimation_service.estimate_depth_array(image)
    except Exception as e:
        logger.error(f"  Lỗi khi ước lượng depth: {e}")
        return False

    try:
        points = depth_estimation_service.generate_point_cloud(image, max_points=5000)
    except Exception as e:
        logger.error(f"  Lỗi khi sinh point cloud: {e}")
        points = []

    # Vẽ 3 hình cạnh nhau: ảnh gốc | depth map | point cloud nhìn từ trên xuống (X-Z)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    axes[0].imshow(image)
    axes[0].set_title("Ảnh gốc")
    axes[0].axis("off")

    im = axes[1].imshow(depth_array, cmap="inferno")
    axes[1].set_title("Depth map (sáng = gần camera)")
    axes[1].axis("off")
    fig.colorbar(im, ax=axes[1], fraction=0.046)

    if points:
        xs = [p["x"] for p in points]
        zs = [p["z"] for p in points]
        colors = [p["color"] for p in points]
        axes[2].scatter(xs, zs, c=colors, s=1)
        axes[2].set_title("Point cloud (nhìn từ trên xuống: trục X ngang, Z = độ sâu)")
        axes[2].set_xlabel("X")
        axes[2].set_ylabel("Z (độ sâu)")
        axes[2].invert_yaxis()  # gần camera (Z nhỏ) ở phía dưới, giống góc nhìn từ trên
    else:
        axes[2].text(0.5, 0.5, "Không sinh được point cloud", ha="center", va="center")
        axes[2].axis("off")

    plt.tight_layout()
    output_path = OUTPUT_DIR / f"{image_path.stem}_result.png"
    plt.savefig(output_path, dpi=120)
    plt.close(fig)

    logger.info(f"  ✅ Đã lưu kết quả: {output_path}")
    return True


def main():
    if not INPUT_DIR.exists():
        INPUT_DIR.mkdir(parents=True)
        logger.warning(
            f"Đã tạo thư mục {INPUT_DIR}/ - hãy bỏ vài ảnh quán ăn vào đó rồi chạy lại script."
        )
        return

    image_files = [f for f in INPUT_DIR.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not image_files:
        logger.warning(f"Không tìm thấy ảnh nào trong {INPUT_DIR}/ (hỗ trợ: {SUPPORTED_EXTENSIONS})")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Tìm thấy {len(image_files)} ảnh, bắt đầu xử lý...")
    logger.info("(Lần chạy đầu tiên sẽ tải model Depth Anything V2 - cần internet, mất vài phút)")

    success_count = 0
    for image_path in image_files:
        if process_one_image(image_path):
            success_count += 1

    logger.info(f"Hoàn thành: {success_count}/{len(image_files)} ảnh xử lý thành công.")
    logger.info(f"Xem kết quả trong thư mục: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
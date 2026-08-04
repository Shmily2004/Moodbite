"""
MoodBite - Tải dataset floorplan CubiCasa5K (bản đã convert sẵn sang YOLO format
trên Roboflow Universe) và đặt đúng vị trí để train_yolo.py dùng được ngay.

VỀ DATASET:
- CubiCasa5K: 5000 ảnh floorplan thật, annotation 80+ category (tường, cửa, cửa sổ,
  đồ nội thất...). Gốc: https://github.com/CubiCasa/CubiCasa5k
- License gốc: Creative Commons Attribution-NonCommercial 4.0 International.
  => CHỈ dùng cho nghiên cứu/đồ án/phi thương mại. Nếu dự án sau này thương mại hóa,
     cần liên hệ xin phép riêng hoặc thay bằng dataset khác có license phù hợp.
- Bản dùng trong script này lấy từ Roboflow Universe (đã convert sẵn sang format
  bounding-box YOLO, dùng để train nhận diện đồ nội thất/cửa/cửa sổ).

CẦN API KEY MIỄN PHÍ CỦA ROBOFLOW (không mất phí để tải dataset public):
1. Đăng ký tài khoản miễn phí tại https://roboflow.com
2. Vào Settings -> API Keys, copy "Private API Key"
3. Dán vào biến ROBOFLOW_API_KEY bên dưới, hoặc set biến môi trường ROBOFLOW_API_KEY

CÁCH LẤY ĐÚNG workspace/project/version MỚI NHẤT (đáng tin hơn để mặc định cứng,
vì Roboflow có thể cập nhật version mới theo thời gian):
1. Mở 1 trong các link Universe sau (tìm được lúc viết script này):
   - https://universe.roboflow.com/floorplan-recognition/cubicasa5k-2-qpmsa
   (nếu link này đổi/không còn, search "cubicasa5k yolo roboflow universe")
2. Bấm "Dataset" -> "Download Dataset" -> chọn format "YOLOv11" -> "show download code"
3. Roboflow sẽ hiện đúng đoạn code với workspace/project/version chính xác tại
   thời điểm bạn tải - copy 3 giá trị đó vào ROBOFLOW_WORKSPACE / ROBOFLOW_PROJECT /
   ROBOFLOW_VERSION bên dưới thay vì dùng giá trị mặc định trong script (giá trị mặc
   định có thể đã lỗi thời).

CÁCH DÙNG:
    pip install roboflow --break-system-packages
    python -m data_pipeline.download_floorplan_dataset
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Điền API key vào đây, hoặc để trống và set biến môi trường ROBOFLOW_API_KEY thay vào đó.
ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "")

# Giá trị mặc định - kiểm tra lại theo hướng dẫn phía trên trước khi chạy,
# vì Roboflow có thể đã cập nhật version mới hơn kể từ lúc script này được viết.
ROBOFLOW_WORKSPACE = "floorplan-recognition"
ROBOFLOW_PROJECT = "cubicasa5k-2-qpmsa"
ROBOFLOW_VERSION = 6

TARGET_DIR = Path("data_pipeline/data_raw/floorplans_yolo")
DATA_YAML_TARGET = Path("data_pipeline/data.yaml")


def download_dataset() -> Path | None:
    if not ROBOFLOW_API_KEY:
        logger.error(
            "Chưa có ROBOFLOW_API_KEY. Đăng ký tài khoản miễn phí tại roboflow.com, "
            "lấy API key trong Settings -> API Keys, rồi set biến môi trường "
            "ROBOFLOW_API_KEY hoặc điền trực tiếp vào script này."
        )
        return None

    try:
        import roboflow
    except ImportError:
        logger.error("Chưa cài package roboflow. Chạy: pip install roboflow --break-system-packages")
        return None

    logger.info(f"Kết nối Roboflow: {ROBOFLOW_WORKSPACE}/{ROBOFLOW_PROJECT} v{ROBOFLOW_VERSION}")
    try:
        rf = roboflow.Roboflow(api_key=ROBOFLOW_API_KEY)
        project = rf.workspace(ROBOFLOW_WORKSPACE).project(ROBOFLOW_PROJECT)
        version = project.version(ROBOFLOW_VERSION)
    except Exception as e:
        logger.error(
            f"Không kết nối được tới dataset {ROBOFLOW_WORKSPACE}/{ROBOFLOW_PROJECT} "
            f"v{ROBOFLOW_VERSION}: {e}\n"
            "Rất có thể workspace/project/version mặc định trong script đã lỗi thời. "
            "Hãy lấy giá trị mới nhất theo hướng dẫn ở đầu file này và sửa lại "
            "ROBOFLOW_WORKSPACE/ROBOFLOW_PROJECT/ROBOFLOW_VERSION."
        )
        return None

    # Tải vào 1 thư mục tạm, tên đơn giản (không lồng nhiều cấp) trước - thư viện
    # roboflow-python xử lý không ổn định với đường dẫn lồng sâu trên Windows
    # (đã xác nhận qua thực tế: cùng lệnh download() thất bại âm thầm với đường dẫn
    # "data_pipeline/data_raw/floorplans_yolo" nhưng chạy đúng với "test_debug2").
    temp_download_dir = Path("_cubicasa5k_download_tmp")
    if temp_download_dir.exists():
        shutil.rmtree(temp_download_dir)

    logger.info(f"Đang tải dataset vào thư mục tạm {temp_download_dir} (có thể mất vài phút)...")
    dataset = version.download("yolov11", location=str(temp_download_dir))
    logger.info(f"Tải xong vào thư mục tạm: {dataset.location}")

    # Di chuyển sang đúng vị trí cuối cùng bằng Python thay vì để roboflow tự ghi
    # trực tiếp vào đường dẫn lồng sâu.
    TARGET_DIR.parent.mkdir(parents=True, exist_ok=True)
    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    shutil.move(str(temp_download_dir), str(TARGET_DIR))
    logger.info(f"Đã di chuyển dataset tới vị trí cuối cùng: {TARGET_DIR}")

    return TARGET_DIR


def link_data_yaml(dataset_location: Path) -> None:
    """train_yolo.py đang tìm data.yaml tại data_pipeline/data.yaml (đường dẫn cố định).
    Roboflow tải về sẽ sinh ra data.yaml bên trong thư mục dataset - copy nó ra đúng
    vị trí train_yolo.py mong đợi, đồng thời sửa lại đường dẫn train/val bên trong
    cho khớp vị trí mới (Roboflow mặc định ghi đường dẫn tương đối theo thư mục dataset)."""
    source_yaml = dataset_location / "data.yaml"
    if not source_yaml.exists():
        logger.warning(f"Không tìm thấy {source_yaml} - kiểm tra lại cấu trúc thư mục tải về.")
        return

    content = source_yaml.read_text(encoding="utf-8")

    # Roboflow ghi "train: ../train/images" (tương đối theo vị trí data.yaml gốc).
    # Khi copy sang vị trí mới (data_pipeline/data.yaml), cần trỏ tuyệt đối
    # về đúng thư mục ảnh đã tải, tránh lỗi "path not found" khi train.
    absolute_dataset_path = dataset_location.resolve()
    content = content.replace("../train/images", str(absolute_dataset_path / "train" / "images"))
    content = content.replace("../valid/images", str(absolute_dataset_path / "valid" / "images"))
    content = content.replace("../test/images", str(absolute_dataset_path / "test" / "images"))

    DATA_YAML_TARGET.write_text(content, encoding="utf-8")
    logger.info(f"Đã tạo {DATA_YAML_TARGET}, sẵn sàng cho train_yolo.py")
    logger.info("Bước tiếp theo: python -m src.infrastructure.ai.train_yolo")


if __name__ == "__main__":
    location = download_dataset()
    if location:
        link_data_yaml(location)

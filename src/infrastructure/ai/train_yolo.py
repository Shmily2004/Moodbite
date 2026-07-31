from ultralytics import YOLO
from pathlib import Path
import logging
import sys

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[3]))
from src.infrastructure.config_service import config_service

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def train_yolo():
    """
    Huấn luyện YOLOv11 cho Object Detection (Furniture & Openings).
    """
    # 1. Load Configuration
    conf_threshold = config_service.get('ai.yolo.confidence_threshold', 0.5)
    iou_threshold = config_service.get('ai.yolo.iou_threshold', 0.45)
    model_version = config_service.get('ai.yolo.model_version', 'v11n')
    
    logger.info(f"Initializing YOLO with config: Conf={conf_threshold}, IoU={iou_threshold}, Version={model_version}")

    # 2. Khởi tạo model
    # Note: model weights will be downloaded automatically if not present locally
    model_name = f"yolo{model_version}.pt" if "yolo" not in model_version else f"{model_version}.pt"
    try:
        model = YOLO(model_name)
    except Exception as e:
        logger.error(f"Failed to initialize YOLO model '{model_name}': {e}")
        return

    # 3. Huấn luyện
    data_yaml = Path('data_pipeline/data.yaml')
    
    logger.info("Starting training YOLOv11...")
    
    if data_yaml.exists():
        results = model.train(
            data=str(data_yaml),
            epochs=100,
            imgsz=640,
            conf=conf_threshold,
            iou=iou_threshold,
            device='0' if config_service.get('ai.yolo.use_gpu', True) else 'cpu'
        )
        logger.info(f"YOLO training completed. Results: {results}")
    else:
        logger.warning(f"Data config {data_yaml} not found. YOLO training script verified but skipped execution.")

    # 4. Exporting model
    output_dir = Path("outputs/yolo")
    output_dir.mkdir(parents=True, exist_ok=True)
    # model.export(format='onnx')
    logger.info(f"YOLO training script initialized and ready.")

if __name__ == "__main__":
    train_yolo()
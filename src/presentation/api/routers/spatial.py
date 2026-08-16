"""Router các tính năng KHÔNG GIAN (floorplan -> 3D, depth estimation).

TRẠNG THÁI: TẠM DỪNG. Chỉ được đăng ký khi MOODBITE_ENABLE_SPATIAL=1.

Lý do tách riêng: các tính năng này cần torch/ultralytics (nặng, hay lỗi môi trường) và
đang không nằm trong luồng sản phẩm chính (gợi ý món/quán). Để chung với router chính
khiến app không khởi động được trên máy chưa cài đủ thư viện AI.

Xem docs/architecture_decisions.md trước khi làm tiếp phần này.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from PIL import Image

logger = logging.getLogger("moodbite.spatial")

router = APIRouter(tags=["spatial (paused)"])

YOLO_MODEL_PATH = Path("runs/detect/train/weights/best.pt")
YOLO_HF_URL = (
    "https://huggingface.co/Shmily2004/moodbite-yolo-floorplan/resolve/main/best.pt"
)

_yolo_model = None
_depth_service = None


def _get_yolo():
    """Nạp model lần đầu dùng tới. Không nạp lúc khởi động vì model nặng."""
    global _yolo_model
    if _yolo_model is None:
        from ultralytics import YOLO

        source = str(YOLO_MODEL_PATH) if YOLO_MODEL_PATH.exists() else YOLO_HF_URL
        logger.info("Đang nạp YOLO từ %s", source)
        _yolo_model = YOLO(source)
    return _yolo_model


def _get_depth_service():
    global _depth_service
    if _depth_service is None:
        from src.infrastructure.ai.depth_estimation_service import DepthEstimationService

        _depth_service = DepthEstimationService()
    return _depth_service


async def _read_image(file: UploadFile) -> Image.Image:
    contents = await file.read()
    try:
        return Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Không đọc được ảnh: {exc}")


@router.post("/predict-floorplan")
async def predict_floorplan(file: UploadFile = File(...)):
    """Nhận diện cửa/tường/cửa sổ từ ảnh bản vẽ mặt bằng."""
    image = await _read_image(file)
    try:
        model = _get_yolo()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Không nạp được model YOLO: {exc}")

    predictions = [
        {
            "class": result.names[int(box.cls)],
            "confidence": float(box.conf),
            "bbox": box.xyxy[0].tolist(),
        }
        for result in model(image)
        for box in result.boxes
    ]
    return {
        "status": "success",
        "predictions": predictions,
        "total_detections": len(predictions),
    }


@router.post("/estimate-depth")
async def estimate_depth(file: UploadFile = File(...)):
    """Ước lượng depth map từ 1 ảnh chụp thường.

    LƯU Ý: đây là depth TƯƠNG ĐỐI từ 1 ảnh duy nhất, KHÔNG phải bản scan 3D chính xác.
    """
    image = await _read_image(file)
    try:
        service = _get_depth_service()
        depth_image = service.estimate_depth(image)
        depth_base64 = service.depth_map_to_base64_png(depth_image)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return {
        "status": "success",
        "depth_map_base64_png": depth_base64,
        "image_size": {"width": image.width, "height": image.height},
    }


@router.post("/generate-point-cloud")
async def generate_point_cloud(
    file: UploadFile = File(...),
    max_points: int = Query(default=20000, le=100000),
):
    """Sinh point cloud 3D đơn giản từ 1 ảnh chụp.

    LƯU Ý: dùng camera pinhole giả định (không có thông số camera thật), nên toạ độ mang
    tính minh hoạ cảm giác chiều sâu, KHÔNG chính xác để đo đạc.
    """
    image = await _read_image(file)
    try:
        service = _get_depth_service()
        points = service.generate_point_cloud(image, max_points=max_points)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return {"status": "success", "total_points": len(points), "points": points}

"""
MoodBite - Depth Estimation Service (photo -> depth map -> basic 3D point cloud).

THAY THẾ cho hướng train_segformer.py (SegFormer/CubiCasa5K) cho tính năng "floorplan -> 3D":
input thực tế là ẢNH CHỤP THẬT không gian quán ăn (từ review/chủ quán đăng), không phải
bản vẽ kỹ thuật 2D - nên hướng train custom segmentation model trên blueprint dataset
(CubiCasa5K) không phù hợp (xem thảo luận trong lịch sử conversation).

Dùng Depth Anything V2 - model FOUNDATION đã pretrain sẵn (không cần train lại), nhận
BẤT KỲ ảnh thường nào (góc chụp, ánh sáng bất kỳ) và trả về depth map (ảnh xám thể hiện
điểm nào gần/xa camera). Tích hợp chính thức vào thư viện `transformers` từ 07/2024.

GIỚI HẠN CẦN HIỂU RÕ: đây là depth map TƯƠNG ĐỐI (relative depth) từ 1 ảnh duy nhất,
KHÔNG PHẢI 1 bản scan 3D đầy đủ như ảnh quét LiDAR/nhiều góc chụp. Point cloud sinh ra
dùng model camera pinhole đơn giản (giả định focal length mặc định vì không có thông số
camera thật) - đủ để tạo cảm giác chiều sâu khi xoay xem, KHÔNG đủ chính xác để đo đạc
kích thước thật hay dựng mô hình kiến trúc chính xác.

CÀI ĐẶT:
    pip install transformers torch pillow numpy --break-system-packages
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any

import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"

# Giả định focal length (đơn vị pixel) khi sinh point cloud - vì ảnh review/chủ quán
# đăng không có metadata camera intrinsics thật. Giá trị này là ước lượng hợp lý cho
# ảnh chụp điện thoại góc rộng thông thường, KHÔNG chính xác tuyệt đối.
ASSUMED_FOCAL_LENGTH_PX = 500.0


class DepthEstimationService:
    def __init__(self, model_id: str = MODEL_ID):
        self.model_id = model_id
        self._pipe = None
        self.is_ready = False
        self._load_error: str | None = None

    def _ensure_loaded(self) -> bool:
        """Lazy load - chỉ tải model khi thực sự cần dùng lần đầu, không load ngay
        lúc import module (tránh làm chậm/crash lúc khởi động app nếu mạng có vấn đề,
        đúng nguyên tắc graceful degradation đã áp dụng cho recommendation_service.py)."""
        if self._pipe is not None:
            return True
        if self._load_error is not None:
            return False

        try:
            from transformers import pipeline
            logger.info(f"Đang tải model {self.model_id} (lần đầu có thể mất vài phút)...")
            self._pipe = pipeline(task="depth-estimation", model=self.model_id)
            self.is_ready = True
            logger.info("✅ Depth estimation model đã sẵn sàng.")
            return True
        except Exception as e:
            self._load_error = str(e)
            logger.error(f"Không tải được model depth estimation: {e}")
            return False

    def estimate_depth(self, image: Image.Image) -> Image.Image:
        """Trả về depth map dạng ảnh xám (PIL Image), cùng kích thước ảnh gốc."""
        if not self._ensure_loaded():
            raise RuntimeError(f"Depth estimation model chưa sẵn sàng: {self._load_error}")

        result = self._pipe(image)
        return result["depth"]

    def estimate_depth_array(self, image: Image.Image) -> np.ndarray:
        """Trả về depth map dạng mảng số thực (dùng để sinh point cloud)."""
        if not self._ensure_loaded():
            raise RuntimeError(f"Depth estimation model chưa sẵn sàng: {self._load_error}")

        from transformers import AutoImageProcessor, AutoModelForDepthEstimation
        import torch

        if not hasattr(self, "_processor"):
            self._processor = AutoImageProcessor.from_pretrained(self.model_id)
            self._model = AutoModelForDepthEstimation.from_pretrained(self.model_id)

        inputs = self._processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = self._model(**inputs)
            predicted_depth = outputs.predicted_depth

        prediction = torch.nn.functional.interpolate(
            predicted_depth.unsqueeze(1),
            size=image.size[::-1],
            mode="bicubic",
            align_corners=False,
        )
        return prediction.squeeze().cpu().numpy()

    def generate_point_cloud(
        self, image: Image.Image, max_points: int = 20000
    ) -> list[dict[str, Any]]:
        """Sinh point cloud đơn giản (x, y, z, color) từ 1 ảnh, dùng model camera
        pinhole với focal length giả định. Downsample để giữ response size hợp lý
        cho việc trả về qua API (ảnh gốc có thể có hàng triệu pixel)."""
        depth_array = self.estimate_depth_array(image)
        rgb_array = np.array(image.convert("RGB"))

        h, w = depth_array.shape
        cx, cy = w / 2.0, h / 2.0

        # Downsample: lấy mẫu đều trên lưới thay vì random, giữ được cấu trúc không gian.
        total_pixels = h * w
        stride = max(1, int(np.sqrt(total_pixels / max_points)))

        points = []
        for y in range(0, h, stride):
            for x in range(0, w, stride):
                z = float(depth_array[y, x])
                if z <= 0:
                    continue
                # Chiếu ngược từ pixel (x, y) + depth -> tọa độ 3D (X, Y, Z) qua mô hình
                # pinhole camera: X = (x - cx) * Z / f, Y = (y - cy) * Z / f
                X = (x - cx) * z / ASSUMED_FOCAL_LENGTH_PX
                Y = (y - cy) * z / ASSUMED_FOCAL_LENGTH_PX
                r, g, b = rgb_array[y, x][:3]
                points.append({
                    "x": round(X, 4), "y": round(Y, 4), "z": round(z, 4),
                    "color": f"#{r:02x}{g:02x}{b:02x}",
                })

        return points

    @staticmethod
    def depth_map_to_base64_png(depth_image: Image.Image) -> str:
        """Chuyển depth map thành base64 PNG để trả về qua JSON API."""
        # Chuẩn hóa về 0-255 để hiển thị được như ảnh xám thông thường.
        arr = np.array(depth_image).astype(np.float32)
        arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8) * 255.0
        normalized = Image.fromarray(arr.astype(np.uint8))

        buf = io.BytesIO()
        normalized.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")


depth_estimation_service = DepthEstimationService()

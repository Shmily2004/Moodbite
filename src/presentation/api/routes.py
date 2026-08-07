from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pydantic import BaseModel
from PIL import Image
import io
from pathlib import Path
from src.application.services.recommendation_service import recommendation_service
from src.application.services.depth_estimation_service import depth_estimation_service

router = APIRouter()

# Pydantic models
class RecommendRequest(BaseModel):
    mood: str
    user_lat: float = 21.0285
    user_lng: float = 105.8542
    top_k: int = 5

# Global model cache
model = None

def get_model():
    """Lazy load model on first use"""
    global model
    if model is None:
        try:
            from ultralytics import YOLO
            
            MODEL_PATH = Path("runs/detect/train/weights/best.pt")
            if MODEL_PATH.exists():
                print(f"✅ Loading model from {MODEL_PATH}")
                model = YOLO(str(MODEL_PATH))
            else:
                print(f"❌ Model not found at {MODEL_PATH}")
                print("Trying HuggingFace...")
                model = YOLO("https://huggingface.co/Shmily2004/moodbite-yolo-floorplan/resolve/main/best.pt")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            model = None
    return model

@router.post("/predict-floorplan")
async def predict_floorplan(file: UploadFile = File(...)):
    """
    Detect rooms/objects từ floorplan image
    
    Input: Image file (JPG, PNG)
    Output: Bounding boxes + class names
    """
    model_instance = get_model()
    if model_instance is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        results = model_instance(image)
        
        predictions = []
        for result in results:
            for box in result.boxes:
                predictions.append({
                    "class": result.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": box.xyxy[0].tolist()
                })
        
        return {
            "status": "success",
            "predictions": predictions,
            "total_detections": len(predictions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/recommend")
def recommend(request: RecommendRequest):
    """
    Get restaurant recommendations based on mood
    
    Input: mood (happy, sad, excited, relaxed)
    Output: Top 5 recommended restaurants
    """
    try:
        recommendations = recommendation_service.recommend(
            mood=request.mood,
            user_lat=request.user_lat,
            user_lng=request.user_lng,
            top_k=request.top_k
        )
        
        return {
            "status": "success",
            "mood": request.mood,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/model-info")
def model_info():
    """Get model information"""
    model_instance = get_model()
    if model_instance is None:
        return {"status": "model not loaded"}
    
    return {
        "model": "YOLOv11",
        "task": "object_detection",
        "classes": list(model_instance.names.values()),
        "status": "ready"
    }

@router.get("/moods")
def get_supported_moods():
    """Get list of supported moods"""
    return {
        "supported_moods": ["happy", "sad", "excited", "relaxed"],
        "description": "Use these mood values in POST /api/recommend"
    }


@router.post("/estimate-depth")
async def estimate_depth(file: UploadFile = File(...)):
    """
    Ước lượng depth map (chiều sâu) từ 1 ảnh chụp thật (VD ảnh review/chủ quán đăng).

    Input: Image file (JPG, PNG) - ảnh chụp thường, không cần bản vẽ kỹ thuật.
    Output: depth map dạng ảnh xám (base64 PNG) - pixel càng sáng càng gần camera.

    LƯU Ý: đây là depth TƯƠNG ĐỐI từ 1 ảnh duy nhất (dùng Depth Anything V2, model
    pretrained, không cần train riêng), không phải bản scan 3D chính xác tuyệt đối.
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        depth_image = depth_estimation_service.estimate_depth(image)
        depth_base64 = depth_estimation_service.depth_map_to_base64_png(depth_image)

        return {
            "status": "success",
            "depth_map_base64_png": depth_base64,
            "image_size": {"width": image.width, "height": image.height},
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate-point-cloud")
async def generate_point_cloud(file: UploadFile = File(...), max_points: int = Query(default=20000, le=100000)):
    """
    Sinh point cloud 3D đơn giản (x, y, z, color) từ 1 ảnh chụp thật.

    Input: Image file (JPG, PNG), max_points (giới hạn số điểm trả về, mặc định 20000).
    Output: Danh sách điểm 3D, mỗi điểm có tọa độ (x, y, z) và màu (hex).

    LƯU Ý: dùng camera pinhole giả định (không có thông số camera thật từ ảnh review),
    nên tọa độ mang tính minh họa cảm giác chiều sâu, KHÔNG chính xác để đo đạc thật.
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        points = depth_estimation_service.generate_point_cloud(image, max_points=max_points)

        return {
            "status": "success",
            "total_points": len(points),
            "points": points,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
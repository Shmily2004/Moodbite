from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pydantic import BaseModel
from PIL import Image
import io
from pathlib import Path
from ultralytics import YOLO
from src.application.services.recommendation_service import recommendation_service

router = APIRouter()

# Pydantic models
class RecommendRequest(BaseModel):
    mood: str
    user_lat: float = 21.0285
    user_lng: float = 105.8542
    top_k: int = 5

# Load YOLO model
MODEL_PATH = Path("runs/detect/train/weights/best.pt")

try:
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

@router.post("/predict-floorplan")
async def predict_floorplan(file: UploadFile = File(...)):
    """
    Detect rooms/objects từ floorplan image
    
    Input: Image file (JPG, PNG)
    Output: Bounding boxes + class names
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        results = model(image)
        
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
    if model is None:
        return {"status": "model not loaded"}
    
    return {
        "model": "YOLOv11",
        "task": "object_detection",
        "classes": list(model.names.values()),
        "status": "ready"
    }

@router.get("/moods")
def get_supported_moods():
    """Get list of supported moods"""
    return {
        "supported_moods": ["happy", "sad", "excited", "relaxed"],
        "description": "Use these mood values in POST /api/recommend"
    }
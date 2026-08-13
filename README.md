# MoodBite: From Floorplan to 3D & Personalized Dining

MoodBite is an AI-driven platform that transforms 2D floorplans into immersive 3D environments and provides personalized dish suggestions based on user context and restaurant data.

## 🚀 Project Overview

This project consists of two main pillars:
1.  **AI Spatial Reconstruction:** Converting 2D architectural floorplans into 3D models using Computer Vision (SegFormer for wall segmentation and YOLOv11 for object detection).
2.  **Mood-Based Recommendation:** Suggesting dishes and restaurants based on user "mood" signals extracted from reviews and environmental context.

## 🛠️ Tech Stack

-   **Backend:** Python 3.10+, FastAPI
-   **AI/ML:** PyTorch, Transformers (SegFormer), Ultralytics (YOLOv11), OpenCV
-   **Frontend:** React, Three.js, TypeScript
-   **Architecture:** Clean Architecture (Domain-Driven Design)

## 📁 Project Structure

```text
MoodBite_Project/
├── config/             # Centralized thresholds and configurations
├── data_pipeline/      # Data cleaning, feature engineering, and preprocessing
├── docs/               # Technical documentation and spatial schemas
├── src/
│   ├── domain/         # Core business logic and entities
│   ├── application/    # Use cases and ports
│   ├── infrastructure/ # AI models, adapters, and external services
│   └── presentation/   # API controllers and UI
├── tests/              # Unit and integration tests
└── schema.json         # Authoritative Spatial JSON contract
```

## ⚙️ Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Shmily2004/Moodbite.git
    cd Moodbite
    ```

2.  **Environment Setup:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    Adjust thresholds and AI parameters in `config/thresholds.yaml`.

## 🏃 Execution

### Data Pipeline (Nhà hàng)
```bash
# 1. Gộp các file JSON cào được (Apify/OSM), khử trùng lặp, lọc chỉ đồ ăn cho người
python -m data_pipeline.merge_and_prepare_raw

# 2. Làm sạch dữ liệu
python -m data_pipeline.data_cleaning

# 3. Trích xuất đặc trưng mood-score
python -m data_pipeline.feature_engineering
```

Kết quả: `data_pipeline/data_cleaned/dataset_moodbite_features.csv` — được `CsvRestaurantRepository`/`CsvDishRepository`
(TypeScript) tự động đọc khi khởi động app (`src/config/diContainer.ts`). Nếu file này chưa tồn tại, app tự
fallback về dữ liệu mẫu (`InMemory*Repository`) thay vì lỗi.

Để cào thêm dữ liệu miễn phí từ OpenStreetMap (bổ sung cho Apify):
```bash
python -m data_pipeline.scrape_osm_hanoi
```

### AI Training (Phase 1 - Floorplan → 3D)

Dataset floorplan (CubiCasa5K qua Roboflow, ~5000 ảnh, license CC BY-NC 4.0 - chỉ dùng phi thương mại):
```bash
pip install roboflow --break-system-packages
export ROBOFLOW_API_KEY="your_api_key"   # lấy miễn phí tại roboflow.com
python -m data_pipeline.download_floorplan_dataset
```

Train (khuyến nghị dùng Google Colab để có GPU miễn phí - train trên CPU rất chậm):
```bash
python -m src.infrastructure.ai.train_segformer
python -m src.infrastructure.ai.train_yolo --epochs 3   # test nhanh trước
python -m src.infrastructure.ai.train_yolo               # train full (100 epoch)
```

### Model đã train

Model weight (`.pt`, `.onnx`) **không được commit vào git** (quá nặng, đã `.gitignore`).

Model YOLO (door/wall/window detection, train trên CubiCasa5K) đã được lưu tại HuggingFace Hub:
- Repo: https://huggingface.co/Shmily2004/moodbite-yolo-floorplan
- Tải trực tiếp: https://huggingface.co/Shmily2004/moodbite-yolo-floorplan/resolve/main/best.pt

Tải về để dùng lại (không cần train lại từ đầu):
```bash
curl -L -o best.pt https://huggingface.co/Shmily2004/moodbite-yolo-floorplan/resolve/main/best.pt
```

Upload model mới (sau khi train lại) lên HuggingFace:
```bash
pip install huggingface_hub
python -c "from huggingface_hub import login; login()"
python -m data_pipeline.upload_model_to_hf --file runs/detect/train/weights/best.pt --repo-name moodbite-yolo-floorplan
```

## 🧪 Testing

Run tests using `pytest`:
```bash
pytest
```

## 🍽️ Dish-suggestion (ML-backed) — quickstart

The project includes a lightweight demo for an ML-backed adapter that predicts a
knowledge-base `rule_id` from `categoryName`/`cuisine` and returns dishes from
`data_pipeline/dish_knowledge_base.json`. Use the demo to reproduce the workflow:

1. Ensure the data pipeline has been run and `dataset_moodbite_features.csv` exists:
```bash
python -m data_pipeline.merge_and_prepare_raw
python -m data_pipeline.data_cleaning
python -m data_pipeline.feature_engineering
```

2. Train the simple classifier (demo):
```bash
python scripts/train_dish_classifier.py
```

3. Quick demo of predictions:
```bash
python scripts/predict_dish_from_model.py
```

4. Run the service-level smoke demo (calls `DishRecommendationService`):
```bash
python scripts/run_suggest_demo.py
```

Notes:
- The ML model is a lightweight TF-IDF + LogisticRegression demo saved to `models/`.
- The runtime service prefers ML rule assignment when the model is available and
    falls back to the rule-based KB matching.


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

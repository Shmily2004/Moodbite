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

### Data Pipeline
```bash
python data_pipeline/data_cleaning.py
python data_pipeline/feature_engineering.py
```

### AI Training (Phase 1)
```bash
python src/infrastructure/ai/train_segformer.py
python src/infrastructure/ai/train_yolo.py
```

## 🧪 Testing

Run tests using `pytest`:
```bash
pytest
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

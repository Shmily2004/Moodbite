# Traceability Matrix - MoodBite

## Phase 0: Infrastructure & Standards

| ID | Requirement | Implementation | Validation |
|---|---|---|---|
| R0.1 | Standard Folder Structure | Repository Root | Manual Review |
| R0.2 | Centralized Configuration | `config/thresholds.yaml`, `src/infrastructure/config_service.py` | `tests/test_config.py` |
| R0.3 | Coding Standards | `CODING_STANDARDS.md` | Linter Config (ruff) |
| R0.4 | Spatial JSON Contract | `schema.json`, `docs/spatial_schema.md` | `tests/test_schema.py` |
| R0.5 | Git Cleanliness | `.gitignore` | Manual Review |

## Phase 1: Data Pipeline & AI Foundations

| ID | Requirement | Implementation | Validation |
|---|---|---|---|
| R1.1 | Data Cleaning Pipeline | `data_pipeline/data_cleaning.py` | `tests/test_data_pipeline.py` |
| R1.2 | Feature Engineering | `data_pipeline/feature_engineering.py` | `tests/test_data_pipeline.py` |
| R1.3 | Floorplan Preprocessing | `data_pipeline/floorplan_preprocessing.py` | `tests/test_preprocessing.py` |
| R1.4 | Wall Segmentation (SegFormer) | `src/infrastructure/ai/train_segformer.py` | ABANDONED (see notes)
| R1.5 | Object Detection (YOLOv11) | `src/infrastructure/ai/train_yolo.py` | ABANDONED (see notes)
| R1.6 | Annotation Guidelines | `docs/labeling_guidelines.md` | Manual Review |

## Phase 2: Spatial Reconstruction & Suggester (Future)

| ID | Requirement | Implementation | Validation |
|---|---|---|---|
| R2.1 | Spatial JSON Generation | TBD | PAUSED/ARCHIVED (blueprint-based approach abandoned)
| R2.2 | 3D Frontend (Three.js) | TBD | PAUSED/NOT PRIORITY
| R2.3 | Suggestion Engine | `src/application/use-cases/SuggestDishForUserUseCase.ts` | ACTIVE (see tests & deployment)

## Status Update (2026-08-13)
- Blueprint-based Floorplan → Spatial JSON → 3D pipeline (SegFormer + YOLO on CubiCasa5K) is ABANDONED: training on architectural blueprints does not transfer to real photos used by the product.
- Photo→3D experiments using Depth Anything V2 (`src/application/services/depth_estimation_service.py`) were TRIED but are currently PAUSED due to environment issues and product prioritization.
- Primary focus is Recommendation Engine using `data_pipeline/data_cleaned/dataset_moodbite_features.csv` and corresponding TypeScript/Python implementations.

Notes: rely on git commit history and deployed services as source-of-truth rather than older markdown requirements.

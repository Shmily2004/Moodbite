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
| R1.4 | Wall Segmentation (SegFormer) | `src/infrastructure/ai/train_segformer.py` | Model Init Tests |
| R1.5 | Object Detection (YOLOv11) | `src/infrastructure/ai/train_yolo.py` | Model Init Tests |
| R1.6 | Annotation Guidelines | `docs/labeling_guidelines.md` | Manual Review |

## Phase 2: Spatial Reconstruction & Suggester (Future)

| ID | Requirement | Implementation | Validation |
|---|---|---|---|
| R2.1 | Spatial JSON Generation | TBD | TBD |
| R2.2 | 3D Frontend (Three.js) | TBD | TBD |
| R2.3 | Suggestion Engine | `src/application/use-cases/SuggestDishForUserUseCase.ts` | TBD |

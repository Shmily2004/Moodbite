# Trạng thái dự án - MoodBite (Cập nhật: 2026-08-13)

## 📅 Current Status: Phase 1 (Data Pipeline & ML Foundations)

### ✅ Phase 0: Infrastructure & Standards (COMPLETED)
- **Repo Structure:** Clean Architecture established (`src/config/di.py`).
- **Standards:** `CODING_STANDARDS.md` and `.gitignore` finalized.
- **Config:** `ConfigService` and `thresholds.yaml` implemented for centralized management.
- **Schema:** `schema.json` and `docs/spatial_schema.md` synchronized.

### 🚧 Phase 1: Data Pipeline & Recommendation Engine (ACTIVE)
- **Data Cleaning & Feature Engineering:** 
    - `data_pipeline/feature_engineering.py` fixed and ran successfully. 
    - Output: `dataset_moodbite_features.csv` (4169 records). 
    - **Coverage:** 98.08% of records have at least one mood-score > 0 (up from ~52.3%).
- **Machine Learning & Recommendation (PRIMARY FOCUS):** 
    - Prototype ML pipeline (`scripts/train_dish_classifier.py`) implemented (TF-IDF + LogisticRegression).
    - Holdout test accuracy: **0.9856**.
    - ML Adapter + DI integrated (`src/infrastructure/adapters/ml_dish_adapter.py`, `src/application/services/dish_recommendation_service.py`).
- **Floorplan / Photo→3D work (ABANDONED/PAUSED):**
    - Legacy scripts (`train_segformer.py`, `train_yolo.py`) remain but original CubiCasa5K approach is ABANDONED.
    - Depth Anything V2 approach (`depth_estimation_service.py`) is PAUSED due to environment issues. Do NOT prioritize 3D frontend work now.

### ⚠️ Risks & Limitations
- **Model in Repo:** The demo model (`models/dish_rule_classifier.joblib`) was accidentally committed. It must be removed from Git to avoid bloating the repo.
- **Test Suite Issues:** `pytest` has collection errors due to module naming/duplicate folders. Needs fixing for CI automation.
- **Scope drift / outdated docs:** Some docs (SRS, spatial schema) describe the old blueprint direction. They are outdated.
- **ML Adapter robustness:** Needs better logging, metrics, error handling (corrupt/missing model), and unit tests for fallback logic.

### ⏭️ Next Practical Steps (Prioritized)
1. **Git Cleanup (URGENT):** Remove the `.joblib` model artifact from git tracking, add `models/` to `.gitignore`, and create `scripts/download_model.py`.
2. **Fix Test Suite & CI:** Resolve `pytest` collection issues and setup GitHub Actions (CI) to run lint + tests automatically.
3. **Enhance ML Adapter:** Write unit tests for missing file, corrupt file, and fallback KB.
4. **Dataset Expansion:** Use `enhanced_osm_query.py` to expand dataset (bbox `20.85,105.70,21.40,106.05` for Hanoi) when needed.
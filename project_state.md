# Project State - MoodBite

## 📅 Current Status: Phase 1 (Data Pipeline & AI Foundations)
### ✅ Phase 0: Infrastructure & Standards (COMPLETED)
- **Repo Structure:** Clean Architecture established.
- **Standards:** `CODING_STANDARDS.md` and `.gitignore` finalized.
- **Config:** `ConfigService` and `thresholds.yaml` implemented for centralized management.
- **Schema:** `schema.json` and `docs/spatial_schema.md` synchronized for Spatial JSON v1.0.

### 🚧 Phase 1: Data Pipeline & Recommendation Engine (ACTIVE)

- **Data Cleaning:** `data_pipeline/data_cleaning.py` implemented with automated filtering (active).
- **Feature Engineering:** `data_pipeline/feature_engineering.py` implements mood lexicon scoring (active).
- **Recommendation Engine (PRIMARY FOCUS):** 
    - Core logic in `src/application/use-cases/SuggestDishForUserUseCase.ts` and `src/application/services/recommendation_service.py` (deployed).
    - Recent commit `54fab2b` expanded mood-score using `cuisine` and added rating as tie-breaker.
- **Floorplan / Photo→3D work:**
    - Legacy scripts `src/infrastructure/ai/train_segformer.py` and `src/infrastructure/ai/train_yolo.py` remain in the repo but the original plan to train on CubiCasa5K and generate Spatial JSON/Three.js has been ABANDONED (see rationale below).
    - Alternative Photo→3D approach (`Depth Anything V2`) was TRIED (`src/application/services/depth_estimation_service.py`) but is currently PAUSED due to environment and priority decisions.

**Testing:** Base test suite remains and should be used as the canonical health check (see next steps).

### 🔍 Evidence of Progress & Current Decisions
- `ConfigService` and data pipeline tests present and maintained.
- `dataset_moodbite_features.csv` contains ~4180 real Hanoi restaurants and is the primary data source for recommendations.
- Photo→3D via blueprint-based training (SegFormer/YOLO on CubiCasa5K) was found to be a mismatched approach for real photos and is ABANDONED.
- Depth Anything V2 experiments exist but are PAUSED; code kept for future re-evaluation (`/api/estimate-depth`, `/api/generate-point-cloud`).

### ⚠️ Risks & Limitations (Updated)
- **Scope drift / outdated docs:** Some docs (SRS, spatial schema, labeling guidelines) describe an earlier blueprint-based direction — they are outdated and must not be used as the source of truth for current work.
- **Environment issues:** Depth Anything experiments failed due to environment (`Could not import module 'pipeline'`); these are paused and not blocking recommendation work.
- **Data quality:** Recommendation logic depends on `dataset_moodbite_features.csv` completeness (watch for missing `categoryName`/`placeId`).

### ⏭️ Next Practical Steps (Prioritized)
1. Treat recommendation pipeline as PRIMARY: continue improving mood-score, ranking, and dataset quality.
2. Run and fix tests/typechecks: `pytest` and `npx tsc --noEmit` are the canonical verification steps.
3. Use `data_pipeline/scrapers/enhanced_osm_query.py` to expand dataset with bbox `20.85,105.70,21.40,106.05` for Hanoi when needed.
4. Keep Photo→3D artifacts archived for later; do NOT prioritize training or 3D frontend work now.

---
_Edited 2026-08-13: Updated to reflect current project pivot and priorities._

# Trạng thái dự án - MoodBite (Cập nhật: 2026-08-13)

## 📅 Current Status: Phase 1 (Data Pipeline & ML Foundations)

### ✅ Phase 0: Infrastructure & Standards (COMPLETED)
- **Repo Structure:** Clean Architecture established (`src/config/di.py`).
- **Standards:** `CODING_STANDARDS.md` and `.gitignore` finalized.
- **Config:** `ConfigService` and `thresholds.yaml` implemented for centralized management.
- **Schema:** `schema.json` and `docs/spatial_schema.md` synchronized.

### 🚧 Phase 1: Data Pipeline & Recommendation Engine (ACTIVE)
- **Data Cleaning & Feature Engineering:**
    - `data_pipeline/feature_engineering.py` đã được sửa (giữ lại cột `cuisine`) và chạy thành công.
    - File features: `data_pipeline/data_cleaned/dataset_moodbite_features.csv` — Row count: **4169** (verified).
    - Mood-score coverage: **98.08%** (4089/4169) — verified.
    - Verification (commands & raw outputs):

```
Get-ChildItem data_pipeline/data_raw/:
Mode          LastWriteTime   Length Name                           
----          -------------   ------ ----                           
-a----   8/7/2026   5:15 PM   146979 01_raw_places.json             
-a----   8/7/2026   5:15 PM 12043919 02_raw_places.json             
-a----   8/7/2026   5:15 PM 10836649 03_raw_places.json             
-a----  8/11/2026  10:02 AM  3107321 04_raw_places_osm.json         
-a----  8/11/2026  10:23 AM   165222 04_raw_places_osm_enhanced.json
-a----  8/13/2026   2:03 PM 16141064 merged_places.csv              

git diff --stat data_pipeline/data_cleaned/dataset_moodbite_features.csv:
(no output — working-tree CSV matches committed CSV)

Committed (HEAD) row count:
HEAD_ROWS:4169

Remote (origin/main) row count:
ORIGIN_MAIN_ROWS:4169

Script output (fresh run / verification):
FILE: data_pipeline/data_cleaned/dataset_moodbite_features.csv
ROWS: 4169
MOOD_COLS: ['comfort_cozy_score', 'spicy_hot_score', 'fresh_healthy_score', 'cheap_budget_score', 'quick_fast_score']
ROWS_WITH_MOOD_GT0: 4089
PCT_WITH_MOOD_GT0:98.08%
```

    - Note: `git diff --stat` produced no differences, and both `HEAD` and `origin/main` have 4169 rows. This indicates the regenerated 4169-row CSV is not a local regression from missing raw files on this machine; it matches the committed & remote state.
    - Dish-first: `dish_recommendation_service.py` + `dish_knowledge.py`/`dish_knowledge_base.json` (Python) và `CsvDishRepository.ts`/`DishKnowledgeBase.ts` (TS) — đã verify chạy được với dữ liệu thật.
    - ML adapter (`ml_dish_adapter.py`) và script train (`train_dish_classifier.py`) ĐÃ BỊ GỠ BỎ — model cũ bị lỗi rò rỉ nhãn (label suy ra trực tiếp từ chính input), độ chính xác 98.56% không có giá trị thật.
    - Tests: `pytest` — 14/14 pass khi chạy TOÀN BỘ cùng lúc (đã verify, không phải từng file riêng lẻ).
- **Floorplan / Photo→3D work (ABANDONED/PAUSED):**
    - Legacy scripts (`train_segformer.py`, `train_yolo.py`) còn tồn tại nhưng hướng CubiCasa5K đã bị BỎ.
    - Depth Anything V2 (`depth_estimation_service.py`) TẠM DỪNG do lỗi môi trường. Đừng ưu tiên làm tiếp phần 3D.

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
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
    - File features: `data_pipeline/data_cleaned/dataset_moodbite_features.csv` — SỐ BẢN GHI CẦN XÁC NHẬN LẠI (đã thấy 2 con số khác nhau ở các thời điểm: 4169 và 4180 — kiểm tra thật trước khi ghi chính thức).
    - Tỷ lệ mood-score > 0: con số 98.08% CHƯA được verify lại trong phiên gần nhất — cần tự kiểm tra trước khi coi là chính thức.
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
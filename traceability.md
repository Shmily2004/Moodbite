# Ma trận truy vết — MoodBite

**Cập nhật:** 2026-08-19.
**Nguyên tắc:** mỗi dòng chỉ được ghi file **THẬT SỰ TỒN TẠI** và test **THẬT SỰ CHẠY**.

> ⚠️ **Vì sao file này bị viết lại toàn bộ (2026-08-19).**
> Bản cũ ghi 10 đường dẫn thì **9 cái không tồn tại** (`config/thresholds.yaml`,
> `tests/test_config.py`, `schema.json`, `data_pipeline/floorplan_preprocessing.py`…),
> và dòng R2.3 còn trỏ tới `src/application/use-cases/SuggestDishForUserUseCase.ts` —
> file TypeScript của backend cũ đã bị gỡ — kèm trạng thái "ACTIVE (see tests &
> deployment)". Đó đúng là loại tài liệu mà CLAUDE.md mục 0 cảnh báo: **tin code chạy
> được, đừng tin tài liệu**. Kiểm lại đường dẫn bằng:
> ```powershell
> python scripts/verify.py
> ```

---

## Luồng chính — chọn món trước, tìm quán sau

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| D1.1 | Bộ lọc trang chủ → danh sách MÓN | `src/presentation/api/routers/dishes.py` · `src/application/use_cases/suggest_dishes.py` | `tests/test_dish_api.py` |
| D1.2 | Quy tắc lọc & xếp hạng món | `src/domain/services/dish_ranking.py` | `tests/test_dish_ranking.py` |
| D1.3 | Tổng trọng số xếp hạng = 1.0 | `dish_ranking.W_*` | `test_weights_sum_to_one` |
| D1.4 | Món thiếu dữ liệu KHÔNG bị loại | `dish_ranking._passes_hard_filter` | `test_hard_filter_keeps_dish_with_missing_data` |
| D1.5 | Ẩn món 0 quán **và nói rõ đã ẩn** | `suggest_dishes._drop_dead_ends` | `test_dish_without_nearby_restaurant_is_hidden_and_announced` |
| D2.1 | Giới thiệu ngắn về món | `src/domain/entities/dish.py` (`description`, `has_description`) | `test_dish_detail_returns_short_intro` |
| D2.2 | Phân biệt "chưa tra được" với "không có gì" | `Dish.has_description` | `test_blank_description_counts_as_missing` |
| D3.1 | Món → quán bán món đó | `src/application/use_cases/find_restaurants_for_dish.py` | `test_restaurants_for_dish_returns_matching_restaurants` |
| D3.2 | Đối chiếu món ↔ quán (tên, loại hình) | `src/domain/services/dish_matching.py` | `test_phrase_does_not_span_name_and_category_boundary` |
| D3.3 | Trích món từ **nội dung review** (đề án mục 7) | `dish_matching._matching_dish_ids_in_review` | `test_review_mention_links_dish_to_restaurant` |
| D3.4 | Nới bán kính thì phải **nói ra** | `find_restaurants_for_dish._warn_if_radius_was_widened` | `test_far_restaurant_is_shown_but_the_widened_radius_is_announced` |
| D4.1 | Mã lỗi riêng cho món | `src/presentation/api/envelope.py` (`DISH_NOT_FOUND`) | `test_unknown_dish_returns_404_with_its_own_code` |

## Dữ liệu

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| R1.1 | Làm sạch dữ liệu | `data_pipeline/data_cleaning.py` | `tests/test_data_pipeline.py` |
| R1.2 | Sinh đặc trưng | `data_pipeline/feature_engineering.py` | `tests/test_data_pipeline.py` |
| R1.3 | Hợp đồng chung cho mọi nguồn | `data_pipeline/sources/base.py` | `tests/test_data_sources.py` |
| R1.4 | Thu thập quán (OSM, nhiều thành phố) | `data_pipeline/sources/osm_overpass.py` (`CITY_BBOXES`) | `tests/test_data_sources.py` |
| R1.5 | Dựng danh mục món | `scripts/build_dish_catalog.py` | chạy tay, có báo cáo số đo |
| R1.6 | Tìm món mới từ Wikipedia | `scripts/discover_dishes.py` | chạy tay, ghi `data_pipeline/data_cleaned/dish_candidates.json` |
| R1.7 | Giới thiệu + ảnh món | `data_pipeline/sources/wikipedia_dish.py` | chạy tay |
| R1.8 | Theo dõi dung lượng | `scripts/disk_report.py` | chạy tay |

## Lối vào thứ hai — tìm quán bằng câu tự nhiên

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| R2.1 | Tìm kiếm + xếp hạng quán | `src/application/use_cases/search_restaurants.py` | `tests/test_use_cases.py`, `tests/test_api.py` |
| R2.2 | Công thức xếp hạng quán | `src/domain/services/search_ranking.py` | `tests/test_domain_ranking.py` |
| R2.3 | Gợi ý món kèm mỗi quán | `search_restaurants._suggest_dish` | `tests/test_use_cases.py` |
| R2.4 | Chi tiết quán (review, ảnh, giá) | `src/application/use_cases/get_restaurant_details.py` | `tests/test_api.py` |

## Năm lớp mô hình của đề án

| Lớp | Trạng thái | Ở đâu |
|---|---|---|
| 1. Phân cụm trải nghiệm | ✅ KMeans k=7 | `data_pipeline/clustering.py` |
| 2. Tìm kiếm ngữ nghĩa | ✅ TF-IDF cosine | `src/infrastructure/adapters/tfidf_semantic_search.py` |
| 3. Xếp hạng ngữ cảnh | 🟡 công thức trọng số cố định | `src/domain/services/search_ranking.py` |
| 4. Tóm tắt review | ❌ chưa làm | — |
| 5. Gợi ý món | ✅ **là cửa vào chính** | `src/domain/services/dish_ranking.py` |

## Nền tảng

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| R0.1 | Hướng phụ thuộc Clean Architecture | `src/` (4 tầng) | `scripts/check_architecture.py` |
| R0.2 | Cấu hình tập trung | `src/infrastructure/config/settings.py` | `tests/test_repositories.py` |
| R0.3 | Chuẩn viết code | `CODING_STANDARDS.md`, `CLAUDE.md` | đọc tay |
| R0.4 | Kiến trúc frontend FSD | `frontend/apps/*/src/` | `npx steiger ./src` |
| R0.5 | Một backend duy nhất | `src/` | `scripts/verify.py` mục 4 |

## Đã DỪNG — không còn trong luồng chạy

| ID | Việc | Trạng thái |
|---|---|---|
| X1 | Floorplan → Spatial JSON → 3D (SegFormer + YOLO) | **BỎ** — train trên bản vẽ kiến trúc không chuyển được sang ảnh chụp thật. Code ở `archive/spatial-3d/`; 210MB ảnh còn ở `data_pipeline/data_raw/floorplans_yolo` (xoá được) |
| X2 | Photo → 3D bằng Depth Anything V2 | **TẠM DỪNG** |
| X3 | Backend TypeScript song song | **BỎ** — ở `archive/typescript-backend/`. Đây là lý do bản cũ của file này trỏ vào file `.ts` không còn tồn tại |

# Trạng thái dự án - MoodBite (Cập nhật)

**Cập nhật:** 2026-08-13

## Tóm tắt hiện trạng (thực tế)

- `data_pipeline/feature_engineering.py` đã được sửa (loại PowerShell wrapper) và chạy thành công.
- File features sinh ra: `data_pipeline/data_cleaned/dataset_moodbite_features.csv` — Tổng bản ghi: **4169**.
- Tỷ lệ bản ghi có ít nhất một mood-score > 0: **98.08%** (trước: ~52.3%).
- Đã thử nghiệm pipeline huấn luyện mẫu cho gợi ý món ăn: `scripts/train_dish_classifier.py` — Test accuracy (holdout): **0.9856**.
- Mô hình demo được lưu: `models/dish_rule_classifier.joblib` (hiện đang được commit trong repo — xem phần hành động tiếp theo).
- Clean Architecture: `src/config/di.py` (DI), `src/infrastructure/adapters/ml_dish_adapter.py` (ML adapter) và `src/application/services/dish_recommendation_service.py` đã được cập nhật để hỗ trợ luồng ML/KB.
- Tests: Thêm và chạy chọn lọc `tests/test_ml_dish_adapter.py` và `tests/test_dish_recommendation_service.py` (passed khi chạy từng file).
- Git: Các thay đổi đã được commit và push lên `origin/main`.

## Việc đã hoàn thành (gần đây)

- Sửa và chạy lại feature engineering → tạo `dataset_moodbite_features.csv` với coverage tăng mạnh.
- Thêm prototype ML pipeline (TF-IDF + LogisticRegression) và lưu artifact mẫu.
- Tích hợp adapter ML + DI và cập nhật `DishRecommendationService` để dùng `predict_rule_id()`.
- Viết các script demo và test smoke; commit & push thay đổi.

## Vấn đề hiện tại & rủi ro

- Mô hình demo (`models/dish_rule_classifier.joblib`) đang trong git — không nên để artifact huấn luyện trong repo cho môi trường production.
- `pytest` toàn bộ chưa chạy sạch do xung đột tên module/tests (khi có nhiều bản sao repo cùng lúc) — cần fix để CI chạy tự động.
- ML adapter cần được hoàn thiện: logging, metrics, xử lý lỗi (corrupt/missing model), và unit tests cho fallback.

## Hành động ưu tiên đề xuất (next steps)

1. Loại bỏ artifact mô hình khỏi git, thêm `models/` vào `.gitignore`, và cung cấp script tải/mô phỏng mô hình.

   Gợi ý lệnh để thực hiện ngay (chạy trong thư mục repo):

```bash
git rm --cached models/dish_rule_classifier.joblib
echo "models/" >> .gitignore
git add .gitignore
git commit -m "chore: remove model artifact and ignore models/"
git push
```

2. Thêm script `scripts/download_model.py` hoặc hướng dẫn trong README để người dev có thể tái tạo/tải mô hình (HuggingFace/artifacts).
3. Viết unit tests bổ sung cho ML adapter: missing file, corrupt file, fallback KB.
4. Sửa test-collection issues để `pytest` chạy toàn bộ test suite trong CI (đặt tên test rõ ràng, loại trừ thư mục duplicate).
5. Thiết lập CI (GitHub Actions) để chạy lint + `pytest` + kiểm tra model-presence (optional: build artifact step).

## Nhiệm vụ tiếp theo tôi có thể làm ngay (bạn cho phép)

- A. Thực hiện các lệnh git trên (loại bỏ model khỏi commit và update `.gitignore`) rồi push.
- B. Tạo `scripts/download_model.py` + cập nhật `README.md` hướng dẫn tải hoặc tái huấn luyện.
- C. Thêm unit tests cho ML adapter và chạy `pytest` toàn bộ để xác thực.
- D. Tạo workflow CI cơ bản (GitHub Actions) để chạy tests và báo lỗi khi `pytest` fail.

Vui lòng cho biết bạn muốn tôi bắt đầu với bước nào (A/B/C/D), tôi sẽ tiếp tục tự động.

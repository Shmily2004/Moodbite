# Lưu trữ: tải model phân loại món (đã gỡ)

Chuyển vào đây ngày 2026-10-06. Hai file này KHÔNG còn chạy được:

- `download_model.yml` (từng ở `.github/workflows/`): workflow thủ công tải
  `models/dish_rule_classifier.joblib`. Dùng `actions/setup-python@v4` (cũ).
- `download_model.py` (từng ở `scripts/`): script tải model, và khi không có URL thì
  hướng dẫn chạy `scripts/train_dish_classifier.py` — file đó KHÔNG tồn tại trong repo.

Lý do gỡ: model cũ bị rò rỉ nhãn nên đã bỏ (xem README.md gốc, mục "Model ML gợi ý
món"); gợi ý món hiện dùng khớp từ khoá (`dish_seed_manual.json`). Giữ lại để tham khảo,
không khôi phục nếu chưa hỏi chủ dự án (CLAUDE.md mục −1/8).

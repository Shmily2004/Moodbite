## Quyết định kiến trúc (đã chốt)

Các quyết định sau đây đã được thống nhất — KHÔNG thay đổi mà không hỏi user trước.

1. Photo→3D và Web UI: **đang tiến triển** — frontend features (including floorplan upload) are expected to continue development; do not leave the docs claiming the UI is paused.
2. `totalScore` KHÔNG `fillna(0)` — để null khi không có rating thật (NaN → `null` tầng ứng dụng).
3. Kết quả đề xuất giới hạn: `DEFAULT_MAX_RESULTS = 20` (TypeScript) / `top_k=5` mặc định (Python).
4. Nguồn data ưu tiên: Apify + OpenStreetMap (bbox chuẩn: `20.85,105.70,21.40,106.05`).
5. Mọi script cào OSM mới PHẢI có `categoryName` và `placeId` trong output.
6. Cấu trúc thư mục: mọi script cào dữ liệu nằm trong `data_pipeline/` hoặc `data_pipeline/scrapers/`.
7. Rating dùng làm tiêu chí PHỤ (tiebreaker) khi mood-score hòa, KHÔNG thay thế mood-score làm tiêu chí chính.

### Ghi chú vận hành & lỗi đã gặp

- Khi cài dependency trên môi trường công ty, dùng `python -m pip install` nếu `pip install` bị chặn.
- Tránh copy-paste code dài qua Notepad để không bị mojibake; gửi file trực tiếp và verify encoding UTF-8.
- Git ignore: dùng `dir/*` nếu thư mục cha bị exclude.
- Nếu pandas bị lỗi trên môi trường dev: xóa thư mục site-packages pandas và cài lại với `--force-reinstall --no-cache-dir`.
- Khi sửa TypeScript, không gán field tạm trực tiếp vào DTO đã định nghĩa; dùng type trung gian rồi `.map()` để loại bỏ field tạm.

### Quy trình kiểm tra trước khi merge

- Luôn chạy `git clone` sạch rồi `pytest tests/` và `npx tsc --noEmit`.
- Kiểm thử các trường hợp biên: null/NaN, các giá trị thiếu `placeId`/`categoryName`, mood-score hòa.

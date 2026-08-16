# Scraper cũ — ĐÃ NGỪNG DÙNG

Giữ lại để tham khảo lịch sử. **Không chạy, không khôi phục nếu chưa bàn lại.**

## Bị thay thế bởi kiến trúc mới

| File cũ | Thay bằng | Lý do |
|---|---|---|
| `scrape_osm_hanoi.py` | `data_pipeline/sources/osm_overpass.py` | Bản mới có chia ô, đổi mirror, thử lại, cache, và lấy nhiều tag hơn hẳn |
| `enhanced_osm_query.py` | `data_pipeline/sources/osm_overpass.py` | Gộp làm một adapter duy nhất, hết trùng lặp |

## Gỡ bỏ vì VI PHẠM ĐIỀU KHOẢN SỬ DỤNG

| File | Nguồn | Vấn đề |
|---|---|---|
| `foody_parser.py` | Foody.vn | ToS cấm truy cập tự động / sao chép có hệ thống |
| `toididau_parser.py` | Toididay | ToS cấm |
| `master_restaurant_pipeline.py` | điều phối 2 file trên | — |

Đồ án tốt nghiệp không nên xây trên nền vi phạm ToS — đây là điểm rất dễ bị hỏi khi bảo vệ.

Phương án hợp pháp thay thế cho cùng nhu cầu (menu, giá, review): xem
[`docs/data_sources.md`](../../docs/data_sources.md) mục 3.

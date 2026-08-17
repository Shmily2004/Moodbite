# Floorplan → 3D (CubiCasa5K + YOLO/SegFormer + Depth Anything) — ĐÃ TẠM DỪNG

**Chuyển vào đây:** 2026-08-17 · **Trạng thái trước đó:** tắt mặc định
(`MOODBITE_ENABLE_SPATIAL=1` mới bật)

## Vì sao chuyển đi

Không phải vì code hỏng. Code vẫn chạy được. Lý do là **chi phí duy trì không tương xứng
với giá trị**:

Tính năng này kéo theo **8 thư viện** mà phần còn lại của MoodBite không hề dùng:

| Thư viện | Chỉ dùng ở |
|---|---|
| `torch`, `transformers`, `ultralytics` | `src/ai/` (train + suy luận) |
| `opencv-python-headless` | `data_pipeline/floorplan_preprocessing.py` |
| `Pillow` | `spatial_router.py`, `depth_estimation_service.py` |
| `python-multipart` | upload ảnh ở `spatial_router.py` |
| `PyYAML` | `config_service.py` |
| `jsonschema` | `tests/test_schema.py` |

Cộng lại khoảng **2GB**, và CI phải tải về ở **mọi lần chạy** — cho code không endpoint
nào đang gọi. `requirements.txt` từ 15 dòng còn 7.

Ngoài ra `config_service.py` chứa một **singleton cấp module** (`config_service =
ConfigService()` ở cuối file) — đúng thứ `CLAUDE.md` mục 6 cấm, vì nó đọc file ngay lúc
import và làm test khó. Nó chỉ tồn tại để phục vụ 2 script train ở đây.

## Có gì trong này

```
archive/spatial-3d/
├── src/
│   ├── ai/                      train_yolo.py, train_segformer.py,
│   │                            depth_estimation_service.py
│   ├── spatial_router.py        router cũ: src/presentation/api/routers/spatial.py
│   └── config_service.py        cũ: src/infrastructure/config/config_service.py
├── data_pipeline/               floorplan_preprocessing.py,
│                                download_floorplan_dataset.py, demo_depth_pipeline.py
├── config/thresholds.yaml       ngưỡng cho YOLO/SegFormer + độ dày tường
├── tests/                       test_config.py, test_schema.py, test_preprocessing.py
└── schema.json                  lược đồ JSON của bản vẽ mặt bằng
```

## Muốn khôi phục thì làm gì

Đọc `docs/spatial_schema.md` và `docs/architecture_decisions.md` trước — ở đó ghi vì sao
hướng này bị dừng (Depth Anything V2 lỗi môi trường).

Nếu vẫn quyết định làm tiếp:

1. `git mv` các file về đúng chỗ cũ (xem bảng trên).
2. Thêm lại 8 thư viện vào `requirements.txt`.
3. Thêm lại `enable_spatial_features` vào `src/infrastructure/config/settings.py` và
   phần `include_router` trong `src/presentation/api/main.py`.
4. **BẮT BUỘC trước khi viết thêm code:** tạo port `DepthEstimator` ở
   `src/application/ports/` — bản cũ gọi thẳng `depth_estimation_service` từ router,
   tức là `presentation` phụ thuộc trực tiếp `infrastructure`, sai hướng phụ thuộc.
   Đó là khoản nợ kỹ thuật đã được ghi nhận trong `scripts/check_architecture.py`.
5. Bỏ singleton cấp module trong `config_service.py`, đưa qua `dependencies.py`.

## Lịch sử vẫn còn nguyên

Không có gì bị xoá. `git log --follow <đường-dẫn-cũ>` vẫn xem được toàn bộ lịch sử.

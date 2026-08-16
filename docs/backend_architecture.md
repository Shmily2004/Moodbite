# Kiến trúc Backend — MoodBite

Tài liệu này giải thích **code nằm ở đâu và vì sao**. Đọc file này trước khi sửa backend.

---

## 1. Bốn tầng

```
        ┌─────────────────────────────────────────┐
        │  presentation/   HTTP, FastAPI, schema  │
        └───────────────────┬─────────────────────┘
                            │
        ┌───────────────────▼─────────────────────┐
        │  application/     use case + port        │
        └───────────────────┬─────────────────────┘
                            │
        ┌───────────────────▼─────────────────────┐
        │  domain/          quy tắc nghiệp vụ      │  ← thuần Python
        └─────────────────────────────────────────┘
                            ▲
        ┌───────────────────┴─────────────────────┐
        │  infrastructure/  CSV, JSON, ML          │
        └─────────────────────────────────────────┘
```

**Mũi tên luôn chỉ vào trong.** `domain/` không biết gì về ba tầng còn lại — đó là điểm mấu
chốt khiến quy tắc nghiệp vụ test được trong vài mili-giây, không cần file, không cần server.

Kiểm tra tự động: `python scripts/check_architecture.py` (chạy trong CI).

---

## 2. Trách nhiệm từng tầng

### `domain/` — quy tắc nghiệp vụ
Thuần Python. **Cấm** import `fastapi`, `pandas`, `torch`, `pydantic`.

| File | Nội dung |
|---|---|
| `value_objects/mood.py` | 4 mood, bảng trọng số `MOOD_PROFILES` |
| `value_objects/location.py` | Toạ độ + khoảng cách haversine |
| `value_objects/context_signal.py` | Thời tiết/giờ ăn ảnh hưởng xếp hạng thế nào |
| `value_objects/text.py` | Bỏ dấu + khớp từ nguyên vẹn (dùng chung) |
| `entities/restaurant.py` | Quán ăn, cách tính điểm mood |
| `entities/dish.py` | Món ăn, rule món ăn |
| `entities/interaction.py` | Sự kiện tương tác, quy tắc `is_positive_signal` |
| `services/search_ranking.py` | **Công thức xếp hạng tổng hợp** (Lớp 3) |
| `services/text_relevance.py` | Khớp câu tự do với quán (Lớp 2) |

> Muốn đổi cách gợi ý hoạt động → gần như luôn là sửa ở đây.

### `application/` — điều phối
| Thư mục | Nội dung |
|---|---|
| `ports/` | **Hợp đồng** (Protocol). Không có code thật. Nói "tôi cần thứ biết `list_all()`", không quan tâm nó đọc CSV hay PostgreSQL |
| `use_cases/` | Mỗi file = 1 tính năng. Gọi port → gọi domain → trả kết quả |
| `errors.py` | Lỗi nghiệp vụ, độc lập với HTTP |

### `infrastructure/` — thế giới bên ngoài
| File | Nội dung |
|---|---|
| `repositories/csv_restaurant_repository.py` | CSV → entity. **pandas dừng ở đây** |
| `repositories/json_*.py` | JSON → entity |
| `repositories/jsonl_interaction_repository.py` | Ghi tương tác (append-only) |
| `adapters/open_meteo_context_provider.py` | Thời tiết (miễn phí, không cần key) |
| `adapters/ml_rule_predictor.py` | Model ML (tuỳ chọn) |
| `config/settings.py` | **Mọi đường dẫn file**, đọc từ biến môi trường |
| `ai/` | Script train — tạm dừng, không nằm trong luồng request |

### `presentation/` — HTTP
| File | Nội dung |
|---|---|
| `main.py` | `create_app()` |
| `dependencies.py` | **Nơi duy nhất lắp adapter thật vào use case** |
| `schemas.py` | Hợp đồng với frontend (snake_case) |
| `envelope.py` | `{data}`/`{error}` + bảng mã lỗi |
| `error_handlers.py` | Lỗi nghiệp vụ → mã HTTP + `error.code` |
| `routers/` | search, restaurants, interactions, meta. Mỏng, không logic |

---

## 3. Một request đi qua đâu

`POST /api/v1/search {"session_id": "...", "query_text": "quán lẩu ấm cúng"}`:

```
1. routers/search.py
   pydantic kiểm tra body → SearchRequest       (thiếu/sai → 400 INVALID_REQUEST)

2. dependencies.get_search_restaurants()
   lấy use case đã lắp sẵn từ app.state.container

3. use_cases/search_restaurants.py
   kiểm tra repository.is_ready                 (chưa có data → 503 DATA_NOT_READY)
   đoán mood từ câu tự do  (text_relevance.infer_mood_weights)
   lấy ngữ cảnh thời điểm  (context_provider — hỏng thì dùng trung lập)
   gọi repository.list_all()

4. infrastructure/csv_restaurant_repository.py
   trả list[Restaurant] đã nạp sẵn lúc khởi động (không đọc lại file)

5. domain/services/search_ranking.py          ← TRÁI TIM HỆ THỐNG
   với mỗi quán, tính 4 tín hiệu:
       text     0.40  ← khớp câu tự do (tên → loại hình → không gian → review)
       mood     0.30  ← mood suy từ câu + đẩy nhẹ theo thời tiết/giờ
       distance 0.20  ← giảm dần theo khoảng cách
       rating   0.10  ← quán chưa có đánh giá dùng mức TRUNG LẬP, không phải 0
   → predicted_score ∈ [0,1]
   ẩn quán is_active=false, lọc bán kính, sắp xếp, cắt limit

6. use_cases/search_restaurants._suggest_dish()
   gắn suggested_dish cho từng quán (Lớp 5) — tên quán trước, loại hình sau

7. routers/search.py
   map sang schema → bọc envelope → {"data": {...}} 200
```

Bốn điểm đáng chú ý:

- **Một lượt gọi trả cả quán lẫn món.** Trước đây là 2 endpoint riêng, khiến client gọi 2
  lần và có thể nhận 2 tập quán khác nhau.
- **Không đọc file ở mỗi request.** Dữ liệu nạp một lần lúc khởi động.
- **Ánh xạ tên field làm thủ công** ở router, cố ý: đổi tên bên trong không âm thầm làm vỡ
  hợp đồng API.
- **Thiếu dữ liệu không bị phạt.** Quán chưa có rating/giờ mở cửa vẫn được xếp hạng bình
  thường — thiếu dữ liệu là hạn chế thu thập, không phải quán dở.

---

## 4. Vì sao lại làm như vậy — các quyết định đã cân nhắc

### Repository trả entity, không trả DataFrame
Cách cũ trả `DataFrame` rồi `df.copy()` **toàn bộ 4170 dòng ở mỗi request**. Nay chuyển
thành entity một lần lúc khởi động; xếp hạng bằng Python thuần trên 4170 phần tử là chuyện
nhỏ. Đổi lại: `pandas` biến mất khỏi domain và application → test nhanh và không dính framework.

### Không có singleton cấp module
Cách cũ có `recommendation_service = RecommendationService()` ở cuối file. Hậu quả: đọc file
ngay khi import, hai bản dữ liệu trong RAM (một do singleton, một do DI), và test buộc phải
lách bằng `__new__`. Nay mọi thứ đi qua `dependencies.py`.

### Thiếu dữ liệu không làm sập app
Repository ghi nhận lỗi thay vì ném exception lúc khởi động. `/health` báo `ready: false`
kèm lý do; endpoint liên quan trả 503 **kèm lệnh cần chạy**.

### Lỗi được ánh xạ tập trung
Cách cũ bọc `except Exception` quanh từng route rồi trả 400 → mọi bug lập trình đều hiện
thành "400 Bad Request". Nay `error_handlers.py` phân biệt rõ 400 / 422 / 503 / 500.

### Tính năng 3D tách riêng và tắt mặc định
`routers/spatial.py` chỉ được đăng ký khi `MOODBITE_ENABLE_SPATIAL=1`. Nhờ vậy app khởi
động được trên máy chưa cài `torch`/`ultralytics`.

---

## 5. Thêm một endpoint mới — ví dụ đầy đủ

Giả sử cần `GET /api/restaurants/nearby`:

```
1. application/ports/          → port đã có (RestaurantRepository) thì dùng lại
2. application/use_cases/find_nearby_restaurants.py
                               → Query + UseCase, chỉ điều phối
3. domain/services/            → nếu cần quy tắc mới thì thêm ở đây
4. presentation/api/schemas.py → NearbyResponse
5. presentation/api/dependencies.py
                               → thêm vào Container + hàm get_...
6. presentation/api/routers/restaurants.py
                               → route mỏng, gọi use case
7. tests/                      → test domain → test use case → test API
```

**Không được** viết logic thẳng trong router. **Không được** cho router import
`infrastructure` (checker sẽ bắt).

---

## 6. Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `MOODBITE_RESTAURANTS_CSV` | `data_pipeline/data_cleaned/dataset_moodbite_features.csv` | Dataset chính |
| `MOODBITE_RESTAURANT_DETAILS_JSON` | `data_pipeline/data_cleaned/restaurant_details.json` | Chi tiết quán |
| `MOODBITE_DISH_KNOWLEDGE_JSON` | `data_pipeline/dish_knowledge_base.json` | Tri thức món ăn |
| `MOODBITE_DISH_MODEL` | `models/dish_rule_classifier.joblib` | Model ML (tuỳ chọn) |
| `DISH_ADAPTER` | `auto` | `auto` / `kb` / `ml` |
| `MOODBITE_CORS_ORIGINS` | `*` | Danh sách origin, phân tách bằng dấu phẩy |
| `MOODBITE_INTERACTIONS` | `data_pipeline/data_cleaned/interactions.jsonl` | Nơi ghi tương tác |
| `MOODBITE_ENABLE_WEATHER` | *(tắt)* | `1` để gọi API thời tiết Open-Meteo |
| `MOODBITE_ENABLE_SPATIAL` | *(tắt)* | `1` để bật tính năng floorplan/3D |

---

## 7. Chạy và kiểm tra

```bash
uvicorn app:app --reload --port 8001     # chạy server
# http://localhost:8001/docs             # Swagger UI

python -m pytest -q                      # 93 test
python scripts/check_architecture.py     # kiểm tra hướng phụ thuộc
curl http://localhost:8001/health        # nguồn dữ liệu nào đã sẵn sàng
python scripts/run_suggest_demo.py sad   # thử luồng nghiệp vụ không cần server
```

## 8. Chỉ có MỘT backend

Toàn dự án chỉ có một app FastAPI. Backend TypeScript cũ nằm ở
`archive/typescript-backend/` và KHÔNG được khôi phục nếu chưa bàn lại — xem `CLAUDE.md`
mục −1.

# MoodBite

Gợi ý quán ăn ở Hà Nội theo **nhu cầu diễn đạt tự do**, vị trí và thời điểm.

Gõ "quán lẩu ấm cúng gần đây" hoặc "chỗ yên tĩnh để làm việc" thay vì chọn trong bộ lọc
cứng — kết quả kèm sẵn gợi ý món ăn cho từng quán.

> 📍 **Không biết dự án đang ở đâu?** Đọc [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) —
> đã làm gì, đang làm gì, làm gì tiếp theo.

---

## Chạy thử trong 3 bước

```bash
# 1. Cài thư viện
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# 2. Chạy backend
uvicorn app:app --reload --port 8001

# 3. Mở Swagger UI để thử API
# http://localhost:8001/docs
```

Kiểm tra mọi thứ sẵn sàng chưa:

```bash
curl http://localhost:8001/health
```

Chạy frontend (cửa sổ terminal khác):

```powershell
cd frontend
copy .env.example .env.local    # macOS/Linux: cp .env.example .env.local
npm install
npm run dev                     # http://localhost:5173
```

---

## API

Base URL: `/api/v1`. Mọi response bọc trong `data` (thành công) hoặc `error` (lỗi).

| Method | Endpoint | Công dụng |
|---|---|---|
| POST | `/api/v1/search` | Tìm quán bằng **câu tự do** + vị trí, trả danh sách đã xếp hạng |
| GET | `/api/v1/restaurants/{id}` | Chi tiết quán (giá, review, ảnh) |
| POST | `/api/v1/interactions` | Ghi tương tác — nhãn cho mô hình xếp hạng sau này |
| GET | `/api/v1/moods` | 4 mood dùng cho nút bấm nhanh |
| GET | `/health` | Trạng thái từng nguồn dữ liệu |

Ví dụ:

```bash
curl -X POST http://localhost:8001/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
        "session_id": "3f9a0000-0000-4000-8000-000000000000",
        "query_text": "quán lẩu ấm cúng gần đây",
        "latitude": 21.0285,
        "longitude": 105.8542,
        "limit": 5
      }'
```

Mỗi kết quả kèm sẵn `suggested_dish` — không phải gọi thêm endpoint nào.

Bốn quy ước quan trọng khi đọc response:

- **Tên trường là `snake_case`** (`restaurant_id`, `predicted_score`) theo đặc tả API mục 1.3.
- `price_range`, `rating`, `user_ratings_total` bằng `null` nghĩa là **chưa có dữ liệu**,
  không phải "miễn phí" hay "0 sao". Phần lớn quán lấy từ OpenStreetMap.
- `price_range` là **chuỗi** (`"100-200 N ₫"`), không phải số.
- `match_source` cho biết quán được gợi ý nhờ đâu (tên / loại hình / không gian / review),
  và `warnings` liệt kê những gì server **không** làm được với request đó.

---

## Cấu trúc dự án

```
MoodBite/
├── src/                    Backend (Clean Architecture 4 tầng)
│   ├── domain/             Quy tắc nghiệp vụ — thuần Python
│   ├── application/        Use case + port
│   ├── infrastructure/     Đọc CSV/JSON, ML
│   └── presentation/       FastAPI
├── data_pipeline/          Cào, làm sạch, tính đặc trưng dữ liệu
├── frontend/               React + Vite
├── tests/                  137 test
├── scripts/                Công cụ, gồm checker kiến trúc
├── docs/                   Tài liệu kỹ thuật
├── rules/                  Quy tắc nghiệp vụ theo tài liệu gốc
└── archive/                Code cũ giữ lại để tham khảo
```

Chi tiết: [`docs/backend_architecture.md`](docs/backend_architecture.md)

---

## Dữ liệu

Dataset đã có sẵn trong repo — **không cần chạy lại pipeline** trừ khi muốn cào thêm.

| | Số lượng | Tỷ lệ |
|---|---|---|
| Quán ăn | **4226** | — |
| Có toạ độ, tên, loại hình, địa chỉ | 4226 | **100%** |
| Có nguồn gốc (`source`, `data_confidence`) | 4226 | **100%** |
| Có đơn vị hành chính (`district`) | 3620 | 85.7% |
| Có gợi ý món (`dishes`) | 1487 | 35.2% |
| Có số điện thoại | 1023 | 24.2% |
| Có giờ mở cửa | 954 | 22.6% |
| Có tiện nghi | 656 | 15.5% |
| Có rating | 350 | 8.3% |
| Có giá | 228 | 5.4% |
| Có khai báo chế độ ăn | 117 | 2.8% |

Đơn vị hành chính phủ: **125**. Trùng lặp: **0%**.
Đo lại bất cứ lúc nào: `python scripts/data_report.py`

Thu thập thêm dữ liệu (miễn phí, không cần API key):

```bash
python -m data_pipeline.harvest --list              # xem nguồn nào sẵn sàng
python -m data_pipeline.harvest                     # chạy mọi nguồn
```

Rồi chạy lại pipeline:

```bash
python -m data_pipeline.merge_and_prepare_raw
python -m data_pipeline.data_cleaning
python -m data_pipeline.feature_engineering
python scripts/data_report.py                       # đo độ phủ trước/sau
```

Thêm nguồn mới (Google Places...) — xem [`docs/data_sources.md`](docs/data_sources.md).

---

## Kiểm tra chất lượng

Một lệnh, chạy được ở PowerShell / CMD / bash / macOS / Linux:

```
python scripts/verify.py
```

Kiểm 5 việc: app dựng được · 137 test · hướng phụ thuộc Clean Architecture ·
chỉ có 1 backend · frontend build được. Tất cả cũng chạy tự động trong CI
(`.github/workflows/ci.yml`).

> ⚠️ **Windows:** PowerShell 5.1 không hỗ trợ `&&` để nối lệnh, và không có
> `grep`/`wc`. Dùng lệnh trên thay vì gõ tay từng bước.

---

## Tài liệu

| File | Nội dung |
|---|---|
| [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) | **Tiến độ dự án — đọc đầu tiên** |
| [`CLAUDE.md`](CLAUDE.md) | Quy tắc bắt buộc cho AI khi sửa code |
| [`docs/backend_architecture.md`](docs/backend_architecture.md) | Backend nằm ở đâu, vì sao |
| [`docs/frontend_architecture.md`](docs/frontend_architecture.md) | 3 phương án frontend (đã chọn & triển khai A) |
| [`docs/google_maps_integration.md`](docs/google_maps_integration.md) | Bản đồ + vị trí người dùng |
| [`docs/data_sources.md`](docs/data_sources.md) | Đánh giá nguồn dữ liệu, vì sao dùng/không dùng |
| [`docs/frontend_readiness.md`](docs/frontend_readiness.md) | **Mức sẵn sàng frontend + phương án kiến trúc** |
| [`CODING_STANDARDS.md`](CODING_STANDARDS.md) | Quy ước viết code |
| [`rules/`](rules/) | Quy tắc nghiệp vụ theo tài liệu gốc |

---

## Trạng thái các tính năng

- ✅ **Tìm kiếm bằng câu tự do + gợi ý món** — chạy được
- ✅ **Ghi nhận tương tác** — chuẩn bị dữ liệu cho mô hình xếp hạng
- 🟡 **Ngữ cảnh thời điểm** — giờ ăn đã bật; thời tiết tắt mặc định (`MOODBITE_ENABLE_WEATHER=1`)
- ✅ **Frontend** — ô tìm kiếm tự do + định vị thật
- ⬜ **Bản đồ** — chưa làm, đã có hướng dẫn
- ⬜ **Phân cụm / tóm tắt review** — chưa đủ dữ liệu (chỉ 8.3% quán có review)
- ✅ **Lọc theo khu vực / giờ mở cửa / chế độ ăn** — mới bổ sung
- ⏸️ **Floorplan → 3D** — tạm dừng, tắt mặc định (bật bằng `MOODBITE_ENABLE_SPATIAL=1`)
- ⏸️ **Model ML gợi ý món** — model cũ bị rò rỉ nhãn nên đã gỡ; hiện dùng khớp từ khoá.
  ⚠️ Con số "98.56% chính xác" trong tài liệu cũ **không có giá trị thật**.

---

## License

MIT

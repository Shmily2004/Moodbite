# MoodBite

Gợi ý quán ăn ở Hà Nội theo **nhu cầu diễn đạt tự do**, vị trí và thời điểm.

Gõ "quán lẩu ấm cúng gần đây" hoặc "chỗ yên tĩnh để làm việc" thay vì chọn trong bộ lọc
cứng — kết quả kèm sẵn gợi ý món ăn cho từng quán.

> 📍 **Không biết dự án đang ở đâu?** Đọc [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) —
> đã làm gì, đang làm gì, làm gì tiếp theo.

---

## 🚀 Chạy và XEM GIAO DIỆN

**Cài một lần:**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

**Chạy — MỘT lệnh khởi động cả backend lẫn giao diện:**

```powershell
python scripts/run_dev.py            # backend + app người dùng
python scripts/run_dev.py --admin    # thêm cả app quản trị
```

Script tự kiểm điều kiện, khởi động mọi thứ, rồi in ra địa chỉ để mở.

### 👉 Giao diện nằm ở đâu

| Cái gì | Địa chỉ | Cần gì trước |
|---|---|---|
| **App người dùng** (tìm quán) | **http://localhost:5173** | backend chạy |
| **App quản trị** (sửa/ẩn quán) | **http://localhost:5174** | backend chạy + [đã cấu hình quyền](#bật-trang-quản-trị) |
| Swagger UI (thử API tay) | http://localhost:8001/docs | backend chạy |
| Trạng thái hệ thống | http://localhost:8001/api/v1/health | backend chạy |

> ⚠️ **Màn hình trắng?** Ba nguyên nhân, theo thứ tự hay gặp:
> 1. **Chưa chạy dev server.** Giao diện là ứng dụng React, KHÔNG phải file HTML tĩnh.
>    Phải có `npm run dev` (hoặc `python scripts/run_dev.py`) đang chạy.
> 2. **Mở thẳng file `frontend/apps/client/dist/index.html`** bằng cách bấm đúp.
>    Không dùng được: file build tham chiếu `/assets/...` theo đường dẫn tuyệt đối, mở
>    bằng `file://` sẽ không tìm thấy → trang trắng. Phải mở qua `http://localhost:5173`.
> 3. **Backend chưa chạy.** Giao diện vẫn hiện khung và ô tìm kiếm, nhưng tìm sẽ báo lỗi
>    "Không kết nối được tới server".

Chạy tay từng phần (mỗi lệnh MỘT cửa sổ terminal riêng):

```powershell
python -m uvicorn app:app --reload --port 8001   # backend
```
```powershell
cd frontend
npm run dev          # app người dùng  -> http://localhost:5173
```
```powershell
cd frontend
npm run dev:admin    # app quản trị    -> http://localhost:5174
```

### Bật trang quản trị

Trang quản trị **fail-closed**: chưa cấu hình thì mọi `/api/v1/admin/*` trả 503 và không
đăng nhập được. Xem còn thiếu gì:

```powershell
python scripts/check_permissions.py
```

Làm đủ 3 bước rồi khởi động lại backend:

```powershell
python scripts/build_sqlite.py          # 1. CSDL ghi được (CSV chỉ đọc)
python scripts/make_admin_password.py   # 2. sinh tài khoản, in ra 3 biến cần đặt
$env:MOODBITE_STORAGE = "sqlite"        # 3. bật kho ghi được
```

Mẫu đầy đủ các biến môi trường: [`.env.example`](.env.example)

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
├── frontend/               React + TypeScript + FSD (monorepo)
├── tests/                  171 test
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
| Quán ăn | **4938** | — |
| Có toạ độ, tên, loại hình, địa chỉ | 4938 | **100%** |
| Có nguồn gốc (`source`, `data_confidence`) | 4938 | **100%** |
| Có đơn vị hành chính (`district`) | 4787 | 96.9% |
| Có số điện thoại | 1641 | 33.2% |
| Có giờ mở cửa | 1608 | 32.6% |
| Có gợi ý món (`dishes`) | 1462 | 29.6% |
| Có đánh giá (rating) | 1145 | 23.2% |
| Có review + ảnh + giá | 1310 | 26.5% |
| Có giá | 643 | 13.0% |
| Có tiện nghi | 645 | 13.1% |
| Có khai báo chế độ ăn | 115 | 2.3% |

Nguồn: OpenStreetMap 3528 · Google Maps (Apify) 1410.
Đơn vị hành chính phủ: **142**. Trùng lặp: **0%**.
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

Kiểm 5 việc: app dựng được · 171 test · hướng phụ thuộc Clean Architecture ·
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
- ✅ **App người dùng** (`localhost:5173`) — ô tìm kiếm tự do + định vị thật
- ✅ **App quản trị** (`localhost:5174`) — đăng nhập, sửa, ẩn/bỏ ẩn quán.
  ⚠️ Phải cấu hình quyền trước, xem [Bật trang quản trị](#bật-trang-quản-trị)
- ✅ **Bản đồ** — Leaflet + OpenStreetMap, miễn phí, không cần API key
- ✅ **Phân cụm trải nghiệm (Lớp 1)** — KMeans k=7, Silhouette 0.318
- ✅ **Tìm kiếm ngữ nghĩa (Lớp 2)** — TF-IDF cosine trên 4938 quán
- ⬜ **Tóm tắt review (Lớp 4)** — chưa làm; đo lại thấy khả thi cho 592 quán
- ✅ **Lọc theo khu vực / giờ mở cửa / chế độ ăn**
- ⏸️ **Floorplan → 3D** — đã chuyển vào `archive/spatial-3d/`, không còn trong app
- ⏸️ **Model ML gợi ý món** — model cũ bị rò rỉ nhãn nên đã gỡ; hiện dùng khớp từ khoá.
  ⚠️ Con số "98.56% chính xác" trong tài liệu cũ **không có giá trị thật**.

---

## License

MIT

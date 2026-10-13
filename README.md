# MoodBite

Gợi ý **MÓN ĂN** rồi mới tới **QUÁN** ở Hà Nội, theo tâm trạng, thời tiết và vị trí.

Luồng chính (chốt 2026-08-19) đi đúng thứ tự người ta vốn nghĩ:

```
trang chủ: chọn điều kiện        🌧️ trời mưa · 🔥 đồ nướng · 🍜 đồ nóng
        ↓
DANH SÁCH MÓN                    "Bún chả · hợp trời mưa · 86 quán gần bạn"
        ↓  bấm vào một món
GIỚI THIỆU NGẮN VỀ MÓN           món đó là gì, ăn thế nào
        ↓
DANH SÁCH QUÁN bán món đó        xếp theo khoảng cách + đánh giá + ngữ cảnh
        ↓  bấm vào một quán
REVIEW · ẢNH · GIÁ · CHỈ ĐƯỜNG
```

Vẫn còn **lối vào thứ hai** ở `/search` (đường cũ `/tim-kiem` tự chuyển hướng): gõ thẳng "quán lẩu ấm cúng gần đây" để ra ngay
danh sách quán, mỗi quán kèm sẵn gợi ý món.

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
| **App người dùng** (chọn món → tìm quán) | **http://localhost:5173** | backend chạy |
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

Làm đủ 2 bước rồi khởi động lại backend:

```powershell
python scripts/build_sqlite.py          # 1. CSDL ghi được (CSV chỉ đọc)
python scripts/make_admin_user.py       # 2. tạo tài khoản admin trong bảng users
```

Bước 2 tự ghi `MOODBITE_ADMIN_SECRET` và `MOODBITE_STORAGE=sqlite` vào `.env.local` (đã
.gitignore) — KHÔNG cần đặt `$env:` bằng tay. Máy cũ còn admin dạng biến môi trường
(`MOODBITE_ADMIN_USER` / `MOODBITE_ADMIN_PASSWORD_HASH`) thì chuyển sang bảng `users`, giữ
nguyên mật khẩu:

```powershell
python scripts/make_admin_user.py --tu-env
```

Mẫu đầy đủ các biến môi trường: [`.env.example`](.env.example)

---

## API

Base URL: `/api/v1`. Mọi response bọc trong `data` (thành công) hoặc `error` (lỗi).

| Method | Endpoint | Công dụng |
|---|---|---|
| POST | `/api/v1/dishes/suggest` | **Luồng chính, bước 1** — bộ lọc → danh sách MÓN đã xếp hạng |
| GET | `/api/v1/dishes/{id}` | **Bước 2** — giới thiệu ngắn về món + số quán gần bạn |
| GET | `/api/v1/dishes/{id}/restaurants` | **Bước 3** — quán bán món đó, cùng kiểu trả về với `/search` |
| POST | `/api/v1/search` | Lối vào thứ hai: tìm quán bằng **câu tự do** + vị trí |
| GET | `/api/v1/restaurants/{id}` | Chi tiết quán (giá, review, ảnh) |
| POST | `/api/v1/interactions` | Ghi tương tác — nhãn cho mô hình xếp hạng sau này |
| GET | `/api/v1/moods` | 4 mood dùng cho nút bấm nhanh |
| GET | `/api/v1/health` | Trạng thái từng nguồn dữ liệu (cũng có ở `/health`) |
| — | `/api/v1/auth/*`, `/api/v1/me/*`, `/api/v1/admin/*` | Tài khoản, dữ liệu cá nhân, quản trị — cần `Authorization: Bearer <token>` |

Danh sách đầy đủ + mã lỗi: [`docs/extracted/MoodBite_Dac_Ta_API.md`](docs/extracted/MoodBite_Dac_Ta_API.md)
(mục *BỔ SUNG 2026-10*). Schema chi tiết: `frontend/openapi.json` (sinh bằng
`python scripts/export_openapi.py`).

**Thử API nhanh nhất: mở Swagger UI http://localhost:8001/docs** — điền body và bấm
"Execute", không phải gõ lệnh.

Gọi từ PowerShell 5.1 (chạy được nguyên văn, mỗi lệnh một dòng). Hai điểm bắt buộc trên
PowerShell 5.1: gửi body dưới dạng **byte UTF-8** (nếu không, chữ có dấu trong câu tìm kiếm
bị hỏng trước khi tới server), và **tự giải mã response bằng UTF-8** (server trả
`application/json` không kèm `charset`, PowerShell 5.1 đọc sai thành kiểu `Nem nÆ°á»ng`).

Ví dụ — luồng chính, "nay trời mưa, muốn ăn đồ nướng":

```powershell
$body = '{"session_id": "3f9a0000-0000-4000-8000-000000000000", "weather": "rain", "cooking_methods": ["nuong"], "latitude": 21.0285, "longitude": 105.8542, "max_distance_km": 5, "limit": 3}'
$resp = Invoke-WebRequest -UseBasicParsing -Method Post -Uri http://localhost:8001/api/v1/dishes/suggest -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body))
$json = [Text.Encoding]::UTF8.GetString($resp.RawContentStream.ToArray()) | ConvertFrom-Json
$json.data.results | Select-Object name, restaurant_count
```

Ví dụ — lối vào thứ hai (tìm bằng câu tự do):

```powershell
$body = '{"session_id": "3f9a0000-0000-4000-8000-000000000000", "query_text": "quán lẩu ấm cúng gần đây", "latitude": 21.0285, "longitude": 105.8542, "limit": 5}'
$resp = Invoke-WebRequest -UseBasicParsing -Method Post -Uri http://localhost:8001/api/v1/search -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body))
$json = [Text.Encoding]::UTF8.GetString($resp.RawContentStream.ToArray()) | ConvertFrom-Json
$json.data.results | Select-Object name, distance_m
```

Mỗi kết quả của `/search` kèm sẵn `suggested_dish` — không phải gọi thêm endpoint nào.

`description` bằng `null` kèm `has_description: false` nghĩa là **chưa tra được giới
thiệu**, không phải "món này không có gì để nói" — giao diện phải nói đúng như vậy.

Bốn quy ước quan trọng khi đọc response:

- **Tên trường là `snake_case`** (`restaurant_id`, `predicted_score`) theo đặc tả API mục 1.3.
- `price_range`, `rating`, `user_ratings_total` bằng `null` nghĩa là **chưa có dữ liệu**,
  không phải "miễn phí" hay "0 sao". ~97% quán lấy từ Overture Maps và OpenStreetMap — hai
  nguồn này không có rating/giá (xem bảng *Dữ liệu* bên dưới).
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
├── tests/                  test backend (pytest)
├── scripts/                Công cụ, gồm checker kiến trúc
├── docs/                   Tài liệu kỹ thuật
├── rules/                  Quy tắc nghiệp vụ theo tài liệu gốc
└── archive/                Code cũ giữ lại để tham khảo
```

Chi tiết: [`docs/backend_architecture.md`](docs/backend_architecture.md)

---

## Dữ liệu

Dataset đã có sẵn trong repo — **không cần chạy lại pipeline** trừ khi muốn cào thêm.

Đo bằng `python scripts/data_report.py` ngày 2026-10-06:

| | Số lượng | Tỷ lệ |
|---|---|---|
| Quán ăn (chỉ Hà Nội) | **52.872** | — |
| Có toạ độ, tên, loại hình | 52.872 | **100%** |
| Có địa chỉ | 52.859 | ~100% |
| Có nguồn gốc (`source`, `data_confidence`) | 52.872 | **100%** |
| Có đơn vị hành chính (`district`) | 52.872 | 100% |
| Có số điện thoại | 43.192 | 81,7% |
| Có website | 13.821 | 26,1% |
| Có giờ mở cửa | 1.635 | 3,1% |
| Có gợi ý món (`dishes`) | 1.463 | 2,8% |
| Có đánh giá (rating) | 1.178 | 2,2% |
| Có chi tiết (review + ảnh, `restaurant_details.json`) | 1.345 | 2,5% |
| Có giá | 671 | 1,3% |
| Có tiện nghi | 646 | 1,2% |
| Có khai báo chế độ ăn | 125 | 0,2% |

Nguồn: Overture Maps 48.406 · OpenStreetMap 3.025 · Google Maps (Apify) 1.441.
Đơn vị hành chính phủ: **125**. Trùng lặp: **0%**.
Rating / giá / review chỉ có ở phần nhỏ quán lấy từ Google Maps — đó là **lớp làm giàu**,
không phải dữ liệu lõi.
Đo lại bất cứ lúc nào: `python scripts/data_report.py`

Thu thập thêm dữ liệu (miễn phí, không cần API key):

```powershell
python -m data_pipeline.harvest --list              # xem nguồn nào sẵn sàng
python -m data_pipeline.harvest                     # chạy mọi nguồn
```

Rồi chạy lại pipeline, **đúng thứ tự này** (mỗi lệnh một dòng):

```powershell
python -m data_pipeline.merge_and_prepare_raw
python -m data_pipeline.data_cleaning
python -m data_pipeline.feature_engineering
python -m data_pipeline.clustering                  # PHẢI chạy CUỐI
python scripts/data_report.py                       # đo độ phủ trước/sau
```

⚠️ `clustering` phải chạy sau `feature_engineering`: chạy `feature_engineering` sau sẽ xoá
mất hai cột `experience_cluster_id` / `experience_cluster_label` (CLAUDE.md mục 4c).

Thêm nguồn mới (Google Places...) — xem [`docs/data_sources.md`](docs/data_sources.md).

---

## Kiểm tra chất lượng

Một lệnh, chạy được ở PowerShell / CMD / bash / macOS / Linux:

```
python scripts/verify.py
```

Kiểm 9 mục: (1) app FastAPI dựng được · (2) toàn bộ test backend (pytest) · (3) hướng
phụ thuộc Clean Architecture · (4) chỉ có 1 backend · (5) frontend typecheck + build ·
(6) test frontend (client + admin) · (7) luật import FSD · (8) CI cài đặt được (lockfile,
đường dẫn trong `ci.yml`) · (9) bộ dữ liệu mẫu frontend không giàu hơn dữ liệu thật.
Số test hiện tại: xem output của lệnh trên, hoặc dòng *Test* trong `PROJECT_CHECKLIST.md`.
Chạy một mục: `python scripts/verify.py --chi 4`.

CI (`.github/workflows/ci.yml`) chạy lại mục 1–7 thành từng bước riêng (mục 4 bằng
`verify.py --chi 4`), backend trên Python 3.11 và 3.14. Mục 8 được chính lần chạy CI
chứng minh (`npm ci` cài được hay không). Mục 9 **chỉ chạy ở máy local**.

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
- ✅ **Tìm kiếm ngữ nghĩa (Lớp 2)** — TF-IDF cosine trên 52.871 quán (đếm lúc khởi động 2026-10-06)
- ✅ **Tóm tắt review (Lớp 4)** — trích rút nguyên văn, 884/1.025 quán có ≥3 review (đo 2026-10-10)
- ✅ **Lọc theo khu vực / giờ mở cửa / chế độ ăn**
- ⏸️ **Floorplan → 3D** — đã chuyển vào `archive/spatial-3d/`, không còn trong app
- ⏸️ **Model ML gợi ý món** — model cũ bị rò rỉ nhãn nên đã gỡ; hiện dùng khớp từ khoá.
  ⚠️ Con số "98.56% chính xác" trong tài liệu cũ **không có giá trị thật**.

---

## License

MIT

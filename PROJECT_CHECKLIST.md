# MoodBite — Bảng theo dõi tiến độ

**Cập nhật:** 2026-08-16
**Nguyên tắc:** file này chỉ ghi thứ đã **chạy thật và kiểm chứng được**. Không ghi theo
kế hoạch, không ghi theo tài liệu. Mỗi mục ✅ đều có lệnh để tự kiểm lại.

---

## 🚦 Tình trạng trong 30 giây

| Phần | Trạng thái | Ghi chú |
|---|---|---|
| **Một backend duy nhất** | ✅ Xong | 1 app FastAPI, 0 file TypeScript ngoài `archive/` |
| API khớp đặc tả | ✅ Xong | `/api/v1`, envelope `data`/`error`, snake_case |
| Tìm kiếm bằng câu tự do | ✅ Chạy được | đúng ý đề án, thay cho dropdown mood |
| Gợi ý món trong kết quả | ✅ Xong | lồng trong từng quán, không còn endpoint riêng |
| Ghi nhận tương tác | ✅ Xong | `POST /interactions` → nhãn cho mô hình sau này |
| Ngữ cảnh thời điểm | ✅ Giờ ăn · 🟡 thời tiết tắt mặc định | bật bằng `MOODBITE_ENABLE_WEATHER=1` |
| Frontend | ✅ Chạy được | ô tìm kiếm tự do + định vị, chưa có bản đồ |
| Bản đồ Google Maps | ⬜ Chưa làm | đã có hướng dẫn đầy đủ |
| Kiến trúc | ✅ Sạch | Clean Architecture + checker tự động trong CI |
| Test | ✅ 146 test xanh | gồm test "app phải dựng được" |
| Dữ liệu | ✅ 4938 quán · 142 đơn vị HC | provenance 100%, trùng lặp 0% |
| Thu thập dữ liệu đa nguồn | ✅ Xong | kiến trúc `SourceAdapter`, thêm nguồn không sửa pipeline |
| Lọc giờ mở cửa / chế độ ăn / quận | ✅ Xong | thiếu dữ liệu KHÔNG bị loại |
| Phân cụm / tóm tắt review | ⬜ Chưa làm | **dữ liệu chưa đủ** — xem mục ⚠️ |
| Đăng nhập / tài khoản | ⬜ Ngoài phạm vi | SRS mục 8, Won't-have |

**Tự kiểm toàn bộ bằng MỘT lệnh** (chạy được ở PowerShell, CMD, bash, macOS, Linux):

```
python scripts/verify.py
```

Lệnh này kiểm 5 việc và in rõ từng mục đạt/hỏng:
app dựng được · test · hướng phụ thuộc · **chỉ có 1 backend** · frontend build.

> ⚠️ **Đừng nối lệnh bằng `&&` trên Windows.** PowerShell 5.1 không hỗ trợ `&&`
> (báo lỗi *"The token '&&' is not a valid statement separator"*), cũng không có
> `grep`/`wc`. Dùng `python scripts/verify.py` là xong, không phải nhớ cú pháp shell.
>
> Nếu vẫn muốn chạy tay từng bước trên PowerShell — mỗi lệnh một dòng riêng:
> ```powershell
> python -c "from src.presentation.api.main import create_app; create_app()"
> python -m pytest -q
> python scripts/check_architecture.py
> cd frontend
> npm run build
> cd ..
> ```

---

## ✅ ĐÃ LÀM XONG

### Gộp về MỘT backend duy nhất
Trước đây `src/` chứa **hai backend song song** (Python FastAPI + TypeScript Clean
Architecture) nằm xen kẽ trong cùng thư mục và không gọi nhau — đây là lý do chính khiến
cấu trúc dự án không thể hiểu nổi.

- [x] TypeScript chuyển vào `archive/typescript-backend/` (không xoá, còn nguyên trong git)
- [x] Xoá `tsconfig.json` / `package.json` ở gốc (chỉ phục vụ backend TS cũ)
- [x] Xoá module trùng lặp: 2 nơi tính haversine, 2 module xếp hạng, 2 tầng service
- [x] CI bỏ bước typecheck TypeScript không còn tồn tại

Kiểm lại (mục 4 của `python scripts/verify.py` đã tự kiểm việc này):

```powershell
# PowerShell - Windows
(Get-ChildItem src -Recurse -Filter *.py | Select-String 'FastAPI\(').Count      # phải = 1
(Get-ChildItem -Recurse -Filter *.ts |
  Where-Object { $_.FullName -notmatch 'archive|node_modules' }).Count           # phải = 0
```

### API khớp đặc tả (`docs/extracted/MoodBite_Dac_Ta_API.md`)
- [x] Tiền tố version `/api/v1`
- [x] Envelope: `{"data": …}` khi thành công, `{"error": {"code","message","details"}}` khi lỗi
- [x] Tên trường **snake_case** (`restaurant_id`, `predicted_score`) — đúng quyết định mục 1.3
- [x] Bảng mã lỗi: `INVALID_REQUEST` · `RESTAURANT_NOT_FOUND` · `DATA_NOT_READY` · `INTERNAL_ERROR`
- [x] `session_id` do client sinh, không có tài khoản người dùng

| Endpoint | Công dụng |
|---|---|
| `POST /api/v1/search` | Tìm kiếm bằng câu tự do + vị trí, trả danh sách đã xếp hạng |
| `GET /api/v1/restaurants/{id}` | Chi tiết quán |
| `POST /api/v1/interactions` | Ghi tương tác → nhãn cho mô hình xếp hạng |
| `GET /api/v1/health`, `/health` | Trạng thái từng nguồn dữ liệu |
| `GET /api/v1/moods` | 4 mood dùng cho nút bấm nhanh |

### Các lớp mô hình theo đề án
- [x] **Lớp 2 (bản khả thi) — tìm kiếm câu tự do:** khớp lai theo tên → loại hình →
      không gian → review, kèm `match_source` nói rõ khớp nhờ đâu
- [x] **Lớp 3 — xếp hạng theo ngữ cảnh:** `predicted_score` tổng hợp câu tự do (0.40) +
      mood (0.30) + khoảng cách (0.20) + đánh giá (0.10)
- [x] **Lớp 4 (một phần) — tín hiệu thời điểm:** giờ ăn/cuối tuần luôn bật; thời tiết qua
      Open-Meteo (miễn phí, không cần key), tắt mặc định
- [x] **Lớp 5 — gợi ý món:** lồng trong từng kết quả, kèm `confidence`
- [x] Chuẩn bị cho mô hình học: ghi tương tác + `is_positive_signal` tính ở server

### Chất lượng gợi ý món (đo được)
- [x] Knowledge base: **21 → 38 rule**, thêm bún chả, bún bò, bánh mì, ốc, cháo, xôi…
      (chọn theo số liệu thật, không đoán)
- [x] Suy luận món từ **TÊN QUÁN** trước, loại hình sau — đo được: 144 quán có "phở" trong
      tên nhưng chỉ 14 quán có trong `categoryName` (**gấp ~10 lần tín hiệu**)
- [x] Khớp không dấu: "Pho Bo", "O Bun Cha", "Banh mi" nay đều nhận đúng món

### Bug đã sửa (đều kiểm chứng được)
- [x] **App không khởi động được** — `@app.exception_handler` dùng trước khi `app` tồn tại
- [x] **`/recommend`, `/suggest-dish` luôn lỗi** — đọc `request.mood` trên object `Request`
- [x] **`price` sai kiểu** — schema khai `float`, dữ liệu thật là chuỗi (`"1-100.000 ₫"`)
- [x] **Bug server bị nguỵ trang thành lỗi client** — `except Exception` → 400
- [x] **Đọc dữ liệu 2 lần vào RAM** + `df.copy()` toàn dataset mỗi request
- [x] **`sad` và `relaxed` trả kết quả giống hệt nhau**
- [x] **Quán cách 36km lọt top-5** — thêm lọc bán kính 10km
- [x] **`/suggest-dish` lặng lẽ bỏ qua `max_distance_km`** client gửi lên
- [x] **Tìm kiếm khớp chuỗi con** — "bo" khớp "bột"/"bọt" nên "phở bò" ra quán bánh tráng
- [x] **Review lấn át tên quán** — quán tên "Phở Bò" thua quán chỉ nhắc "bò" trong review
- [x] **Gợi ý món sai** — "Bún Chả - Nem Cua Bê" bị gợi ý "Gà rán"
- [x] **`.env.local` chưa được `.gitignore`** — API key có thể bị commit

### Frontend
- [x] Dựng lại theo cấu trúc feature-based (phương án A trong `docs/frontend_architecture.md`)
- [x] Ô tìm kiếm bằng câu tự do + gợi ý câu mẫu
- [x] Định vị thật qua Geolocation API (**miễn phí, không cần key**)
- [x] Tầng `services/` bóc envelope; component không gọi `fetch` trực tiếp
- [x] Huỷ request cũ bằng `AbortController` (bấm nhanh 2 lần không còn ghi đè kết quả)
- [x] 1 lượt gọi API thay vì 2 lượt tuần tự
- [x] Hiện `match_source` và `dish_confidence` — nói thật vì sao quán được gợi ý
- [x] Ghi tương tác khi người dùng xem chi tiết / bấm chỉ đường

---

## ⚠️ ĐỘ PHỦ DỮ LIỆU (đo bằng `python scripts/data_report.py`)

### Trước → Sau (đo bằng `python scripts/data_report.py`)

Mốc "trước" = dataset gốc ngày 2026-08-16, đo lại từ git bằng cùng công cụ.

| Chỉ số | Trước | Sau | Thay đổi |
|---|---|---|---|
| Tổng số quán | 4170 | **4938** | +768 |
| Quán duy nhất | 4170 | 4938 | trùng lặp **0%** |
| Đơn vị hành chính phủ | **0** | **142** | +142 |
| `district` | 0% | **96.9%** | +96.9đ |
| **`totalScore` (đánh giá)** | **8.4%** | **23.2%** | **+14.8đ** |
| `reviewsCount` | 11.7% | **25.5%** | +13.8đ |
| Quán có review + ảnh + giá | 440 | **1310** | +870 |
| `price` | 5.5% | **13.0%** | +7.5đ |
| `openingHours` | 22.7% | **32.6%** | +9.9đ |
| `phone` | 0% | **33.2%** | +33.2đ |
| `dishes` | 0% | **29.6%** | +29.6đ |
| `amenities` | 0% | **13.1%** | +13.1đ |
| `website` | 8.5% | **12.5%** | +4.0đ |
| `Bầu không khí` | 8.7% | **21.9%** | +13.2đ |
| `aliases` | 0% | **6.6%** | +6.6đ |
| `dietary` | 0% | **2.3%** | +2.3đ |
| `source` / `data_confidence` | 0% | **100%** | +100đ |
| `cuisine` | 36.5% | 30.4% | −6.1đ (mẫu số tăng) |

**Nguồn:** `openstreetmap` 3528 · `google_maps_apify` 1410.

### Đã làm gì để đạt được

1. **Nguồn OSM mới** (`data_pipeline/sources/osm_overpass.py`) — lấy đủ tag mà bản cào cũ
   bỏ phí: `phone`, `opening_hours`, `diet:*`, `outdoor_seating`, `cuisine`…
2. **Gán khu vực từ toạ độ** — ranh giới hành chính OSM + point-in-polygon offline.
3. **3 đợt cào Apify Google Maps** (~1276 quán mới, 87% có đánh giá).
4. **Khử trùng lặp giữa các nguồn** — OSM và Google đánh id khác nhau nên cùng một quán
   xuất hiện 2 lần; nay gộp theo *gần nhau ≤50m + trùng tên*, giữ bản giàu thông tin hơn
   và bù các trường còn trống từ bản kia.

### Vì sao đánh giá vẫn chỉ 23.2%

OpenStreetMap (3528 quán, 71% dataset) là dữ liệu **bản đồ**, **không có** rating/review/
ảnh/giá. Toàn bộ 1145 quán có đánh giá đều đến từ Apify Google Maps.

**Còn thiếu 3793 quán chưa có đánh giá.** Vùng đáng cào tiếp, xếp theo mật độ:

| Khu vực | Thiếu | Tâm `[lng, lat]` | Bán kính | Mật độ |
|---|---|---|---|---|
| **Phường Hoàn Kiếm** | **770** | `[105.8509, 21.0325]` | 0.7 km | **499/km²** |
| Phường Cửa Nam | 183 | `[105.8505, 21.0235]` | 0.9 km | 74/km² |
| Phường Ba Đình | 210 | `[105.8381, 21.0395]` | 1.1 km | 55/km² |
| Hai Bà Trưng | 185 | `[105.8582, 21.0075]` | 1.3 km | 33/km² |

Từ khoá nên dùng (chiếm 81% khoảng trống): `nhà hàng` · `quán cà phê` · `quán ăn`.
KHÔNG dùng tên món (`phở`, `bún chả`…) — đã có 251 quán phở, 747 quán cà phê rồi.

Các nguồn có sẵn rating khác (ShopeeFood, GrabFood, Foody, Facebook) đều **cấm thu thập
tự động trong ToS** → không dùng. Phân tích đầy đủ: `docs/data_sources.md`.

### Hệ quả tới tính năng

| Tính năng | Làm được chưa | Lý do |
|---|---|---|
| Bản đồ, khoảng cách | ✅ | 100% quán có toạ độ |
| Tìm bằng câu tự do | ✅ | tên + loại hình phủ 100% |
| Lọc theo khu vực | ✅ **mới** | 96.9% có `district` |
| Lọc theo giờ mở cửa | ✅ **mới** | 32.6% có dữ liệu, thiếu thì giữ lại |
| Lọc chay/thuần chay | 🟡 **mới** | chỉ 2.3% khai báo |
| Gợi ý món | ✅ | suy luận từ tên quán + `cuisine` |
| Xếp hạng theo đánh giá | 🟡 | 23.2% có rating (tập trung ở trung tâm) |
| Lọc theo giá | 🟡 | 13.0% có giá |
| Tìm kiếm ngữ nghĩa (embedding) | 🟡 | 23.2% có review — gần ngưỡng đáng làm |
| Phân cụm trải nghiệm | ❌ | thuộc tính không gian chỉ 8.6% |

---

## 🚧 VIỆC TIẾP THEO (ưu tiên từ trên xuống)

### 1. Bản đồ tương tác 🔥
Đề án mục 5 nói toàn bộ trải nghiệm nên diễn ra trên bản đồ, không phải danh sách rời.
Dữ liệu đã sẵn sàng 100% (mọi quán đều có toạ độ).

- [ ] Lấy API key + **giới hạn key theo tên miền** (bắt buộc)
- [ ] `npm install @vis.gl/react-google-maps`
- [ ] `features/map/RestaurantMap.jsx`, ghim kết quả lên bản đồ
- [ ] Hướng dẫn đầy đủ: `docs/google_maps_integration.md`

### 2. Google Places API — nút thắt lớn nhất 🔥
Chặn cả 3 lớp mô hình còn lại (embedding, phân cụm, tóm tắt review) VÀ mọi tính năng
dựa trên đánh giá/giá.

- [ ] Lấy API key (cần thẻ thanh toán)
- [ ] Viết `data_pipeline/sources/google_places.py` (chỗ cắm đã sẵn sàng)
- [ ] ⚠️ Đọc kỹ ToS: Google cấm lưu trữ lâu dài phần lớn nội dung Places

### 3. Bật thời tiết khi chạy thật
- [ ] `MOODBITE_ENABLE_WEATHER=1` (Open-Meteo miễn phí, không cần key)
- [ ] Xác nhận lại cơ chế tự khắc phục khi API lỗi trên môi trường thật

### 4. Frontend — CHỜ BẠN CHỌN KIẾN TRÚC 🔥
- [ ] Đọc `docs/frontend_readiness.md`, chọn: công nghệ (P1-P4) + cách tách Client/Admin (A-D)
- [ ] Client frontend: **READY** để bắt đầu ngay
- [ ] Admin frontend: **NOT READY** — cần SQLite + auth + endpoint admin trước

### 5. Khi đã có dữ liệu tương tác
- [ ] Huấn luyện mô hình xếp hạng thay cho công thức trọng số (Lớp 3 đầy đủ)
- [ ] Đánh giá bằng NDCG / Precision@K theo đề án mục 8
- [ ] ⚠️ Chỉ làm khi có nhãn thật — huấn luyện khi chưa có nhãn chỉ tạo ảo giác chính xác

---

## ⏸️ TẠM DỪNG (đừng làm tiếp nếu chưa bàn lại)

- **Floorplan → 3D (CubiCasa5K + YOLO/SegFormer):** đã bỏ hướng này. Code ở
  `src/infrastructure/ai/`, router `routers/spatial.py`, **tắt mặc định**
  (`MOODBITE_ENABLE_SPATIAL=1` để bật).
- **Depth Anything V2:** dừng vì lỗi môi trường.
- **Model ML gợi ý món:** model cũ **rò rỉ nhãn** — học `rule_id` từ `categoryName` trong
  khi `categoryName` chính là input, nên đạt 98.56% một cách vô nghĩa. Đã gỡ.
  ⚠️ **Không được trích dẫn 98.56% như bằng chứng có model tốt.**

---

## 🗺️ Bản đồ mã nguồn

```
src/
├── domain/                          QUY TẮC NGHIỆP VỤ — thuần Python, không framework
│   ├── entities/                      Restaurant, Dish, InteractionEvent
│   ├── value_objects/
│   │   ├── mood.py                    bảng điểm mood ⭐
│   │   ├── context_signal.py          thời tiết/giờ ảnh hưởng xếp hạng thế nào ⭐
│   │   ├── location.py                toạ độ + haversine
│   │   └── text.py                    bỏ dấu, khớp từ nguyên vẹn ⭐
│   └── services/
│       ├── search_ranking.py          CÔNG THỨC XẾP HẠNG ⭐⭐
│       └── text_relevance.py          khớp câu tự do với quán ⭐
├── application/
│   ├── ports/                         hợp đồng (Protocol) — không có code thật
│   └── use_cases/                     search_restaurants ⭐, log_interaction, get_restaurant_details
├── infrastructure/
│   ├── repositories/                  CSV/JSON → entity (pandas dừng ở đây)
│   ├── adapters/                      thời tiết Open-Meteo, model ML
│   ├── config/settings.py             mọi đường dẫn + biến môi trường ⭐
│   └── ai/                            script train (tạm dừng)
└── presentation/api/
    ├── dependencies.py                lắp mọi thứ lại ⭐
    ├── schemas.py                     hợp đồng với frontend ⭐
    ├── envelope.py                    {data}/{error} + mã lỗi
    ├── error_handlers.py              lỗi → mã HTTP
    └── routers/                       search, restaurants, interactions, meta

frontend/src/
├── domain/          session.js (UUID phiên), formatters.js (quy tắc hiển thị)
├── services/        httpClient.js (bóc envelope) ⭐, moodbiteApi.js (ánh xạ field) ⭐
└── features/
    ├── search/      useSearch.js, SearchPage.jsx, RestaurantCard.jsx
    └── map/         useUserLocation.js
```

⭐ = nên đọc đầu tiên khi quay lại dự án.

**Muốn sửa gì thì vào đâu:**

| Muốn sửa | Vào file |
|---|---|
| Công thức xếp hạng / trọng số | `domain/services/search_ranking.py` |
| Cách hiểu câu tìm kiếm | `domain/services/text_relevance.py` |
| Thời tiết/giờ ảnh hưởng thế nào | `domain/value_objects/context_signal.py` |
| Bảng điểm mood | `domain/value_objects/mood.py` |
| Danh sách món ăn | `data_pipeline/dish_knowledge_base.json` |
| Đường dẫn file, biến môi trường | `infrastructure/config/settings.py` |
| Field trả về cho frontend | `presentation/api/schemas.py` |
| Cách gọi API ở frontend | `frontend/src/services/moodbiteApi.js` |

---

## 📌 Quy ước cập nhật file này

- Chỉ đánh ✅ **sau khi đã chạy thật**.
- Mỗi ✅ nên kèm cách kiểm chứng.
- Phát hiện mục ✅ nào thực ra không chạy → **sửa lại ngay**, đây là lỗi nghiêm trọng nhất.

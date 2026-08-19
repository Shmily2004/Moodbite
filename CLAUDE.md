# CLAUDE.md — Quy tắc BẮT BUỘC cho AI khi làm việc trên MoodBite

File này dành riêng cho AI (Claude). Đọc TRƯỚC KHI sinh bất kỳ dòng code nào.
Mục tiêu: code chuyên nghiệp, sạch, cấu trúc rõ ràng — và quan trọng nhất là **chủ dự án
đọc lại phải hiểu được**.

> Quy tắc nghiệp vụ theo tài liệu gốc nằm ở `rules/`. File này nói về **cách làm việc**.
> Khi hai bên mâu thuẫn: `rules/` thắng về NGHIỆP VỤ, `CLAUDE.md` thắng về QUY TRÌNH.

## −1. MỘT BACKEND DUY NHẤT

Dự án CHỈ có một backend: **Python + FastAPI** ở `src/`.

Đã từng tồn tại backend TypeScript song song trong cùng thư mục `src/` — đó là nguyên nhân
gốc khiến cấu trúc không thể hiểu nổi. Nay nằm ở `archive/typescript-backend/`.

**TUYỆT ĐỐI KHÔNG:**
- Tạo thêm server thứ hai (Node/Express/Next API route/BFF) dưới bất kỳ tên gọi nào.
- Khôi phục code từ `archive/` mà không hỏi.
- Tạo file `.ts`/`.tsx` ngoài `frontend/`.
- Tạo `package.json` ở thư mục gốc.

Kiểm tra bất cứ lúc nào — mục 4 của `python scripts/verify.py` đã tự kiểm việc này.

Cần chức năng mới → thêm use case vào backend Python đang có, không dựng dịch vụ mới.

---

## 0. Ba luật tuyệt đối

1. **Không báo cáo thành công nếu chưa chạy thật.** "Tests pass" chỉ được nói sau khi đã
   chạy `pytest` và dán kết quả. "API hoạt động" chỉ được nói sau khi đã gọi endpoint thật.
2. **Không bịa số liệu, không bịa tên file, không bịa tên hàm.** Chưa kiểm chứng thì nói
   "chưa kiểm chứng".
3. **Không im lặng thu hẹp phạm vi.** Làm được 3/5 việc thì phải nói rõ 2 việc còn lại là
   gì và vì sao chưa làm.

**Bài học có thật của dự án này:** app từng KHÔNG khởi động được (`NameError` ở `main.py`)
trong khi toàn bộ test vẫn xanh, vì không test nào import app. Tài liệu vẫn ghi "hoạt động
tốt". → **Tin code chạy được, không tin tài liệu.**

---

## 1. Bắt buộc VERIFY trước khi nói xong

Sau MỌI thay đổi, chạy đúng một lệnh này và dán output:

```
python scripts/verify.py
```

Nó kiểm: app dựng được · test · hướng phụ thuộc · chỉ 1 backend · frontend build.

Không chạy được (thiếu thư viện, sai môi trường) → **nói rõ là chưa verify**, không được
suy đoán là "chắc ổn".

### ⚠️ Máy của chủ dự án chạy Windows PowerShell 5.1

Mọi lệnh đưa cho người dùng PHẢI chạy được ở đó. Cụ thể:

| KHÔNG dùng | Vì sao | Dùng thay thế |
|---|---|---|
| `a && b` | PowerShell 5.1 báo lỗi *"The token '&&' is not a valid statement separator"* | Mỗi lệnh một dòng riêng |
| `grep`, `wc`, `cat`, `head`, `sed` | Không tồn tại trên PowerShell | `Select-String`, `.Count`, `Get-Content` |
| `cp`, `rm -rf`, `/dev/null` | Cú pháp POSIX | `copy`, `Remove-Item`, `$null` |
| `export VAR=x` | Không phải cú pháp PowerShell | `$env:VAR = "x"` |

**Cách an toàn nhất: viết một script Python rồi bảo người dùng chạy `python scripts/....py`.**
Python chạy giống nhau ở mọi shell — không phải viết 2 phiên bản lệnh.

Đây là lỗi ĐÃ XẢY RA: tài liệu từng ghi `cd frontend && npm run build`, người dùng chạy
trên PowerShell và gặp ParserError ngay.

---

## 1b. KIẾN TRÚC ĐÃ CHỐT — hai tầng, hai kiến trúc, một nguyên tắc

Quyết định ngày 2026-08-16. **Không đổi nếu chưa bàn lại.**

```
FRONTEND (React)          Kiến trúc: FSD + MVVM
  app → pages → widgets → features → entities → shared
  Việc: TRÌNH BÀY + TƯƠNG TÁC
            │  HTTP /api/v1 (JSON)
            ▼
BACKEND (FastAPI)         Kiến trúc: Clean Architecture
  presentation → application → domain ← infrastructure
  Việc: NGHIỆP VỤ + DỮ LIỆU
```

### Vì sao hai bên KHÁC nhau

| | Backend | Frontend |
|---|---|---|
| Có quy tắc nghiệp vụ riêng | ✅ Có | ❌ Không |
| Bài toán chính | Nghiệp vụ phức tạp, nhiều nguồn dữ liệu | Tổ chức UI, luồng tương tác |
| Kiến trúc | Clean Architecture | Feature-Sliced Design + MVVM |
| Kiểm tra tự động | `python scripts/check_architecture.py` | `npx steiger ./src` |

**Điểm chung — nguyên tắc gốc duy nhất: DEPENDENCY RULE.**
Phụ thuộc chỉ đi MỘT CHIỀU, và phải cưỡng chế được bằng máy trong CI.

### 🚫 BUSINESS LOGIC CHỈ ĐƯỢC NẰM Ở BACKEND

Đây là chốt chặn quan trọng nhất của mục này.

Frontend **KHÔNG** được chứa: công thức xếp hạng · bảng điểm mood · quy tắc suy luận món ·
ngưỡng lọc · quy tắc nghiệp vụ bất kỳ.

Frontend **CHỈ** được chứa: quy tắc HIỂN THỊ (định dạng khoảng cách, giá, nhãn tin cậy),
state của giao diện, điều phối gọi API.

> Lý do: dự án này từng suýt chết vì có HAI nơi chứa nghiệp vụ (hai backend song song).
> Thêm "business layer" ở frontend là tái phạm đúng sai lầm đó — sửa công thức xếp hạng
> sẽ phải sửa 2 chỗ, và chắc chắn sẽ có lúc quên một chỗ.

### Ánh xạ thuật ngữ (dùng khi viết báo cáo / bảo vệ)

Dự án CÓ ĐỦ 3 lớp cổ điển, chỉ khác tên gọi:

| Thuật ngữ cổ điển | Trong MoodBite | File |
|---|---|---|
| Model / Business | Backend Clean Architecture | `src/domain/`, `src/application/` |
| Data Access | Repository + Port | `src/infrastructure/repositories/` |
| Controller | Hook (ViewModel) | `features/*/model/use*.js` |
| View | Component React | `features/*/ui/*.jsx` |

React không có khái niệm Controller như MVC server-render, nên Controller được hiện thực
bằng hook. Đây là lựa chọn CÓ CHỦ ĐÍCH, không phải thiếu sót.

### Cấu trúc frontend bắt buộc

```
src/
├── app/        khởi tạo, router, provider
├── pages/      một route = một page
├── widgets/    khối UI ghép sẵn dùng lại được
├── features/   MỘT hành động người dùng = một feature
│   └── <ten-feature>/
│       ├── ui/      VIEW — chỉ JSX, không gọi API, không giữ state phức tạp
│       ├── model/   VIEWMODEL — hook: state + điều phối
│       └── api/     gọi shared/api
├── entities/   khái niệm nghiệp vụ (restaurant, dish, interaction)
└── shared/     api client, UI cơ bản, lib, config
```

**Luật import: chỉ được đi XUỐNG.** `pages → widgets → features → entities → shared`.
Cấm import ngược lên, cấm import ngang giữa hai feature.

### Ràng buộc CHI PHÍ — chủ dự án không có thẻ thanh toán

Không được đề xuất giải pháp cần thẻ tín dụng/ghi nợ. Cụ thể:

| Cần trả tiền / cần thẻ | Dùng thay thế miễn phí |
|---|---|
| Google Maps JavaScript API | **Leaflet + tile OpenStreetMap** |
| Google Places API (rating/review) | Apify free tier theo tháng, hoặc nhập tay |
| Google Routes API (thời gian đi thật) | Khoảng cách haversine (đã có) |
| Dịch vụ embedding trả phí | TF-IDF (đã có, chạy CPU) |

Google Maps có hạn mức miễn phí NHƯNG vẫn bắt buộc bật thanh toán mới dùng được — với
người không có thẻ thì coi như không dùng được.

---

## 2. Hướng phụ thuộc — chốt chặn không được phá

```
presentation ──┐
               ├──> application ──> domain
infrastructure ┘
```

| Tầng | Được import | CẤM |
|---|---|---|
| `domain/` | chỉ `domain` | fastapi, pandas, torch, pydantic, joblib… — **thuần Python** |
| `application/` | `domain` | fastapi, pandas, mọi framework |
| `infrastructure/` | `domain`, `application` | `presentation` |
| `presentation/` | tất cả | import `infrastructure` ngoài `dependencies.py`/`main.py` |

`scripts/check_architecture.py` kiểm tra tự động trong CI. **Vi phạm = CI đỏ.**
Không được "sửa" bằng cách nới lỏng checker — phải sửa code.

Đặt code ở đâu:

- Quy tắc nghiệp vụ (chấm điểm mood, xếp hạng, khoảng cách) → `domain/`
- Điều phối một luồng (gọi repo → gọi domain → trả kết quả) → `application/use_cases/`
- Đọc/ghi file, DB, gọi API ngoài, ML → `infrastructure/`
- HTTP, schema, mã lỗi → `presentation/`

**Test nhanh:** nếu phải import pandas hoặc fastapi để test một quy tắc nghiệp vụ →
quy tắc đó đang nằm sai tầng.

---

## 3. Thêm tính năng — thứ tự bắt buộc

1. Viết/ sửa **port** ở `application/ports/` (hợp đồng trước, code sau).
2. Viết **use case** ở `application/use_cases/` — chỉ điều phối, không logic nghiệp vụ.
3. Quy tắc nghiệp vụ → `domain/`.
4. **Adapter** ở `infrastructure/` triển khai port.
5. Lắp vào `presentation/api/dependencies.py`.
6. Router ở `presentation/api/routers/` — mỏng, không try/except nuốt lỗi.
7. Test: domain (thuần) → use case (repo giả) → API (TestClient).

Không được nhảy cóc, đặc biệt không được viết logic nghiệp vụ thẳng trong router.

---

## 4. Quy tắc về dữ liệu — đã trả giá để học

Bốn quy ước dưới đây phản ánh dữ liệu THẬT của dự án. Vi phạm = hiển thị sai cho người dùng.

1. **`None` nghĩa là CHƯA CÓ DỮ LIỆU, không phải 0.**
   Chỉ 350/4170 quán có rating, 228/4170 có giá. Biến `None` thành `0` là nói dối người
   dùng ("0 sao", "miễn phí"). Được phép coi là 0 **chỉ khi xếp hạng nội bộ**, và giá trị
   trả về vẫn phải là `None`.

2. **`price` là CHUỖI, không phải số.** Giá trị thật: `"1-100.000 ₫"`, `"70 US$"`,
   `"Trên 1 Tr ₫"`. Ép về `float` làm hỏng response — đây là bug đã từng xảy ra.

3. **Thiếu file dữ liệu KHÔNG được làm sập app.** Repository ghi nhận lỗi, `/health` báo
   `ready: false` kèm lý do, endpoint liên quan trả **503 kèm cách khắc phục**.

4. **Món ăn là SUY LUẬN, không phải menu thật.** Luôn trả kèm `confidence`
   (`specific` / `generic_fallback` / `unknown` / `ml`) và UI phải hiển thị nó.
   Điều này áp cho CẢ hai chiều: chiều quán→món (`suggested_dish`) lẫn chiều món→quán
   (`/dishes/{id}/restaurants`). Ta đối chiếu theo TÊN QUÁN, chưa bao giờ đọc thực đơn
   thật, nên không được nói chắc là quán có bán.

5. **So khớp chữ tiếng Việt: BỎ DẤU + khớp TỪ NGUYÊN VẸN.** Dùng
   `domain/value_objects/text.py`, đừng tự viết lại. Hai bug thật đã xảy ra vì làm sai:
   - Khớp chuỗi con: `"bo"` khớp `"bột"` → tìm "phở bò" ra quán bánh tráng.
   - Không bỏ dấu: quán tên `"Pho Bo"`, `"O Bun Cha"` không bao giờ khớp được.

6. **Suy luận món thì ưu tiên TÊN QUÁN hơn `categoryName`.** Đo được: 144 quán có "phở"
   trong tên nhưng chỉ 14 quán có trong `categoryName`. Quán "Bún Chả - Nem Cua Bê" bị
   Google gắn nhãn "Nhà hàng ăn nhanh" → chỉ dùng category sẽ gợi ý "Gà rán".

7. **Tín hiệu ngữ cảnh (thời tiết/giờ) hỏng KHÔNG được làm hỏng lượt tìm kiếm.**
   Trả ngữ cảnh trung lập là đủ.

---

## 4b. Thu thập dữ liệu — quy tắc bắt buộc

**Kiến trúc:** mọi nguồn tuân theo `SourceAdapter` ở `data_pipeline/sources/base.py`.
Thêm nguồn mới = 1 adapter + 1 dòng đăng ký. **KHÔNG sửa pipeline, KHÔNG viết script rời.**

**PHẠM VI ĐỊA LÝ: CHỈ HÀ NỘI** (chủ dự án chốt 2026-08-19). Không thu thập quán ở tỉnh
/thành khác. `CITY_BBOXES` trong `sources/osm_overpass.py` chỉ có đúng một mục `ha_noi`,
và `harvest.py` báo lỗi nếu truyền `--city` khác. Muốn mở rộng thì phải HỎI TRƯỚC.

**CẤM thu thập từ:** ShopeeFood, GrabFood, Foody, TripAdvisor, Facebook — ToS của họ cấm
truy cập tự động. Đồ án tốt nghiệp không được xây trên nền vi phạm ToS. Xem
`docs/data_sources.md` để biết phương án thay thế hợp pháp cho từng nhu cầu.

**Mọi bản ghi BẮT BUỘC có:** `source`, `source_url`, `last_updated`, `data_confidence`.
Không có nguồn rõ ràng thì không được đưa vào dataset.

**KHÔNG BỊA DỮ LIỆU.** Thiếu thì để `None`. Tuyệt đối không suy đoán rating, giá, hay
giờ mở cửa.

**Khi làm việc với Overpass API:**
- Luôn CHIA Ô — hỏi cả Hà Nội một lần luôn trả HTTP 504.
- Luôn có nhiều mirror + thử lại nhiều vòng; 504 là lỗi TẠM THỜI, cùng query lúc rảnh
  chỉ mất ~8 giây. Bỏ ô = mất vĩnh viễn toàn bộ quán khu vực đó.
- Luôn cache theo ô để chạy lại không tốn công.
- Kiểm tra `https://overpass-api.de/api/status` để biết còn slot không.

**Đo trước và sau mỗi lần bổ sung dữ liệu:**
```
python scripts/data_report.py
```
Không có số đo thì không được nói "dữ liệu đã cải thiện".

### Review / ảnh / rating / giá — ĐỪNG XOÁ, ĐỪNG HỨA THÊM

Trạng thái thật (đo 2026-08-16): **440/4226 quán (10.4%)** có review + ảnh + giá, lấy từ
Apify Google Maps từ trước. Phần này **ĐÃ CHẠY XONG**: lưu ở `restaurant_details.json`,
trả qua `GET /api/v1/restaurants/{id}`, hiển thị ở `RestaurantCard.jsx`, và được dùng làm
tín hiệu tìm kiếm (trọng số 0.55 trong `text_relevance.py`).

- ❌ **KHÔNG xoá** phần này. Nó đang chạy tốt và không tốn công duy trì.
- ❌ **KHÔNG hứa** sẽ cào thêm bằng cách miễn phí. Không tồn tại cách miễn phí + hợp pháp:
  OSM không có rating/review/ảnh; Apify và Google Places đều trả phí; ShopeeFood/Foody/
  Facebook cấm theo ToS.
- ✅ **Gọi đúng tên:** đây là **lớp làm giàu (enrichment)**, không phải tính năng lõi.
  Luôn kèm tỷ lệ phủ khi nhắc tới.

### Công cụ KHÔNG liên quan tới thu thập dữ liệu quán

Nếu người dùng đề xuất dùng các thứ sau để "lấy dữ liệu Google Maps", phải nói rõ là
không liên quan, thay vì làm theo:

| Công cụ | Thực chất làm gì |
|---|---|
| `faster-whisper` / Whisper | Chuyển GIỌNG NÓI thành chữ. Không biết Google Maps là gì |
| OCR | Đọc chữ trong ảnh |
| YOLO / SegFormer | Nhận diện vật thể trong ảnh (phần floorplan đã tạm dừng) |

Whisper CÓ một công dụng hợp lệ khác, đúng như đề án mục 7 nhắc tới: chuyển video review
TikTok/YouTube thành chữ rồi trích tên quán. Nhưng đó là **bài toán khác**, cần thêm bước
nhận diện thực thể và đối chiếu dataset — không phải "trích xuất Google Maps".

---

## 4c. Các lớp mô hình — thứ tự chạy pipeline BẮT BUỘC

```
merge_and_prepare_raw  →  data_cleaning  →  feature_engineering  →  clustering
```

⚠️ `clustering` PHẢI chạy CUỐI. Chạy `feature_engineering` sau sẽ **xoá mất** 2 cột
`experience_cluster_id` / `experience_cluster_label` và phải phân cụm lại.

| Lớp (đề án) | Trạng thái | Ở đâu |
|---|---|---|
| 1. Phân cụm trải nghiệm | ✅ KMeans k=7 | `data_pipeline/clustering.py` (offline) |
| 2. Tìm kiếm ngữ nghĩa | ✅ TF-IDF cosine | `infrastructure/adapters/tfidf_semantic_search.py` |
| 3. Xếp hạng ngữ cảnh | 🟡 công thức trọng số | `domain/services/search_ranking.py` |
| 4. Tóm tắt review | ❌ chưa làm | review TB 106 ký tự, quá ngắn |
| 5. Gợi ý món | ✅ **cửa vào chính** | `domain/services/dish_ranking.py` + `use_cases/suggest_dishes.py` |

**Quy tắc bắt buộc khi động vào các lớp này:**

- **sklearn CHỈ được xuất hiện ở `data_pipeline/` và `infrastructure/`.** Domain phải
  thuần Python — checker kiến trúc sẽ chặn nếu vi phạm.
- **Cold Start (rules/rules.md mục 3.3):** quán chưa phân cụm dùng `NEUTRAL_CLUSTER_SCORE`
  (0.5), TUYỆT ĐỐI không dùng 0 hay NULL. Quán chưa phân cụm ≠ quán dở.
- **Tổng trọng số xếp hạng phải = 1.0** để `predicted_score` luôn trong [0,1]. Có test khoá.
- **Mọi thành phần ML phải suy biến an toàn:** thiếu sklearn / chưa đủ dữ liệu → trả rỗng
  và hệ thống lui về khớp từ khoá, KHÔNG được làm hỏng lượt tìm kiếm.
- **Chọn siêu tham số bằng SỐ ĐO, không bằng cảm tính.** Mọi hằng số (k, ngưỡng tín hiệu
  tối thiểu, kích thước cụm nhỏ nhất) đều phải có comment ghi rõ đã thử gì và vì sao chọn.

---

## 5. Hợp đồng API — bất di bất dịch

Nguồn sự thật: `docs/extracted/MoodBite_Dac_Ta_API.md`. Bốn quy ước KHÔNG được phá:

1. **Base URL `/api/v1`** — có version ngay từ đầu.
2. **Envelope:** thành công `{"data": …}`, lỗi `{"error": {"code","message","details"}}`.
   Router phải trả qua `envelope.success()` / `envelope.error()`.
3. **Tên trường `snake_case`** (`restaurant_id`, `predicted_score`) — KHÔNG camelCase.
4. **Có HAI lối vào, đừng nhầm** (chốt 2026-08-19):
   - `POST /dishes/suggest` → `GET /dishes/{id}` → `GET /dishes/{id}/restaurants`
     là **luồng chính**: chọn món trước, tìm quán sau.
   - `POST /search` (tìm bằng câu tự nhiên) vẫn giữ, và `suggested_dish` vẫn nằm TRONG
     từng kết quả của nó — KHÔNG tách thành endpoint riêng cho luồng đó.
   Hai lối vào dùng CHUNG một bộ từ khoá món (`dish_seed_manual.json`) nên không thể
   nói khác nhau. Đừng tạo bộ từ khoá thứ hai.

| Tình huống | HTTP | `error.code` |
|---|---|---|
| Thiếu trường bắt buộc / giá trị sai | 400 | `INVALID_REQUEST` |
| Không tìm thấy quán (hoặc `is_active=false`) | 404 | `RESTAURANT_NOT_FOUND` |
| Chưa chạy data_pipeline | 503 | `DATA_NOT_READY` (**kèm lệnh cần chạy**) |
| API bên thứ ba lỗi, không có fallback | 503 | `EXTERNAL_SERVICE_UNAVAILABLE` |
| Bug của server | 500 | `INTERNAL_ERROR` (log traceback, **không** trả cho client) |
| Quán chưa có chi tiết | **200** + `has_details: false` | KHÔNG phải 404 — quán vẫn tồn tại |

**Cấm** bọc `except Exception` quanh route rồi trả 400 — cách đó từng biến mọi bug lập
trình thành "400 Bad Request" và giấu lỗi thật. Lỗi được ánh xạ tập trung ở
`presentation/api/error_handlers.py`.

**Không im lặng bỏ qua tham số client gửi lên.** Không làm được thì thêm câu giải thích
vào `data.warnings` (đã có tiền lệ: `dietary_restrictions` không có dữ liệu, và
`/suggest-dish` cũ từng lặng lẽ bỏ qua `max_distance_km` → gợi ý quán cách 46km).

---

## 6. Chuẩn viết code

- **Đặt tên nói ý định:** `filter_by_radius` chứ không `process`. Không viết tắt tự chế.
- **Comment giải thích TẠI SAO, không phải CÁI GÌ.** Code đã nói cái gì rồi.
  - Tốt: `# Lọc bán kính TRƯỚC khi xếp hạng: quán cách 36km là vô dụng dù điểm cao.`
  - Vô dụng: `# lọc theo bán kính`
- **Số magic phải thành hằng số có tên** kèm lý do (xem `DEFAULT_MAX_DISTANCE_KM`).
- **Một file một trách nhiệm.** File > ~300 dòng là tín hiệu cần tách.
- **Không `print()` trong code chạy production** — dùng `logging`.
- **Không tạo singleton cấp module** (`service = Service()` ở cuối file). Đây là lỗi cũ
  của dự án: nó đọc file ngay lúc import, tạo 2 bản dữ liệu trong RAM, và làm test khó.
  Mọi thứ đi qua `dependencies.py`.
- **Không hardcode đường dẫn.** Thêm vào `infrastructure/config/settings.py`.
- Tiếng Việt trong comment/docstring là **được khuyến khích** (chủ dự án đọc bằng tiếng
  Việt). Tên biến/hàm dùng tiếng Anh.

---

## 7. Sửa bug

1. **Tái hiện trước.** Chưa tái hiện được thì chưa được sửa.
2. **Viết test đỏ trước**, rồi sửa cho xanh.
3. **Sửa nguyên nhân gốc**, không vá triệu chứng.
4. Comment lại **tại sao** bug xảy ra, nếu không người sau sẽ "dọn dẹp" đúng chỗ đó.

---

## 8. Trước khi xoá / refactor lớn

- Xoá code đang chạy được → **hỏi trước**.
- Đổi tên field API → **breaking change**, phải sửa `frontend/src/services/` cùng lúc.
- Code có thể còn dùng lại → chuyển vào `archive/` thay vì xoá hẳn.
- Không tự ý đổi hành vi mà người dùng không yêu cầu.

---

## 9. Khi không chắc

- Mơ hồ nhưng đoán được ý → **chọn phương án hợp lý, nói rõ đã giả định gì**, rồi làm tiếp.
- Hai cách hiểu dẫn tới kết quả khác hẳn nhau → **hỏi**.
- Phát hiện thứ nằm ngoài phạm vi được giao → **báo cáo, không tự sửa**.

Không hỏi những câu đã có câu trả lời trong repo — đọc code trước.

---

## 10. Checklist tự kiểm trước khi trả lời "xong"

- [ ] Đã chạy `pytest` và dán kết quả thật?
- [ ] Đã chạy `scripts/check_architecture.py`?
- [ ] Đã chạy thử endpoint/tính năng vừa sửa?
- [ ] Có tạo singleton cấp module không? (không được)
- [ ] Có hardcode đường dẫn không? (không được)
- [ ] `None` có bị biến thành `0` ở chỗ nào trả về cho client không?
- [ ] Có logic nghiệp vụ nằm trong router không?
- [ ] Đã cập nhật `PROJECT_CHECKLIST.md` nếu trạng thái dự án đổi?
- [ ] Đã nói rõ phần nào CHƯA làm / CHƯA verify?

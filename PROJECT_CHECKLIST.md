# MoodBite — Bảng theo dõi tiến độ

**Cập nhật:** 2026-08-17
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
| Ngữ cảnh thời điểm | ✅ Giờ ăn · ✅ thời tiết (tắt mặc định) | đã gọi thật Open-Meteo: 27.2°C, 0.94s; 17 test suy biến |
| Frontend Client | ✅ **TypeScript + FSD** | 21 test, có bản đồ, steiger trong CI |
| Bản đồ | ✅ **Xong** | Leaflet + OpenStreetMap, miễn phí, không cần key |
| Kiến trúc | ✅ Sạch | Clean Architecture + checker tự động trong CI |
| Test | ✅ 234 backend + 47 frontend | tổng 281, chạy hết 15 giây |
| Giao diện | ✅ Theo bản duyệt | thanh trên + bản đồ + rail đề xuất; mức phù hợp là nhãn chữ |
| Router + layout | ✅ Xong | react-router v6, khung dùng chung, `RequireAuth` cho admin |
| Chạy xem giao diện | ✅ **một lệnh** | `python scripts/run_dev.py --admin` |
| Kho lưu trữ | ✅ CSV (mặc định) · ✅ SQLite (chọn được) | `MOODBITE_STORAGE=sqlite`, kết quả GIỐNG HỆT |
| **Frontend Admin** | ✅ **Code xong** · ⬜ **chưa bật** | `python scripts/check_permissions.py` để xem thiếu gì |
| Xác thực admin | ✅ Code xong | 1 tài khoản, token HMAC 1 giờ, fail-closed |
| Phụ thuộc Python | ✅ 15 → **7** gói | gỡ torch/ultralytics/transformers/opencv (~2GB) khỏi CI |
| Dữ liệu | ✅ 4938 quán · 142 đơn vị HC | provenance 100%, trùng lặp 0% |
| Thu thập dữ liệu đa nguồn | ✅ Xong | kiến trúc `SourceAdapter`, thêm nguồn không sửa pipeline |
| Lọc giờ mở cửa / chế độ ăn / quận | ✅ Xong | thiếu dữ liệu KHÔNG bị loại |
| **Lớp 1 — Phân cụm trải nghiệm** | ✅ **Xong** | KMeans k=7, Silhouette 0.318 |
| **Lớp 2 — Tìm kiếm ngữ nghĩa** | ✅ **Xong** | TF-IDF cosine, 4938 quán |
| Lớp 4 — Tóm tắt review | 🟡 Chưa làm, nhưng ĐÃ KHẢ THI | đo lại: gộp theo quán TB 666 ký tự, 592 quán đủ điều kiện |
| Đăng nhập / tài khoản | 🟡 **Backend xong, chưa có UI** | `/api/v1/auth/*`: đăng ký · đăng nhập · `/me`. Đổi phạm vi có chủ đích so với SRS mục 8 — xem ghi chú dưới bảng |
| Phân quyền (`role`) | 🟡 Có `user`/`admin` + guard 403 | admin VẪN dùng biến môi trường, chưa chuyển sang bảng `users` |

> **Ghi chú — tài khoản người dùng là ĐỔI PHẠM VI CÓ CHỦ ĐÍCH (2026-08-17).**
> SRS mục 8 và `docs/extracted/MoodBite_Dac_Ta_API.md` xếp tài khoản vào *Won't-have*.
> Chủ dự án quyết định đưa vào vì phân quyền và cá nhân hoá là phần làm đề tài có giá trị
> hơn. Hai tài liệu trong `docs/extracted/` **cố ý giữ nguyên** — chúng là bản gốc đã nộp,
> sửa lại là làm sai lịch sử. Chỗ nào mâu thuẫn thì **code + dòng này thắng**.
>
> Chưa làm: đăng xuất có thu hồi token, `user_id` trong `POST /interactions`, lưu quán yêu
> thích ở server, và toàn bộ giao diện Login/Register/Profile.

**Tự kiểm toàn bộ bằng MỘT lệnh** (chạy được ở PowerShell, CMD, bash, macOS, Linux):

```
python scripts/verify.py
```

Lệnh này kiểm 8 việc và in rõ từng mục đạt/hỏng: app dựng được · test backend ·
hướng phụ thuộc · **chỉ có 1 backend** · frontend build · test frontend · luật import
FSD · **CI cài đặt được**.

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
- [x] **Lớp 1 — Phân cụm trải nghiệm (KMeans):** `data_pipeline/clustering.py`
      - Đặc trưng: mức giá · đánh giá · độ phổ biến (log) · không gian · số tiện nghi
      - **k=7** chọn bằng Silhouette (thử k=3..8, có ràng buộc cụm ≥1% để loại cụm nhiễu)
      - **Silhouette 0.318 · Davies-Bouldin 1.025 · Calinski-Harabasz 413.1**
      - Phân cụm 1197/4938 quán có đủ tín hiệu; còn lại để TRỐNG theo quy tắc Cold Start
      - Cụm dùng làm 1 tín hiệu xếp hạng (trọng số 0.10), KHÔNG phải quyết định cuối cùng
- [x] **Lớp 2 — Tìm kiếm ngữ nghĩa (TF-IDF + cosine):**
      `infrastructure/adapters/tfidf_semantic_search.py`, chỉ mục 4938 quán
      - n-gram ký tự (2-4) thay vì tách từ, vì tiếng Việt không tách từ bằng khoảng trắng
      - Khớp được cách diễn đạt khác nhau: "yên tĩnh" ↔ review "tĩnh lặng"
      - Đứng sau một PORT nên đổi sang sentence-transformers sau này không phải sửa use case
- [x] **Lớp 2 (bổ trợ) — khớp từ khoá:** tên → loại hình → không gian → review,
      kèm `match_source` nói rõ khớp nhờ đâu
- [x] **Lớp 3 — xếp hạng theo ngữ cảnh:** `predicted_score` tổng hợp 6 tín hiệu
      (tổng trọng số = 1.0, nên điểm luôn nằm trong [0,1] và giải thích được):

      | Tín hiệu | Trọng số |
      |---|---|
      | khớp từ khoá | 0.22 |
      | **khớp ngữ nghĩa (Lớp 2)** | **0.16** |
      | mood + ngữ cảnh thời điểm | 0.26 |
      | khoảng cách | 0.17 |
      | đánh giá | 0.09 |
      | **cụm trải nghiệm (Lớp 1)** | **0.10** |
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
- [x] **CI frontend chắc chắn đỏ sau khi chuyển sang monorepo** (2026-08-17) —
      `frontend/package-lock.json` bị xoá lúc dựng lại frontend, nhưng `ci.yml` vẫn
      `cache-dependency-path: frontend/package-lock.json` + `npm ci`. Máy local vẫn xanh
      vì `node_modules` đã cài sẵn → **verify.py không phát hiện được**. Đã sinh lại
      lockfile và kiểm chứng bằng chính lệnh CI dùng (`npm ci` → exit 0).
- [x] **`npm run typecheck` không chạy được** — script gọi `tsc --build` nhưng không có
      `frontend/tsconfig.json` (TS5083). Không nằm trong CI nên hỏng âm thầm.
- [x] **`@moodbite/ui` trỏ vào file không tồn tại** — đã khai dependency + alias ở
      `vite.config.ts`/`tsconfig.json` nhưng `packages/ui/src/index.ts` chưa có
- [x] **Quán đã ẩn VẪN XEM ĐƯỢC nếu biết link** (2026-08-17) — `GET /restaurants/{id}`
      chỉ đọc kho CHI TIẾT, mà kho đó không có khái niệm `is_active`. Ẩn quán xong nó
      biến mất khỏi `/search` nhưng vào thẳng link vẫn ra 200.
      ⚠️ **Test đơn vị KHÔNG bắt được** — chúng chỉ kiểm ở tầng repository. Chỉ test
      end-to-end chạy uvicorn thật mới lộ ra.
- [x] **Test khoá SAI hành vi** (2026-08-17) — `test_restaurant_detail_missing_is_200_not_404`
      dùng id KHÔNG tồn tại rồi khẳng định phải trả 200, trong khi bảng mã lỗi mục 5 nói
      id không tồn tại phải là 404. Đã sửa test cho đúng đặc tả và tách thành 2 ca.
- [x] **CI frontend chắc chắn đỏ** (2026-08-17) — `frontend/package-lock.json` bị xoá lúc
      chuyển monorepo nhưng `ci.yml` vẫn `npm ci`. Máy local xanh vì đã có `node_modules`.
      Nay `verify.py` mục 8 tự kiểm việc này.

### Frontend
- [x] Dựng lại theo cấu trúc feature-based (phương án A trong `docs/frontend_architecture.md`)
- [x] Ô tìm kiếm bằng câu tự do + gợi ý câu mẫu
- [x] Định vị thật qua Geolocation API (**miễn phí, không cần key**)
- [x] Tầng `services/` bóc envelope; component không gọi `fetch` trực tiếp
- [x] Huỷ request cũ bằng `AbortController` (bấm nhanh 2 lần không còn ghi đè kết quả)
- [x] 1 lượt gọi API thay vì 2 lượt tuần tự
- [x] Hiện `match_source` và `dish_confidence` — nói thật vì sao quán được gợi ý
- [x] Ghi tương tác khi người dùng xem chi tiết / bấm chỉ đường

### Tín hiệu thời tiết (2026-08-17)
- [x] Gọi THẬT Open-Meteo: Hoàn Kiếm 27.2°C, `CLEAR`, mất 0.94s, không cần key
- [x] 17 test ở `tests/test_context_provider.py` khoá cơ chế suy biến: mất mạng /
      timeout / HTTP 500 / JSON hỏng đều cho ngữ cảnh trung lập, **tín hiệu giờ vẫn đúng**
- [x] Kiểm bằng mutation test: bỏ `except Exception` → 5 test đỏ ngay

### Kho lưu trữ ghi được — SQLite (2026-08-17)
- [x] `SqliteRestaurantRepository` — use case KHÔNG đổi một dòng nào.
      Bật bằng `MOODBITE_STORAGE=sqlite`, mặc định vẫn là CSV.
- [x] Dựng CSDL: `python scripts/build_sqlite.py` → 4938 quán, 4.0 MB
- [x] **Đối chiếu từng trường của 4938 quán: KHỚP HOÀN TOÀN với bản CSV**
- [x] Gọi API thật trên cả hai kho: `predicted_score` giống hệt tới 6 chữ số
- [x] Có cột `is_active` (soft-delete) — thứ bản CSV không lưu được

### Trang quản trị (2026-08-17)
- [x] **Xác thực** — 1 tài khoản + token HMAC ngắn hạn (mặc định 1 giờ).
      Dùng `hmac`/`hashlib`/`secrets` của thư viện chuẩn, KHÔNG thêm thư viện nào.
      PBKDF2-SHA256 600k vòng. **Fail-closed**: thiếu cấu hình → 503, không bao giờ mở.
- [x] **Endpoint `/api/v1/admin/*`** — login · list · PATCH · hide · restore
      - Trường sửa được do DOMAIN quyết định (`domain/value_objects/restaurant_edit.py`),
        không phải router. Sửa `rating`/cụm → 400, vì chúng do pipeline sinh ra.
      - Xác thực gắn ở CẤP ROUTER → thêm endpoint mới KHÔNG THỂ quên bảo vệ.
- [x] **`apps/admin`** — React + TS, cùng cấu trúc FSD với client, cổng 5174
- [x] **Ranh giới client/admin cưỡng chế bằng KIỂU**: `createApi()` trả lớp không hề có
      method quản trị; `createAdminApi()` bắt buộc truyền hàm lấy token
- [x] 37 test ở `tests/test_admin_api.py`, chạy thật end-to-end với uvicorn

### Chốt chặn MÀN HÌNH TRẮNG + cách chạy (2026-08-17)

Chủ dự án báo "mở giao diện lên không thấy gì". Đã kiểm bằng trình duyệt THẬT (Edge
headless, `--dump-dom`): **cả hai app đều render đúng** — client hiện header + ô tìm kiếm,
admin hiện form đăng nhập. Code không hỏng. Hỏng là ở CÁCH HƯỚNG DẪN CHẠY.

- [x] **Smoke test render `<App />`** cho cả hai app — trước đó KHÔNG CÓ.
      21 test frontend cũ chỉ kiểm `format.ts` và `RestaurantCard.tsx` (hai file lá),
      app quản trị thì **0 test**. Đây đúng là lỗ hổng backend đã trả giá để học
      (CLAUDE.md mục 0): test xanh nhưng app không chạy được, vì không test nào dựng app.
- [x] Test app admin vào `verify.py` mục 6 và vào CI — trước đó CI chỉ chạy test client
- [x] **`python scripts/run_dev.py [--admin]`** — một lệnh chạy cả backend lẫn giao diện,
      tự kiểm điều kiện và in rõ địa chỉ. Trước đây phải mở 3 terminal, nhớ 3 lệnh ở 2
      thư mục; thiếu một bước là màn hình trắng mà không có gì báo thiếu bước nào.
- [x] README gốc: thêm hẳn mục "Giao diện nằm ở đâu" + 3 nguyên nhân màn hình trắng.
      README cũ **không hề nhắc tới app quản trị**, và còn ghi sai (bản đồ "chưa làm",
      floorplan "bật bằng biến môi trường" trong khi đã archive).

> Nguyên nhân hay gặp nhất của màn hình trắng: bấm đúp mở
> `frontend/apps/client/dist/index.html`. File build trỏ `/assets/...` theo đường dẫn
> TUYỆT ĐỐI, mở bằng `file://` sẽ không tìm thấy. Phải mở qua `http://localhost:5173`.

### Router + layout dùng chung (2026-08-17)
- [x] **react-router v6** cho cả hai app. Trước đó client render thẳng 1 trang, admin
      chỉ bật/tắt giữa 2 trạng thái — thêm trang thứ hai là phải sửa `App.tsx`.
- [x] **Khung dùng chung** ở `app/layout/`: client có `RootLayout` (header + footer),
      admin có `AdminLayout` (thanh trên + điều hướng + đăng xuất). Trang cắm qua `<Outlet />`.
- [x] **`RequireAuth` đặt ở tầng NGOÀI** cây route admin → thêm trang mới là tự động
      được bảo vệ, KHÔNG THỂ quên. Bản song song của việc backend gắn xác thực cấp router.
- [x] Đăng nhập xong quay lại đúng trang đang định vào (`state.from`)
- [x] Trang 404 cho cả hai app, **vẫn nằm trong khung layout**
- [x] `ROUTES` để ở `shared/config/` chứ không ở `app/` — vì `pages/` cũng cần, mà luật
      FSD cấm import ngược lên. `steiger` đã chặn đúng lúc viết sai chỗ này.
- [x] Kiểm bằng TRÌNH DUYỆT THẬT: 4 đường dẫn (client `/`, client 404, admin `/login`,
      admin `/` chưa đăng nhập → đá về login) đều render đúng. Deep-link không 404.

### Giao diện theo bản duyệt của chủ dự án (2026-08-17)

Chủ dự án nhận xét giao diện xấu và chưa đúng ý. Đã dựng **bản đặc tả 12 màn hình để
DUYỆT TRƯỚC**, chốt xong mới code — không tự ý redesign nữa.

- [x] **Bố cục: thanh trên + bản đồ + rail đề xuất.** Bản đồ KHÔNG còn chiếm cả màn hình.
      MoodBite không phải Google Maps clone — gõ "quán lẩu ấm cúng gần đây" thì thứ cần
      thấy trước là QUÁN NÀO PHÙ HỢP, không phải bản đồ.
- [x] **Mức phù hợp lên vị trí thứ hai trong thẻ**, ngay dưới tên quán.
- [x] **`match_source` dịch sang câu người đọc hiểu**: 😌 Hợp với "..." · 🔎 Khớp tên quán,
      đánh giá · 🍽 món + mức tin cậy.
- [x] Trạng thái thiếu: không kết quả (kèm nút "Mở rộng 20 km" / "Bỏ lọc đang mở"), lỗi
      mạng, đang tải (vệt xương).
- [x] **Admin dùng CHUNG hệ token với client**, chỉ khác màu nhấn (xanh dương) và chấm
      thương hiệu vuông thay vì tròn — cố ý, để không nhầm màn hình khi sửa dữ liệu thật.
- [x] `thumbnail_url` vào kết quả tìm kiếm (entity → 2 repository → cột SQLite → schema
      → router). Đo được: **chỉ 1064/4938 quán (21.5%) có ảnh**, nên quán không ảnh dùng
      ô màu sinh từ tên + biểu tượng theo loại hình — trông có chủ đích, không phải ảnh vỡ.

**⚠️ KHÔNG hiện `predicted_score × 100` thành "% phù hợp".** Đo 40 kết quả của 4 câu tìm:
điểm cao nhất 0.721, trung vị 0.613, thấp nhất 0.576. Hiện "61% phù hợp" khiến người dùng
tưởng máy gợi ý kém, trong khi đó lại là quán khớp nhất — vì `predicted_score` là điểm
XẾP HẠNG, không phải xác suất. Dùng nhãn định tính (Rất phù hợp / Phù hợp / Có thể hợp)
+ thanh so sánh tương đối. Ngưỡng và lý do ghi đầy đủ ở
`entities/restaurant/model/format.ts`, có 10 test khoá.

### Dọn dẹp phụ thuộc (2026-08-17)
- [x] Chuyển toàn bộ floorplan/3D vào `archive/spatial-3d/` (11 file)
- [x] `requirements.txt`: **15 → 7 gói**, bỏ torch/ultralytics/transformers/opencv/
      Pillow/python-multipart/jsonschema/PyYAML (~2GB CI phải tải mỗi lần chạy)
- [x] Thêm `pytest.ini` — trước đó KHÔNG có cấu hình pytest nào, nên pytest quét từ
      thư mục gốc và thu thập cả test của code đã nghỉ hưu
- [x] Tiêm container vào `create_app()` cho test — bộ test **38s → 15s** dù thêm 63 test

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

## 🚧 VIỆC TIẾP THEO

> **Quy ước:** mục dưới đây CHỈ chứa việc **chưa làm hoặc chưa xong**.
> Việc đã xong nằm ở phần ✅ ĐÃ LÀM XONG bên trên — không lặp lại ở đây.

### Tổng hợp: 14 việc chưa xong, chia theo thứ đang CHẶN chúng

*(16 ô `[ ]` trong file này — 14 việc thật, cộng 2 dòng ⚠️ là ghi chú ràng buộc chứ
không phải việc phải làm.)*

| # | Việc | Chặn bởi | Ai làm được |
|---|---|---|---|
| 1 | Dựng lại CSDL SQLite | — | **làm ngay được** |
| 2 | Sinh tài khoản quản trị | — | **làm ngay được** |
| 3 | Đặt 3 biến `MOODBITE_ADMIN_*` | — | **làm ngay được** |
| 4 | Đặt `MOODBITE_STORAGE=sqlite` | — | **làm ngay được** |
| 5 | Tóm tắt review trích rút | — | **lập trình được** |
| 6 | Cảnh báo tỷ lệ phủ 12% của Lớp 4 | mục 5 | lập trình được |
| 7 | `POST /admin/restaurants` (thêm quán mới) | — | **lập trình được** |
| 8 | Form thêm quán ở `apps/admin` | mục 7 | lập trình được |
| 9 | Apify free tier hàng tháng | tài khoản + credit | cần người thật |
| 10 | Nhập tay 50-100 quán Hoàn Kiếm | mục 1-4 | cần người thật |
| 11 | Google Places API | **cần thẻ thanh toán** | ⏸️ để sau |
| 12 | Huấn luyện mô hình xếp hạng | `interactions.jsonl` = **0 bản ghi** | ⛔ chờ dữ liệu |
| 13 | Đánh giá NDCG / Precision@K | mục 12 | ⛔ chờ dữ liệu |
| 14 | Bật thời tiết + siết CORS khi deploy | chưa deploy | cần môi trường thật |

**Đọc nhanh:** 4 việc đầu chỉ là **cấu hình** (vài phút). 4 việc tiếp là **lập trình
được ngay**. 6 việc còn lại chờ tiền, người, hoặc dữ liệu — không phải chờ code.

### 1. Mở rộng đánh giá — MIỄN PHÍ, không cần Google Places
Hiện 23.2% quán có đánh giá. **Đây KHÔNG còn là nút thắt**: Lớp 1 (phân cụm) và Lớp 2
(tìm kiếm ngữ nghĩa) đã chạy được với dữ liệu hiện có.

Cách miễn phí, theo thứ tự đáng làm:

- [ ] **Apify free tier mỗi tháng** — credit miễn phí được cấp lại theo chu kỳ. Mỗi đợt
      ~500 quán. Chạy 3-4 tháng là phủ xong trung tâm Hà Nội. Cấu hình + toạ độ vùng đã
      có sẵn ở mục "Vì sao đánh giá vẫn chỉ 23.2%" bên trên.
- [ ] **Tự nhập tay quán trọng điểm** — 50-100 quán nổi tiếng ở Hoàn Kiếm. Chậm nhưng
      miễn phí và chất lượng cao.
      ✅ **KHÔNG CÒN BỊ CHẶN** từ 2026-08-17: trang Admin đã chạy (`npm run dev:admin`),
      sửa được tên/loại hình/địa chỉ/giá/điện thoại/website. Đây giờ là việc NHẬP LIỆU
      thủ công, không phải việc lập trình.
      ⚠️ Admin CHƯA thêm mới được quán, mới chỉ SỬA quán đã có. Cần thêm `POST
      /api/v1/admin/restaurants` nếu muốn nhập quán hoàn toàn mới.
- [ ] ⏸️ Google Places API — **để sau**, chỉ làm nếu có thẻ thanh toán. Chỗ cắm adapter
      đã sẵn sàng (`data_pipeline/sources/`), viết thêm 1 file là chạy.

> ⚠️ ĐỪNG scrape ShopeeFood/GrabFood/Foody/Facebook để lách — vi phạm ToS, rất dễ bị hỏi
> khi bảo vệ. Xem `docs/data_sources.md`.

### 2. Bật quyền quản trị trên máy đang dùng — CHỈ LÀ CẤU HÌNH, không phải lập trình

Code đã xong và đã chạy thật. Nhưng **quyền chưa được đặt trên máy này**, nên
`/api/v1/admin/*` đang trả 503 (đúng thiết kế fail-closed). Kiểm bất cứ lúc nào:

```
python scripts/check_permissions.py
```

- [ ] Dựng CSDL ghi được: `python scripts/build_sqlite.py` *(đã có file, chỉ cần dựng lại
      sau mỗi lần chạy data_pipeline)*
- [ ] Sinh tài khoản: `python scripts/make_admin_password.py`
- [ ] Đặt 3 biến `MOODBITE_ADMIN_USER` / `_PASSWORD_HASH` / `_SECRET` (script in sẵn lệnh)
- [ ] Đặt `MOODBITE_STORAGE=sqlite` rồi khởi động lại backend

Mẫu đầy đủ ở `.env.example`.

### 3. Lớp 4 — tóm tắt review (đã đo, CHƯA làm)

Kết luận cũ "review TB 106 ký tự, quá ngắn" đo SAI ĐƠN VỊ — nó đo từng review lẻ, trong
khi tóm tắt làm việc trên TOÀN BỘ review của một quán gộp lại.

Đo lại bằng `python scripts/review_report.py` (1310 quán có chi tiết):

| Chỉ số | Giá trị |
|---|---|
| Một review lẻ | TB 122.8 ký tự · trung vị 63 — **vẫn ngắn** |
| **Gộp theo quán** | **TB 666.2 ký tự · trung vị 468 · p90 1556** |
| Số review mỗi quán | TB 5.4 · trung vị 6 |
| **Quán đáng tóm tắt** (≥300 ký tự gộp và ≥5 review) | **592 quán = 45.2%** số quán có chi tiết |

- [ ] Làm tóm tắt **trích rút** (chọn câu tiêu biểu), KHÔNG dùng LLM trả phí
- [ ] ⚠️ Chỉ phủ được 592/4938 quán (12%) — phải nói rõ tỷ lệ phủ, đây là lớp LÀM GIÀU

### 4. Admin thêm mới quán — CHƯA có

Hiện admin chỉ SỬA được quán đã tồn tại.

- [ ] `POST /api/v1/admin/restaurants` để nhập quán hoàn toàn mới
- [ ] Form thêm quán ở `apps/admin` (cần tối thiểu: tên + toạ độ)

### 5. Lớp 3 đầy đủ — CHẶN, chờ dữ liệu tương tác
- [ ] Huấn luyện mô hình xếp hạng thay công thức trọng số
- [ ] Đánh giá bằng NDCG / Precision@K (đề án mục 8)
- [ ] ⚠️ Chỉ làm khi có nhãn thật — `interactions.jsonl` hiện **0 bản ghi**.
      Huấn luyện khi chưa có nhãn chỉ tạo ảo giác chính xác.

### 6. Triển khai thật — chưa deploy
- [ ] Bật `MOODBITE_ENABLE_WEATHER=1` trên môi trường thật (code + test đã xong)
- [ ] Đặt `MOODBITE_CORS_ORIGINS` cụ thể thay vì `*`

---

## ⏸️ TẠM DỪNG (đừng làm tiếp nếu chưa bàn lại)

- **Floorplan → 3D (CubiCasa5K + YOLO/SegFormer):** đã chuyển TOÀN BỘ vào
  `archive/spatial-3d/` ngày 2026-08-17. Lý do: nó kéo theo 8 thư viện (~2GB) mà CI phải
  cài ở MỌI lần chạy, cho code không endpoint nào gọi. `requirements.txt` từ 15 dòng còn 7.
  Cách khôi phục ghi đầy đủ ở `archive/spatial-3d/README.md`.
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

frontend/                            Monorepo npm workspaces — React + TS + FSD
├── packages/
│   ├── api-client/src/              DÙNG CHUNG cho client + admin (admin chưa dựng)
│   │   ├── schema.d.ts                SINH TỰ ĐỘNG từ openapi.json — KHÔNG sửa tay
│   │   ├── http.ts                    nơi DUY NHẤT biết envelope {data}/{error} ⭐
│   │   └── endpoints.ts               các endpoint, gắn kiểu từ schema ⭐
│   └── ui/src/index.ts              cố ý còn rỗng — chờ apps/admin
└── apps/client/src/
    ├── app/                         App.tsx, styles.css
    ├── pages/search/                SearchPage.tsx
    ├── widgets/                     restaurant-list, restaurant-map (Leaflet)
    ├── features/                    MỘT hành động = MỘT feature
    │   ├── search-restaurants/        model/useSearch.ts ⭐ + ui/SearchForm.tsx
    │   ├── pick-location/             model/useUserLocation.ts
    │   ├── view-restaurant-detail/    model/useRestaurantDetail.ts
    │   └── log-interaction/           model/useInteractionLogger.ts
    ├── entities/restaurant/         model/format.ts (quy tắc HIỂN THỊ) ⭐ + ui/RestaurantCard.tsx
    └── shared/                      api/ (dựng client), config/env.ts, lib/session.ts
```

> Bản frontend JavaScript cũ nằm ở `archive/frontend-v1/` — **không dùng nữa**, giữ lại
> để đối chiếu. Đừng sửa file trong đó.

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
| Cách gọi API ở frontend | `frontend/packages/api-client/src/endpoints.ts` |
| Quy tắc hiển thị (khoảng cách, giá, nhãn tin cậy) | `frontend/apps/client/src/entities/restaurant/model/format.ts` |

---

## 📌 Quy ước cập nhật file này

- Chỉ đánh ✅ **sau khi đã chạy thật**.
- Mỗi ✅ nên kèm cách kiểm chứng.
- Phát hiện mục ✅ nào thực ra không chạy → **sửa lại ngay**, đây là lỗi nghiêm trọng nhất.

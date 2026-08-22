# MoodBite — Bảng theo dõi tiến độ

**Cập nhật:** 2026-08-22
**Nguyên tắc:** file này chỉ ghi thứ đã **chạy thật và kiểm chứng được**. Không ghi theo
kế hoạch, không ghi theo tài liệu. Mỗi mục ✅ đều có lệnh để tự kiểm lại.

---

## 🚦 Tình trạng trong 30 giây

| Phần | Trạng thái | Ghi chú |
|---|---|---|
| **Một backend duy nhất** | ✅ Xong | 1 app FastAPI, 0 file TypeScript ngoài `archive/` |
| API khớp đặc tả | ✅ Xong | `/api/v1`, envelope `data`/`error`, snake_case |
| Tìm kiếm bằng câu tự do | ✅ Chạy được | đúng ý đề án, thay cho dropdown mood |
| Gợi ý món trong kết quả `/search` | ✅ Xong | lồng trong từng quán. Đây là LỐI VÀO THỨ HAI — luồng chính nay là chọn món trước |
| Ghi nhận tương tác | ✅ Xong | `POST /interactions` → nhãn cho mô hình sau này |
| Ngữ cảnh thời điểm | ✅ Giờ ăn · ✅ thời tiết (tắt mặc định) | đã gọi thật Open-Meteo: 27.2°C, 0.94s; 17 test suy biến |
| Frontend Client | ✅ **TypeScript + FSD** | 86 test, có bản đồ, steiger trong CI |
| Bản đồ | ✅ **Xong** | Leaflet + OpenStreetMap, miễn phí, không cần key |
| Kiến trúc | ✅ Sạch | Clean Architecture + checker tự động trong CI |
| Test | ✅ **422 backend + 115 frontend** | tổng **537** (client 107 · admin 8), chạy hết ~40 giây |
| Giao diện | ✅ Theo bản duyệt | trang chủ = LƯỚI MÓN + chips lọc; trang món = giới thiệu + bản đồ + danh sách quán; `/tim-kiem` giữ bố cục bản đồ + rail cũ |
| Router + layout | ✅ Xong | react-router v6, khung dùng chung, `RequireAuth` cho admin |
| Chạy xem giao diện | ✅ **một lệnh** | `python scripts/run_dev.py --admin` |
| Kho lưu trữ | ✅ CSV (mặc định) · ✅ SQLite (chọn được) | `MOODBITE_STORAGE=sqlite`, kết quả GIỐNG HỆT |
| **Frontend Admin** | ✅ **Code xong** · ⬜ **chưa bật** | `python scripts/check_permissions.py` để xem thiếu gì |
| Xác thực admin | ✅ Code xong | 1 tài khoản, token HMAC 1 giờ, fail-closed |
| Phụ thuộc Python | ✅ 15 → **7** gói | gỡ torch/ultralytics/transformers/opencv (~2GB) khỏi CI |
| Dữ liệu | ✅ **40.719 quán** · **747 món** | Overture 36.176 · OSM 3.135 · Apify 1.409. Đã loại 1 quán đóng hẳn |
| Thu thập dữ liệu đa nguồn | ✅ Xong | kiến trúc `SourceAdapter`, thêm nguồn không sửa pipeline |
| Lọc giờ mở cửa / chế độ ăn / quận | ✅ Xong | thiếu dữ liệu KHÔNG bị loại |
| **Tuổi thật của dữ liệu** | ✅ **Xong, ĐÃ HIỆN RA UI 2026-08-20** | 97,3% quán có ngày NGUỒN cập nhật (khác ngày ta cào). OSM: chỉ 28,5% thuộc 2026. Thẻ quán hiện "nguồn cập nhật N năm trước" |
| **Đối chiếu đa nền tảng** | ✅ **Xong, ĐÃ HIỆN RA UI 2026-08-20** | Meta · Microsoft · Foursquare · AllThePlaces · PinMeTo qua Overture. 337 quán được ≥2 nguồn xác nhận |
| **Quán đã đóng cửa** | ✅ **Xong, ĐÃ HIỆN RA UI 2026-08-20** | đóng hẳn → ẩn; đóng tạm → hiện + nhãn ⚠ trên thẻ |
| **Người dùng báo đóng cửa** | ✅ **Xong 2026-08-20** | đủ 3 phiên khác nhau thì ẩn. Nút ở panel chi tiết, hỏi lại trước khi gửi |
| **Tóm tắt review (Lớp 4)** | ✅ Xong | 851/1.310 quán, trích nguyên văn |
| Kiểm tra định kỳ nguồn | ✅ Xong | `python scripts/refresh_check.py` — báo cáo quán mới/mất/đổi tên |
| **Lớp 1 — Phân cụm trải nghiệm** | ✅ **Xong** | KMeans k=7, Silhouette 0.318 |
| **Lớp 2 — Tìm kiếm ngữ nghĩa** | ✅ **Xong** | TF-IDF cosine, 40.720 quán |
| **Luồng "chọn món trước, tìm quán sau"** | ✅ **Backend + Client xong** · ⬜ chưa có UI admin cho món | `/dishes/suggest` → `/dishes/{id}` → `/dishes/{id}/restaurants`; trang chủ là LƯỚI MÓN. Tài liệu đề án đã sửa cho khớp (2026-08-19) |
| **Danh mục món ăn** | ✅ **747 món** · **100% có giới thiệu** · 87.1% có ảnh | `python scripts/build_dish_catalog.py --enrich` |
| ↳ trong đó tìm được quán ở Hà Nội | 🟡 **189 món (25.3%)** | 610 món còn lại là món quốc tế chưa quán nào ở HN bán. Trang chủ **tự ẩn** và nói rõ lý do; chúng sẽ tự hiện khi có thêm dữ liệu quán |
| Giới thiệu ngắn về món | ✅ Wikipedia REST summary + soạn tay | ĐÃ BỎ phần nguyên liệu (chốt 2026-08-19). ĐÃ BỎ trích regex vì sinh dữ liệu sai — xem `sources/wikipedia_dish.py` |
| Ảnh món | ✅ 87.1% · **chỉ lưu URL, không tải file** | ~2000 món cache ≈ 1.4MB; tải ảnh về sẽ tốn ~400MB |
| Tìm món mới tự động | ✅ 37 thể loại Wikipedia | `python scripts/discover_dishes.py` — quét 1959 trang, thêm 640 món |
| Phạm vi địa lý | 🔒 **CHỈ HÀ NỘI** (chốt 2026-08-19) | `CITY_BBOXES` chỉ còn `ha_noi`; truyền `--city` khác bị từ chối. Dữ liệu hiện tại 100% trong Hà Nội (lat 20.729–21.400, lng 105.416–106.050) |
| Theo dõi dung lượng | ✅ Có công cụ | `python scripts/disk_report.py` |
| Nguồn quán ngoài OSM/Google | ✅ **Overture Maps** | `python -m data_pipeline.harvest --source overture --city ha_noi`. Wikidata đã thử và LOẠI (chỉ 5 quán toàn VN) |
| Xếp hạng 2 tầng cho trang món | ✅ Xong | quán có TÊN chứa tên món luôn trên quán chỉ được review nhắc |
| **Bộ mẫu frontend** | ✅ **Đã sửa 2026-08-19** | Nguyên nhân: `HAN_MUC` viết cứng tỉ lệ của dataset 4.938 quán nên bộ mẫu không thể khớp tập gốc mới. Nay hạn mức SUY TỪ POOL. Không nới ngưỡng checker |
| Trích món từ review (đề án mục 7) | ✅ Xong | 1076 quán có review; bún chả 86 → 94 quán |
| Ma trận truy vết | ✅ Viết lại 2026-08-19 | bản cũ có 9/10 đường dẫn KHÔNG tồn tại — xem `traceability.md` |
| **Lớp 4 — Tóm tắt review** | ✅ **XONG 2026-08-19** | Trích rút TF-IDF centroid, **851/1310 quán** có nhận xét tổng hợp (339 quán có cả điểm yếu). Mọi câu TRÍCH NGUYÊN VĂN, không sinh chữ. `python -m data_pipeline.review_summary` |
| Đăng nhập / tài khoản | ✅ **Đăng nhập + đăng ký xong (2026-08-22)** | `/api/v1/auth/*` đủ 3 endpoint. Client: `/dang-nhap` và `/dang-ky` chạy thật qua `createAuthApi()`. CHƯA làm: trang hồ sơ, chỗ hiện "đang đăng nhập là ai", đăng xuất trên giao diện. Đổi phạm vi có chủ đích so với SRS mục 8 — xem ghi chú dưới bảng |
| Phân quyền (`role`) | 🟡 Có `user`/`admin` + guard 403 | admin VẪN dùng biến môi trường, chưa chuyển sang bảng `users` |

> **Ghi chú — tài khoản người dùng là ĐỔI PHẠM VI CÓ CHỦ ĐÍCH (2026-08-17).**
> SRS mục 8 và `docs/extracted/MoodBite_Dac_Ta_API.md` xếp tài khoản vào *Won't-have*.
> Chủ dự án quyết định đưa vào vì phân quyền và cá nhân hoá là phần làm đề tài có giá trị
> hơn. Hai tài liệu trong `docs/extracted/` **cố ý giữ nguyên** — chúng là bản gốc đã nộp,
> sửa lại là làm sai lịch sử. Chỗ nào mâu thuẫn thì **code + dòng này thắng**.
>
> Chưa làm: đăng xuất có thu hồi token, `user_id` trong `POST /interactions`, lưu quán yêu
> thích ở server, giao diện Profile, và chỗ hiển thị "đang đăng nhập là ai" (kèm nút đăng
> xuất). Giao diện Login + Register đã xong 2026-08-22 (xem mục dưới).

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

**HAI ROUTER LÀM RƠI 4 TRƯỜNG — sửa 2026-08-20.** Bug im lặng nhất từ trước tới nay.

`temporarily_closed` · `source_updated_at` · `source_datasets` · `surveyed_at` có đủ
trong CSV (39.613/40.720 bản ghi), repository đọc đúng, use case gán đúng, schema khai
đúng — nhưng `search.py` và `dishes.py` mỗi bên **tự tay liệt kê lại** danh sách trường
để dựng dict, và cả hai đều quên bốn trường này. Pydantic có giá trị mặc định nên
response vẫn hợp lệ: API trả `null` cho 100% quán, không ai thấy lỗi.

- **Đo được:** trước khi sửa `0/10` kết quả có `source_updated_at`; sau khi sửa `10/10`.
- **Nguyên nhân gốc:** hai nơi cùng mô tả một hợp đồng — đúng sai lầm đã suýt giết dự án
  ở phía backend. Nay gộp về `presentation/api/result_mapping.py`, thêm trường chỉ sửa
  MỘT chỗ.
- **Vì sao test cũ không bắt được:** `test_closed_restaurants.py` dừng ở tầng domain và
  chỉ GHI CHÚ rằng "phải gắn nhãn cảnh báo ở tầng API". Ghi chú không phải là test.
  Nay có `tests/test_search_result_contract.py` khoá cả hai endpoint, kèm một test bắt
  hai endpoint phải trả **cùng bộ trường**.

**Dọn DANH MỤC MÓN 2026-08-19** — chủ dự án: *"đừng cố tình kiếm những món rất khó
kiếm quán hoặc thậm chí không có quán bán"*.

- [x] **Món không quán nào bán → tự động TẮT.** `build_dish_catalog.py` nay đặt
      `is_active = restaurant_count > 0`. Tắt chứ không xoá, và **tính lại mỗi lần dựng**
      — mai có quán mở bán Aligot thì lần dựng sau tự bật lại.
- **Đo được nguyên nhân:** 565/747 món không có quán, và **cả 565 đều đến từ
  `wikipedia_vi`** (đợt quét tự động thể loại Wikipedia). Món Việt chỉ có **đúng 1** món
  không tìm được quán — *Khoai deo Quảng Bình*, đặc sản vùng khác nên Hà Nội không có là
  đúng. Nói cách khác: phần soạn tay rất tốt, phần quét tự động là chỗ sinh rác.
- **Kiểm ngược lại có món phổ biến nào bị THIẾU không:** quét cụm từ xuất hiện ≥150 lần
  trong tên quán rồi đối chiếu với danh mục — **không sót món phổ biến nào**.
  Trà sữa (561) · Trà chanh (536) · Bún đậu mắm tôm (285) · Bún bò Huế (203) ·
  Lẩu nướng (421) · Hải sản nướng (716) đều đã có.
- Danh mục hoạt động: **182 món**, cảnh báo *"558 món chưa tìm được quán"* đã biến mất.

> ⚠️ **Còn tồn đọng — top trang chủ đang là ĐỒ UỐNG và TÊN NHÓM.** Khi chưa bấm lọc gì,
> 6 món đầu là *Cà phê sữa đá (10.080 quán) · Bia hơi · Đồ nhắm · Bún · Bún nước · Burger*.
> Nguyên nhân: từ khoá quá rộng (`cà phê`/`coffee`/`cafe` khớp mọi quán cà phê;
> `ăn nhanh`/`fast_food` khớp mọi quán ăn nhanh) nên chúng luôn thắng ở tín hiệu "dễ tìm".
> **Chưa sửa** — cần chủ dự án quyết: siết từ khoá, hay hạ trọng số `W_AVAILABILITY`, hay
> tách đồ uống thành nhóm riêng.

**Đợt ĐỐI CHIẾU NHIỀU NGUỒN 2026-08-19**

Phát hiện gốc: `last_updated` ghi 97,4% dữ liệu "cập nhật 3 ngày trước" — nhưng đó là
**ngày ta cào**, không phải ngày quán được xác minh. Sự thật sau khi lấy ngày thật về:

| | Trước | Sau |
|---|---|---|
| Quán có ngày cập nhật **thật** | 0% | **97,3%** |
| Quán OSM cập nhật trong 2026 | *không biết* | **28,5%** (71,5% từ 2025 trở về trước, cũ nhất 2010) |
| Quán Overture cập nhật trong 2026 | *không biết* | **100%** |
| Có người **xác minh tận nơi** | 0 | **106 quán** |
| Được **≥2 nền tảng độc lập** xác nhận | 0 | **337 quán** |
| Có link mạng xã hội | 0 | **35.938 (88,3%)** |

- [x] **A — Lấy tuổi thật + xuất xứ từ Overture.** Cột `sources` **vốn đã nằm trong file
      parquet ta tải về**, chỉ là câu `SELECT` không lấy ra. Không tốn thêm byte mạng nào.
      Nền tảng đóng góp: **meta 287.839 · Microsoft 1.075 · Foursquare 514 ·
      AllThePlaces 430 · PinMeTo 13**.
- [x] **B — Đối chiếu chéo OSM ↔ Overture.** Overture Places dựng từ Meta/Microsoft/
      Foursquare — **không có OSM** (kiểm bằng chính cột `sources`), nên hai bên là nguồn
      thật sự độc lập. 663 quán được xác nhận thêm. Ghép theo tên **và** khoảng cách ≤150m.
- [x] **C — Tag `check_date` của OSM.** Adapter nay gọi `out center tags meta` (thêm cả
      timestamp lần sửa cuối). 106 quán có ngày người thật đi xác minh tận nơi.
- [x] **D — `scripts/check_websites.py`.** Thử 250 tên miền: **60,4% sống · 35,6% chết**.
      Tự động bỏ qua link nền tảng (facebook/shopeefood/maps.app.goo.gl) vì chúng luôn
      sống nên không mang tín hiệu gì. **Chỉ báo cáo** — quán vỉa hè làm ăn tốt vẫn hay
      để tên miền hết hạn.

> ⚖️ **Facebook/Instagram — đường hợp pháp.** Cào trực tiếp thì mục 4b cấm và vi phạm ToS.
> Nhưng chính **Meta đóng góp** dữ liệu doanh nghiệp vào Overture dưới giấy phép
> **CDLA-Permissive-2.0**, nên lấy qua đường đó là hợp pháp hoàn toàn. 99,4% quán Overture
> có sẵn link Facebook — ta vẫn tải về mỗi lần rồi vứt đi.

> 🚫 **Vẫn KHÔNG làm được:** giờ mở cửa và trạng thái đóng/mở theo thời gian thực. Chỉ
> Google Places có, mà nó bắt bật thanh toán. ShopeeFood/GrabFood/Foody cấm truy cập tự
> động. Chỗ đó dựa vào nút người dùng báo đóng cửa.

**Đợt CẬP NHẬT DỮ LIỆU 2026-08-19** (chủ dự án chọn 3 hạng mục):

- [x] **Ẩn quán đã đóng cửa.** `permanentlyClosed`/`temporarilyClosed` do Apify cào về sẵn
      nhưng pipeline cắt mất -> 1 quán đóng hẳn + 15 quán đóng tạm vẫn được gợi ý.
      Nay: đóng hẳn -> biến mất hoàn toàn; đóng tạm -> vẫn hiện, có cờ `temporarily_closed`
      trong response để giao diện gắn nhãn. Ba trạng thái True/False/**None** (96,5% quán
      OSM+Overture không có trường này — "không biết" phải khác "biết chắc đang mở").
- [x] **Backend cho nút "quán này đã đóng cửa".** `ClosureReportTally` + action type
      `report_closed`. Đủ **3 PHIÊN KHÁC NHAU** báo thì ẩn quán. Đếm theo phiên chứ không
      theo lượt bấm — kiểm chứng: bấm 50 lần từ một phiên vẫn chỉ tính 1 phiếu. Bộ đếm
      dựng lại từ `interactions.jsonl` lúc khởi động nên khởi động lại không mất.
      ✅ **Nút bấm ở giao diện XONG 2026-08-20** (`features/report-closure`): hai bước
      bấm → hỏi lại → gửi, vì một phiếu báo góp phần làm quán biến mất với MỌI người.
      Câu cảm ơn cố ý KHÔNG nhắc con số ngưỡng — ngưỡng là nghiệp vụ, chỉ nằm ở backend.
- [x] **`scripts/refresh_check.py`** — cào lại OSM rồi báo cáo khác biệt. Chạy thật:
      769 quán mới · 39 quán biến mất · 1 đổi tên · 3.095 không đổi.
      **CHỈ BÁO CÁO, KHÔNG TỰ SỬA** — một ô Overpass lỗi là vài chục quán "biến mất".

> 🔍 **Số đo bác bỏ một giả thuyết sai.** Ban đầu tưởng các quán trùng tên ở cả hai phía
> (Highlands, KFC, Starbucks) chỉ là node bị vẽ lại với ID mới. Đo khoảng cách thật: 73
> cặp đều cách nhau **1,1 – 22,3 km** — là CHI NHÁNH KHÁC NHAU của cùng chuỗi. Ghép theo
> tên sẽ giấu mất 10 quán thật sự đã biến mất. Nay bắt buộc cùng tên **và** dưới 150 m.

> ⚠️ **Tuổi thật của dữ liệu — ĐÃ ĐO, CHƯA LÀM.** Đo 981 quán khu trung tâm: chỉ **34,9%**
> bản ghi OSM được sửa trong năm 2026, cũ nhất là **2010**. Trường `last_updated` hiện chỉ
> là NGÀY TA CÀO, nên đang tạo cảm giác dữ liệu tươi hơn thực tế. Overpass có trả ngày sửa
> thật (`out meta`) nhưng adapter chưa lấy về. Chủ dự án chưa chọn làm phần này.

**Đợt rà soát chuyên sâu 2026-08-19** (tất cả đều đo được trước/sau):

> ⏳ **Còn dở, chạy lại là xong:** `python scripts/backfill_dish_cuisine.py --apply`
> Wikipedia chặn tốc độ nên 4/22 thể loại chưa hỏi xong (trong đó có *Ẩm thực Việt Nam*).
> `cuisine` hiện **47,3%** (trước 10,4%). Script có cache theo từng thể loại nên chạy lại
> chỉ hỏi phần còn thiếu — chạy vài lần cách nhau vài phút là đủ.


- [x] **Đụng độ dấu: 39,2% kết quả trang món Phở là quán SAI.** `phở`/`phố`/`phớ` bỏ dấu
      đều thành `"pho"`, mà cả ba đều là từ nguyên vẹn nên luật cũ không chặn được.
      Trang "Phở gà" xếp *Vua Tào Phớ* và *Nhà Hàng Hải Sản Phố* ở hạng 2-4.
      → Thêm quy tắc **dấu là bằng chứng** vào `text.py` (chỉ loại khi CẢ HAI vế có dấu).
      **1948 → 1135 kết quả, còn 0 quán sai**, và 147 quán ghi biển không dấu vẫn giữ.
- [x] **Điểm mood gần như vô dụng ở tín hiệu NẶNG NHẤT (W_MOOD = 0,26).**
      Chuẩn hoá theo `max` toàn dataset khiến chỉ **460/40.720 quán (1,1%)** có điểm > 0,1,
      trung vị = 0. → Đếm SỐ TỪ KHOÁ RIÊNG BIỆT + đường cong bão hoà `n/(n+2)`.
      **Điểm > 0,3: 0,4% → 38,3%**; độ lệch chuẩn của nhóm Overture **0,011 → 0,193**.
- [x] **100% quán OSM bị chấm nhầm là "quán rẻ".** Từ khoá `street` khớp CHUỖI CON vào
      chữ `openstreetmap` ở cột nguồn. Tự viết `str.count` thay vì dùng `text.py` —
      đúng thứ mục 4 quy tắc 5 đã cấm. → Số thật: **9,3%**.
- [x] **Quán chưa có dữ liệu bị phạt như quán dở.** 40% quán không dò được từ khoá cảm xúc
      nào bị chấm 0 ở cả 5 chiều. `rules.md` mục 3.3 đã cấm đúng chuyện này cho *cụm*.
      → Thêm `NEUTRAL_MOOD_SCORE`, phân biệt "chưa biết" với "biết là không hợp".
- [x] **`mood_score` báo ra ngoài KHÁC giá trị thật dùng để xếp hạng** — bị tính lại lần
      thứ hai bằng công thức thô (thiếu ép [0,1], thiếu Cold Start). → Mang theo 1 giá trị.
- [x] **Phở bò / Phở gà / Phở trả về danh sách Y HỆT NHAU** (cùng từ khoá "phở") — chọn
      món xong không đổi gì thì luồng "chọn món trước" mất ý nghĩa. → Thêm **tầng tin cậy
      thứ ba** (tên quán ghi đúng tên món). Đo được 178 quán ghi rõ "phở bò", 202 ghi rõ
      "phở gà". Hai trang món nay khác hẳn nhau.
- [x] **Món có từ khoá 1 chữ không bao giờ dò được review** — ngưỡng 2 chữ loại sạch
      "phở", "bún". → Dò review dùng cả TÊN MÓN.
- [x] **`/health` (không cần đăng nhập) rò đường dẫn tuyệt đối** kèm tên người dùng máy.
      → `describe_path()` trả đường dẫn tương đối so với gốc dự án. 16 chỗ.
- [x] **Wikipedia trả 429 bị nuốt thành "thể loại rỗng"** — 13/22 nền ẩm thực ra 0 món;
      ghi thẳng thì đã xoá dữ liệu bằng một lỗi mạng thoáng qua. Đúng bài học Overpass ở
      mục 4b. → Thử lại có lùi thời gian + **từ chối ghi** nếu còn thể loại nào hỏng.
- [x] **Danh mục món không dựng lại được khi offline** — `load_manual_seed` đọc
      `description` nhưng quên `image_url`, nên ảnh chỉ có khi chạy kèm `--enrich` (gọi
      mạng). Dựng lại lúc không mạng: ảnh **87,1% → 0%**, không có gì báo. Seed vẫn giữ
      sẵn 607 đường dẫn ảnh, chỉ là không ai đọc lên. → Đọc cả `image_url`/`source_url`;
      nay **81,3%** và không cần mạng. Có test khoá.
- [x] **`cuisine` trống 89,6% khiến bộ lọc ẩm thực vô dụng** — → điền từ chính thể loại
      Wikipedia đã dùng để tìm ra món (nguồn thật, không suy đoán). **10,4% → 47,3%**.
- [x] **`DtypeWarning` in ra ở mọi lần khởi động** — 14 cột trộn kiểu. Tiếng ồn cỡ đó là
      chỗ tốt nhất để một cảnh báo thật lẩn vào. → `low_memory=False`.
- [x] **Bộ mẫu frontend nghèo hơn dữ liệu thật** — bước lấp đầy duyệt pool theo thứ tự nên
      đủ 100 quán trước khi chạm hạn mức ảnh (23% vs 28,2% thật). → Lấp đủ hạn mức từng
      thuộc tính trước. Không nới ngưỡng checker.

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

### Trang đăng nhập + đăng ký cho máy tính (2026-08-21 → 22)

Dựng theo bản thiết kế `frontend/design/Login - register.png`. **Logo lấy từ
`frontend/design/attribute/Logo.png`** — chủ dự án chốt: logo vẽ trong ảnh mẫu là bản CŨ,
bản trong `attribute/` mới đúng, và luật này áp cho MỌI layout về sau.

- [x] `/dang-nhap` — bố cục hai cột: tiêu đề + tranh Hà Nội bên trái, thẻ form bên phải.
      Kiểm chứng: chụp màn hình thật ở 1440×900 bằng Edge headless, khớp bản thiết kế.
- [x] **Nối THẬT vào `POST /api/v1/auth/login`**, không phải form giả: token vào
      `sessionStorage`, hoặc `localStorage` nếu tick "Ghi nhớ đăng nhập". 5 test đi qua
      đúng lớp `HttpClient` (giả lập `fetch`, không mock module).
- [x] **Câu lỗi lấy từ backend**, không dùng `userMessage` soạn sẵn — nếu không thì sai
      mật khẩu lại hiện "Phiên đăng nhập đã hết hạn". Có test khoá.
- [x] **Nền sáng/tối bấm được** (`features/switch-theme`, 4 test). `styles.css` đổi từ
      `@media (prefers-color-scheme)` sang `[data-theme]`; script nhỏ trong `index.html`
      dán sẵn thuộc tính trước khi trang vẽ để không nháy trắng.
- [x] Ảnh khai ở `shared/config/images.ts` (`logo`, `nen_dang_nhap`), file đặt ở
      `public/anh/`. Thiếu file thì hiện bản thay thế, không để ô ảnh vỡ.
- [x] Chỗ để layout sau: `widgets/auth-layout` (khung dùng chung), `app/styles/brand.css`
      (màu thương hiệu), `shared/ui` (logo, icon, ô ngôn ngữ).
- [x] **`/dang-ky` (2026-08-22)** — dùng LẠI đúng khung của trang đăng nhập, chỉ đổi tranh
      nền (`Register background.png`). Nối thật vào `POST /auth/register`, đăng ký xong
      vào thẳng app vì backend trả luôn token. 5 test.
- [x] **Phiên tài khoản chuyển sang `entities/user` (2026-08-22).** Lý do: đăng nhập và
      đăng ký là HAI feature mà FSD cấm feature này import feature kia — để state ở
      `features/auth-login` thì đăng ký xong app vẫn tưởng chưa đăng nhập cho tới khi tải
      lại trang. Khái niệm dùng chung phải nằm ở tầng dùng chung.
- [x] **Sửa theo nhận xét của chủ dự án (2026-08-22), vòng 2 — ĐO chứ không đoán:**
      - Logo 34 → 46 → 64 → **clamp(72px, 11vw, 158px)**. Cỡ lấy từ bản thiết kế: logo
        rộng bằng 0,74 lần bề ngang thẻ form.
      - Tranh nền TRÀN CẢ BỀ NGANG (bản đầu chỉ 46vw nên dừng giữa trang).
      - **Câu khẩu hiệu nay là ẢNH** (`design/attribute/slogan.png`) chứ không dựng bằng
        chữ hệ thống — bản dựng bằng chữ sai bộ chữ nên trông "xượng".
      - **`mix-blend-mode: multiply` cho tranh nền.** Đây là nguyên nhân thật của lỗi
        "tranh với nền không ăn nhập": đo được phần giấy trong tranh là TRẮNG TINH
        (255,255,255) còn trang màu kem #FCF4EA — hai mảng màu khác nhau dán cạnh nhau.
        Nhân với nền thì trắng thành đúng màu kem, mép cắt biến mất.
      - Tranh trang đăng ký nằm ở NỬA TRÁI (không luồn dưới thẻ form) — đúng bản thiết kế.
- [x] **KHÔNG CẮT XÉN TRANH (2026-08-22, vòng 3).** Chủ dự án phát hiện tranh bị mất một
      phần so với file gốc. Đo lại: `object-fit: cover` + chặn chiều cao đã XÉN 396/810
      pixel chiều cao ở màn hình 1440×900 — **mất 49% tấm tranh** (ngọn cây, nóc nhà).
      File trong `public/anh/` vẫn nguyên vẹn (MD5 trùng khớp bản trong `design/attribute/`)
      — lỗi hoàn toàn nằm ở CSS. Nay tranh giữ NGUYÊN TỈ LỆ, hiện trọn vẹn, phần trên MỜ
      DẦN vào nền thay vì bị cắt ngang.
- [x] **Màn sương (`.auth::after`)** — hệ quả của việc trên: tranh hiện trọn thì tán cây
      dâng lên ngang đoạn giới thiệu, chữ đọc không ra. Phủ một lớp kem mờ dần TRẢI KÍN
      màn hình (bọc riêng khối chữ thì lộ nguyên hình chữ nhật sáng trên tranh).
      ⚠ Phải là `::after` chứ không phải `::before`: cùng z-index thì `::before` bị chính
      tấm tranh phủ lên.
- [x] **`python scripts/prepare_design_assets.py`** — xử lý ảnh thiết kế, chạy lại được.
      Cần vì `slogan.png` xuất ra KHÔNG có kênh trong suốt (là ảnh phẳng, dính nguyên nền
      caro của công cụ thiết kế). Script tách nền, cắt sát, thu nhỏ: 1601×982 (912 KB) →
      1120×310 (179 KB). Thuần Python, không cần cài thêm thư viện.

**Ghi chú số liệu — bản thiết kế ghi khác backend, và BACKEND THẮNG:**
mẫu ghi mật khẩu "Ít nhất 6 ký tự" và tên đăng nhập "3–30 ký tự"; luật thật ở
`src/domain/entities/user.py` là **≥ 8 ký tự** và **3–32 ký tự**. Giao diện hiển thị theo
luật thật, nếu không thì người dùng gõ 6 ký tự rồi bị server từ chối mà không hiểu vì sao.

**CHƯA làm, cố ý:**
- **Quên mật khẩu** — không có dịch vụ gửi email, nên nút đó chỉ nói thẳng là chưa có
  chứ không dẫn đi đâu.
- **Điều khoản sử dụng** — chưa có trang điều khoản, nên chữ đó chỉ mở ra một dòng giải
  thích chứ không dẫn đi đâu.
- **Đa ngôn ngữ** — ô "VI" chỉ có đúng một lựa chọn; làm i18n thật là việc riêng.
- **Bản mobile trong thiết kế** — hiện mới xếp dọc cho dùng được, chưa có thanh ☰.
- **Ảnh nền trang đăng ký chỉ 404×269 px** (trang đăng nhập là 1672×941). Nét vẽ hơi nhoè
  khi phóng to. Có bản xuất lớn hơn thì thay file trong `design/attribute/` rồi chạy lại
  `python scripts/prepare_design_assets.py`.
- **Khẩu hiệu ở nền tối** đang lật màu bằng bộ lọc CSS (`invert` + `hue-rotate`) nên chữ
  "mood" hơi ngả đỏ so với màu cam gốc. Muốn chuẩn tuyệt đối thì cần xuất thêm một bản
  ảnh khẩu hiệu cho nền tối.

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
| Lọc theo khu vực | ✅ | **99.6%** có `district` |
| Lọc theo giờ mở cửa | 🟡 | **3.9%** có dữ liệu, thiếu thì giữ lại |
| Lọc chay/thuần chay | 🟡 | chỉ **0.3%** khai báo |
| Gợi ý món | ✅ | suy luận từ tên quán + `cuisine` + **nội dung review** |
| Xếp hạng theo đánh giá | 🟡 | **2.8%** có rating |
| Lọc theo giá | 🟡 | **1.6%** có giá |
| Tóm tắt review (Lớp 4) | ✅ | 851 quán có nhận xét tổng hợp |
| Phân cụm trải nghiệm | 🟡 | **2.9%** đã phân cụm; quán chưa phân cụm dùng điểm TRUNG TÍNH 0.5 (Cold Start), không phải 0 |

> ⚠️ **Vì sao mấy tỉ lệ trên TỤT so với bản trước** (đo lại 2026-08-19): dataset tăng từ
> 4.938 lên **40.720 quán**, trong đó 36.176 quán từ Overture Maps — nguồn này rất mạnh về
> ĐỊNH DANH (100% có địa chỉ, 80.9% có điện thoại) nhưng KHÔNG có rating/review/giá.
> Tổng số quán có rating gần như không đổi, chỉ là mẫu số lớn hơn 8 lần. Đây là ĐÁNH ĐỔI
> CÓ CHỦ ĐÍCH: nhiều quán hơn nhưng mỗi quán ít tín hiệu hơn.

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

# MoodBite — Bảng theo dõi tiến độ

**Cập nhật:** 2026-08-23
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
| Test | ✅ **489 backend + 147 frontend** | tổng **636** (client 139 · admin 8) |
| Giao diện | ✅ Theo bản duyệt · **trang chủ + tài khoản dựng lại 2026-08-22** | trang chủ = LƯỚI MÓN + chips lọc; trang món = giới thiệu + bản đồ + danh sách quán; `/tim-kiem` giữ bố cục bản đồ + rail cũ |
| Router + layout | ✅ Xong | react-router v6, khung dùng chung, `RequireAuth` cho admin |
| Chạy xem giao diện | ✅ **một lệnh** | `python scripts/run_dev.py --admin` |
| Kho lưu trữ | ✅ CSV (mặc định) · ✅ SQLite (chọn được) | `MOODBITE_STORAGE=sqlite`, kết quả GIỐNG HỆT |
| **Frontend Admin** | ✅ **Code xong + ĐÃ BẬT 2026-08-23** | sửa quán · ẩn/bỏ ẩn · **thêm quán mới**. `python scripts/run_dev.py --admin` |
| Xác thực admin | ✅ Code xong | 1 tài khoản, token HMAC 1 giờ, fail-closed, **giới hạn 5 lần/15 phút (thêm 2026-08-24)** |
| Phụ thuộc Python | ✅ 15 → **7** gói | gỡ torch/ultralytics/transformers/opencv (~2GB) khỏi CI |
| **Làm việc trên 2 máy** | ✅ **Xong 2026-08-25** | `python scripts/chuan_bi_may_moi.py` (kiểm 4 thứ nằm ngoài git) + `dong_bo_du_lieu.py --tai/--day` (đồng bộ 39MB dữ liệu qua HuggingFace, miễn phí, không cần thẻ). Không còn phải điều khiển từ xa để chạy dự án |
| **Trang kết quả gợi ý** | ✅ **Xong 2026-08-25** | `/recommend` — tách khỏi trang chủ (trang chủ lo KHÁM PHÁ, trang này lo KẾT QUẢ). Bộ lọc nằm trên query string nên chia sẻ link được, F5 không mất, nút Back đúng |
| **Chân trang + ghi công nguồn** | ✅ **Xong 2026-08-24** | Trước đó ghi công OSM CHỈ có trên bản đồ Leaflet, trong khi dữ liệu dùng khắp app — thiếu nghĩa vụ của ODbL/CDLA/CC BY-SA |
| **Email bắt buộc khi đăng ký** | ✅ **Xong 2026-08-24** | Đảo quyết định cũ ("tuỳ chọn"), vì nay đã có xác minh email và đó là đường DUY NHẤT lấy lại mật khẩu. Tài khoản cũ không email vẫn dùng được |
| **Xác minh email** | ✅ **Xong 2026-08-24** | đăng ký có email → tự gửi thư; token HMAC 24h, dùng MỘT lần, đổi email là link cũ chết. Secret riêng `MOODBITE_EMAIL_VERIFY_SECRET` |
| **Rà soát bảo mật** | ✅ **2026-08-24** | sửa 3 lỗi: secret đặt lại mật khẩu bị dán nhầm bằng CÂU LỆNH sinh nó · CORS mặc định `*` · `/admin/login` không giới hạn tần suất. Có `tests/test_bao_mat.py` canh |
| **Phạm vi Hà Nội** | ✅ **Sửa 2026-08-24** | bbox cũ cắt mất 1/3 thành phố (Ba Vì, Sơn Tây, Mỹ Đức, Ứng Hoà…) và lấn sang Bắc Ninh. Ranh giới nay hỏi theo AREA của Hà Nội → đúng 126 đơn vị |
| Dữ liệu | ✅ **52.854 quán** · **855 món** | Overture · OSM · Apify — **cả ba nguồn đã cạn** (Overture chưa ra bản mới, OSM 110/110 ô 0 lỗi, Wikipedia+Wikidata chỉ còn trả về rác). **Làm sạch 2026-08-24:** bỏ 7.534 quán ở tỉnh khác, sửa 803 `district`, làm sạch 519 tên. Kiểm tra lại: `district` **100% thuộc Hà Nội**, 0 trùng lặp, 0 tên rác |
| **Ảnh món gắn nhầm** | ✅ **Đã soát và gỡ 2026-08-23** | `python scripts/audit_dish_images.py` — 4 món đang hiện ảnh SAI (bãi biển cho món lẩu). Đã chặn ở nguồn |
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
| **Danh mục món ăn** | ✅ **855 món** · 93.0% có giới thiệu · 81.5% có ảnh | `python scripts/build_dish_catalog.py --enrich`. Hai tỷ lệ này TỤT so với mốc 747 món (100% / 87.1%) vì 108 món mới đào từ tên quán và Wikidata chưa có bài Wikipedia để lấy ảnh + giới thiệu |
| ↳ trong đó tìm được quán ở Hà Nội | 🟡 **297 món (34.7%)** | +108 món so với 2026-08-23, nhờ nguồn thứ ba: đào cụm từ trong TÊN của 53.461 quán thật (`python scripts/mine_dish_names.py`). 558 món còn lại là món quốc tế chưa quán nào ở HN bán — trang chủ **tự ẩn** và nói rõ lý do |
| Giới thiệu ngắn về món | ✅ Wikipedia REST summary + soạn tay | ĐÃ BỎ phần nguyên liệu (chốt 2026-08-19). ĐÃ BỎ trích regex vì sinh dữ liệu sai — xem `sources/wikipedia_dish.py` |
| Ảnh món | ✅ 87.1% · **chỉ lưu URL, không tải file** | ~2000 món cache ≈ 1.4MB; tải ảnh về sẽ tốn ~400MB |
| Tìm món mới tự động | ✅ **3 nguồn** | `discover_dishes.py` (37 thể loại Wikipedia + **Wikidata CC0**, 4.793 mục) và `mine_dish_names.py` (đào từ tên quán). Mọi `--apply` phải đi qua danh sách duyệt tay `data_pipeline/dish_approved.json` |
| Phạm vi địa lý | 🔒 **CHỈ HÀ NỘI** (chốt 2026-08-19) | `CITY_BBOXES` chỉ còn `ha_noi`; truyền `--city` khác bị từ chối. Dữ liệu hiện tại 100% trong Hà Nội (lat 20.729–21.400, lng 105.416–106.050) |
| Theo dõi dung lượng | ✅ Có công cụ | `python scripts/disk_report.py` |
| Nguồn quán ngoài OSM/Google | ✅ **Overture Maps** | `python -m data_pipeline.harvest --source overture --city ha_noi`. Wikidata đã thử và LOẠI (chỉ 5 quán toàn VN) |
| Xếp hạng 2 tầng cho trang món | ✅ Xong | quán có TÊN chứa tên món luôn trên quán chỉ được review nhắc |
| **Bộ mẫu frontend** | ✅ **Đã sửa 2026-08-19** | Nguyên nhân: `HAN_MUC` viết cứng tỉ lệ của dataset 4.938 quán nên bộ mẫu không thể khớp tập gốc mới. Nay hạn mức SUY TỪ POOL. Không nới ngưỡng checker |
| Trích món từ review (đề án mục 7) | ✅ Xong | 1076 quán có review; bún chả 86 → 94 quán |
| Ma trận truy vết | ✅ Viết lại 2026-08-19 | bản cũ có 9/10 đường dẫn KHÔNG tồn tại — xem `traceability.md` |
| **Lớp 4 — Tóm tắt review** | ✅ **XONG 2026-08-19** | Trích rút TF-IDF centroid, **851/1310 quán** có nhận xét tổng hợp (339 quán có cả điểm yếu). Mọi câu TRÍCH NGUYÊN VĂN, không sinh chữ. `python -m data_pipeline.review_summary` |
| Đăng nhập / tài khoản | ✅ **Đăng nhập · đăng ký · quên mật khẩu · TRANG TÀI KHOẢN 7 TAB (2026-08-23)** | `/api/v1/auth/*` + `/api/v1/me/*`. Trang `/account` có thanh bên 7 mục, ảnh đại diện, số liệu thật, cấp độ, huy hiệu. Đổi phạm vi có chủ đích so với SRS mục 8 — xem ghi chú dưới bảng |
| Phân quyền (`role`) | 🟡 Có `user`/`admin` + guard 403 | admin VẪN dùng biến môi trường, chưa chuyển sang bảng `users` |
| **Quán & món yêu thích (server)** | ✅ **Xong 2026-08-23** | bảng `saved_items`, `GET/POST/DELETE /me/favorites`. Khách vẫn lưu ở máy và được ĐỒNG BỘ LÊN khi đăng nhập |
| **Lượt khám phá · cấp độ · huy hiệu** | ✅ **Xong 2026-08-23** | `GET /me/stats`. `POST /interactions` nay ghi thêm `user_id` (LẤY TỪ TOKEN, không nhận từ body) |
| **Song ngữ Việt–Anh** | ✅ **Giao diện xong 2026-08-23** · ⬜ dữ liệu vẫn tiếng Việt | `shared/i18n/tu_dien.ts` — 1 file, kiểm kiểu lúc biên dịch. Tên món/quán và chữ do máy chủ sinh KHÔNG dịch (cần i18n ở backend) |

> **Ghi chú — tài khoản người dùng là ĐỔI PHẠM VI CÓ CHỦ ĐÍCH (2026-08-17).**
> SRS mục 8 và `docs/extracted/MoodBite_Dac_Ta_API.md` xếp tài khoản vào *Won't-have*.
> Chủ dự án quyết định đưa vào vì phân quyền và cá nhân hoá là phần làm đề tài có giá trị
> hơn. Hai tài liệu trong `docs/extracted/` **cố ý giữ nguyên** — chúng là bản gốc đã nộp,
> sửa lại là làm sai lịch sử. Chỗ nào mâu thuẫn thì **code + dòng này thắng**.
>
> Đã xong (2026-08-23): `user_id` trong `POST /interactions` · lưu quán & món yêu thích ở
> server · trang Profile 7 tab · chỗ hiển thị "đang đăng nhập là ai" kèm nút đăng xuất ·
> đổi mật khẩu khi đang đăng nhập.
> **Còn lại:** đăng xuất có THU HỒI token (cần cột `token_version` — đổi lược đồ, phải chốt
> trước) và xác minh email lúc đăng ký.

**Tự kiểm toàn bộ bằng MỘT lệnh** (chạy được ở PowerShell, CMD, bash, macOS, Linux):

```
python scripts/verify.py
```

Lệnh này kiểm 9 việc và in rõ từng mục đạt/hỏng: app dựng được · test backend ·
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
- [x] **Logo bản mới 2026-08-22 (2172×724, tỉ lệ 3:1)** thay bản cũ 226×114 (tỉ lệ 2:1).
      Bản cũ quá nhỏ nên phóng lên 300px là vỡ nét. Cỡ hiển thị tính lại theo tỉ lệ mới:
      rộng ~305px thì cao ~102px (trước là 154px). Script thu nhỏ còn 930×310 (1422 → 370 KB).
      ⚠ File đổi tên `Logo.png` → `logo.png`; script nay tìm file KHÔNG phân biệt hoa
      thường, nếu không thì Linux/CI sẽ lặng lẽ bỏ qua.
- [x] **Bố cục tranh tính lại theo hình học thật (2026-08-22, vòng 4).** Khung bản thiết
      kế gần vuông (813×815) nên tranh vừa rộng hết khung vừa chỉ chiếm 56% chiều cao.
      Cửa sổ trình duyệt bẹt hơn nhiều (1920×887 ≈ 2,2:1): trải tranh hết bề ngang thì
      theo tỉ lệ 1,777 nó cao 1080px — CAO HƠN cả màn hình, chân trời rơi vào giữa trang,
      đúng chỗ đặt chữ. Vì vậy khống chế theo CHIỀU CAO (66% màn hình) và để `contain` tự
      tính bề ngang: không cắt, không méo, giữ đúng bố cục "trời quang trên, phố dưới".
      Mép tranh tan bằng dải mờ toả từ góc dưới trái (xử lý cả mép ngang lẫn mép dọc).
- [x] **TOÀN MÀN HÌNH (2026-08-22, vòng 6) — chốt cuối.** Chủ dự án bác bỏ hẳn phương án
      khung hẹp: trang đăng nhập phải chiếm TRỌN màn hình, tranh là NỀN của cả trang.
      Nay `.auth__scene` là `position: fixed; inset: 0; object-fit: cover` neo ĐÁY — phủ
      kín mép này sang mép kia. Phần bị cắt chỉ là dải trời phía trên (đo được alpha = 0
      ở 10% trên cùng), không mất nét vẽ nào. Chữ đọc được nhờ hai lớp kem mờ ở
      `.auth::after`: một dải ngang ở đỉnh + một vệt bầu dục ôm khối chữ bên trái.
      Cỡ các thành phần đo từ bản thiết kế chủ dự án gửi (khung 1456px): logo 23% bề ngang
      (≈7,4vw), tiêu đề 38%, thẻ form 465px.
- [x] ~~KHUNG BỐ CỤC buộc theo CHIỀU CAO màn hình (vòng 5) — `--khung`~~ ĐÃ BỎ ở vòng 6.
      Giữ lại ghi chú để người sau khỏi làm lại: phương án đó giữ đúng tỉ lệ bản thiết kế
      nhưng để lại lề kem hai bên trên màn hình rộng, và chủ dự án không chấp nhận.
- [x] **Tranh nền vẽ bằng `background-image`, KHÔNG dùng thẻ `<img>` (2026-08-22).**
      Bug thật: bản cũ dùng `<img onError>` để ẩn ảnh khi tải hỏng, nhưng `onError` chỉ
      cần nổ MỘT lần — ví dụ đúng lúc `prepare_design_assets.py` đang ghi đè file — là
      React nhớ luôn "ảnh hỏng" và trang MẤT SẠCH NỀN cho tới khi tải lại. Chủ dự án gặp
      đúng lỗi này. Nền là thứ trang trí thuần tuý nên `background-image` hợp hơn: không
      có sự kiện lỗi, không giữ state, hỏng thì chỉ là không vẽ gì.
- [x] **Thẻ form nhích lên ~5% chiều cao màn hình** so với chính giữa (chủ dự án yêu cầu).
- [x] **Hai lớp kem mờ (`.auth::after`)** — cần vì tranh phủ kín màn hình nên tán cây
      dâng lên tận góc trên bên trái, đúng chỗ đặt logo và chữ.
      ⚠ Phải là `::after` chứ không phải `::before`: cùng z-index thì thứ tự vẽ theo DOM,
      mà `::before` đứng trước các phần tử con nên bị chính tấm tranh phủ lên — đã thử và
      màn sương mất tác dụng hoàn toàn.
- [x] **`python scripts/prepare_design_assets.py`** — xử lý ảnh thiết kế, chạy lại được.
      Cần vì `slogan.png` xuất ra KHÔNG có kênh trong suốt (là ảnh phẳng, dính nguyên nền
      caro của công cụ thiết kế). Script tách nền, cắt sát, thu nhỏ: 1601×982 (912 KB) →
      1120×310 (179 KB). Thuần Python, không cần cài thêm thư viện.

### Trang chủ dựng lại theo bản thiết kế (2026-08-22)

Theo `design/Home.jpg`. Cấu trúc: thanh trên · lời chào + ô tìm + tranh · mood nhanh ·
lọc chi tiết · lưới món · dải mời đăng nhập.

- [x] `widgets/site-header` — logo, điều hướng, khu vực (Hà Nội), nút nền tối, tài khoản
      (tên người dùng thật lấy từ `/auth/me`, kèm nút đăng xuất).
- [x] `widgets/home-hero` — lời chào theo giờ máy, khẩu hiệu (ảnh), **chip ngữ cảnh lấy
      THẲNG từ `context` của API** (không viết cứng "28°C trời mưa" như bản vẽ), ô tìm dẫn
      sang luồng tìm bằng câu tự nhiên, tranh `banner home.png`.
- [x] `widgets/mood-quick-pick` — 7 thẻ, mỗi thẻ ánh xạ vào MỘT bộ lọc có thật.
- [x] `/auth/me` + `useUserSession.user` — mở lại tab vẫn biết mình là ai; token hết hạn
      thì tự đăng xuất (trước đây chưa có gì kiểm token cũ).

**KHÁCH vs ĐÃ ĐĂNG NHẬP (spec chủ dự án 2026-08-22) — đã dựng:**

| | Khách | Đã đăng nhập |
|---|---|---|
| Thanh trên | Đăng nhập · Đăng ký | tên thật + Đăng xuất |
| Hero | khẩu hiệu + dải mời đăng nhập nhẹ | "Chào buổi …, <tên> 👋" + "Hôm nay bạn muốn ăn gì?" |
| Mood | "Gợi ý nhanh theo mood" | "Mood của bạn hôm nay là gì?" |
| Kết quả | "🔥 Món phổ biến hôm nay" | "✨ Gợi ý hôm nay dành cho <tên>" |
| Khối riêng | "🧭 Khám phá theo nhu cầu" (6 thẻ) | "🕘 Xem gần đây" |
| Cuối trang | dải mời đăng ký (2 nút) | (không có) |

⚠️ **Nguyên tắc:** với khách TUYỆT ĐỐI không viết "phù hợp với bạn" — hệ thống chưa biết
họ là ai. Có test khoá điều này.

"🕘 Xem gần đây" lưu ở **localStorage**, không phải server: `POST /interactions` ghi theo
QUÁN và không có endpoint đọc lại. Nó chỉ hứa "món bạn vừa xem trên máy này" — đúng thứ
làm được.

**Sửa theo nhận xét "chưa giống mẫu" (2026-08-22, vòng 2):**
- [x] Thẻ món dựng lại theo mẫu: ảnh 4:3 phía trên, nhãn "MoodBite đề xuất" (rank 1),
      nút TIM, tên, số quán. Bày thành HÀNG NGANG trượt được; "Xem tất cả (30) →" mở lưới.
- [x] Bỏ đoạn giới thiệu khỏi thẻ (mẫu không có) — nó vẫn còn đủ ở trang chi tiết món.
      Có test khoá để không ai nhét lại.
- [x] Thẻ ngữ cảnh có icon (mẫu), không còn là viên thuốc một dòng.
- [x] Ô tìm có kính lúp; lời chào hiện cho CẢ khách (không kèm tên).
- [x] **Lời chào tự đổi theo giờ THẬT**: hẹn giờ tới mốc kế tiếp (11h/14h/18h/0h) rồi vẽ
      lại, thay vì chỉ đúng lúc mở trang. Mở lúc 17:59 để đó tới 18:05 vẫn đúng.
- [x] **Favicon + mascot** vào pipeline ảnh; favicon khai ở `index.html` (một file 180px
      dùng cho cả tab lẫn màn hình chính iOS).
- [x] **Banner trang chủ TO và TRÀN ra mép phải** màn hình (chủ dự án: "ảnh vẫn nhỏ").
- [x] **Thẻ món hết lệch hàng**: bỏ `aspect-ratio` (ảnh Wikipedia có tấm DỌC làm một thẻ
      cao vọt, kéo cả hàng), thay bằng chiều cao ảnh cố định 160px + `object-fit: cover`.
- [x] Nút TIM lưu ở localStorage (`features/save-dish`) — backend ghi được `save` theo QUÁN
      nhưng KHÔNG có endpoint đọc lại, nên lưu ở máy là cách duy nhất không nói dối. 2 test.

**ẢNH MÓN — tự tìm được, MIỄN PHÍ và HỢP PHÁP (2026-08-22):**
`python scripts/find_dish_images.py [--apply]` — tìm ảnh cho món chưa có, thử lần lượt:
Wikipedia VI (tìm kiếm rồi lấy ảnh bài khớp nhất) → Wikipedia EN → Wikimedia Commons.
Không cần khoá API, không cần thẻ. **Kết quả: 607 → 691/747 món có ảnh (81% → 92%)**,
tìm thêm được 84/87 món.

⚠️ Bài học đã trả giá: để 0,3 giây/lượt thì Wikimedia CHẶN TẦN SUẤT từ món thứ ~49, kết
quả tụt còn 19/87 dù chạy lẻ từng món vẫn ra ảnh. Nay 0,8 giây + thử lại có chờ (giống
cách xử lý Overpass 504). Script in ra số lượt bị chặn để không nhầm "bị chặn" với
"không có ảnh".

⚠️ Script chọn BÀI KHỚP NHẤT chứ không hiểu nghĩa — "Phở gà"/"Phở bò" đều nhận ảnh của
bài "Phở". Mỗi ảnh đều ghi `image_source` + `image_credit` để soi lại được, và sửa từng
món bằng `python scripts/set_dish_image.py --dish <id> --url <...> --credit <...>`
(`--credit` BẮT BUỘC — CLAUDE.md mục 4b).

⚠️ KHÔNG dùng Google Images / cào ShopeeFood, Foody, Facebook: ToS cấm và bản quyền không
rõ. Đây là chỗ dễ bị hỏi nhất khi bảo vệ.

**CẦN CHỦ DỰ ÁN GỬI THÊM:**
- ~~Ảnh mascot~~ ✅ đã có (2026-08-22), dùng ở dải mời đăng ký + favicon.
- Bộ icon mood vẽ riêng (ớt, lá, nồi, tim, mây, vỉ nướng) — chủ dự án đang làm, gửi dần.

**CỐ TÌNH KHÔNG DỰNG — vì không có dữ liệu thật phía sau (CLAUDE.md mục 4: thiếu thì để
trống, không bịa):**

| Trong bản vẽ | Vì sao chưa làm |
|---|---|
| ⭐ điểm sao từng món | Món KHÔNG có trường rating. Chỉ QUÁN mới có, và chỉ 37,9% quán có |
| "~1,2 km" từng món | Món không có khoảng cách; khoảng cách là của quán |
| Chuông thông báo | Không có API nào phía sau |
| "Bộ sưu tập", "Blog", "Theo mood", "Theo thời tiết" | Chưa có trang; link chết còn tệ hơn |
| Thẻ mood "Lười nấu", "Hẹn hò", "Healthy" | Backend chỉ có 4 mood: happy/sad/excited/relaxed |
| "❤️ Dành riêng cho bạn" + "98% phù hợp" | Chưa có endpoint đọc lịch sử/sở thích. `predicted_score` là điểm XẾP HẠNG, hiện thành % là hiểu sai |
| "❤️ Quán & món đã lưu" | Ghi được `action=save` nhưng KHÔNG có endpoint đọc danh sách đã lưu |
| "Ăn dưới 50K" | Giá là CHUỖI ("1-100.000 ₫"), chỉ 273/4000 quán có; món không có giá |
| "Ăn một mình" / "Đi ăn cùng bạn" | `portion_size` chỉ 55/747 món có và KHÔNG được API trả ra |
| "Quán đang hot" | Không có số liệu lượt xem/đặt nào |
| Trái tim lưu món | `POST /interactions` có `action=save` nhưng CHƯA có endpoint đọc lại danh sách đã lưu |

### Đường dẫn tiếng Anh + trang tài khoản + ảnh đại diện (2026-08-22, khuya)

- [x] **Đổi toàn bộ đường dẫn sang tiếng Anh**: `/login` `/register` `/forgot-password`
      `/reset-password` `/dishes/:id` `/search` `/account`. Đường dẫn CŨ giữ làm CHUYỂN
      HƯỚNG (giữ nguyên query string) — quan trọng nhất là `/dat-lai-mat-khau?token=…` vì
      link đó đã nằm trong hộp thư người dùng. Backend đổi link trong thư theo. 2 test khoá.
- [x] **`GET /auth/me` trả thêm `email` + `created_at`** qua `User.to_self()`.
      ⚠️ `to_public()` vẫn KHÔNG có email — `to_self()` chỉ dùng cho chính chủ xem hồ sơ
      mình, tuyệt đối không dùng cho danh sách người dùng.
- [x] **Trang `/account`** — ảnh đại diện, tên, email, ngày tham gia, sở thích, món đã lưu,
      đã xem gần đây, cài đặt (nền tối + đăng xuất). Chỉ hiện SỐ ĐẾM CÓ THẬT (món đã lưu,
      món đã xem); bốn ô còn lại trong bản thiết kế chưa có gì để đếm — xem bảng dưới.
- [x] **Ảnh đại diện: mặc định sinh từ tên + cho tải ảnh lên, 4 LỚP CHẶN bảo mật**
      (`features/change-avatar`, 6 test tấn công thật):
      1. lọc MIME, **từ chối SVG** (SVG là XML, chạy được `<script>`)
      2. đọc **số ma thuật** — file HTML đổi đuôi thành `.png` bị chặn ở đây
      3. **vẽ lại qua canvas** rồi xuất PNG mới — thứ lưu lại là pixel do trình duyệt vẽ,
         không còn byte nào của file gốc (mã nhúng, EXIF, payload đều biến mất)
      4. chặn kích thước 2 MB trước khi giải mã (chống bom nén)
      Lưu ở localStorage, **không gửi lên máy chủ** — không có endpoint nhận file thì cũng
      không có bề mặt tấn công nào ở phía server.
      ⚠️ `Blob.arrayBuffer()` không có ở Safari < 14 và jsdom → có đường lui `FileReader`.
      Thiếu nó thì phép kiểm số ma thuật ném lỗi và file độc hại LỌT trong im lặng.

**Bốn mục chủ dự án đánh dấu "cần xem kỹ trước khi làm" — chốt 2026-08-23:**

| Mục | Trạng thái | Ghi chú |
|---|---|---|
| Viết review + "Đánh giá của tôi" | ⬜ **HOÃN — chủ dự án quyết định không làm** | *"tôi không thích mục 1, cũng không muốn tự tạo thêm vấn đề"*. Nội dung do người dùng viết kéo theo kiểm duyệt, chống spam, xử lý báo cáo — việc lớn hơn nó trông thấy. Đưa vào phần ĐỊNH HƯỚNG |
| "Quán yêu thích" | ✅ **Xong** | bảng `saved_items` + `/me/favorites` |
| "Lượt khám phá" | ✅ **Xong** | = số QUÁN KHÁC NHAU đã xem đủ lâu; server đếm |
| Cấp độ + huy hiệu | ✅ **Xong** | 5 cấp · 5 huy hiệu · `GET /me/stats` |

### Đào thêm dữ liệu — 3 lỗi thật, +2.414 quán (2026-08-23, đợt 3)

Chủ dự án: *"hãy xem có thể đào thêm dữ liệu gì thì đào, đào từ mọi nguồn có thể"*.
Không tìm được nguồn MỚI nào hợp pháp và miễn phí, nhưng tìm ra **ba lỗi đang chặn dữ
liệu sẵn có** — sửa xong lấy thêm được 2.414 quán mà không tốn một đồng.

| Bước | Trước | Sau |
|---|---:|---:|
| Tổng số quán | 40.704 | **43.118** (+2.414) |
| Quán có điện thoại | 32.926 | **34.9xx** |
| Quán có website | 10.514 | **11.6xx** |

**Lỗi 1 — cache Overture GHIM CHẶT bản phát hành đầu tiên.**
`_cache_file()` đặt tên `ha_noi_places.parquet`, không kèm tên bản. Overture ra bản mới
hàng tháng và `_latest_release()` tra đúng bản mới, nhưng ngay sau đó thấy file cache cũ
là dùng luôn — **cào lại bao nhiêu lần cũng ra đúng dữ liệu tháng đầu**, không một dòng
log nào báo. Nay tên cache kèm bản phát hành.

**Lỗi 2 — bản phát hành mới làm sập cả lượt cào.**
`row.get("src_datasets") or []` — với bản 2026-08-19, cột đó về dưới dạng **mảng numpy**,
và `mảng or []` ném `ValueError: truth value of an array is ambiguous`. Cả lượt cào chết
giữa chừng. Nay đi qua `_danh_sach()`; không bao giờ dùng `or` với thứ có thể là mảng.

**Lỗi 3 — bảy danh mục ăn uống bị vứt nhầm.**
Soát 218.907 POI bị loại "không phải ăn uống", lọc ra danh mục có chữ liên quan đồ ăn rồi
xét từng cái: `food` (460) · `desserts` (139) · `delicatessen` (123) · `gastropub` (38) ·
`night_market` (12) · `donuts` (9) · `soul_food` (3) đều là **chỗ người ta ngồi ăn**.
Vẫn KHÔNG lấy `health_food_store` (820), `farmers_market` (136), `food_delivery_service`,
`restaurant_equipment_and_supply`, `food_tours` — đó là cửa hàng/dịch vụ, không phải quán.

**Gộp HAI bản phát hành Overture thay vì thay thế.** Bản 2026-08-19 có ÍT hơn bản
2026-07-22 (35.795 vs 39.567 quán ăn uống). Overture dọn bớt bản ghi không có nghĩa là
"quán đó đóng cửa" — có thể chỉ là hạ điểm tin cậy hoặc gộp trùng lặp. Giữ cả hai ảnh chụp
rồi để bước merge khử trùng lặp: không mất quán nào, cũng không đếm trùng.

### Soát ảnh món bằng MẮT — `scripts/review_dish_images.py` (2026-08-23)

Chủ dự án chỉ ra: ảnh **Nem nướng** là mấy xiên thịt đỏ au đang nướng trên vỉ than, nhìn
như thịt sống. Kiểm lại: ảnh lấy từ ĐÚNG bài "Nem nướng" trên Wikipedia, file tên
`Nem_nướng_by_Baoothersks.jpg` — **dữ liệu đúng, tấm ảnh tệ**.

`audit_dish_images.py` bất lực trước loại lỗi này: nó chỉ bắt được ảnh lấy từ bài KHÔNG
PHẢI món ăn. Không có mô hình thị giác thì máy không tự biết "tấm này trông có giống món
không" — nhưng mắt người làm việc đó trong nửa giây.

- [x] `python scripts/review_dish_images.py` dựng một trang HTML bày TOÀN BỘ ảnh món
      (175 món đang bật có ảnh). Bấm vào ảnh nào sai -> đánh dấu đỏ, lưu ở localStorage,
      cuối trang có sẵn lệnh `set_dish_image.py --clear` cho từng món đã đánh dấu.
- ⚠️ Đây là việc của NGƯỜI, không tự động được. Nhưng 175 tấm soát hết trong vài phút.

### Bật quản trị · thêm quán mới · menu ☰ · tông màu (2026-08-23, đợt 2)

- [x] **Trang quản trị ĐÃ BẬT trên máy này.** `build_sqlite.py` dựng lại từ dataset mới
      (40.703 quán), sinh tài khoản admin, ghi 4 biến vào `.env.local` (đã .gitignore).
      `python scripts/check_permissions.py` -> **QUYEN DA CAU HINH DAY DU**.
      `make_admin_password.py` thêm cờ `--write-env`: ghi thẳng vào `.env.local` thay vì
      bắt chép tay ba dòng dài vào PowerShell (biến `$env:` chỉ sống trong cửa sổ đang mở,
      đóng là mất và lần sau lại thấy 503 mà không hiểu vì sao).
- [x] **`POST /api/v1/admin/restaurants` — thêm quán hoàn toàn mới.**
      Luật ở `domain/value_objects/restaurant_new.py`: bắt buộc tên + toạ độ, **toạ độ
      phải nằm trong Hà Nội** (phạm vi chốt 2026-08-19), `place_id` do SERVER sinh với
      tiền tố `manual:` — nhìn mã là biết quán do người nhập tay.
      **KHÔNG nhận `rating`/`reviews_count` từ form**: gõ tay vào là làm sai lệch chính
      con số dùng để xếp hạng. 8 test, trong đó có test khoá việc quán mới phải hiện ra
      ngay ở luồng người dùng cuối (quên `reload()` bộ nhớ đệm là bug âm thầm).
- [x] **Form thêm quán ở `apps/admin`** — đóng sẵn, mở ra là 10 ô. Ô để trống thì KHÔNG
      gửi trường đó lên (cột trong CSDL là NULL = chưa có dữ liệu, khác chuỗi rỗng).
- [x] **Menu ☰ cho điện thoại.** Dưới 760px, hàng điều hướng + khu công cụ phải cuộn
      ngang — thao tác gần như không ai nghĩ tới nên các mục đó coi như biến mất.
      Đã đo thật ở bề ngang 405px: `scrollWidth == viewport`, không tràn ngang.
- [x] **Bộ mẫu frontend dựng lại** sau khi đổi dataset (`scripts/make_fixture.py`) —
      tỉ lệ mẫu lệch < 0,5% so với dữ liệu thật.

### Tông màu trang chủ — sửa theo góp ý (2026-08-23)

Chủ dự án: *"mẫu tôi gửi là trang chủ all in về cùng 1 tông màu mà sao của bạn lại có
nguyên 1 dải màu trắng rồi CTA cũng nguyên dải trắng?"* — **đúng**.

Nguyên nhân: khối "Lọc chi tiết" và dải mời đăng ký dùng `--auth-card` (#FFFFFF) và
`--auth-line` (#E2E7F0 — xám **ánh xanh**), vốn là màu của nhóm trang đăng nhập/đăng ký.
Trên nền kem chúng thành hai dải trắng cắt ngang trang.

- [x] Thêm bộ token **ẤM** riêng: `--surface` (#FFFCF6) · `--surface-soft` (#FBF1E2) ·
      `--line-warm` (#F0E2CD). Trang chủ + trang tài khoản dùng bộ này.
- [x] Dải mời đăng ký đổi sang `--surface-soft` (kem đậm hơn nền), bỏ đổ bóng.
- ⚠️ **KHÔNG sửa thẳng `--auth-card`**: trang đăng nhập/đăng ký cố ý là "tờ giấy trắng"
      đặt trên tranh nền và chủ dự án đã duyệt bản đó. Đổi token chung là phá luôn hai
      trang kia.

### Bộ icon mood — chủ dự án gửi dần (2026-08-23)

| Thẻ | Icon | Trạng thái |
|---|---|---|
| Thèm cay | `spicy.png` | ✅ đã lắp |
| Thư giãn | `Relax.png` | ✅ đã lắp |
| Vui vẻ · Cần an ủi · Trời mưa · Đồ nướng · Món nóng | | ⬜ chờ |

- [x] `prepare_design_assets.py` thêm chế độ **`nen_den`**: file gốc là hình PHÁT SÁNG
      trên nền ĐEN, thừa rất nhiều lề (spicy.png là 1536×1024 với quả ớt lệch hẳn sang
      phải). Không xử lý thì trang chủ nền kem sẽ hiện một ô đen sì.
      Cách tách: ảnh sáng trên nền đen chính là ảnh **đã nhân sẵn alpha**, nên
      `alpha = max(R,G,B)` rồi chia màu cho alpha. Quầng sáng nhờ đó chuyển thành phần
      trong suốt dần thay vì để lại viền tối lởm chởm. Sau đó **cắt sát** phần có hình.
- [x] `ICON_MOOD` ở `shared/config/images.ts` — khoá theo `value` của thẻ mood
      (KHÔNG theo nhãn: nhãn đổi theo ngôn ngữ VI/EN, `value` thì không).
      `null` = chưa có -> thẻ đó tự dùng emoji. Thêm icon mới chỉ sửa **một dòng**.

### Cào lại OpenStreetMap + soát ảnh món (2026-08-23)

**Cào lại toàn bộ 35 ô OSM Hà Nội** (xoá cache để lấy dữ liệu tươi, giữ bản sao lưu).
Overpass đêm đó trả 500/502/504 liên tục nên mất ~50 phút, nhưng **không bỏ ô nào**.

Đo bằng `python scripts/data_report.py` TRƯỚC và SAU:

| Chỉ số | Trước | Sau | Chênh |
|---|---:|---:|---:|
| Tổng số quán | 40.720 | 40.704 | **−16** |
| Đơn vị hành chính phủ | 183 | 185 | +2 |
| Quán có trường `dishes` | 1.458 | 1.493 | **+35** |
| Quán có `amenities` | 645 | 659 | +14 |
| Quán có `dietary` | 115 | 124 | +9 |
| Quán có `aliases` | 326 | 329 | +3 |

**Kết luận thẳng thắn: cào lại OSM KHÔNG thêm được quán mới.** Ảnh chụp OSM Hà Nội cũ đã
gần như đầy đủ; cái được là **tag phong phú hơn** (món, tiện nghi, chế độ ăn). 16 bản ghi
biến mất là bản ghi **thiếu tên hoặc thiếu toạ độ** — bước làm sạch loại đúng, vì không có
hai thứ đó thì quán vô dụng.

➡️ **Muốn thêm quán thật thì phải đi đường khác**, không phải cào lại OSM:
Apify (xem `docs/apify_huong_dan.md`) hoặc nhập tay qua trang admin.

**Sửa một chỗ log nói sai:** trước đây báo "12 ô lỗi" trong khi cả 35 ô đều lấy được — 12
ô đó chỉ là **RỖNG** (vùng nông thôn ở rìa hộp bao, không có quán nào). Nay log phân biệt
rõ "ô RỖNG" và "ô LỖI", và cảnh báo riêng khi thật sự có ô lỗi.

**Soát ảnh món — 4 món đang hiện ảnh SAI:**

| Món | Đang hiện ảnh của | |
|---|---|---|
| Lẩu gà lá é | bài "Tuy Hoà (thành phố)" | **ảnh bãi biển** |
| Trà đào cam sả | bài "Lào Cai" | ảnh một tỉnh miền núi |
| Sữa chua trân châu | bài "Hoa Kỳ" | ảnh nước Mỹ |
| Bánh xèo tôm nhảy | bài "Quy Nhơn" | ảnh một thành phố |

Nguyên nhân: `find_dish_images.py` hỏi Wikipedia "bài nào khớp tên món nhất" rồi lấy ảnh
đại diện của bài đó. Món là ĐẶC SẢN vùng nào thì máy tìm kiếm chấm bài về vùng đó cao nhất.

- [x] `scripts/audit_dish_images.py` — soát bằng `description` (mô tả ngắn Wikidata),
      loại bài mô tả một nơi chốn/con người. Đã gỡ 4 ảnh sai (`--clear`).
- [x] Chặn ngay tại nguồn: `find_dish_images.py` nay từ chối bài không phải món ăn.
- ⚠️ **Hai luật đã phải trả giá mới có** (lần chạy đầu báo nhầm 5/9 món):
      chỉ xét `description` chứ không xét tóm tắt · khớp TỪ NGUYÊN VẸN qua
      `contains_phrase` — khớp chuỗi con thì "song" nằm trong "rau sống" và món salad bị
      chấm là "con sông". Đúng lỗi kinh điển ở CLAUDE.md mục 4.5, vừa tái diễn.

### Đổi mật khẩu khi đang đăng nhập + 2 lỗi vận hành (2026-08-23)

- [x] **`POST /auth/change-password`** + ô nhập ở tab Cài đặt. **Vẫn hỏi mật khẩu hiện tại**
      dù đã có token: token sống 24 giờ trong trình duyệt, ai mượn được máy là chiếm được
      tài khoản. 5 test. Câu trả về nói rõ giới hạn: máy khác vẫn dùng được tới khi token
      hết hạn (thu hồi thật cần cột `token_version` — đổi lược đồ, phải chốt trước).
- [x] **Sửa lỗi `.gitignore` làm frontend KHÔNG BUILD ĐƯỢC khi clone về.**
      Dòng `lib/` (chép từ mẫu .gitignore của Python) khớp MỌI thư mục tên `lib` ở mọi độ
      sâu, và trong dự án chỉ có đúng hai thư mục như vậy — cả hai đều là MÃ NGUỒN:
      `frontend/apps/{client,admin}/src/shared/lib/` (session.ts, tokenStorage.ts).
      Nay là `/lib/` (chỉ ở gốc). Thêm `*.tsbuildinfo` vào .gitignore.
- [x] **Sửa 8 script chết giữa chừng trên PowerShell.** Console Windows mặc định cp1252,
      in chữ tiếng Việt là `UnicodeEncodeError` và script dừng ngang. `data_report.py`
      chết đúng ở dòng `additionalInfo/Bầu không khí`. Nay tất cả đều ép stdout về UTF-8.

### Quán yêu thích · lượt khám phá · cấp độ · huy hiệu (2026-08-23)

**Nút thắt phải gỡ trước:** `POST /interactions` chỉ ghi `session_id` — mã ngẫu nhiên của
một tab trình duyệt, đổi mỗi lần xoá dữ liệu. Vì vậy KHÔNG có cách nào đếm "người này đã
khám phá bao nhiêu quán", và đó là lý do bốn con số trên bản thiết kế (27·15·18·5) không
thể dựng được. Nay `InteractionEvent` có thêm `user_id`.

- [x] **`user_id` LẤY TỪ TOKEN, không nhận từ body.** Có test khoá: kẻ gian gửi
      `user_id` của người khác trong JSON thì điểm vẫn rơi vào chủ của token.
- [x] **Khách chưa đăng nhập VẪN ghi được tương tác** (`get_optional_user` không bao giờ
      ném lỗi) — đó là nguồn nhãn huấn luyện và nguồn của tính năng báo đóng cửa.
      Token hết hạn cũng coi như khách, KHÔNG trả 401: chặn ghi nhật ký vì một chuyện
      chẳng liên quan chỉ làm client hiện lỗi ở chỗ vô nghĩa.
- [x] **Bảng `saved_items`** trong `moodbite_users.db` (CÙNG file với tài khoản, vì cả hai
      là dữ liệu GỐC — `moodbite.db` là dữ liệu dẫn xuất và tài liệu còn khuyến khích xoá
      đi dựng lại). Một bảng cho cả quán lẫn món, phân biệt bằng `item_type`.
- [x] **`GET/POST/DELETE /me/favorites` · `GET /me/stats`** — không endpoint nào nhận
      `user_id` từ client. Có test: A không đọc và không xoá được mục của B.
- [x] **Khách lưu ở máy, đăng nhập thì ĐƯỢC ĐẨY LÊN server rồi xoá bản cục bộ.** Không làm
      bước này thì người dùng lưu 5 món, đăng ký tài khoản, và thấy danh sách trống —
      mất dữ liệu ngay tại bước ta đang mời họ đăng ký.
- [x] **Bảng điểm** (`domain/services/gamification.py`, thuần Python):
      xem quán mới **+2** · chỉ đường **+3** · đánh giá **+3** · lưu **+5** ·
      báo quán đóng cửa **+10**.
      Đóng góp cho cộng đồng đáng giá hơn tiêu thụ — đó là lý do báo đóng cửa gấp 5 lần.
- [x] **ĐẾM THỨ KHÁC NHAU, KHÔNG ĐẾM SỐ LẦN BẤM.** Xem lại cùng một quán 20 lần vẫn chỉ
      được tính 1 (có test). Không có luật này thì cấp độ chỉ đo được ai bấm F5 nhiều hơn.
      Lượt `save` cố ý KHÔNG tính ở bộ đếm — số mục đã lưu lấy từ bảng `saved_items`, nếu
      không thì lưu rồi bỏ lưu vẫn còn điểm.
- [x] **5 cấp:** Người mới (0) · Foodie Explorer (50) · Thổ địa Hà Nội (150) ·
      Sành ăn (400) · Huyền thoại ẩm thực (900). Khoảng cách tăng dần (50→100→250→500):
      thưởng dày ở đầu, thưa dần về sau. Thanh tiến độ tính TRONG khoảng giữa hai cấp.
- [x] **5 huy hiệu**, mỗi cái kiểm chứng được từ số đếm thật. Huy hiệu chưa đạt vẫn hiện
      ở dạng mờ kèm tiến độ ("0/20") — chỉ hiện cái đã đạt thì người mới nhìn vào ô trống.
- [x] **Bộ đếm dựng lại từ nhật ký lúc khởi động** (giống bộ đếm báo đóng cửa), nên khởi
      động lại KHÔNG xoá cấp độ của ai.
- [x] 32 test mới (18 domain + 14 HTTP). **Test khoá quan trọng nhất:** tài khoản mới thì
      mọi số phải là **0 thật** — bản thiết kế vẽ 27·15·18·5 và 320/500 điểm, chép mấy con
      số đó vào code là nói dối người dùng.

### Trang tài khoản dựng lại theo `design/profile.png` (2026-08-23)

- [x] **Thanh bên 7 mục, bấm được hết:** Tổng quan · Hồ sơ cá nhân · Sở thích & khẩu vị ·
      Quán & món đã lưu · Đã xem gần đây · Cấp độ & huy hiệu · Cài đặt.
- [x] **Tab nằm trên URL** (`/account?tab=saved`) chứ không phải state trong bộ nhớ — nút
      Back chạy đúng và gửi link tới đúng mục được.
- [x] **Bốn ô số liệu** đúng như thiết kế, và cả bốn đều là số đếm thật.
- [x] Cột phải: thẻ **Cấp độ** + lưới **Huy hiệu**, đúng vị trí trong bản thiết kế.

**BA mục trong bản thiết kế CHƯA dựng — thiếu DỮ LIỆU, không phải thiếu thời gian:**

| Mục | Thiếu gì |
|---|---|
| "Địa chỉ của tôi" | Không có bảng địa chỉ, không có endpoint. Vị trí hiện lấy từ trình duyệt |
| "Bộ sưu tập của tôi" | Cần bảng `collections` + endpoint. Khác "đã lưu" ở chỗ người dùng tự đặt tên nhóm — là một tính năng riêng |
| "Thông báo" (chuông đỏ) | Không có nguồn thông báo nào. Cái chuông sẽ luôn trống |

### Song ngữ Việt–Anh (2026-08-23)

- [x] **Một file từ điển duy nhất**: `frontend/apps/client/src/shared/i18n/tu_dien.ts`.
      Bản `en` khai kiểu `Record<Khoa, string>` nên **thiếu một câu là lỗi biên dịch** —
      không thể quên dịch mà vẫn build được.
- [x] Ô chọn VI/EN ở thanh trên và trong Cài đặt; nhớ lựa chọn ở localStorage; cập nhật
      `<html lang>` (trình đọc màn hình dựa vào đó để chọn giọng).
- [x] **Mặc định LUÔN là tiếng Việt**, cố ý KHÔNG đoán theo `navigator.language`: nhiều
      máy ở Việt Nam cài Windows bản tiếng Anh, buổi bảo vệ mở ra thành giao diện tiếng
      Anh là hỏng việc.
- [x] 6 test: bản tiếng Anh không còn sót chữ tiếng Việt · không câu nào rỗng ·
      placeholder `{name}` phải giống nhau ở cả hai bản.
- ⬜ **KHÔNG dịch được:** tên món, tên quán, địa chỉ, câu ngữ cảnh ("buổi tối", "trời
      mưa"), thông báo lỗi từ API, giới thiệu món lấy từ Wikipedia tiếng Việt. Tất cả do
      **backend** sinh bằng tiếng Việt — dịch nốt nghĩa là làm i18n ở backend, việc riêng
      và tốn hơn hẳn. Ô chọn ngôn ngữ nói rõ điều này ở `title`.

### Sửa lỗi vận hành + trang tài khoản vừa một màn hình (2026-08-22, tối)

- [x] **`run_dev.py` tự né cổng bận.** Nguyên nhân lỗi "Món phổ biến hôm nay báo lỗi":
      Windows để lại SOCKET MA ở cổng 8001 (tiến trình đã chết nhưng cổng vẫn LISTENING),
      uvicorn khởi động rồi chết ngay với WinError 10048, còn frontend vẫn trỏ cổng cũ nên
      chỉ báo "không kết nối được máy chủ" — không ai đoán ra nguyên nhân. Nay `run_dev.py`
      thử bind trước, bận thì nhảy sang 8002-8005 và truyền `VITE_API_BASE` cho frontend.
- [x] **Trang đăng nhập/đăng ký VỪA ĐÚNG MỘT MÀN HÌNH, không cuộn, không cắt form.**
      `.auth` cao đúng `100dvh` + `overflow: hidden`; mọi khoảng cách dọc đo bằng `vh` nên
      màn hình càng thấp thẻ càng co. Dưới 820px ẩn thêm câu phụ + dòng gợi ý ô email (vẫn
      GIỮ dòng gợi ý tên đăng nhập vì sai luật là backend từ chối). Đã chụp kiểm ở 900 /
      800 / 700 / 650px — vừa hết.

### Quên mật khẩu qua email (2026-08-22)

Chủ dự án yêu cầu, làm bằng cách MIỄN PHÍ — không cần thẻ thanh toán (CLAUDE.md mục 1b).

- [x] **SMTP của Gmail + `smtplib` (thư viện chuẩn)** — không thêm phụ thuộc, không cần
      tên miền, không cần thẻ. Dùng **mật khẩu ứng dụng** chứ không phải mật khẩu Gmail
      thật. Hạn mức ~500 thư/ngày, thừa cho demo. Cấu hình: xem `.env.example`.
- [x] **`POST /auth/forgot-password`** — LUÔN trả cùng một câu dù tài khoản có tồn tại hay
      không (nếu khác nhau thì đây thành công cụ dò xem ai đã đăng ký). Giới hạn 3 lần/giờ
      mỗi IP vì mỗi lần gọi là một lá thư thật.
- [x] **`POST /auth/reset-password`** — đổi mật khẩu bằng token trong thư.
- [x] **Token CHỈ DÙNG MỘT LẦN mà KHÔNG thêm bảng nào.** Token mang theo "vân tay" của
      chuỗi băm mật khẩu hiện tại; đổi mật khẩu xong thì băm đổi → vân tay lệch → chính
      cái link vừa dùng chết ngay. Không phải thêm bảng `password_reset_tokens`, không
      phải dọn token hết hạn (đổi lược đồ dữ liệu là việc phải chốt trước — xem
      `docs/API_DECISIONS_PENDING.md`). Sống 30 phút.
- [x] **Secret RIÊNG** `MOODBITE_RESET_SECRET` (bỏ trống thì lui về secret đăng nhập).
      Token này nằm trong hộp thư — nơi dễ lộ hơn trình duyệt — nên chữ ký của nó không
      được mở cửa đăng nhập. Có test khoá: token đăng nhập KHÔNG đổi được mật khẩu.
- [x] **Cột `email` trong bảng `users`** — TUỲ CHỌN, không UNIQUE, không lộ ra `/auth/me`.
      Có bước nâng cấp tại chỗ cho CSDL cũ (`ALTER TABLE` khi thiếu cột).
      ⚠️ Lỗi đã gặp: tạo index trên cột email TRƯỚC khi thêm cột → "no such column".
- [x] **Frontend:** `/quen-mat-khau` và `/dat-lai-mat-khau?token=...`, link "Quên mật
      khẩu?" ở trang đăng nhập nay là link THẬT. Trang đăng ký có thêm ô Email (không bắt
      buộc) — bản thiết kế không có ô này, thêm vì không có email thì không gửi thư được.
- [x] 15 test backend + 8 test frontend, KHÔNG gửi thư thật (dùng `FakeEmailSender`).

**Chưa làm:** đổi mật khẩu khi ĐANG đăng nhập (khác luồng quên mật khẩu), và xác minh email
lúc đăng ký.

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

## 🎨 CẦN THIẾT KẾ BỔ SUNG (báo cáo 2026-08-23)

Những màn hình dưới đây **chưa có bản thiết kế**, nên chưa dựng. Xếp theo mức đáng làm.

| # | Màn hình | Vì sao cần | Backend đã sẵn sàng? |
|---|---|---|---|
| 1 | **Trang chi tiết QUÁN** (`/restaurants/:id`) | Hiện chi tiết quán chỉ là một panel trượt trong trang bản đồ — không gửi link được, không lưu được, không có địa chỉ riêng. Đây là lỗ hổng lớn nhất còn lại của giao diện | ✅ `GET /restaurants/{id}` đã có đủ review · ảnh · giá · giờ |
| 2 | **Bộ lọc dạng ngăn kéo (drawer)** | Xem mục "Bộ lọc" bên dưới | ✅ không cần gì thêm |
| 3 | **Thanh ☰ cho điện thoại** | Thanh trên hiện xếp dọc khi màn hình hẹp, dùng được nhưng chiếm chỗ | ✅ |
| 4 | "Bộ sưu tập của tôi" | Có trong `design/profile.png` và trên thanh điều hướng của `design/Home.jpg` | ❌ cần bảng `collections` + endpoint |
| 5 | "Địa chỉ của tôi" | Có trong `design/profile.png` | ❌ cần bảng địa chỉ |
| 6 | "Thông báo" (chuông đỏ) | Có trong cả hai bản thiết kế | ❌ không có nguồn thông báo nào |
| 7 | "Theo mood" · "Theo thời tiết" (trang riêng) | Có trên thanh điều hướng `design/Home.jpg` | 🟡 lọc được rồi, nhưng hiện nằm TRONG trang chủ |
| 8 | "Blog" | Có trên thanh điều hướng | ❌ không có nội dung |

**Đề xuất:** làm mục 1-3 trước — cả ba đều đã có sẵn dữ liệu, chỉ thiếu bản vẽ.
Mục 4-8 cần quyết định có làm hay không TRƯỚC khi vẽ, vì mỗi mục kéo theo một phần backend.

### 🖼️ Ảnh / icon còn thiếu — cần chủ dự án gửi

Những chỗ này đang dùng **emoji tạm**. Emoji chạy được nhưng mỗi hệ điều hành vẽ một kiểu,
và không khớp bộ nhận diện. Có file thì thay vào `frontend/design/attribute/` rồi chạy
`python scripts/prepare_design_assets.py`.

| Cần gì | Đang tạm dùng | Dùng ở đâu |
|---|---|---|
| **Bộ icon mood** — còn 5/7 | ✅ cay · ✅ thư giãn · ⬜ 😊 🍲 🌧️ 🔥 🍜 | hàng "Gợi ý nhanh theo mood" — *chủ dự án gửi dần* |
| **5 icon huy hiệu** (khối lục giác như thiết kế) | 🧭 👨‍🍳 📅 🗺️ 🛡️ | thẻ "Huy hiệu của bạn" |
| **Icon ngôi sao cấp độ** | ⭐ | thẻ "Cấp độ của bạn" |
| **Icon máy ảnh** trên ảnh đại diện | chữ "Tải ảnh lên" | thiết kế có nút máy ảnh tròn màu cam ở góc avatar |
| **Khẩu hiệu bản tiếng Anh** | dựng bằng chữ hệ thống | trang chủ khi bật EN — bản tiếng Việt là ảnh, bản Anh chưa có |
| **Ảnh nền trang đăng ký bản lớn** | 404×269 px (nhoè khi phóng to) | trang `/register` — bản đăng nhập là 1672×941 |
| **6 icon "khám phá theo nhu cầu"** | 📍 🌙 🌅 🍢 🍜 🧊 | hàng "Khám phá theo nhu cầu" |

### Bộ lọc — có cần một layout riêng không?

**Kết luận: KHÔNG cần một TRANG riêng, nhưng CẦN đổi chỗ đặt.**

Lý do không tách trang:
- Chỉ có **21 điều khiển** (6 mood + 9 cách chế biến + 5 bữa + 1 bán kính). Đủ gọn cho
  một khối, không cần cả một trang.
- Lọc là việc **lặp**: bấm → nhìn kết quả → bấm tiếp. Tách sang trang riêng là cắt đứt
  vòng lặp đó, người dùng phải đi đi về về.

Nhưng chỗ đặt hiện tại **sai**: khối "Lọc chi tiết" đang nằm **DƯỚI** danh sách kết quả,
nên muốn lọc phải cuộn xuống, bấm xong lại cuộn lên. Hai phương án:

| Phương án | Mô tả | Ưu | Nhược |
|---|---|---|---|
| **A (đề xuất)** | Nút "Lọc" cạnh tiêu đề kết quả, bấm ra **ngăn kéo trượt từ phải** | Không chiếm chỗ; dùng chung một component cho cả máy tính lẫn điện thoại; giữ nguyên lưới món rộng | Phải bấm thêm một lần mới thấy bộ lọc |
| B | Cột lọc cố định bên trái (kiểu trang thương mại điện tử) | Luôn nhìn thấy | Bóp lưới món còn ~70% bề ngang; trên điện thoại vẫn phải làm ngăn kéo — thành hai bản |

**Chờ chủ dự án chọn A hay B trước khi dựng.** Không cần bản vẽ tay: cả hai đều dùng lại
đúng các chip đang có, chỉ đổi vị trí.

---

## 📊 TIẾN ĐỘ — đánh giá thẳng thắn (2026-08-23)

**Số liệu thật, không ước lượng cảm tính:**

| Chỉ số | Giá trị |
|---|---|
| Ngày commit đầu tiên | 2026-07-29 |
| Số commit | 112 |
| Số ngày đã làm | ~26 ngày |
| Test | 481 backend + 147 frontend = **628** |
| Dữ liệu quán | 40.720 (Hà Nội) |
| Danh mục món | 747 món · 92% có ảnh · 100% có giới thiệu |
| `python scripts/verify.py` | **9/9 đạt** |

### Đã xong bao nhiêu phần trăm?

Chia theo hạng mục của đề án, chấm theo *chạy được thật*, không theo *đã viết code*:

| Hạng mục | Xong | Ghi chú |
|---|---:|---|
| Backend + API | **95%** | thiếu `POST /admin/restaurants` |
| Dữ liệu quán | **85%** | đủ tên/toạ độ/loại; thiếu sao·giá·giờ (2-4%) |
| Danh mục món | **95%** | |
| Lớp 1 phân cụm | **100%** | |
| Lớp 2 tìm kiếm ngữ nghĩa | **100%** | |
| Lớp 3 xếp hạng | **60%** | công thức trọng số chạy tốt; **mô hình HỌC thì chưa** |
| Lớp 4 tóm tắt review | **100%** | 851/1310 quán |
| Lớp 5 gợi ý món | **100%** | |
| Giao diện người dùng | **85%** | còn trang chi tiết quán riêng, bản mobile |
| Tài khoản + cá nhân hoá | **95%** | ✅ **xác minh email xong 2026-08-24** (`/auth/verify-email/*`, trang `/verify-email`, 15 test). Còn: thu hồi token |
| Trang quản trị | **70%** | code xong, **chưa bật trên máy**, chưa thêm mới quán được |
| Triển khai (deploy) | **10%** | mới có `Procfile`, chưa deploy lần nào |
| Báo cáo / tài liệu bảo vệ | **?** | ngoài phạm vi file này — **tự đánh giá** |

**Trung bình có trọng số: khoảng 82–85%.**

### Bao giờ xong?

Với nhịp hiện tại (~4 commit/ngày, mỗi phiên làm xong 1-2 hạng mục lớn):

| Mốc | Còn lại | Ước tính |
|---|---|---|
| Bật quản trị + thêm quán mới | 4 việc cấu hình + 2 việc code | **1 ngày** |
| Trang chi tiết quán + bản mobile | | **1-2 ngày** |
| Deploy thật (Render/Fly free tier) | | **1 ngày** |
| Bổ sung dữ liệu Apify | phụ thuộc credit | **1 buổi/đợt** |
| Lớp 3 mô hình học | **CHẶN — chờ dữ liệu tương tác** | xem cảnh báo dưới |

➡️ **Phần LÀM ĐƯỢC còn lại: 3–5 ngày làm việc.**
➡️ **Không tính Lớp 3 học máy** — mục đó không phụ thuộc vào tốc độ code.

### ⚠️ RỦI RO LỚN NHẤT — nói thẳng

**`interactions.jsonl` mới có 1 bản ghi.**

Đề án hứa Lớp 3 là *mô hình xếp hạng học có giám sát*. Muốn học thì phải có nhãn, mà nhãn
chính là file này. Với 1 bản ghi thì **không thể huấn luyện, cũng không thể đánh giá bằng
NDCG/Precision@K** — hai thứ đề án mục 8 nêu đích danh.

Đây **không phải** vấn đề lập trình (code ghi nhãn đã chạy từ lâu). Đây là vấn đề **chưa
có ai dùng app**. Ba đường ra, chọn sớm chừng nào tốt chừng đó:

1. **Nhờ 20-30 người dùng thử 15 phút** → vài trăm tương tác → đủ để huấn luyện một mô
   hình nhỏ và đo được. *Rẻ nhất, thật nhất, và làm được ngay tuần này.*
2. **Sinh nhãn mô phỏng** — huấn luyện được, nhưng **phải nói rõ trong báo cáo là mô
   phỏng**. Giấu đi là gian lận học thuật.
3. **Đổi cách trình bày**: nói thẳng Lớp 3 hiện là công thức trọng số giải thích được,
   và mô hình học là hướng phát triển. Trung thực, nhưng mất một điểm mạnh của đề án.

**Khuyến nghị: chọn (1), và chọn NGAY.** Càng để muộn càng không kịp thu dữ liệu trước
ngày bảo vệ. Mọi thứ khác trong danh sách đều làm được trong vài ngày; riêng việc này cần
NGƯỜI THẬT và cần THỜI GIAN TRÔI QUA — không rút ngắn được bằng cách code nhanh hơn.

### Có đang chậm tiến độ không?

**Không chậm về khối lượng code** — 26 ngày, 112 commit, 628 test, 9/9 mục kiểm đạt là
nhịp tốt.

**Chậm ở đúng một chỗ: thu thập tương tác người dùng.** Và đó lại là thứ chặn phần "học
máy" — phần dễ bị hỏi nhất khi bảo vệ. Nhắc lại ở mỗi lần cập nhật file này cho tới khi
`interactions.jsonl` có ít nhất **500 bản ghi từ người thật**.

---

## 🚧 VIỆC TIẾP THEO

> **Quy ước:** mục dưới đây CHỈ chứa việc **chưa làm hoặc chưa xong**.
> Việc đã xong nằm ở phần ✅ ĐÃ LÀM XONG bên trên — không lặp lại ở đây.

| # | Việc | Chặn bởi | Ai làm được |
|---|---|---|---|
| ~~1-4~~ | ~~Bật quản trị (SQLite + tài khoản + 4 biến)~~ | — | ✅ **XONG 2026-08-23** |
| ~~5-6~~ | ~~`POST /admin/restaurants` + form thêm quán~~ | — | ✅ **XONG 2026-08-23** |
| 7 | **Trang chi tiết QUÁN riêng** (hiện chỉ có panel trong bản đồ) | **chờ bản thiết kế** | xem mục 🎨 CẦN THIẾT KẾ BỔ SUNG |
| ~~8~~ | ~~Bản mobile: thanh ☰~~ | — | ✅ **XONG 2026-08-23** |
| 9 | Xác minh email lúc đăng ký | — | lập trình được |
| 10 | Thu hồi token khi đăng xuất (cột `token_version`) | **cần chốt đổi lược đồ** | chờ quyết định |
| 11 | Bổ sung dữ liệu qua Apify | tài khoản + credit | cần người thật — xem `docs/apify_huong_dan.md` |
| 12 | Nhập tay 50-100 quán Hoàn Kiếm | mục 1-4 | cần người thật |
| 13 | **Thu tương tác từ người dùng thật** | **cần người thật** | ⬅ **ƯU TIÊN CAO NHẤT** |
| 14 | Huấn luyện mô hình xếp hạng | mục 13 | ⛔ chờ dữ liệu |
| 15 | Đánh giá NDCG / Precision@K | mục 14 | ⛔ chờ dữ liệu |
| 16 | Deploy + bật `MOODBITE_ENABLE_WEATHER=1` + siết CORS | chưa deploy | cần môi trường thật |
| 17 | Google Places API | **cần thẻ thanh toán** | ⏸️ để sau |

**Đọc nhanh:** mục 1-6 và 8 đã xong. Mục 7 **chờ bản thiết kế**, mục 9 lập trình được.
Mục 13 là thứ **quan trọng nhất và không code thay được**.

### Đổi mật khẩu quản trị

```powershell
python scripts/make_admin_password.py --write-env
```

Ghi thẳng vào `.env.local` (đã .gitignore), rồi khởi động lại backend.
Kiểm bất cứ lúc nào: `python scripts/check_permissions.py`.
Chạy app quản trị: `python scripts/run_dev.py --admin` (cổng 5174).

### Mở rộng dữ liệu — miễn phí trước, trả phí sau

- [ ] **Apify free tier mỗi tháng** — xem hướng dẫn đầy đủ kèm thông số ở
      **`docs/apify_huong_dan.md`** (2026-08-23). Ưu tiên **giờ mở cửa · sao · giá**,
      không phải tìm quán mới (Overture đã cho 36.176 quán miễn phí).
- [ ] **Nhập tay quán trọng điểm** ở Hoàn Kiếm qua trang admin.
- [ ] ⏸️ Google Places API — chỉ khi có thẻ thanh toán.

> ⚠️ ĐỪNG scrape ShopeeFood/GrabFood/Foody/Facebook để lách — vi phạm ToS, rất dễ bị hỏi
> khi bảo vệ. Xem `docs/data_sources.md`.

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

> 📖 **Bản đầy đủ, giải thích từng file và cách mở từng màn hình:
> [`docs/BAN_DO_DU_AN.md`](docs/BAN_DO_DU_AN.md)** (viết 2026-08-23).
> Dưới đây chỉ là bản rút gọn.

```
src/                                 BACKEND — Clean Architecture
├── domain/                          QUY TẮC NGHIỆP VỤ — thuần Python, không framework
│   ├── entities/                      Restaurant · Dish · InteractionEvent · User · SavedItem
│   ├── value_objects/
│   │   ├── mood.py                    bảng điểm mood ⭐
│   │   ├── context_signal.py          thời tiết/giờ ảnh hưởng xếp hạng thế nào ⭐
│   │   ├── location.py                toạ độ + haversine
│   │   ├── price.py · opening_hours.py
│   │   └── text.py                    bỏ dấu, khớp từ nguyên vẹn ⭐⭐
│   └── services/
│       ├── search_ranking.py          CÔNG THỨC XẾP HẠNG QUÁN ⭐⭐
│       ├── dish_ranking.py            CÔNG THỨC XẾP HẠNG MÓN ⭐⭐
│       ├── dish_matching.py           suy món từ tên quán ⭐
│       ├── text_relevance.py          khớp câu tự do với quán ⭐
│       ├── closure_reports.py         ngưỡng báo quán đóng cửa
│       ├── gamification.py            ĐIỂM · CẤP ĐỘ · HUY HIỆU ⭐ (2026-08-23)
│       └── activity_tally.py          đếm lượt khám phá theo NGƯỜI (2026-08-23)
├── application/
│   ├── ports/                         hợp đồng (Protocol) — không có code thật
│   └── use_cases/                     search_restaurants ⭐ · suggest_dishes ⭐ ·
│                                      find_restaurants_for_dish · log_interaction ·
│                                      manage_account · manage_favorites · get_user_stats
├── infrastructure/
│   ├── repositories/                  CSV/JSON/SQLite → entity (pandas dừng ở đây)
│   ├── adapters/                      thời tiết Open-Meteo · TF-IDF · model ML
│   ├── auth/                          băm mật khẩu · token HMAC · giới hạn tần suất
│   ├── notifications/                 gửi thư SMTP
│   └── config/settings.py             mọi đường dẫn + biến môi trường ⭐
└── presentation/api/
    ├── dependencies.py                LẮP MỌI THỨ LẠI ⭐⭐ (đọc file này trước tiên)
    ├── schemas.py                     hợp đồng với frontend ⭐
    ├── envelope.py                    {data}/{error} + mã lỗi
    ├── error_handlers.py              lỗi → mã HTTP
    └── routers/                       search · dishes · restaurants · interactions ·
                                       meta · auth · me · admin

frontend/                            Monorepo npm workspaces — React + TS + FSD
├── packages/api-client/src/         DÙNG CHUNG cho app client và app admin
│   ├── schema.d.ts                    SINH TỰ ĐỘNG từ openapi.json — KHÔNG sửa tay
│   ├── http.ts                        nơi DUY NHẤT biết envelope {data}/{error} ⭐
│   ├── endpoints.ts · auth.ts · admin.ts
└── apps/client/src/
    ├── app/                         App.tsx · routes.tsx · layout/ · styles/
    │   └── styles/                    brand · auth · home · account
    ├── pages/                       home · dish · search · account · login · register ·
    │                                forgot-password · reset-password · not-found
    ├── widgets/                     site-header · home-hero · mood-quick-pick ·
    │                                explore-needs · dish-list · restaurant-list ·
    │                                restaurant-map · user-progress · auth-layout
    ├── features/                    MỘT hành động = MỘT feature
    │   ├── suggest-dishes/            model/useDishSuggestions.ts ⭐ + ui/DishFilters.tsx
    │   ├── search-restaurants/        model/useSearch.ts ⭐
    │   ├── save-favorite/             model/useFavorites.ts ⭐ (máy ↔ server)
    │   ├── change-avatar/             4 lớp chặn bảo mật ⭐
    │   ├── change-password/           đổi mật khẩu khi đang đăng nhập
    │   ├── taste-preferences · recent-dishes · report-closure ·
    │   ├── pick-location · switch-theme · log-interaction ·
    │   └── auth-login · auth-register · auth-recover-password
    ├── entities/                    restaurant (format ⭐) · dish · user (session, stats)
    └── shared/                      api/ · config/ · lib/ · ui/ · i18n/ (từ điển VI–EN ⭐)
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

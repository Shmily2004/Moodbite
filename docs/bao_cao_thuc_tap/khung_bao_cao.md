# Khung báo cáo thực tập tốt nghiệp — MoodBite

**Tên đề tài (chốt 2026-09-08):**
*Nghiên cứu và xây dựng hệ thống gợi ý món ăn theo ngữ cảnh sử dụng mô hình lai phân cụm
và tìm kiếm ngữ nghĩa — thử nghiệm trên dữ liệu quán ăn Hà Nội*
(*A Hybrid Clustering and Semantic Search Approach to Context-Aware Food Recommendation:
A Case Study on Hanoi Restaurant Data*)

**Cách dùng file này.** Mỗi mục ghi: (1) cần viết gì, (2) lấy bằng chứng ở đâu trong repo,
(3) hình/bảng nên có. Độ dài ghi trong ngoặc chỉ là gợi ý cho báo cáo khoảng 60–80 trang;
theo mẫu của khoa nếu khác.

**Luật cho mọi con số trong báo cáo** (theo `CLAUDE.md` mục 0 và 4b): mỗi số phải chạy lại
được bằng một lệnh. Các mục dưới đây ghi sẵn lệnh. **Đo lại ngay trước khi nộp**, đừng chép
số từ `PROJECT_CHECKLIST.md`: dữ liệu đổi thì số đổi.

---

## Phần đầu (không đánh số chương)

- Bìa · Lời cam đoan · Lời cảm ơn · Nhận xét của đơn vị thực tập / giảng viên
- Mục lục · Danh mục hình · Danh mục bảng · Danh mục từ viết tắt
  (API, REST, TF-IDF, KMeans, NDCG, MRR, LTR, OSM, FSD, MVVM, HMAC, CI…)
- **Giới thiệu đơn vị thực tập** (1–2 trang): chỉ thêm nếu khoa bắt buộc. Nhiều khoa đặt
  mục này ở đầu Chương 1; đối chiếu với mẫu.

---

## CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI VÀ CƠ SỞ LÝ THUYẾT  (≈ 18–22 trang)

### 1.1. Lý do chọn đề tài
- **Bối cảnh:** quá nhiều lựa chọn quán, thiếu thông tin để quyết định *đúng lúc, đúng chỗ*.
  Vấn đề không phải thiếu dữ liệu mà dữ liệu không được sắp theo nhu cầu tức thời.
- **Bốn nỗi đau** (lấy từ `docs/original/MoodBite_De_An_Y_Tuong.md` mục 1): không biết quán
  nào hợp tâm trạng; không diễn đạt được nhu cầu bằng bộ lọc cứng; không tính tới thời
  tiết/giờ; đọc nhiều review mà vẫn không ra kết luận.
- **Khoảng trống của công cụ hiện có:** tìm *quán* trước, còn người dùng thường nghĩ tới *món*
  trước ("trời lạnh muốn ăn gì nóng"). Đây là lý do của quyết định đảo luồng 2026-08-19.
- **Phát biểu bài toán:** xếp hạng theo ngữ cảnh động (context-aware ranking), không phải
  bài toán phân loại.

### 1.2. Mục tiêu, đối tượng và phạm vi
- Mục tiêu: hệ thống web gợi ý MÓN → QUÁN, gồm 5 lớp mô hình (đề án mục 3).
- Đối tượng: người dùng cuối ở Hà Nội; quản trị viên dữ liệu.
- **Phạm vi (nói rõ, hội đồng sẽ hỏi):**
  - Địa lý: **chỉ Hà Nội** (chốt 2026-08-19).
  - Dữ liệu: chỉ nguồn hợp pháp (OSM, Overture Maps, Apify trước đây). **Không** cào
    ShopeeFood/Foody/GrabFood/TripAdvisor/Facebook vì ToS cấm, xem `docs/data_sources.md`.
  - Chi phí bằng 0, không cần thẻ thanh toán, nên dùng Leaflet + OSM thay Google Maps và
    haversine thay Google Routes.
  - Món là **suy luận** từ tên quán và review, không phải thực đơn thật.

### 1.3. Phương pháp nghiên cứu
- Nghiên cứu tài liệu (hệ gợi ý, IR, xử lý tiếng Việt).
- Thực nghiệm có đo đạc: mọi siêu tham số được chọn bằng số đo (k của KMeans, ngưỡng…).
- Phát triển phần mềm có kiểm thử tự động và kiểm kiến trúc bằng máy.

### 1.4. Khảo sát các hệ thống liên quan  (≈ 2–3 trang)
- Google Maps, Foody/ShopeeFood, GrabFood, TripAdvisor: mô tả tính năng gợi ý **dựa trên
  quan sát khi dùng**, không dựa trên dữ liệu cào.
- Bảng so sánh: tìm bằng câu tự nhiên · ngữ cảnh thời tiết/giờ · gợi ý món trước · bản đồ
  · minh bạch độ tin cậy dữ liệu.
- Kết luận: khoảng trống MoodBite nhắm tới.

### 1.5. Cơ sở lý thuyết  (≈ 10–12 trang, lõi của chương)

| Mục | Nội dung cần trình bày | Gắn với phần nào của hệ thống |
|---|---|---|
| 1.5.1 Hệ gợi ý | Content-based, collaborative filtering, hybrid; **context-aware RS** (pre-filtering / post-filtering / contextual modeling, Adomavicius & Tuzhilin); bài toán **cold start** | Toàn hệ thống; luật Cold Start `NEUTRAL_CLUSTER_SCORE = 0.5` |
| 1.5.2 Phân cụm | KMeans, chuẩn hoá đặc trưng, chọn k; **Silhouette, Davies–Bouldin, Calinski–Harabasz** | Lớp 1 — `data_pipeline/clustering.py` |
| 1.5.3 Truy hồi thông tin | Mô hình không gian vector, **TF-IDF**, n-gram ký tự, **độ tương đồng cosine**; so sánh với embedding nơ-ron (sentence-transformers, PhoBERT) và lý do chọn TF-IDF (chạy CPU, miễn phí, giải thích được) | Lớp 2 — `src/infrastructure/adapters/tfidf_semantic_search.py` |
| 1.5.4 Xếp hạng | Hàm điểm tuyến tính có trọng số; **learning-to-rank** (pointwise/pairwise/listwise, LambdaMART); **thiên lệch vị trí** (position bias) trong dữ liệu bấm | Lớp 3 — `src/domain/services/search_ranking.py` |
| 1.5.5 Tóm tắt văn bản | Tóm tắt trích rút và tóm tắt sinh; centroid TF-IDF; vì sao chọn trích rút (không bịa chữ) | Lớp 4 — `data_pipeline/review_summary.py` |
| 1.5.6 Xử lý tiếng Việt | Dấu thanh, Unicode **NFC/NFD**, bỏ dấu để khớp, **đụng độ sau khi bỏ dấu** (phở/phố/phớ), khớp từ nguyên vẹn thay vì chuỗi con | `src/domain/value_objects/text.py` |
| 1.5.7 Dữ liệu không gian | Toạ độ WGS84, công thức **haversine**, bbox, OpenStreetMap / Overpass / Overture Maps | `domain`, `data_pipeline/sources/` |
| 1.5.8 Đánh giá xếp hạng | **NDCG@K, Precision@K, MRR**, coverage; baseline ngẫu nhiên và baseline khoảng cách | `scripts/synthetic/metrics.py` |
| 1.5.9 Kiến trúc phần mềm | **Clean Architecture** (dependency rule), **Feature-Sliced Design**, **MVVM**, REST + envelope | `docs/backend_architecture.md`, `docs/frontend_architecture.md` |
| 1.5.10 Công nghệ | FastAPI, Pydantic, SQLite; React + TypeScript + Vite; Leaflet; scikit-learn | `requirements.txt`, `frontend/package.json` |

> Mỗi lý thuyết chỉ trình bày phần **có dùng** trong hệ thống; cuối mỗi mục ghi một câu
> "Trong MoodBite, lý thuyết này được áp dụng ở…". Hội đồng thường hỏi "học cái này để làm gì".

### 1.6. Kết luận chương 1

---

## CHƯƠNG 2. THIẾT KẾ VÀ XÂY DỰNG HỆ THỐNG  (≈ 28–35 trang)

### 2.1. Phân tích yêu cầu  (≈ 4 trang)
- **Tác nhân:** Khách · Người dùng đã đăng nhập · Quản trị viên.
- **Sơ đồ use case** tổng quát + đặc tả 4–6 use case chính (gợi ý món, xem quán của món, tìm
  bằng câu tự nhiên, lưu yêu thích, admin ẩn/sửa quán, admin xem chất lượng dữ liệu).
  Nguồn: `traceability.md` (mỗi use case đã có file hiện thực + test).
- **Yêu cầu chức năng / phi chức năng:** `docs/extracted/MoodBite_SRS_v1.2.md`.
- **Ghi chú thay đổi phạm vi có chủ đích:** tài khoản người dùng ban đầu là *Won't-have*,
  sau đưa vào (xem ghi chú ở `PROJECT_CHECKLIST.md`). Nói thẳng, đừng giấu.

### 2.2. Kiến trúc tổng thể  (≈ 3 trang)
- Sơ đồ 2 tầng: Frontend (FSD + MVVM) ⇄ HTTP `/api/v1` JSON ⇄ Backend (Clean Architecture).
- Nguyên tắc chung: **dependency rule**, cưỡng chế bằng máy
  (`scripts/check_architecture.py`, `npx steiger`).
- **Quyết định kiến trúc và bài học** (`docs/architecture_decisions.md`): từng có 2 backend
  song song nên gộp về 1; logic nghiệp vụ chỉ ở backend.
- Bảng ánh xạ thuật ngữ cổ điển ↔ MoodBite (Model/Data Access/Controller/View), lấy từ
  `CLAUDE.md` mục 1b.

### 2.3. Thu thập và xử lý dữ liệu  (≈ 5–6 trang)
- Nguồn: OSM (Overpass, chia 110 ô), Overture Maps, Apify (lớp làm giàu: review, ảnh, giá).
- Kiến trúc `SourceAdapter` (`data_pipeline/sources/base.py`): thêm nguồn = 1 adapter.
- Pipeline bắt buộc: `merge_and_prepare_raw → data_cleaning → feature_engineering →
  clustering` (vì sao clustering phải chạy cuối).
- Khử trùng lặp (50 m + tên), làm sạch phạm vi Hà Nội, provenance
  (`source`, `source_url`, `last_updated`, `data_confidence`).
- **Bảng thống kê dữ liệu:** số quán, tỷ lệ có rating/giá/ảnh/review theo nguồn.
  Lệnh: `python scripts/data_report.py` và `python scripts/compute_dataset_stats.py`.
- Danh mục món: nguồn Wikipedia/Wikidata + đào cụm từ trong tên quán, có bước duyệt tay
  (`data_pipeline/dish_approved.json`). Lệnh: `python scripts/build_dish_catalog.py`.
- Hình: sơ đồ pipeline; biểu đồ độ phủ trường dữ liệu.

### 2.4. Thiết kế cơ sở dữ liệu  (≈ 3 trang)
- **ERD**. Các bảng thật (đếm từ `CREATE TABLE` trong `src/`): `restaurants`, `users`,
  `saved_items`, `collections`, `collection_items`, `user_addresses`, `posts`, `audit_log`,
  `quality_snapshot`, `issue_resolution`; tương tác lưu ở `interactions.jsonl`.
- Từ điển dữ liệu: `docs/extracted/MoodBite_Data_Dictionary_ERD.md`.
- **Quy ước dữ liệu quan trọng:** `None` ≠ 0 · `price` là chuỗi · thiếu file không làm sập app.

### 2.5. Thiết kế mô hình lai 5 lớp  (≈ 8–10 trang, phần khoa học chính)

Mỗi lớp trình bày cùng một khuôn: **đầu vào → thuật toán → siêu tham số và cách chọn → kết
quả đo → giới hạn**.

| Lớp | Thuật toán | Số liệu cần đo lại | Lệnh |
|---|---|---|---|
| 1. Phân cụm trải nghiệm | KMeans, chọn k bằng Silhouette, ràng buộc cụm ≥ 1% | k, Silhouette, DBI, CH, số quán được phân cụm | `python -m data_pipeline.clustering` |
| 2. Tìm kiếm ngữ nghĩa | TF-IDF n-gram ký tự 2–4 + cosine | số quán, số đặc trưng; bảng ví dụ truy vấn → kết quả | log khởi động app |
| 3. Xếp hạng ngữ cảnh | Hàm trọng số 6 tín hiệu, **tổng = 1.0** | bảng trọng số; có test khoá tổng | `pytest -k weights_sum_to_one` |
| 4. Tóm tắt review | Trích rút, centroid TF-IDF, câu nguyên văn | số quán có ≥ 3 review được tóm tắt | `python -m data_pipeline.review_summary` |
| 5. Gợi ý món (cửa vào) | Luật + điểm trọng số, ràng buộc "phải có quán gần" | số món, số món có quán ở HN | `python scripts/build_dish_catalog.py` |

- **Đối chiếu món ↔ quán:** ưu tiên tên quán hơn `categoryName` (có số đo), khớp từ nguyên
  vẹn, luật dấu khi bỏ dấu. Mỗi kết quả kèm `confidence`.
- **Tín hiệu ngữ cảnh:** giờ ăn/cuối tuần; thời tiết Open-Meteo (tắt mặc định); suy biến an toàn.
- Hình: sơ đồ luồng phối hợp 5 lớp (đề án mục 3, đoạn cuối).

### 2.6. Thiết kế API  (≈ 2–3 trang)
- Base `/api/v1`, envelope `data` / `error`, `snake_case`, bảng mã lỗi (`CLAUDE.md` mục 5).
- Hai lối vào: `/dishes/suggest → /dishes/{id} → /dishes/{id}/restaurants` và `/search`.
- Danh sách endpoint đầy đủ: `docs/extracted/MoodBite_Dac_Ta_API.md` (bổ sung 2026-10).
  Bảng chi tiết để ở Phụ lục.

### 2.7. Xây dựng backend  (≈ 3 trang)
- 4 tầng `domain / application / infrastructure / presentation`; ví dụ đi xuyên một request
  `POST /dishes/suggest` qua cả 4 tầng.
- Xử lý lỗi tập trung (`error_handlers.py`) và vì sao cấm `except Exception` trả 400.
- App factory, không singleton cấp module (bài học `NameError` ở `main.py`).

### 2.8. Xây dựng frontend  (≈ 3 trang)
- FSD: `app → pages → widgets → features → entities → shared`; MVVM: `ui/` (View) và
  `model/use*.ts` (ViewModel).
- App người dùng + khu quản trị; bản đồ Leaflet; song ngữ giao diện.
- Ảnh chụp các màn chính (để dành cho Chương 3 nếu trùng).

### 2.9. Bảo mật  (≈ 2 trang)
- Token HMAC, tách secret người dùng/admin, không nhét `role` vào token, thu hồi bằng
  `token_version`, fail-closed khi thiếu secret, giới hạn tần suất, xác minh email.
- Nguồn: `docs/ra_soat_bao_mat.md`, `tests/test_bao_mat.py`.

### 2.10. Kiểm thử và đảm bảo chất lượng  (≈ 2–3 trang)
- Chiến lược: domain (thuần) → use case (repo giả) → API (TestClient) → frontend (Vitest).
- `python scripts/verify.py`: 10 mục kiểm. **Dán số test thật từ lần chạy cuối.**
- 2–3 bug thật đáng kể làm ví dụ (phở/phố; `"street"` khớp vào `openstreetmap`; route đăng
  ký trùng). Mỗi bug: triệu chứng → nguyên nhân gốc → test khoá. Phần này cho thấy quy trình,
  hội đồng thường đánh giá cao.

### 2.11. Kết luận chương 2

---

## CHƯƠNG 3. DEMO, ĐÁNH GIÁ VÀ PHƯƠNG HƯỚNG PHÁT TRIỂN  (≈ 14–18 trang)

### 3.1. Môi trường cài đặt và triển khai  (≈ 1–2 trang)
- Yêu cầu phần mềm; lệnh chạy một bước `python scripts/run_dev.py --admin`; chuẩn bị máy mới
  `python scripts/chuan_bi_may_moi.py`; đồng bộ dữ liệu qua HuggingFace.

### 3.2. Kịch bản demo  (≈ 6–8 trang, chủ yếu ảnh chụp)
Chụp bằng `python scripts/chup_man_hinh.py` (có `--token` cho trang cần đăng nhập).

| # | Kịch bản | Điểm cần nhấn khi demo |
|---|---|---|
| 1 | Trang chủ: chọn bộ lọc (trời mưa, món nóng) → lưới MÓN | Lý do gợi ý + số quán gần; món không có quán bị ẩn **và có thông báo** |
| 2 | Mở một món → giới thiệu → danh sách quán + bản đồ | Nhãn `confidence` (món là suy luận); nới bán kính thì có báo |
| 3 | Tìm bằng câu tự nhiên "quán yên tĩnh để học bài" | Khớp ngữ nghĩa, `match_source`, tóm tắt review |
| 4 | Chi tiết quán: có / không có chi tiết | `has_details: false` vẫn là 200; dữ liệu thiếu hiện "chưa có", không hiện 0 |
| 5 | Đăng ký → xác minh email → yêu thích, bộ sưu tập, địa chỉ | Phân quyền, thu hồi token khi đăng xuất |
| 6 | Quản trị: Tổng quan, Chất lượng dữ liệu, Cần xử lý, Nhật ký | Minh bạch chất lượng dữ liệu; nhật ký ai làm gì |

### 3.3. Đánh giá kết quả  (≈ 4–5 trang)
- **Lớp 1:** bảng chỉ số phân cụm + mô tả 7 cụm (nhãn trải nghiệm).
- **Lớp 2:** bảng 10–20 truy vấn mẫu, chấm tay độ liên quan top-5 (đề án mục 8 yêu cầu
  đúng cách này).
- **Lớp 3:** NDCG@K / P@K / MRR trên dữ liệu **GIẢ LẬP**, so với baseline ngẫu nhiên và baseline
  khoảng cách. Lệnh: `python scripts/danh_gia_xep_hang.py`.
  > ⚠️ **Trình bày trung thực.** Kết quả hiện tại: MoodBite thắng ngẫu nhiên nhưng **thua
  > baseline khoảng cách**. Nguyên nhân: nhãn giả lập chỉ dựa trên khoảng cách + khẩu vị +
  > rating + giá, không có mood/ngữ nghĩa/cụm, tức là thước đo đang thiên về khoảng cách.
  > Viết rõ "dữ liệu giả lập", nêu giới hạn này và xem nó như kết quả phân tích. Giấu đi hoặc
  > chỉnh trọng số cho đẹp số là sai về học thuật.
- **Lớp 4:** độ phủ tóm tắt + 2–3 ví dụ (câu nguyên văn).
- **Lớp 5:** chấm tay các cặp (ngữ cảnh, món) theo đề án mục 8.
- **Hiệu năng:** độ trễ `/search`, `/dishes/suggest`; thời gian khởi động. Đo trên máy demo.
- **Độ phủ dữ liệu:** bảng từ `scripts/data_report.py`.

### 3.4. Đối chiếu với mục tiêu đề án  (≈ 1–2 trang)
Bảng ba cột: **Đạt / Đạt một phần / Chưa đạt**, mỗi dòng ghi lý do. Gợi ý các dòng "một phần":
- Lớp 3 mới là công thức trọng số, **chưa** là mô hình học có giám sát vì chưa có đủ tương
  tác thật.
- Lớp 2 dùng TF-IDF thay cho embedding nơ-ron (chi phí, CPU).
- "Giao thông thực tế" được thay bằng khoảng cách haversine (Google Routes cần thẻ thanh toán).
- Rating/review/ảnh chỉ phủ một phần nhỏ số quán (lớp làm giàu, ghi tỷ lệ thật).

### 3.5. Hạn chế
Dữ liệu tương tác thật rất ít; món là suy luận; dữ liệu làm giàu phủ thấp; chỉ Hà Nội; nhãn
giả lập thiên về khoảng cách.

### 3.6. Phương hướng phát triển  (≈ 2 trang)
1. **Thu tương tác thật + ghi lượt hiển thị (impression)**, rồi huấn luyện LTR
   (LightGBM LambdaMART) thay cho công thức trọng số; đánh giá offline bằng NDCG.
2. Embedding tiếng Việt (PhoBERT / multilingual-E5) sau cùng port tìm kiếm ngữ nghĩa, không
   phải sửa use case.
3. Phân tích cảm xúc theo khía cạnh (ABSA, bộ VLSP 2018 nhà hàng) cho Lớp 4.
4. Mô hình học cho Lớp 5 khi có dữ liệu bấm chọn món.
5. Mở rộng địa lý (cần quyết định lại phạm vi), dịch dữ liệu, ứng dụng di động (PWA).

---

## KẾT LUẬN  (1–2 trang)
Tóm tắt đóng góp: (1) luồng món-trước, (2) mô hình lai 5 lớp đo được, (3) quy trình dữ
liệu hợp pháp, minh bạch độ tin cậy, (4) kiến trúc cưỡng chế bằng máy. Nhắc lại hạn chế chính.

## TÀI LIỆU THAM KHẢO
Gợi ý tối thiểu: Adomavicius & Tuzhilin (context-aware RS) · Ricci et al., *Recommender
Systems Handbook* · Manning et al., *Introduction to Information Retrieval* (TF-IDF, NDCG) ·
Rousseeuw 1987 (Silhouette) · Burges 2010 (LambdaMART) · Joachims et al. (position bias) ·
Martin, *Clean Architecture* · tài liệu FastAPI, React, Leaflet, OSM/Overture.
**Chỉ đưa tài liệu đã thực sự đọc**, ghi đúng chuẩn trích dẫn khoa yêu cầu (IEEE hoặc APA).

## PHỤ LỤC
- A. Danh sách endpoint API đầy đủ
- B. Ma trận truy vết (`traceability.md`)
- C. Hướng dẫn cài đặt chi tiết
- D. Kết quả `python scripts/verify.py` lần chạy cuối (dán nguyên văn)
- E. Bảng trọng số xếp hạng và lý do chọn

# scripts/ — công cụ dòng lệnh

Mọi script chạy từ **thư mục gốc dự án** bằng `python scripts/<ten>.py`. Viết bằng Python
chính là để chạy giống nhau trên PowerShell 5.1 / CMD / bash — đừng nối lệnh bằng `&&`.
Chi tiết từng script: đọc docstring đầu file (luôn có ví dụ chạy và lý do tồn tại).

Danh sách đối chiếu với thư mục ngày 2026-10-06. Code ở đây là CÔNG CỤ, không phải code
production — production nằm ở `src/`.

## Hằng ngày: chạy, kiểm tra, cấu hình

| Script | Làm gì | Ví dụ |
|---|---|---|
| `run_dev.py` | Chạy backend + app (gồm khu quản trị ở `/quan-tri`) bằng một lệnh, tự chọn cổng | `python scripts/run_dev.py` |
| `verify.py` | Kiểm 10 mục: app dựng được · pytest · Clean Architecture · chỉ 1 backend · frontend typecheck+build · frontend test · FSD · CI cài được · bộ dữ liệu mẫu · ma trận truy vết | `python scripts/verify.py` (một mục: `--chi 4`) |
| `check_architecture.py` | Kiểm hướng phụ thuộc backend (chạy trong CI) | `python scripts/check_architecture.py` |
| `check_permissions.py` | Trang quản trị đã cấu hình đủ chưa (fail-closed → 503 nếu thiếu) | `python scripts/check_permissions.py` |
| `make_admin_user.py` | Tạo / nâng quyền tài khoản admin trong bảng `users`; ghi `MOODBITE_ADMIN_SECRET` + `MOODBITE_STORAGE=sqlite` vào `.env.local`. `--tu-env`: chuyển admin cũ (biến môi trường) sang bảng `users`, giữ nguyên mật khẩu | `python scripts/make_admin_user.py` |
| `build_sqlite.py` | Dựng CSDL SQLite ghi được (`moodbite.db`) từ CSV — cần cho trang quản trị. Không đụng CSDL tài khoản | `python scripts/build_sqlite.py` |
| `check_email.py` | Thử cấu hình SMTP (quên mật khẩu / xác minh email) | `python scripts/check_email.py --to ban@gmail.com` |
| `gui_thu_thu.py` | In / gửi thật một lá thư xác minh để xem bằng mắt | `python scripts/gui_thu_thu.py` |
| `export_openapi.py` | Xuất `frontend/openapi.json` — chạy mỗi khi đổi schema/endpoint, rồi `npm run gen:api` trong `frontend/` | `python scripts/export_openapi.py` |
| `chuan_bi_may_moi.py` | Dựng môi trường trên máy mới (kiểm tra, `--cai` để cài, `--du-lieu` để tải dữ liệu) | `python scripts/chuan_bi_may_moi.py --cai` |
| `dong_bo_du_lieu.py` | Đồng bộ dữ liệu giữa các máy qua HuggingFace Hub (miễn phí) | `python scripts/dong_bo_du_lieu.py --xem` |
| `disk_report.py` | Đo dung lượng dự án, chỉ chỗ dọn được | `python scripts/disk_report.py` |
| `deploy_vps.py` | Cập nhật production (VPS) bằng một lệnh: `backend` / `frontend` / `data` / `all` / `backup` / `status` / `rollback`. Cần `MOODBITE_DEPLOY_HOST`; `--dry-run` chỉ in lệnh. Xem `docs/cap_nhat_production.md` | `python scripts/deploy_vps.py status` |

## Đo dữ liệu quán

| Script | Làm gì | Ví dụ |
|---|---|---|
| `data_report.py` | Độ phủ từng trường của dataset — **chạy trước và sau mỗi lần bổ sung dữ liệu** | `python scripts/data_report.py` |
| `review_report.py` | Đo dữ liệu review (cơ sở quyết định Lớp 4 tóm tắt review) | `python scripts/review_report.py` |
| `ghi_anh_chup_chat_luong.py` | Ghi chỉ số chất lượng dữ liệu của hôm nay (mỗi ngày 1 dòng) | `python scripts/ghi_anh_chup_chat_luong.py` |
| `scrape_targets.py` | Chỉ ra khu vực thiếu dữ liệu Google Maps kèm toạ độ | `python scripts/scrape_targets.py` |
| `refresh_check.py` | Cào lại OSM rồi so với dữ liệu đang dùng (quán mới / mất / đổi tên) | `python scripts/refresh_check.py --dung-cache` |
| `check_websites.py` | Website của quán còn sống không (tín hiệu yếu) | `python scripts/check_websites.py --gioi-han 200` |
| `enrich_freshness.py` | Bổ sung tuổi thật + bằng chứng xác nhận cho quán (mặc định chỉ xem trước) | `python scripts/enrich_freshness.py` |
| `compute_dataset_stats.py` | Thống kê nhanh dataset (script cũ, không có docstring) | `python scripts/compute_dataset_stats.py` |
| `check_mood_csv.py`, `inspect_mood_features.py` | Soi nhanh các cột mood trong CSV (script cũ, không có docstring) | `python scripts/inspect_mood_features.py` |

## Danh mục món

| Script | Làm gì | Ví dụ |
|---|---|---|
| `build_dish_catalog.py` | Dựng `dish_catalog.json` và đo mỗi món có bao nhiêu quán | `python scripts/build_dish_catalog.py` |
| `discover_dishes.py` | Tìm món mới từ Wikipedia/Wikidata (mặc định chỉ báo cáo) | `python scripts/discover_dishes.py` |
| `mine_dish_names.py` | Tìm món từ chính tên quán trong dataset | `python scripts/mine_dish_names.py` |
| `backfill_dish_cuisine.py` | Điền `cuisine` còn trống từ nguồn gốc thật (mặc định chỉ xem) | `python scripts/backfill_dish_cuisine.py` |
| `extend_dish_knowledge.py` | Bổ sung rule món vào `dish_knowledge_base.json` (số liệu trong docstring là của dataset cũ 4170 quán) | `python scripts/extend_dish_knowledge.py` |
| `find_dish_images.py` | Tìm ảnh miễn phí cho món chưa có ảnh (mặc định chỉ thử) | `python scripts/find_dish_images.py --limit 20` |
| `audit_dish_images.py` | Soát ảnh món gắn nhầm (`--clear` để gỡ) | `python scripts/audit_dish_images.py` |
| `review_dish_images.py` | Dựng bảng soát ảnh món để xem bằng mắt | `python scripts/review_dish_images.py --mo` |
| `set_dish_image.py` | Đặt / xoá ảnh cho một món | `python scripts/set_dish_image.py --list-missing` |

## Đo chất lượng tìm kiếm / xếp hạng

| Script | Làm gì | Ví dụ |
|---|---|---|
| `do_khop_loai_hinh.py` | Trang món nào để quán chỉ khớp LOẠI HÌNH chen trên quán khớp TÊN (CLAUDE.md §4.6) | `python scripts/do_khop_loai_hinh.py` |
| `do_trung_am_tim_kiem.py` | `POST /search` có trả quán trùng âm sau khi bỏ dấu không (phở/phố — CLAUDE.md §4.5) | `python scripts/do_trung_am_tim_kiem.py` |
| `gia_lap_nguoi_dung.py` | Sinh người dùng + tương tác GIẢ LẬP qua API thật (xem mục bên dưới) | `python scripts/gia_lap_nguoi_dung.py --users 60 --days 14 --reset` |
| `danh_gia_xep_hang.py` | Đánh giá xếp hạng offline (NDCG/Precision/MRR) trên phiên giả lập | `python scripts/danh_gia_xep_hang.py` |
| `run_suggest_demo.py` | Gọi thẳng use case tìm kiếm trên dữ liệu thật, không cần server | `python scripts/run_suggest_demo.py` |

Thư mục `synthetic/` là module dùng chung của hai script giả lập ở trên, không chạy trực tiếp.

## Giao diện

| Script | Làm gì | Ví dụ |
|---|---|---|
| `chup_man_hinh.py` | Chụp màn hình bằng trình duyệt thật + đo tràn ngang (xem mục bên dưới) | `python scripts/chup_man_hinh.py http://localhost:5173/` |
| `dem_emoji.py` | Đếm emoji còn sót trong mã nguồn frontend | `python scripts/dem_emoji.py --chi-tiet` |
| `make_fixture.py` | Sinh bộ dữ liệu mẫu 100 quán THẬT cho frontend | `python scripts/make_fixture.py` |
| `verify_ui_data.py` | Gác bộ dữ liệu mẫu không được giàu hơn dữ liệu thật (chạy trong `verify.py`) | `python scripts/verify_ui_data.py` |
| `prepare_design_assets.py` | Chuẩn bị ảnh thiết kế cho frontend | `python scripts/prepare_design_assets.py` |

## Không còn dùng được

| Script | Vì sao |
|---|---|
| `predict_dish_from_model.py` | Demo model phân loại món đã GỠ (rò rỉ nhãn); cần `scripts/train_dish_classifier.py` — file không tồn tại. Đã chuyển sang `archive/scripts/` (rà soát 2026-11-08) |
| `legacy/` | Công cụ chạy một lần hoặc bản cũ, giữ để tham khảo: `check_mood_improvement.py`, `convert_seed_to_intro.py`, `extract_docs.py` (docx → `docs/extracted/`), `merge_csv_direct.py`, `merge_csv_direct_v2.py` |

`download_model.py` (tải model đã gỡ) đã chuyển sang `archive/model-download/` ngày 2026-10-06.

## Chụp màn hình + đo TRÀN NGANG bằng trình duyệt thật

```
python scripts/chup_man_hinh.py http://localhost:5173/
python scripts/chup_man_hinh.py http://localhost:5173/recommend --rong 420 --mobile
```

Mở app trước bằng `python scripts/run_dev.py`. Script in ra `scrollWidth` kèm đường dẫn
ảnh: **ảnh để nhìn, số để kết luận**.

⚠️ **Đừng dùng `msedge --headless --screenshot --window-size=...`.** Nó cho ảnh TRÔNG NHƯ
tràn ngang (chữ bị cắt mép phải) vì không đặt viewport bố cục như điện thoại thật — đã
suýt khiến có người đi sửa một lỗi không tồn tại (2026-09-23). Script này đặt viewport qua
DevTools Protocol nên số đo tin được.

Không cần cài thêm gói nào: WebSocket tự viết bằng thư viện chuẩn của Python.

Trang cần đăng nhập (thêm 2026-10-02):

```
python scripts/chup_man_hinh.py http://localhost:5173/account --token <token-nguoi-dung>
python scripts/chup_man_hinh.py http://localhost:5173/quan-tri --admin-token <token-quan-tri>
python scripts/chup_man_hinh.py http://localhost:5173/login --dang-xuat
```

`--token` ghi vào `localStorage` (app người dùng), `--admin-token` vào `sessionStorage`
(app quản trị). Hồ sơ trình duyệt được dùng lại giữa các lần chạy, nên khi chụp trang
`/login`, `/register` phải thêm `--dang-xuat` để xoá token còn sót từ lần trước.

## Dữ liệu người dùng GIẢ LẬP + đánh giá xếp hạng offline

Sinh người dùng demo, cho họ "dùng app" bằng cách gọi API thật (qua FastAPI TestClient),
rồi đo NDCG / Precision / MRR / độ phủ của thứ tự MoodBite so với 2 baseline.

⚠️ Đây là DỮ LIỆU GIẢ LẬP. Kết quả KHÔNG phải hành vi người dùng thật và không được ghi vào
báo cáo như kết quả thực nghiệm.

Mọi thứ ghi vào `data_pipeline/data_synthetic/` (đã .gitignore). Dữ liệu thật trong
`data_pipeline/data_cleaned/` không bao giờ bị ghi: script tự từ chối thư mục đó và băm
sha256 file thật trước/sau khi chạy. Bản ghi giả lập có dấu nhận diện: session `synthetic-`,
tên đăng nhập `demo_`, email `@example.invalid`. Mật khẩu mọi tài khoản demo: `demo-moodbite-2026`.

### 1. Sinh dữ liệu (PowerShell 5.1, mỗi lệnh một dòng)

```
python scripts/gia_lap_nguoi_dung.py --users 60 --days 14 --reset
```

Tham số: `--users` (mặc định 200) · `--days` (30) · `--seed` (42) ·
`--out-dir` (data_pipeline/data_synthetic) · `--reset` (xoá dữ liệu giả lập cũ trước).
Đo trên máy chủ dự án: 60 người x 14 ngày mất khoảng 6 phút, phần lớn là `POST /search`
(~2 giây/lượt).

File sinh ra:

| File | Nội dung |
|---|---|
| `personas.json` | chân dung từng người demo + tâm phường lấy từ dataset |
| `moodbite_users.db` | tài khoản demo + quán/món đã lưu |
| `interactions.jsonl` | tương tác ghi qua `POST /api/v1/interactions` |
| `sessions.jsonl` | từng phiên: 50 quán ứng viên + utility "sự thật mặt đất" |

Lưu ý: "ngày" chỉ là mốc logic trong `sessions.jsonl`; server đóng dấu giờ thật lúc ghi.

### 2. Đánh giá xếp hạng

```
python scripts/danh_gia_xep_hang.py
```

In bảng và ghi `data_pipeline/data_synthetic/eval_results.json`.

### 3. Chạy app trên dữ liệu giả lập (banner cảnh báo ở trang quản trị)

```
$env:MOODBITE_SYNTHETIC_DATA="1"
$env:MOODBITE_INTERACTIONS="data_pipeline/data_synthetic/interactions.jsonl"
$env:MOODBITE_USERS_DB="data_pipeline/data_synthetic/moodbite_users.db"
python scripts/run_dev.py
```

Kiểm tra: `GET /api/v1/health` và `GET /api/v1/admin/system` trả `synthetic_data: true`.
Quay về dữ liệu thật: đóng cửa sổ PowerShell đó (biến `$env:` chỉ sống trong cửa sổ hiện
tại), hoặc chạy:

```
Remove-Item Env:MOODBITE_SYNTHETIC_DATA
Remove-Item Env:MOODBITE_INTERACTIONS
Remove-Item Env:MOODBITE_USERS_DB
```

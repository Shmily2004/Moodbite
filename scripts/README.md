Legacy and utility scripts

Files moved into `scripts/legacy/` are one-off utilities or older helpers kept for reference.

Contents:
- `check_mood_improvement.py` - quick CSV checks to profile mood coverage
- `merge_csv_direct.py` - specific CSV merge helper (kept for compatibility)
- `merge_csv_direct_v2.py` - generalized CSV merge tool that reads all JSONs
- `extract_docs.py` - docx -> markdown extractor used to generate docs/extracted/

Guidelines:
- Prefer scripts under `scripts/` for non-production utilities. Production code belongs in `src/`.
- When consolidating, keep the most general, well-documented script and archive the rest.

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
python scripts/run_dev.py --admin
```

Kiểm tra: `GET /api/v1/health` và `GET /api/v1/admin/system` trả `synthetic_data: true`.
Quay về dữ liệu thật: đóng cửa sổ PowerShell đó (biến `$env:` chỉ sống trong cửa sổ hiện
tại), hoặc chạy:

```
Remove-Item Env:MOODBITE_SYNTHETIC_DATA
Remove-Item Env:MOODBITE_INTERACTIONS
Remove-Item Env:MOODBITE_USERS_DB
```

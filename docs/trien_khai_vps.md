# Triển khai MoodBite lên VPS (Ubuntu + Caddy + systemd)

Hướng dẫn từng bước đưa MoodBite lên một VPS Linux có domain riêng, chạy 24/7.
Soạn 2026-11-08 cho gói **Vietnix VPS SSD Linux 1** (2 vCPU, 2 GB RAM, Ubuntu 24.04 LTS).

> **Đọc trước:** phần B (bước 3 trở đi) chạy TRÊN SERVER nên chưa được chạy thử khi soạn tài
> liệu này. Chỉ phần build frontend (bước 2) đã được chạy thật. Mục 12 liệt kê rõ cái gì đã
> kiểm chứng, cái gì chưa. Gặp lệnh nào báo lỗi thì dừng lại và hỏi, đừng chạy tiếp.

Thay hai giá trị này trong MỌI lệnh bên dưới:

| Ký hiệu | Là gì |
|---|---|
| `TENMIEN.CUA.BAN` | domain của bạn, ví dụ `moodbite.id.vn` |
| `IP_VPS` | địa chỉ IP trong trang dịch vụ Vietnix |

---

## 0. Kiến trúc triển khai

```
Trình duyệt ──HTTPS──> Caddy (cổng 80/443, tự lấy chứng chỉ HTTPS)
                         ├─ /api/*  và /health ──> uvicorn 127.0.0.1:8001 (backend FastAPI)
                         └─ mọi đường dẫn khác ──> file frontend đã build (/var/www/moodbite)
```

Vì sao có Caddy: backend **không** phục vụ file frontend (đã kiểm tra: `src/` không có
`StaticFiles`). Frontend dùng `createBrowserRouter`, nên mở thẳng `/quan-tri` hay `/login`
mà server không trả `index.html` thì ra 404. Caddy lo cả hai việc, kèm HTTPS miễn phí.

Frontend và API cùng một domain nên trình duyệt coi là cùng nguồn, không bị chặn CORS.
Vẫn đặt `MOODBITE_CORS_ORIGINS` đúng domain theo `docs/ra_soat_bao_mat.md` mục 7.

---

# PHẦN A — Làm trên máy của bạn (Windows PowerShell)

## 1. Trỏ domain về VPS

1. Vào trang quản lý DNS của **nơi đang giữ nameserver** của domain (với `.id.vn` mua ở
   TENTEN thì thường là chính TENTEN). Sửa bản ghi ở nơi khác sẽ không có tác dụng.
2. Thêm bản ghi: loại `A`, tên `@` (hoặc để trống), giá trị `IP_VPS`.
3. Đợi vài phút đến vài giờ, rồi kiểm tra:

```
nslookup TENMIEN.CUA.BAN
```

Kết quả phải hiện đúng `IP_VPS`. Chưa đúng thì **đừng** làm bước Caddy (bước 8): Caddy
không xin được chứng chỉ HTTPS nếu domain chưa trỏ về server.

## 2. Build frontend

```
cd frontend
$env:VITE_API_BASE = "/api/v1"
npm run build
```

- `/api/v1` (đường dẫn tương đối) nghĩa là frontend gọi API cùng domain nó đang chạy, nên
  build MỘT lần dùng được cho mọi domain. Giá trị bị **nhúng cứng** vào file build; đổi thì
  phải build lại.
- Kết quả nằm ở `frontend\apps\client\dist\` (đo thật: 28 file, ~6,7 MB, build ~10 giây).

Kiểm tra giá trị đã nhúng đúng (lệnh KHÔNG được in gì ra là đúng):

```
Select-String -Path apps\client\dist\assets\*.js -SimpleMatch "D:/Git"
```

> ⚠️ **Build bằng PowerShell, KHÔNG bằng Git Bash.** Git Bash tự đổi `/api/v1` thành đường
> dẫn Windows kiểu `D:/Git/api/v1` trước khi đưa cho npm — lỗi này đã gặp thật khi soạn tài
> liệu. Frontend build ra vẫn "thành công" nhưng mọi lệnh gọi API đều sai địa chỉ.

> ⚠️ Đừng để một cửa sổ terminal nào đang đứng trong thư mục `dist` khi build: Windows
> không cho Vite xoá thư mục đó (`EPERM`).

---

# PHẦN B — Làm trên VPS

Đăng nhập (mật khẩu ở email/portal Vietnix, **đừng gửi cho ai**):

```
ssh root@IP_VPS
```

Các lệnh dưới đây là **bash trên Ubuntu**, không phải PowerShell.

## 3. Cập nhật, tường lửa, swap

```bash
apt update && apt upgrade -y
```

Mở cổng TRƯỚC khi bật tường lửa — bật mà quên cổng SSH là tự khoá mình ngoài server:

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

Swap 2 GB (đệm an toàn: backend đo được ~470 MB, đỉnh ~520 MB trên máy Windows của bạn; số
trên Linux có thể khác, kiểm bằng `free -h`). Báo lỗi thì bỏ qua, không bắt buộc:

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

Đổi mật khẩu root (mật khẩu ban đầu đã đi qua email):

```bash
passwd
```

## 4. Cài gói, tạo user chạy ứng dụng, lấy mã nguồn

```bash
apt install -y python3-venv python3-pip git caddy
```

Nếu báo không tìm thấy gói `caddy`, cài theo hướng dẫn chính thức:
https://caddyserver.com/docs/install#debian-ubuntu-raspbian

Chạy ứng dụng bằng user riêng, không dùng root (lỡ có lỗ hổng thì kẻ tấn công không có
quyền root):

```bash
adduser --disabled-password --gecos "" moodbite
mkdir /opt/moodbite
chown moodbite:moodbite /opt/moodbite
sudo -u moodbite git clone https://github.com/Shmily2004/Moodbite.git /opt/moodbite
```

Kho đang trỏ tới `github.com/Shmily2004/Moodbite`. Nếu kho là **private**, lệnh clone sẽ đòi
đăng nhập: cần tạo token hoặc deploy key trên GitHub (chưa kiểm tra kho là public hay
private).

## 5. Python và dữ liệu

```bash
cd /opt/moodbite
sudo -u moodbite python3 -m venv .venv
sudo -u moodbite .venv/bin/pip install -r requirements.txt
```

Bước pip mất vài phút (scikit-learn, pandas, numpy).

Dữ liệu: `dataset_moodbite_features.csv`, `restaurant_details.json` và các file món đã nằm
trong git. Hai thứ bị `.gitignore` nên **phải dựng trên server**:

```bash
sudo -u moodbite .venv/bin/python scripts/build_dish_catalog.py
sudo -u moodbite .venv/bin/python scripts/build_sqlite.py
```

- `build_dish_catalog.py` (không kèm `--enrich`) không gọi mạng. Máy bạn ra **298 món có
  quán**; server phải ra con số tương tự, lệch nhiều là có gì đó sai.
- `build_sqlite.py` dựng `moodbite.db` (dữ liệu dẫn xuất, dựng lại được bất cứ lúc nào).
- `review_summaries.json` cũng không có ở máy bạn mà app vẫn chạy, nên không cần dựng.

## 6. Cấu hình bí mật (`.env.local`)

Tạo file với phần không bí mật:

```bash
cd /opt/moodbite
cat > .env.local <<'EOF'
MOODBITE_STORAGE=sqlite
MOODBITE_CORS_ORIGINS=https://TENMIEN.CUA.BAN
MOODBITE_APP_URL=https://TENMIEN.CUA.BAN
EOF
```

Sinh ba secret và **ghi thẳng vào file** (không hiện ra màn hình, nên không thể dán nhầm
câu lệnh thay vì kết quả — lỗi đã từng xảy ra thật, xem `.env.example`):

```bash
echo "MOODBITE_AUTH_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" >> .env.local
echo "MOODBITE_RESET_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" >> .env.local
echo "MOODBITE_EMAIL_VERIFY_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" >> .env.local
chown moodbite:moodbite .env.local
chmod 600 .env.local
```

Tạo tài khoản quản trị. Script này hỏi tên và mật khẩu (tối thiểu 12 ký tự) nên phải chạy
trong cửa sổ SSH thật, và nó tự thêm `MOODBITE_ADMIN_SECRET` vào `.env.local`:

```bash
sudo -u moodbite .venv/bin/python scripts/make_admin_user.py
```

Tính năng quên mật khẩu qua email cần thêm nhóm `MOODBITE_SMTP_*` (xem `.env.example`).
Thiếu thì tính năng đó trả 503, phần còn lại vẫn chạy.

## 7. Chạy backend bằng systemd

```bash
cat > /etc/systemd/system/moodbite.service <<'EOF'
[Unit]
Description=MoodBite API (FastAPI)
After=network.target

[Service]
User=moodbite
WorkingDirectory=/opt/moodbite
ExecStart=/opt/moodbite/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8001 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now moodbite
```

Hai chi tiết KHÔNG được bỏ:

- `--proxy-headers --forwarded-allow-ips=127.0.0.1`: sau Caddy, backend chỉ thấy IP của
  Caddy. Thiếu cờ này thì bộ giới hạn tần suất theo IP (`dependencies.py`) coi MỌI người
  dùng là một người: cả hệ thống chỉ được 30 lượt tìm kiếm mỗi phút.
- **Một worker duy nhất** (đừng thêm `--workers`): chỉ mục tìm kiếm và bộ đếm giới hạn đều
  nằm trong RAM mỗi tiến trình, thêm worker là nhân đôi RAM và chia nhỏ bộ đếm.

Backend mất khoảng 15 giây để dựng chỉ mục (số đo trên máy bạn). Sau đó kiểm tra:

```bash
systemctl status moodbite --no-pager
curl -s http://127.0.0.1:8001/health
```

`/health` phải báo các nguồn dữ liệu sẵn sàng. Lỗi thì xem log: `journalctl -u moodbite -n 80 --no-pager`.

## 8. Đưa frontend lên và bật Caddy

Tạo thư mục (trên VPS):

```bash
mkdir -p /var/www/moodbite
```

Dùng Xftp (hoặc `scp`) chép **NỘI DUNG** của `frontend\apps\client\dist\` — tức `index.html`
và thư mục `assets`, `anh`, ... — vào `/var/www/moodbite/`. Chép nhầm cả thư mục `dist`
vào trong thì đường dẫn sẽ thành `/var/www/moodbite/dist/index.html` và web trắng.

Hoặc dùng `scp` từ PowerShell trên máy bạn (Windows 10/11 có sẵn). Chép cả thư mục `dist`
vào chỗ tạm trước, rồi trên VPS mới copy NỘI DUNG của nó (dấu `/.` ở cuối là chủ ý):

```
scp -r frontend\apps\client\dist root@IP_VPS:/tmp/moodbite_dist
```

```bash
cp -r /tmp/moodbite_dist/. /var/www/moodbite/
```

Cấu hình Caddy (trên VPS):

```bash
cat > /etc/caddy/Caddyfile <<'EOF'
TENMIEN.CUA.BAN {
	encode zstd gzip

	@api path /api/* /health
	handle @api {
		reverse_proxy 127.0.0.1:8001
	}

	# File build của Vite có tên kèm mã băm nên cache được vô thời hạn.
	header /assets/* Cache-Control "public, max-age=31536000, immutable"

	handle {
		root * /var/www/moodbite
		# createBrowserRouter: mọi đường dẫn không phải file thật phải trả index.html.
		try_files {path} /index.html
		file_server
	}
}
EOF
systemctl reload caddy
```

Caddy tự xin chứng chỉ HTTPS lần đầu (cần bước 1 xong và cổng 80/443 mở). Xem tiến độ:
`journalctl -u caddy -n 50 --no-pager`.

## 9. Kiểm tra từ đầu đến cuối

Từ máy bạn:

```
curl.exe -s https://TENMIEN.CUA.BAN/api/v1/health
```

Rồi mở `https://TENMIEN.CUA.BAN` bằng trình duyệt và thử: tìm món, mở một quán, đăng ký tài
khoản, đăng nhập admin ở `/login` (sẽ được đưa vào `/quan-tri`), và **tải lại trang (F5)
khi đang ở `/quan-tri`** để chắc phần try_files hoạt động.

Chạy bộ kiểm tra bảo mật theo `docs/ra_soat_bao_mat.md` mục 7 (trên VPS):

```bash
cd /opt/moodbite
sudo -u moodbite .venv/bin/python -m pytest tests/test_bao_mat.py -q
sudo -u moodbite .venv/bin/python scripts/check_permissions.py
```

---

# PHẦN C — Sau khi chạy được

## 10. Sao lưu và cập nhật

**`moodbite_users.db` (tài khoản người dùng) là dữ liệu gốc, mất là mất hẳn.** Sao lưu bằng
cách dùng chính cơ chế backup của SQLite (không chép file đang ghi dở), trên VPS:

```bash
cd /opt/moodbite
sudo -u moodbite .venv/bin/python -c "import sqlite3; s=sqlite3.connect('data_pipeline/data_cleaned/moodbite_users.db'); d=sqlite3.connect('/tmp/users_backup.db'); s.backup(d); d.close(); s.close()"
```

Rồi kéo về máy bạn (PowerShell):

```
scp root@IP_VPS:/tmp/users_backup.db .\users_backup.db
```

Cập nhật code sau này (trên VPS):

```bash
cd /opt/moodbite
sudo -u moodbite git pull
sudo -u moodbite .venv/bin/pip install -r requirements.txt
systemctl restart moodbite
```

Đổi code frontend thì build lại ở bước 2 và chép lại `dist`. Đổi dữ liệu quán thì chạy lại
`build_sqlite.py` — **thêm `--keep-hidden`** nếu không muốn mất các quán admin đã ẩn.

## 11. Lỗi thường gặp

| Triệu chứng | Nguyên nhân hay gặp |
|---|---|
| Trình duyệt báo không an toàn / không vào được HTTPS | Domain chưa trỏ về `IP_VPS` (bước 1) hoặc cổng 80/443 chưa mở; xem `journalctl -u caddy` |
| Trang trắng | Chép nhầm cả thư mục `dist` thay vì nội dung của nó (bước 8) |
| "Không kết nối được tới server" | Backend chưa dựng xong (~15 giây sau khi khởi động) hoặc `systemctl status moodbite` đang lỗi |
| Gọi API ra địa chỉ lạ `D:/Git/api/v1` | Build frontend bằng Git Bash (bước 2); build lại bằng PowerShell |
| F5 ở `/quan-tri` ra 404 | Thiếu dòng `try_files` trong Caddyfile |
| 503 `DATA_NOT_READY` | Chưa chạy `build_dish_catalog.py` / `build_sqlite.py` (bước 5) |
| Admin đăng nhập 503 | Thiếu `MOODBITE_ADMIN_SECRET` hoặc `MOODBITE_STORAGE=sqlite` trong `.env.local` |
| Người dùng cùng bị "quá nhiều lượt tìm kiếm" | Thiếu `--proxy-headers` ở bước 7 |
| Quên mật khẩu không gửi được thư | Chưa khai báo nhóm `MOODBITE_SMTP_*` |

## 12. Đã kiểm chứng và CHƯA kiểm chứng

**Đã chạy thật (2026-11-08, máy Windows của chủ dự án):**
- Build frontend bằng PowerShell với `VITE_API_BASE=/api/v1` thành công (~10 giây, 28 file,
  ~6,7 MB); giá trị tương đối nằm đúng trong file build, không có `D:/Git`.
- Cùng lệnh đó trên Git Bash cho ra `D:/Git/api/v1` (lỗi, đã ghi ở bước 2).
- Client API ghép địa chỉ bằng `fetch(`${baseUrl}${path}`)` (`packages/api-client/src/http.ts`),
  nên đường dẫn tương đối dùng được.
- Backend không phục vụ frontend (không có `StaticFiles` trong `src/`).

**CHƯA chạy thử (không có quyền vào server khi soạn):**
- Toàn bộ lệnh ở phần B trên Ubuntu 24.04 thật.
- Backend trên **Python 3.12** (mặc định của Ubuntu 24.04). CI chỉ chạy 3.11 và 3.14; hãy
  chạy `pytest` trên server để biết.
- RAM thực tế trên Linux (số 470 MB là đo trên Windows, Python 3.14).
- Gói `caddy` có trong kho `apt` của Ubuntu hay không.
- Cổng 80/443 có bị tường lửa phía Vietnix chặn mặc định không.
- Kho GitHub là public hay private.

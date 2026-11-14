# Cập nhật môi trường production (VPS)

Mỗi lần dự án có bản mới, đưa nó lên VPS bằng MỘT lệnh. Tài liệu này là bản "để đó dùng
dần": đọc mục 1 một lần, sau đó chỉ cần mục 2 và mục 3.

Cách triển khai lần đầu nằm ở `docs/trien_khai_vps.md`. Tài liệu này chỉ lo việc **cập
nhật** sau khi web đã chạy.

> **Đọc trước:** script `scripts/deploy_vps.py` đã được kiểm tra phần chạy trên máy bạn
> (test, `--dry-run`, kiểm tra bản build, chuỗi lệnh đi qua Windows nguyên vẹn). Phần ssh và
> scp thật tới VPS **chưa được chạy thử** khi soạn (mục 8). Lần đầu hãy dùng `status` và
> `--dry-run` trước.

---

## 0. Một dòng hiểu hết

```
máy bạn  ──git push──>  GitHub  ──git pull (script làm)──>  VPS
```

Bạn **không sửa code trực tiếp trên VPS**. Sửa tay trên VPS làm `git pull` báo xung đột. VPS
chỉ lấy những gì đã nằm trên nhánh `main` của GitHub.

---

## 1. Thiết lập MỘT LẦN

### 1.1. Khai báo địa chỉ VPS

Script cố ý không có địa chỉ mặc định (lệnh nào cũng chạm vào máy thật). Trong PowerShell:

```
[Environment]::SetEnvironmentVariable("MOODBITE_DEPLOY_HOST", "root@luunguyet.id.vn", "User")
```

Rồi **đóng và mở lại** PowerShell (cả cửa sổ terminal của PyCharm, nếu bạn dùng nó). Không
muốn đặt cố định thì mỗi lần thêm `--host root@luunguyet.id.vn` vào lệnh.

### 1.2. Khoá SSH để khỏi gõ mật khẩu (nên làm)

Mỗi lệnh `ssh` hoặc `scp` đều hỏi mật khẩu. Một lần `all` gọi khoảng **6 lần**, nên rất phiền.
Khoá SSH bỏ hết các lần hỏi đó và an toàn hơn mật khẩu root.

```
ssh-keygen -t ed25519
```

Cứ bấm Enter cho mọi câu hỏi (để trống mật khẩu khoá thì tiện nhất, đổi lại ai chiếm được máy
Windows của bạn là vào được VPS). Rồi chép khoá công khai lên VPS (sẽ hỏi mật khẩu lần cuối):

```
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@luunguyet.id.vn "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

Kiểm tra: lệnh này phải chạy **không hỏi mật khẩu** và in ra `ok`:

```
ssh root@luunguyet.id.vn echo ok
```

> Phần khoá SSH chưa được chạy thử trên máy bạn. Chỉ **thêm** khoá, không tắt đăng nhập bằng
> mật khẩu. Tắt nó là việc khác, cần cẩn thận, và chưa cần làm.

### 1.3. Thử kết nối

Lệnh dưới cần `python` chạy được. Nếu PowerShell báo `Python was not found`, bật `.venv` theo
**mục 2.0** trước, rồi quay lại đây.

```
python scripts/deploy_vps.py status
```

Phải thấy `COMMIT=...`, `BACKEND=active`, `CADDY=active` và cuối cùng là `XONG.`. Lệnh này
chỉ đọc, không đổi gì trên VPS.

---

## 2. Mỗi lần cập nhật

Làm từ **thư mục gốc dự án**, bằng PowerShell thường (không cần quyền Administrator).

### 2.0. Bật môi trường Python `.venv` (làm trước, mỗi cửa sổ PowerShell mới một lần)

Mọi lệnh trong tài liệu viết là `python scripts/...`. Nhưng ở PowerShell vừa mở, `python`
trỏ vào **lối tắt Microsoft Store** (`...\AppData\Local\Microsoft\WindowsApps\python.exe`),
không phải Python thật, nên lệnh báo `Python was not found`. Python thật và đủ thư viện của dự
án (fastapi, pytest...) nằm trong thư mục `.venv`. Bật nó lên thì `python` sẽ trỏ đúng vào đó.

```
cd "E:\Projects IntelliiJ\Moodbite"
```

```
.\.venv\Scripts\Activate.ps1
```

Thành công khi đầu dòng lệnh hiện `(.venv)`. Kiểm tra lại cho chắc:

```
(Get-Command python).Source
```

Kết quả phải kết thúc bằng `Moodbite\.venv\Scripts\python.exe`. Từ đây mọi lệnh `python
scripts/...` bên dưới chạy bình thường.

Cần biết:
- Bật venv chỉ có hiệu lực **trong cửa sổ đó**. Đóng cửa sổ, hoặc mở cửa sổ PowerShell mới,
  là phải bật lại. Muốn tắt: gõ `deactivate`.
- **Terminal trong PyCharm** thường tự bật `.venv`, nên bạn có thể bỏ qua bước này ở đó (thấy
  `(.venv)` ở đầu dòng là đã bật).
- Không muốn bật venv thì gọi thẳng Python của dự án:
  `.\.venv\Scripts\python.exe scripts\deploy_vps.py status`. Cách này đủ cho
  `deploy_vps.py` (chỉ dùng thư viện chuẩn). Riêng `verify.py` cần thư viện của dự án nên
  phải dùng Python trong `.venv`, bằng một trong hai cách trên.

Nếu `Activate.ps1` báo **`running scripts is disabled on this system`**, PowerShell đang chặn
chạy script (ExecutionPolicy). Mở khoá cho riêng tài khoản của bạn, một lần duy nhất:

```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

`RemoteSigned` cho chạy script viết trên máy mình và vẫn chặn script tải từ mạng chưa ký. Nó
không đụng tới các tài khoản khác. Máy bạn đã ở mức này (đo 2026-11-14) nên thường không gặp
lỗi trên; chỉ chạy lệnh này khi thật sự thấy lỗi.

**Bước 1: trên máy bạn, chắc chắn bản mới ổn rồi đẩy lên GitHub.**

```
python scripts/verify.py
git push
```

(Chạy từng lệnh một. `verify.py` hiện còn vài mục đỏ cũ, xem ghi chú ở `docs/trien_khai_vps.md`.
Phải `git push` thì VPS mới thấy bản mới. Script sẽ cảnh báo nếu bạn quên.)

**Bước 2: chọn lệnh theo thứ bạn đã đổi** (bảng ngay dưới), thêm `--dry-run` nếu muốn xem
trước các lệnh sẽ chạy mà không động tới VPS.

**Bước 3: chạy thật.** Script in kế hoạch, hỏi `Tiep tuc? [y/N]`, bạn gõ `y`.

**Bước 4: nhìn bằng mắt.** Script đã hỏi site thật (trang chủ và `/api/v1/health`), nhưng
vẫn nên mở `https://luunguyet.id.vn` bấm thử vài chỗ.

---

## 3. Đổi gì thì chạy lệnh nào

| Bạn đã đổi | Lệnh | Ghi chú |
|---|---|---|
| Code backend (Python), `requirements.txt` | `python scripts/deploy_vps.py backend` | API gián đoạn ~15–25 giây lúc khởi động lại |
| Code frontend (giao diện) | `python scripts/deploy_vps.py frontend` | Không đụng backend |
| Cả hai | `python scripts/deploy_vps.py all` | |
| File dữ liệu quán/món trong git | `python scripts/deploy_vps.py data` | Dựng lại SQLite + danh mục món, rồi khởi động lại |
| `.env.local` trên VPS | Sửa tay trên VPS, rồi `systemctl restart moodbite` | File này không nằm trong git |
| Chỉ muốn xem tình hình | `python scripts/deploy_vps.py status` | Không đổi gì |
| Chỉ muốn sao lưu tài khoản | `python scripts/deploy_vps.py backup` | Về thư mục `backups/` |
| Bản mới lỗi, muốn quay lại | `python scripts/deploy_vps.py rollback <mã commit>` | Mục 5 |

Tuỳ chọn thêm cho mọi lệnh: `--dry-run` (chỉ in lệnh), `--yes` (không hỏi xác nhận),
`--skip-backup` (bỏ sao lưu tài khoản), `--host root@...` (đè biến môi trường),
`--url https://...` (đè địa chỉ dùng để kiểm tra site).

### Script làm gì ở từng chế độ

- **`backend`**: sao lưu tài khoản về máy → trên VPS: `git checkout main`, `git pull
  --ff-only`, `pip install -r requirements.txt`, khởi động lại backend, **đợi `/health` trả
  lời** (tối đa 90 giây) → hỏi site thật từ bên ngoài.
- **`frontend`**: build giao diện **bằng tiến trình con của Python** với
  `VITE_API_BASE=/api/v1` → **kiểm tra bản build** (chặn nếu địa chỉ API bị đổi thành đường
  dẫn Windows như `D:/Git/api/v1`) → chép lên VPS → hỏi site thật. Không xoá file web cũ
  (người đang mở tab bản cũ vẫn tải được file cũ).
- **`data`**: như `backend`, thêm `build_sqlite.py --keep-hidden` và `build_dish_catalog.py`
  trước khi khởi động lại.
- **`all`**: sao lưu → `backend` → `frontend`.

Script dừng ngay ở bước lỗi và không chạy các bước sau. Ví dụ sao lưu hỏng thì **không** `git
pull`.

---

## 4. Những thứ không bao giờ bị script đụng tới

- `moodbite_users.db` (tài khoản người dùng): không có lệnh nào ghi hay xoá nó. Có test khoá
  điều này (`tests/test_deploy_vps.py`).
- `.env.local` trên VPS: không bị ghi đè (file này nằm ngoài git).
- Tệp `backups/` trên máy bạn chứa **chuỗi băm mật khẩu** của người dùng. Nó nằm trong
  `.gitignore`. Đừng gửi cho ai, đừng đẩy lên GitHub.

`data` dùng `--keep-hidden` để giữ các quán admin đã ẩn, nhưng vẫn ghi đè bảng quán, nên các
chỉnh sửa khác của admin trên dữ liệu quán có thể mất. Chưa kiểm tra chi tiết phần này.

---

## 5. Quay lại phiên bản cũ

1. Xem commit nào đang chạy trên VPS và commit nào là bản tốt gần nhất:

```
python scripts/deploy_vps.py status
```

```
git log --oneline -10
```

2. Đưa VPS về commit đó (ví dụ `207f86a`):

```
python scripts/deploy_vps.py rollback 207f86a
```

3. Muốn quay lại bản mới nhất sau đó:

```
python scripts/deploy_vps.py backend
```

(Nó tự `git checkout main` trước khi `pull`, vì sau rollback VPS đang ở trạng thái "detached
HEAD".)

**Rollback chỉ lùi code backend.** Hai thứ không lùi theo:
- **Giao diện:** `git checkout <commit cũ>` ở máy bạn (nhớ commit hoặc cất thay đổi chưa
  lưu), chạy `python scripts/deploy_vps.py frontend`, rồi `git checkout main`.
- **Dữ liệu** (`moodbite.db`, `dish_catalog.json`): chạy lại `data` sau khi lùi.

Bản sao lưu tài khoản trong `backups/` dùng để khôi phục `moodbite_users.db` nếu bản mới làm
hỏng nó. Việc đó làm tay, cẩn thận, không có lệnh tự động.

---

## 6. Khi lỗi

| Thấy gì | Nguyên nhân thường gặp |
|---|---|
| `Thieu hoac sai dia chi VPS` | Chưa đặt `MOODBITE_DEPLOY_HOST` (mục 1.1) hoặc chưa mở lại PowerShell |
| `Python was not found; run without arguments to install from the Microsoft Store` | Lối tắt Microsoft Store che `python`, hoặc bạn chưa bật venv. Làm mục 2.0: `.\.venv\Scripts\Activate.ps1` (đầu dòng phải có `(.venv)`) |
| `Activate.ps1 cannot be loaded because running scripts is disabled on this system` | ExecutionPolicy đang chặn. Chạy một lần `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` (mục 2.0) |
| `Activate.ps1 is not recognized` / `Cannot find path ...\.venv\Scripts\Activate.ps1` | Đứng sai thư mục, hoặc chưa tạo `.venv`. `cd "E:\Projects IntelliiJ\Moodbite"`; chưa có `.venv` thì làm phần "Cài một lần" trong `README.md` |
| Vừa bật venv xong, mở cửa sổ mới lại báo `Python was not found` | Bật venv chỉ có hiệu lực trong cửa sổ đó. Bật lại ở cửa sổ mới (mục 2.0) |
| `can't open file '...\scripts\deploy_vps.py': No such file` | Bạn đang đứng sai thư mục. `cd "E:\Projects IntelliiJ\Moodbite"` rồi chạy lại |
| `Khong thay lenh 'ssh'` | Windows: Settings > Apps > Optional features > thêm **OpenSSH Client** |
| `Connection timed out` | VPS tắt, hoặc mạng đang chặn cổng 22 |
| `Not possible to fast-forward` | VPS có thay đổi tay hoặc commit lạ. SSH vào, chạy `git status`. Đừng sửa tay trên VPS |
| `HEALTH_FAIL` kèm log | Backend không lên sau 90 giây. Đọc log script in ra, hoặc `journalctl -u moodbite -n 80 --no-pager` trên VPS; hoặc `rollback` |
| `Ban build khong dung` | Địa chỉ API trong bản build sai. Đừng build bằng Git Bash; để script tự build |
| Build báo `EPERM ... dist` | Một cửa sổ terminal đang đứng trong thư mục `dist`. Thoát ra rồi chạy lại |
| `Chua cai thu vien frontend` | Chạy `npm install` trong thư mục `frontend` |
| Site kiểm tra sau cập nhật báo lỗi | Xem `status`; mở site bằng trình duyệt; nếu là bản vừa đẩy thì cân nhắc `rollback` |

---

## 7. Làm tay (khi script hỏng)

Backend, trên VPS:

```bash
cd /opt/moodbite && sudo -u moodbite git pull --ff-only && sudo -u moodbite .venv/bin/pip install -r requirements.txt && systemctl restart moodbite
```

Đợi khoảng 25 giây rồi kiểm tra: `curl -s http://127.0.0.1:8001/health`.

Frontend, trên máy Windows (PowerShell), rồi trên VPS:

```
cd frontend
$env:VITE_API_BASE = "/api/v1"
npm run build
scp -r apps\client\dist root@luunguyet.id.vn:/tmp/moodbite_dist_new
```

```bash
cp -r /tmp/moodbite_dist_new/. /var/www/moodbite/ && rm -rf /tmp/moodbite_dist_new
```

Chi tiết từng lệnh và lý do nằm ở `docs/trien_khai_vps.md`.

---

## 8. Đã kiểm chứng và CHƯA kiểm chứng

**Đã chạy thật (2026-11-10, máy Windows của chủ dự án):**
- 47 test của `tests/test_deploy_vps.py` đạt (6 test cú pháp bash bị bỏ qua trên Windows, chạy
  trên Linux/CI).
- Mọi chuỗi lệnh chạy trên VPS qua `bash -n` (Git Bash): cú pháp hợp lệ.
- Mọi chuỗi lệnh đi qua cơ chế truyền tham số của Windows nguyên vẹn (không có dấu nháy kép).
- Đoạn Python sao lưu SQLite chạy đúng trên một CSDL thử (3 dòng vào, 3 dòng ra).
- Kiểm tra bản build chạy trên bản build thật của bạn: không có vấn đề.
- `python scripts/deploy_vps.py all --dry-run` in đúng chuỗi lệnh, không chạm vào VPS.
- Bật venv (mục 2.0), đo 2026-11-14 trên máy bạn, với ExecutionPolicy `RemoteSigned`: trước khi
  bật `python` trỏ vào lối tắt Microsoft Store; sau `.\.venv\Scripts\Activate.ps1` nó trỏ vào
  `.venv\Scripts\python.exe` (Python 3.14.7, import được fastapi) và `python
  scripts/deploy_vps.py --help` chạy được; `deactivate` trả về như cũ. Chưa thử trường hợp
  ExecutionPolicy là `Restricted` (máy bạn không ở mức đó), nên lệnh `Set-ExecutionPolicy` ở
  mục 2.0 là theo cách làm chuẩn của PowerShell, chưa chạy thử ở đây.

**CHƯA chạy thử:**
- ssh, scp thật tới VPS của bạn: toàn bộ chuỗi sao lưu, `git pull`, khởi động lại, chép
  frontend. Lần đầu hãy chạy `status`, rồi một lệnh thật nhỏ như `frontend`, khi có mặt để xem.
- Cách ssh.exe của Windows xử lý chuỗi lệnh dài có `$(...)`: đã kiểm tra tới ranh giới tiến
  trình, chưa kiểm tra ở phía ssh.
- Khoá SSH ở mục 1.2.
- Quay lại phiên bản cũ (`rollback`) trên VPS thật.

**Chưa có (cố ý, vì phức tạp hơn mức cần cho đồ án):** tự động triển khai khi push (CI/CD).
Hiện cập nhật là việc bạn chủ động chạy lệnh.

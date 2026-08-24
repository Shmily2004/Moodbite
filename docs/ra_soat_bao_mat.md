# Rà soát bảo mật — 2026-08-24

Rà toàn bộ `src/`, `scripts/`, cấu hình và `frontend/`. Ghi lại **cái đã sửa** và **cái
cố ý chưa sửa**, kèm lý do — để lần sau không phải rà lại từ đầu, và để trả lời được khi
hội đồng hỏi.

Ba lỗi tìm được đều thuộc loại **hỏng mà không ai thấy gì khác lạ**.

---

## 1. ĐÃ SỬA — `MOODBITE_RESET_SECRET` bị dán nhầm bằng câu lệnh sinh ra nó

**Mức độ: NGHIÊM TRỌNG.** Đây là lỗi nặng nhất trong cả lượt rà.

Trong `.env.local` có đúng dòng này:

```
MOODBITE_RESET_SECRET=import secrets; print(secrets.token_hex(32))
```

Người cấu hình đã dán **câu lệnh** thay vì **kết quả chạy câu lệnh**. Hệ thống không hề
báo lỗi: chuỗi đó khác rỗng nên `ensure_configured()` coi là đã cấu hình, và mọi thứ chạy
bình thường.

**Vì sao nguy hiểm.** Chuỗi `import secrets; print(secrets.token_hex(32))` không phải bí
mật — nó nằm nguyên văn trong `.env.example`, trong docstring của `password_reset.py`, và
trong chính câu báo lỗi mà API trả về khi chưa cấu hình. Ai đọc mã nguồn cũng biết. Mà
token đặt lại mật khẩu chỉ được bảo vệ bằng chữ ký HMAC dùng đúng chuỗi đó, nên **bất kỳ
ai cũng tự ký được một token đặt lại mật khẩu cho bất kỳ tài khoản nào** rồi chiếm tài
khoản mà không cần đụng tới hộp thư của nạn nhân.

**Đã làm:** sinh chuỗi ngẫu nhiên 64 ký tự hex, ghi đè vào `.env.local`, và thêm
`MOODBITE_EMAIL_VERIFY_SECRET` cũng bằng chuỗi ngẫu nhiên riêng.

**Hệ quả:** mọi đường dẫn đặt lại mật khẩu phát trước 2026-08-24 nay đã chết. Đúng như
mong muốn.

**Điểm rút ra cho lần sau:** hệ thống KHÔNG có cách nào phân biệt "secret thật" với "một
chuỗi bất kỳ". Nếu muốn chắc chắn thì phải thêm phép kiểm lúc khởi động, ví dụ cảnh báo
khi secret chứa khoảng trắng hoặc chứa chữ `print(`. **Chưa làm** — xem mục 6.

---

## 2. ĐÃ SỬA — `/admin/login` không có giới hạn tần suất

**Mức độ: CAO.**

`/auth/login` của người dùng thường có bộ đếm 5 lần/5 phút. `/admin/login` thì **không có
gì cả**. Đây là bất đối xứng đúng chiều nguy hiểm nhất: dự án chỉ có **một** tài khoản
quản trị, và nó sửa/ẩn được mọi quán.

Còn một hệ quả thứ hai không liên quan tới đoán mật khẩu: mỗi lần thử đều chạy PBKDF2
600.000 vòng, tốn khoảng **0,4 giây CPU**. Endpoint công khai + không giới hạn = ai cũng
làm nghẽn máy chủ được, không cần đoán trúng gì.

**Đã làm:** thêm `ADMIN_LOGIN_MAX_ATTEMPTS = 5` / `ADMIN_LOGIN_WINDOW_SECONDS = 900`,
đếm **trước** khi kiểm mật khẩu, và xoá bộ đếm khi đăng nhập đúng.

**Đo lại sau khi sửa:** 8 lần đoán sai liên tiếp → `[401, 401, 401, 401, 401, 429, 429, 429]`.

---

## 3. ĐÃ SỬA — CORS mặc định `*` kèm `allow_credentials=True`

**Mức độ: TRUNG BÌNH (nói cho đúng: chưa khai thác được ngay).**

`MOODBITE_CORS_ORIGINS` mặc định là `"*"`, trong khi `main.py` bật
`allow_credentials=True`. Đo thật trước khi sửa: một `Origin` hoàn toàn lạ vẫn nhận về

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Credentials: true
```

Hai vấn đề:

1. **Sai chuẩn.** Trình duyệt từ chối gửi credentials khi `ACAO` là `*`, nên
   `allow_credentials=True` đang **vô tác dụng** — và sẽ hỏng âm thầm vào đúng ngày ai đó
   chuyển token từ `localStorage` sang cookie.
2. **Mở API cho mọi trang web** gọi bằng JS.

**Phải nói cho công bằng:** rủi ro khai thác *ngay lúc này* là **thấp**, vì token đăng
nhập nằm trong `localStorage` — trang web khác không đọc được, nên không có gì để đánh
cắp qua đường này. Nhưng "mở hết rồi trông chờ vào một lớp bảo vệ khác" không phải thứ
nên để trong một đồ án đem đi bảo vệ.

**Đã làm:** mặc định đổi thành đúng bốn địa chỉ phát triển của dự án
(`localhost`/`127.0.0.1` cổng 5173 và 5174). Deploy thật vẫn khai được tên miền bằng
`MOODBITE_CORS_ORIGINS`, và vẫn để `*` được — nhưng nay phải là lựa chọn **có ý thức**.

---

## 4. Đã kiểm và KHÔNG có vấn đề

| Hạng mục | Cách kiểm | Kết quả |
|---|---|---|
| SQL injection | Tìm mọi `execute(` nối chuỗi/f-string trong `src/` | **Không có** — toàn bộ dùng tham số `?` |
| Bí mật viết cứng trong mã | Tìm `secret/password/token = "<chuỗi dài>"` | **Không có** |
| `.env.local` lọt vào git | `git ls-files` + soát lịch sử | **Không** — chỉ có `.env.example` |
| Lộ `password_hash` qua API | Test tự động | **Không** — có `tests/test_bao_mat.py` canh, kể cả sau khi `/login` đổi sang `to_self()` |
| Phân quyền trang quản trị | Đọc `routers/admin.py` | `Depends(require_admin)` gắn ở **cấp router**, chỉ `/login` là công khai — đúng thiết kế |
| Fail-closed khi thiếu cấu hình | Đọc `admin_auth`, `user_auth`, `password_reset` | Thiếu secret → **tắt hẳn** + 503, không bao giờ mặc định "cho qua" |
| Hướng phụ thuộc | `scripts/check_architecture.py` | Sạch |
| `print()` trong mã chạy thật | grep `src/` | Không có |
| Singleton cấp module | grep `src/` | Chỉ có `APIRouter` — không giữ dữ liệu, vô hại |

---

## 5. Nhận xét về những chỗ `except Exception`

Có 15 chỗ. **Không cái nào là nuốt lỗi ẩu**, và phần lớn có comment giải thích sẵn:

- `search_restaurants`, `suggest_dishes`, `find_restaurants_for_dish`,
  `tfidf_semantic_search`, `ml_rule_predictor`, `open_meteo_context_provider` — đây là
  **suy biến an toàn có chủ đích**, đúng yêu cầu của `CLAUDE.md` mục 4c: thiếu sklearn
  hay hỏng API thời tiết thì lui về khớp từ khoá, KHÔNG được làm hỏng lượt tìm kiếm.
- `dependencies.py:576` — mọi lỗi xác thực quy về "coi như khách", có `# noqa` kèm lý do.
- `manage_account.py:249` — `try_send` cho thư xác minh, có docstring giải thích tại sao
  lỗi SMTP không được làm hỏng việc tạo tài khoản.

Lỗi lập trình thật vẫn nổi lên 500 qua `error_handlers.py` — đúng như `CLAUDE.md` mục 5
yêu cầu, không có chuyện bọc `except Exception` quanh route rồi trả 400.

---

## 6. CỐ Ý CHƯA SỬA — và vì sao

| Việc | Vì sao chưa làm |
|---|---|
| **Thu hồi token đăng nhập** | Cần thêm cột `token_version` vào bảng `users` = ĐỔI LƯỢC ĐỒ, phải chốt trước (`docs/API_DECISIONS_PENDING.md`). Hiện thiệt hại bị chặn trên bởi hạn 24 giờ |
| **Cảnh báo khi secret trông như chuỗi mẫu** | Sẽ chặn được đúng lỗi ở mục 1, nhưng là thêm hành vi mới lúc khởi động — nên hỏi trước |
| **Giới hạn tần suất theo tài khoản, không chỉ theo IP** | Bộ đếm hiện theo IP. Chung NAT thì chặn oan; đổi IP thì lách được. Với quy mô đồ án thì theo IP là đủ |
| **Bộ đếm nằm trong RAM** | Khởi động lại là mất. Muốn bền phải thêm Redis — đúng thứ `CLAUDE.md` cấm (không đề xuất dịch vụ cần thẻ) |
| **`email` không UNIQUE trong CSDL** | Cố ý, đã ghi rõ trong `user_repository.py`: đồ án cần tạo nhiều tài khoản thử bằng một hộp thư |
| **SMTP dùng mật khẩu ứng dụng Gmail** | Không có phương án miễn phí nào khác. Mật khẩu nằm trong `.env.local`, không lọt git |

---

## 7. Việc nên làm khi deploy thật

1. Đặt `MOODBITE_CORS_ORIGINS=https://tenmien.cua.ban` — **đừng để `*`**.
2. Sinh lại toàn bộ secret bằng `python -c "import secrets; print(secrets.token_hex(32))"`
   và **dán KẾT QUẢ, không dán câu lệnh** (xem mục 1).
3. Đổi mật khẩu quản trị, sinh lại `MOODBITE_ADMIN_PASSWORD_HASH` bằng
   `python scripts/make_admin_password.py`.
4. Bật HTTPS. Toàn bộ phân tích ở trên giả định kênh truyền đã được mã hoá.
5. Chạy `python -m pytest tests/test_bao_mat.py` sau mỗi lần đổi cấu hình.

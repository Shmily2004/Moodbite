# Quyết định API đang chờ duyệt

**Cập nhật:** 2026-08-17

File này giữ các **thay đổi API/data model đã bàn nhưng CHƯA được duyệt để code**.

Tách riêng khỏi `UI_REQUIREMENTS.md` có chủ đích, theo đúng ranh giới đã thống nhất:

| File | Trả lời câu hỏi |
|---|---|
| `UI_REQUIREMENTS.md` | Giao diện **phải làm gì** |
| **`API_DECISIONS_PENDING.md`** *(file này)* | Backend **sẽ được phép thêm gì**, khi nào |
| `PROJECT_CHECKLIST.md` | Cái gì **đã chạy thật** |

> ⛔ **Không được code bất kỳ mục nào dưới đây khi chưa có duyệt.**
> Đây đều là thay đổi hợp đồng API hoặc data model.

---

## 1. `GET /api/v1/admin/stats` — phục vụ Dashboard + Chất lượng dữ liệu

**Trạng thái:** đã chốt hình dạng, **chưa code**.

```json
{
  "total_restaurants": 4938,
  "sources": { "openstreetmap": 3528, "google_maps_apify": 1410 },
  "coverage": {
    "coordinates":   1.000,
    "name":          1.000,
    "district":      0.969,
    "opening_hours": 0.326,
    "rating":        0.232,
    "thumbnail":     0.215,
    "price":         0.130
  },
  "clustering": { "clustered": 1197, "total": 4938 },
  "hidden_count": 0,
  "generated_at": "<ISO-8601 do SERVER sinh lúc gọi>"
}
```

**Bằng chứng cho từng con số** — đếm trực tiếp ngày 2026-08-17:

```
4938 dòng CSV = 4938 dòng SQLite
openstreetmap 3528 + google_maps_apify 1410 = 4938 ✓
experience_cluster_id khác NULL = 1197
```

Kiểm lại: `python scripts/data_report.py`

### ⛔ Ba trường BỊ CẤM trong response này

| Trường | Vì sao cấm |
|---|---|
| `users` | Không có hệ thống tài khoản (`rules/api.md`: *"Không áp dụng hệ thống tài khoản cá nhân đăng nhập ở Giai đoạn MVP"*) |
| `reviews_count` | Review nhúng trong dữ liệu quán, không đếm riêng được |
| `match_quality` | Chỉ số này **không tồn tại** |

**Kể cả trả về `0` cũng không được** — trả 0 vẫn khiến người đọc tưởng hệ thống có đo,
chỉ là chưa ai dùng.

---

## 2. `POST /api/v1/admin/restaurants` — thêm quán thủ công

**Trạng thái:** 🔴 **BLOCKING DECISION** — đây là thay đổi data model, chưa được duyệt.

### Vấn đề chặn: quán thêm tay sẽ BỊ XOÁ

`scripts/build_sqlite.py` chạy `DELETE FROM restaurants` rồi ghi lại toàn bộ từ CSV,
hiện chỉ giữ được cột `is_active` qua `--keep-hidden`.

Nghĩa là **CSV vẫn là source of truth**, và quán admin nhập tay sẽ biến mất ở lần chạy
pipeline tiếp theo — mất công nhập 50–100 quán Hoàn Kiếm.

### Bảng đề xuất (CHƯA phải quyết định)

| Câu hỏi | Đề xuất | Vì sao |
|---|---|---|
| Source of truth? | CSV cho quán pipeline · SQLite cho quán thủ công | thêm cột `origin`; `build_sqlite` chỉ xoá dòng `origin='pipeline'` |
| Trường bắt buộc | `name` · `latitude` · `longitude` | thiếu toạ độ thì không xếp hạng và không lên bản đồ được |
| ID sinh thế nào | `manual-<uuid4>` | nhìn là biết không phải placeId của Google |
| `source` | `"admin_manual"` | CLAUDE.md mục 4b: mọi bản ghi phải có nguồn rõ ràng |
| `data_confidence` | `"manual"` | phân biệt với dữ liệu cào |
| `is_active` mặc định | `true` | nhập xong dùng được ngay |
| `rating` / `price` | **bắt buộc `null`** | admin không được tự chấm sao — đó là bịa số liệu |
| `mood_scores` / cụm | `null` | do pipeline tính; Cold Start dùng 0.5 trung lập |

---

## 3. Trường `reason` cho `explicit_negative`

**Trạng thái:** 🔴 **BLOCKING DECISION** — chưa duyệt.

Ý tưởng: khi người dùng bấm "không phù hợp", cho chọn lý do (quá xa / sai món / sai mood /
giá không hợp / khác).

**Hiện KHÔNG gửi được.** `InteractionRequest` chỉ có:

```
session_id · restaurant_id · action_type · search_query_id · dwell_time_ms · rank_position
```

Không có `reason`. Làm giao diện chọn lý do bây giờ thì lý do **rơi vào hư không**.

---

## 4. `GET /api/v1/admin/interactions` — thống kê tương tác

**Trạng thái:** 🔴 chưa duyệt, và **chưa có dữ liệu để hiển thị**.

Hiện chỉ có `POST /interactions`, không có endpoint đọc. Ngoài ra
`data_pipeline/data_cleaned/interactions.jsonl` **chưa tồn tại (0 bản ghi)** — nên kể cả
làm xong endpoint thì trang thống kê vẫn trống.

> ⚠️ Mọi con số kiểu *"1.284 tương tác · 842 xem chi tiết · 217 lưu"* từng xuất hiện trong
> các bản đề xuất đều là **bịa**. Thực tế là 0.

**Thứ tự đúng:** thêm nút phản hồi vào giao diện → có người dùng thật → có dữ liệu →
lúc đó mới làm trang thống kê.

---

## 5. 🔴 TÀI KHOẢN NGƯỜI DÙNG + PHÂN QUYỀN — mở rộng phạm vi

**Quyết định của chủ dự án 2026-08-17:** người dùng và admin **đều phải đăng nhập**, để
có phân quyền rõ ràng và cá nhân hoá.

**Trạng thái:** 🔴 chưa code. Cần chốt hợp đồng trước.

### 5.1. ⚠️ Việc này MÂU THUẪN với tài liệu gốc — phải sửa tài liệu

| Nguồn | Đang ghi |
|---|---|
| `rules/api.md:19` | *"**Không xác thực người dùng (Auth):** Không áp dụng hệ thống tài khoản cá nhân đăng nhập ở Giai đoạn MVP"* |
| `PROJECT_CHECKLIST.md:36` | `Đăng nhập / tài khoản · ⬜ Ngoài phạm vi · SRS mục 8, Won't-have` |

Nếu làm mà **không sửa hai chỗ này**, dự án sẽ có tài liệu nói một đằng, sản phẩm chạy một
nẻo — đúng bệnh mà `CLAUDE.md` mục 0 cảnh báo. Hội đồng đọc SRS thấy "Won't-have" rồi mở
app thấy có đăng nhập sẽ hỏi ngay.

**➜ Phải cập nhật SRS/`rules/api.md` cùng lúc với việc code, không phải sau.**

### 5.2. Hiện trạng: KHÔNG có gì cho người dùng

Đếm trong `src/`: **0** file có `class User`, `user_id`, `role`, hay `UserRepository`.
Tương tác hiện gắn với `session_id` (UUID client tự sinh), không gắn với người nào.

Nghĩa là đây là xây mới hoàn toàn, không phải mở rộng cái có sẵn.

### 5.3. Ba chốt chặn phải quyết TRƯỚC khi code

#### ⛔ A. Không gửi được email

`requirements.txt` không có thư viện email nào, và chủ dự án **không có thẻ thanh toán**
để dùng dịch vụ gửi mail. Hệ quả trực tiếp:

| Tính năng chuẩn | Làm được không |
|---|---|
| Xác thực email khi đăng ký | ❌ không |
| Quên mật khẩu qua email | ❌ không |
| Đăng nhập bằng magic link | ❌ không |

**Phương án thay thế (cần chọn):**
1. Đăng ký bằng **tên đăng nhập + mật khẩu**, không cần email, không xác thực
2. Có nhập email nhưng **không xác thực** (chỉ để hiển thị)
3. Quên mật khẩu → **admin đặt lại thủ công** qua trang quản trị

#### ⛔ B. Bảo mật phải nâng cấp trước, không phải sau

Audit ngày 2026-08-17 tìm thấy 5 lỗ hổng **khi mới chỉ có 1 tài khoản admin**. Mở đăng ký
công khai thì mức độ nghiêm trọng tăng hẳn:

| Lỗ hổng | Hiện tại | Khi có đăng ký công khai |
|---|---|---|
| Không giới hạn đăng nhập sai | Cao | **Nghiêm trọng** — dò mật khẩu hàng loạt |
| Không giới hạn đăng ký | — | **Nghiêm trọng mới** — bot tạo tài khoản vô hạn |
| Không thu hồi token khi đăng xuất | Trung bình | **Cao** — token của người dùng thật |
| CORS `*` + `credentials: true` | Trung bình | **Cao** |
| PBKDF2 600k vòng | ~0.4s, chấp nhận được với 1 tài khoản | **Tốn CPU** khi nhiều người đăng nhập cùng lúc |

**➜ Rate limiting trở thành BẮT BUỘC, không còn là "nên có".**

#### ⛔ C. `build_sqlite.py` sẽ XOÁ SẠCH người dùng

Script đang chạy `DELETE FROM restaurants` rồi ghi lại từ CSV. Nếu bảng `users` nằm cùng
CSDL mà không xử lý, thì **mỗi lần chạy lại pipeline là mất toàn bộ tài khoản**.

Đây đúng vấn đề đã gặp ở mục 2 (`origin` cho quán thêm tay), nhưng hậu quả nặng hơn nhiều.

### 5.4. Phân quyền — hai vai, không cần RBAC đầy đủ

**Quyết định 2026-08-17: KHÁCH PHẢI ĐĂNG NHẬP.** Không có chế độ dùng thử.

| Hành động | Chưa đăng nhập | `user` | `admin` |
|---|---|---|---|
| Tìm quán, xem bản đồ | ❌ **bị chặn** | ✅ | ✅ |
| Xem chi tiết quán | ❌ **bị chặn** | ✅ | ✅ |
| Lưu quán / thích / không thích | ❌ | ✅ | ✅ |
| Xem lịch sử, gợi ý cá nhân hoá | ❌ | ✅ | ✅ |
| Sửa / ẩn quán | ❌ | ❌ | ✅ |
| Xem thống kê, chất lượng dữ liệu | ❌ | ❌ | ✅ |

Chỉ **2 vai** nên dùng cột `role` đơn giản (`"user"` / `"admin"`), **không** cần bảng
permission hay hệ RBAC đầy đủ — thêm vào chỉ tốn công mà không dùng tới.

### 5.5. Hợp đồng API dự kiến *(ĐỀ XUẤT, chưa chốt)*

```
POST   /api/v1/auth/register     {username, password, display_name}  -> 201 {token}
POST   /api/v1/auth/login        {username, password}                -> 200 {token, role}
POST   /api/v1/auth/logout                                            -> 204
GET    /api/v1/auth/me                                                -> {user_id, username, role}
GET    /api/v1/me/favorites                                           -> danh sách quán đã lưu
POST   /api/v1/me/favorites      {restaurant_id}                      -> 201
DELETE /api/v1/me/favorites/{id}                                      -> 204
GET    /api/v1/me/history                                             -> lịch sử xem
```

**Ảnh hưởng tới thứ đang chạy:**

| Chỗ bị ảnh hưởng | Thay đổi |
|---|---|
| `POST /interactions` | thêm `user_id`; giữ `session_id` cho khách |
| Đăng nhập admin | tài khoản admin thành **một dòng trong bảng `users`** với `role="admin"`, thay cho biến môi trường |
| `Favorites` ở client | chuyển từ `localStorage` sang **server** — đổi máy vẫn còn |
| `interactions.jsonl` | thêm cột `user_id` |
| Bảng mới | `users` (id, username, password_hash, display_name, role, created_at) |

### 5.6. ✅ ĐÃ CHỐT: khách phải đăng nhập

Mọi màn hình của app người dùng đều nằm sau `RequireAuth`. Chưa đăng nhập → đá về `/login`.

**Hệ quả tới thiết kế — phải xử lý ngay từ đầu:**

| Việc | Chi tiết |
|---|---|
| Màn hình đầu tiên | `/login`, không phải trang tìm kiếm |
| Route map client | giống admin: `AuthLayout` (login/register) + `AppLayout` (sau đăng nhập) |
| Lúc demo bảo vệ | **phải có sẵn tài khoản demo** — không ai muốn xem thầy/cô gõ mật khẩu |
| Token hết hạn giữa chừng | đang tìm kiếm mà 401 → về login, **giữ lại câu đang gõ** để quay lại không mất |
| Trang chia sẻ được | link tới quán vẫn cần đăng nhập → sau khi đăng nhập phải **quay đúng link đó** |

⚠️ **Rủi ro cần biết:** bắt đăng nhập ngay làm rào cản cao nhất, và lúc bảo vệ thì màn
hình đầu tiên hội đồng nhìn thấy là form đăng nhập chứ không phải sản phẩm. Cách giảm
thiểu: chuẩn bị sẵn tài khoản demo và đăng nhập trước khi trình bày.

### 5.7. Thứ tự triển khai — tiến độ thật

| # | Việc | Trạng thái |
|---|---|---|
| 1 | Chốt phương án email → **tài khoản nội bộ trước, Google sau** | ✅ đã chốt |
| 2 | Sửa `rules/api.md` + `PROJECT_CHECKLIST.md` — bỏ "Won't-have" | ✅ xong 2026-08-17 |
| 3 | **Backend:** bảng `users`, đăng ký/đăng nhập, `role`, rate limiting, `build_sqlite` | ✅ xong 2026-08-17 |
| 4 | Chuyển admin sang dùng bảng `users` | ⬜ chưa — admin vẫn dùng biến môi trường |
| 5 | Gắn `user_id` vào interaction + quán yêu thích | ⬜ chưa |
| 6 | Giao diện Login / Register / Profile | ⬜ chờ bộ asset thiết kế |

### 5.8. QUYẾT ĐỊNH CÒN TREO — đăng xuất có thu hồi token

**Hiện trạng:** KHÔNG có `POST /auth/logout`. Token ký bằng HMAC là *stateless* — server
không giữ danh sách token đang sống nên không có gì để xoá. Một endpoint chỉ trả 200 rồi
không làm gì là **ảo giác an toàn**, tệ hơn là không có. Đăng xuất hiện tại = client tự
xoá token; thiệt hại khi token bị lộ bị chặn trên bởi thời hạn **24 giờ**.

Ba cách làm thật, phải chọn một:

| Cách | Ưu | Nhược |
|---|---|---|
| **A. Cột `token_version` ở bảng `users`** | Thu hồi thật, bền qua khởi động lại, rẻ (đang đọc sẵn dòng user rồi) | Đăng xuất **giết mọi thiết bị** cùng lúc. Thêm cột = đổi data model |
| **B. Bảng danh sách token bị thu hồi** | Đăng xuất từng thiết bị | Thêm bảng + phải dọn định kỳ. Nặng hơn hẳn cho nhu cầu hiện tại |
| **C. Giữ nguyên, rút hạn còn 1-2 giờ** | Không đổi gì | Người dùng bị đăng xuất liên tục — đổi bảo mật lấy phiền toái |

Khuyến nghị: **A**. Cần chủ dự án đồng ý vì nó ĐỔI DATA MODEL (bảng `users` thêm cột).

⚠️ Danh sách thu hồi để trong BỘ NHỚ tiến trình là phương án **SAI** — khởi động lại là
token đã thu hồi sống lại, và chạy nhiều worker thì mỗi worker giữ một danh sách riêng.
6. **Sau đó mới** thiết kế UI Login/Register/Profile

> Làm ngược thứ tự này là lặp lại đúng lỗi đã audit: vẽ giao diện trước rồi phát hiện
> backend không hỗ trợ.

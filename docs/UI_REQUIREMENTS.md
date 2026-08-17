# MoodBite — Mô tả UI để thiết kế

**Cập nhật:** 2026-08-17 · **Mục đích:** tài liệu bàn giao cho người/AI thiết kế giao diện.

File này mô tả **UI cần gì**, KHÔNG áp đặt màu sắc, font chữ hay bố cục cụ thể.
Mọi con số đều đo trực tiếp từ dữ liệu thật, kiểm lại được bằng lệnh ghi kèm.

---

## 1. Sản phẩm là gì

Gợi ý quán ăn ở Hà Nội theo **nhu cầu diễn đạt bằng câu tự nhiên** + vị trí + thời điểm.

Người dùng gõ *"quán lẩu ấm cúng gần đây"* hoặc *"chỗ yên tĩnh để làm việc"* thay vì chọn
trong bộ lọc cứng. Kết quả trả về đã xếp hạng, kèm **lý do vì sao quán đó được gợi ý**.

> **USP: Context + Mood + Recommendation.**
> MoodBite KHÔNG phải bản sao Google Maps. Bản đồ là công cụ phụ trợ; thứ chính là
> **danh sách đề xuất và lời giải thích**. Thiết kế phải làm nổi bật phần đó.

**Hai ứng dụng riêng biệt:**

| | Client | Admin |
|---|---|---|
| Người dùng | người đi ăn | người quản lý dữ liệu |
| Đăng nhập | ❌ không có | ✅ 1 tài khoản, token 1 giờ |
| Cổng dev | 5173 | 5174 |
| Việc chính | tìm + xem đề xuất | sửa/ẩn quán, theo dõi chất lượng dữ liệu |

---

## 2. Ràng buộc bắt buộc

| Ràng buộc | Chi tiết |
|---|---|
| **Không có tài khoản người dùng** | `rules/api.md`: *"Không áp dụng hệ thống tài khoản cá nhân đăng nhập ở Giai đoạn MVP"*. Không có Profile, không có đăng ký, không có dữ liệu cá nhân. Client dùng `session_id` sinh ngẫu nhiên. |
| **Không dịch vụ trả phí** | Chủ dự án không có thẻ thanh toán. Bản đồ dùng **Leaflet + OpenStreetMap** (không cần API key). Không Google Maps. |
| **Tiếng Việt** | Toàn bộ giao diện. Font phải hiển thị đủ dấu (ă â đ ê ô ơ ư + thanh điệu). |
| **Chế độ tối** | Bắt buộc cho cả hai app. |
| **Không bịa số liệu** | Xem mục 6. Đây là ràng buộc nghiêm ngặt nhất. |

---

## 3. Dữ liệu thật — quyết định phần lớn thiết kế

Đây là phần **quan trọng nhất** với người thiết kế. Dữ liệu rất thưa, nên nhiều ý tưởng
thiết kế đẹp sẽ không dùng được.

**Đếm ngày 2026-08-17** từ `dataset_moodbite_features.csv` và `moodbite.db`:

```
Tổng số quán     4938   (openstreetmap 3528 + google_maps_apify 1410 = 4938 ✓)
```

| Trường | Độ phủ | Hệ quả thiết kế |
|---|---|---|
| Toạ độ | **100%** | mọi quán đều lên bản đồ được |
| Tên quán | **100%** | luôn có |
| Loại hình | ~100% | luôn có |
| Khu vực (phường) | **96.9%** | dùng được |
| Giờ mở cửa | **32.6%** | 2/3 quán KHÔNG biết đang mở hay đóng |
| Đánh giá sao | **23.2%** | **3/4 quán không có sao** |
| Ảnh | **21.5%** | **4/5 quán KHÔNG CÓ ẢNH** |
| Giá | **13.0%** | gần như không có |
| Đã phân cụm | 1197/4938 | phần còn lại chưa phân cụm |

> ⚠️ **Đừng thiết kế giao diện dựa vào ảnh.** Chỉ 1064/4938 quán có ảnh. Bố cục kiểu
> "thẻ ảnh lớn" sẽ trống rỗng ở 4/5 kết quả. Cần một cách thể hiện đẹp cho quán KHÔNG có
> ảnh — đây là trường hợp **phổ biến**, không phải ngoại lệ.

> ⚠️ **Đừng thiết kế dựa vào sao.** 3/4 quán không có đánh giá. Chỗ hiển thị sao phải
> trông ổn khi trống.

**Kiểm lại:** `python scripts/data_report.py`

---

## 4. Danh sách màn hình

### CLIENT — 4 màn hình chức năng + 404

#### 4.1. Explore *(màn hình chính)*
Tìm kiếm + bản đồ + danh sách đề xuất.

**Dữ liệu mỗi kết quả** (từ `POST /api/v1/search`):

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `name` | chuỗi | luôn có |
| `category` | chuỗi\|null | "Nhà hàng phở", "Quán cà phê"… |
| `address` | chuỗi\|null | |
| `distance_m` | số nguyên | mét, đường chim bay |
| `rating` | số\|**null** | null = chưa có đánh giá |
| `user_ratings_total` | số\|null | số lượt đánh giá |
| `price_range` | **chuỗi**\|null | `"1-100.000 ₫"`, `"70 US$"` — KHÔNG phải số |
| `thumbnail_url` | chuỗi\|null | chỉ 21.5% có |
| `predicted_score` | số 0–1 | xem mục 5 |
| `match_source` | chuỗi | `"name+review"`, `"atmosphere+semantic"`… |
| `suggested_dish` | object\|null | `{name, confidence}` |
| `experience_cluster_label` | chuỗi\|null | null = chưa phân cụm |
| `rank_position` | số | thứ hạng |

**Bộ lọc người dùng chỉnh được:** câu tìm tự do · bán kính (2/5/10/20 km/không giới hạn) ·
đang mở cửa · 4 mood (vui, buồn, hào hứng, thư giãn) · vị trí (mặc định trung tâm Hà Nội,
hoặc xin GPS).

**Ngữ cảnh backend trả về:** mảng chuỗi như `["buổi tối", "cuối tuần", "24°C"]` — nên hiện
để người dùng biết hệ thống đang cân nhắc thời điểm.

**Cảnh báo:** `warnings[]` — điều server KHÔNG làm được với yêu cầu này. **Phải hiện**,
không được im lặng bỏ qua.

#### 4.2. Chi tiết quán
`GET /api/v1/restaurants/{id}` → ảnh (nhiều), giờ mở cửa, review, link menu/website/Google Maps.

- Quán **có tồn tại nhưng chưa có chi tiết** → trả `has_details: false`, **KHÔNG phải lỗi**.
  Cần trạng thái riêng: "quán này lấy từ OpenStreetMap, chưa có giá/review/ảnh".
- Quán không tồn tại hoặc đã bị admin ẩn → 404.

#### 4.3. Quán đã lưu
Danh sách quán người dùng tự lưu. **Lưu ở localStorage**, không có backend.
Giao diện **phải ghi rõ**: *"lưu trên máy này, đổi máy sẽ mất"*.

#### 4.4. Cài đặt
Bán kính mặc định, giao diện sáng/tối. Cũng lưu localStorage.

#### 4.5. 404

### ADMIN — 5 màn hình chức năng + 404

#### 4.6. Đăng nhập
1 tài khoản. Sai thông tin → **chỉ nói "sai tài khoản hoặc mật khẩu"**, không nói sai cái
nào (tránh giúp người dò tài khoản). Chưa cấu hình quyền → 503 kèm hướng dẫn.

#### 4.7. Dashboard
Số liệu tổng quan. **Chỉ những chỉ số có nguồn dữ liệu thật** — xem mục 6.

#### 4.8. Quản lý quán
Bảng: tên · loại hình · đánh giá · trạng thái · thao tác. Có ô tìm, có tuỳ chọn
"hiện cả quán đã ẩn".

- **Sửa được:** tên, loại hình, ẩm thực, địa chỉ, khu vực, giá, điện thoại, website
- **KHÔNG sửa được:** đánh giá, số lượt đánh giá, cụm trải nghiệm, toạ độ, placeId
  *(do pipeline sinh ra; sửa tay sẽ bị ghi đè và làm sai lệch số liệu)*
- **Ẩn quán** = soft-delete. Quán biến mất khỏi tìm kiếm của người dùng nhưng admin vẫn
  thấy để bỏ ẩn lại. Quán đã ẩn phải **nhìn là biết ngay**, không chỉ khác chữ ở một cột.

#### 4.9. Chất lượng dữ liệu ⭐
Hiển thị bảng độ phủ ở mục 3 dưới dạng trực quan. **Đây là điểm nhấn của admin** — nó
chứng minh dự án có hệ thống kiểm soát chất lượng dữ liệu, không chỉ hiển thị quán.

#### 4.10. Trạng thái hệ thống
`GET /api/v1/health` → từng nguồn dữ liệu sẵn sàng hay chưa, kèm lý do nếu hỏng.

#### 4.11. 404

---

## 5. `predicted_score` — cạm bẫy hiển thị

Backend trả `predicted_score` trong khoảng 0–1. **Đừng nhân 100 rồi hiện "% phù hợp".**

Đo thật 40 kết quả của 4 câu tìm kiếm:

| Câu tìm | Cao nhất | Thấp nhất |
|---|---|---|
| quán lẩu ấm cúng gần đây | 0.659 | 0.598 |
| phở bò | 0.641 | 0.576 |
| chỗ yên tĩnh để làm việc | 0.658 | 0.594 |
| cà phê | 0.721 | 0.674 |

Kết quả **tốt nhất** cũng chỉ ~0.72, trung vị 0.61. Hiện "61% phù hợp" khiến người dùng
tưởng máy gợi ý kém, trong khi đó lại đúng là quán khớp nhất. Lý do: đây là tổng có trọng
số của 6 tín hiệu, phần lớn quán thiếu dữ liệu nên nhận điểm trung lập → mọi điểm dồn
quanh 0.6. Nó là điểm **xếp hạng**, không phải xác suất.

**Cách hiện đã chốt:** nhãn định tính + thanh so sánh tương đối.

| Điểm | Nhãn |
|---|---|
| ≥ 0.68 | Rất phù hợp |
| 0.60 – 0.68 | Phù hợp |
| < 0.60 | Có thể hợp |

---

## 6. Những gì TUYỆT ĐỐI không được làm

### 6.1. Không biến `null` thành `0`
`null` = **chưa có dữ liệu**, không phải giá trị 0.

- `rating = null` → *"chưa có đánh giá"*, **không bao giờ** "0 sao" hay "0★"
- `price_range = null` → không hiện gì, **không** "miễn phí", **không** "đang cập nhật giá"
- `thumbnail_url = null` → cần cách thể hiện có chủ đích, **không** để ô trắng như ảnh vỡ
- `experience_cluster_label = null` → *"Đang cập nhật"*, không để trống

### 6.2. Không bịa số liệu
Mọi con số trên Dashboard / Chất lượng dữ liệu phải đến từ backend. Không hardcode,
không làm tròn cho đẹp, không điền tạm chờ backend.

**Ba chỉ số KHÔNG TỒN TẠI, không được xuất hiện dù dưới bất kỳ hình thức nào:**

| Chỉ số | Vì sao không có |
|---|---|
| Số người dùng | Không có hệ thống tài khoản |
| Số review | Review cào từ Apify, nhúng trong dữ liệu quán, không đếm riêng được |
| "Match Quality %" | Không tồn tại chỉ số này |

Kể cả hiển thị `0` cũng không được — trả 0 vẫn khiến người đọc tưởng hệ thống có đo,
chỉ là chưa ai dùng.

### 6.3. Không bịa lý do đề xuất
Chỉ dịch `match_source` backend trả về sang tiếng Việt dễ hiểu. Không có `match_source`
thì không hiện dòng lý do nào.

### 6.4. Món ăn là SUY LUẬN, không phải thực đơn
`suggested_dish` được suy ra từ tên quán và loại hình, **không phải menu thật**.
Mỗi món kèm `confidence`:

| Giá trị | Nghĩa |
|---|---|
| `specific` | khớp loại hình cụ thể của quán |
| `generic_fallback` | suy luận rộng, có thể không chính xác |
| `unknown` | chưa xác định |

**Mức tin cậy phải hiện ra CHỮ**, không được giấu trong tooltip — trên điện thoại người
dùng không bao giờ thấy tooltip.

### 6.5. Không thêm mục điều hướng dẫn tới trang trống
Sidebar admin chỉ liệt kê 4 trang có thật. Không thêm "Users", "Reviews", "Reports" dạng
"coming soon".

---

## 7. Mỗi màn hình cần thiết kế đủ 4 trạng thái

| Trạng thái | Yêu cầu |
|---|---|
| **Trống** | chưa tìm gì / chưa lưu gì. Phải có lời mời hành động, không để trắng trơn |
| **Đang tải** | có dấu hiệu rõ ràng, không nhảy giật khi dữ liệu về |
| **Lỗi** | câu người dùng hiểu + **nói phải làm gì**, không hiện mã lỗi kỹ thuật |
| **Có dữ liệu** | trạng thái bình thường |

Riêng Explore cần thêm **không có kết quả** — và nên kèm lối thoát (mở rộng bán kính,
bỏ bớt điều kiện lọc).

**Lỗi thường gặp cần thiết kế sẵn:**

| Tình huống | Hiện gì |
|---|---|
| Backend chưa chạy | "Không kết nối được tới server. Kiểm tra backend đã chạy chưa." |
| Chưa chạy data_pipeline | 503 kèm lệnh cần chạy |
| Token admin hết hạn | "Phiên đăng nhập đã hết hạn" → về trang đăng nhập |
| Chưa cấu hình quyền admin | 503 kèm hướng dẫn cấu hình |

---

## 8. Yêu cầu kỹ thuật tối thiểu

**Responsive:** thiết kế cho 360px (điện thoại), 768px (máy tính bảng), 1440px (máy tính).
Bản đồ và danh sách phải dùng được ở cả ba.

**Tiếp cận:**
- Chữ thường tương phản ≥ 4.5:1, chữ lớn ≥ 3:1
- **Không dùng MỖI màu để truyền tin** — "đang mở cửa" phải có chữ, không chỉ chấm xanh
- Mọi thứ bấm được phải dùng được bằng bàn phím, có viền focus rõ
- Tôn trọng `prefers-reduced-motion`

**Chữ số** (khoảng cách, điểm, giá) nên dùng `tabular-nums` để xếp thẳng cột.

---

## 9. Hiện trạng code

Frontend là **monorepo npm workspaces**, React + TypeScript, kiến trúc Feature-Sliced Design.

```
frontend/
├── packages/api-client/     tầng gọi API dùng chung, kiểu sinh tự động từ OpenAPI
└── apps/
    ├── client/              cổng 5173
    └── admin/               cổng 5174
```

Đang có: 2 layout (client, admin), react-router v6, 47 test frontend.
Toàn bộ CSS nằm ở `apps/*/src/app/styles.css` — **thiết kế mới sẽ ghi đè hai file này**.

**Chạy thử:**
```
python scripts/run_dev.py --admin
```

**Luật kiến trúc** (thiết kế mới vẫn phải tuân theo):
- Import chỉ đi xuống: `app → pages → widgets → features → entities → shared`
- **Không có business logic ở frontend.** Công thức xếp hạng, bảng điểm mood, quy tắc suy
  luận món — tất cả ở backend. Frontend chỉ có quy tắc **hiển thị**.
- Cách tự kiểm: *"đổi dòng này thì THỨ TỰ kết quả có đổi không?"* Nếu đổi → đó là nghiệp
  vụ, đặt sai chỗ.

---

## 10. Kiểm lại mọi con số trong file này

```
python scripts/data_report.py      # độ phủ dữ liệu
python scripts/review_report.py    # dữ liệu review
python scripts/verify.py           # toàn bộ dự án, 8 mục
```

> **Quy ước về số lượng bản ghi:** con số 4938 là của **dataset hiện tại, đo 2026-08-17**.
> Tài liệu cũ có thể ghi 4170 — đó là **baseline trước đợt bổ sung +768 quán**, không phải
> con số hiện hành. Mọi chỗ hiển thị số lượng phải nói rõ thuộc phiên bản dữ liệu nào.

---

## 11. Tương tác & Phản hồi — vòng dữ liệu

Đây là phần **quan trọng nhất cho lộ trình ML**, và hiện là **nút thắt**.

### 11.1. Vòng dữ liệu (data flywheel)

```
Tìm kiếm → Đề xuất → Xem chi tiết → Lưu / Thích / Không thích
                                              ↓
                                    interactions.jsonl
                                              ↓
                                     Mô hình xếp hạng
                                              ↓
                                     Đề xuất tốt hơn
```

Giao diện **là đầu vào duy nhất** của vòng này. Không có nút phản hồi → không có dữ liệu
→ không huấn luyện được → Lớp 3 chặn vĩnh viễn.

Hiện trạng: `interactions.jsonl` có **0 bản ghi**, vì giao diện mới dùng 2/5 loại tương tác.

### 11.2. Năm tín hiệu backend đã hỗ trợ

| `action_type` | Ý nghĩa | Giao diện hiện có |
|---|---|---|
| `view_detail` | mở chi tiết, **bắt buộc kèm `dwell_time_ms`** (xem ghi chú) | ✅ có |
| `get_directions` | bấm chỉ đường | ✅ có |
| `save` | lưu quán | ❌ **chưa có nút** |
| `explicit_positive` | "hợp với tôi" | ❌ **chưa có nút** |
| `explicit_negative` | "không phù hợp" | ❌ **chưa có nút** |

Ba nút còn thiếu là việc **thiết kế phải giải quyết**.

> **Năm giá trị này là HỢP ĐỒNG CỨNG, không phải dự định.** `action_type` khai kiểu
> `ActionType` (enum), nên backend **từ chối** giá trị lạ. Kiểm chứng: gửi
> `action_type: "banana"` → `400 INVALID_REQUEST`; gửi `"save"` → được chấp nhận.

> ⚠️ **`dwell_time_ms` bắt buộc với `view_detail` — nhưng KHÔNG thấy điều đó trong schema.**
> Pydantic khai `Optional[int]` vì nó chỉ bắt buộc với MỘT action type, schema không diễn
> đạt được điều kiện đó. Quy tắc nằm ở tầng use case
> (`application/use_cases/log_interaction.py:65`) — đúng chỗ CLAUDE.md quy định business
> rule phải ở. Kiểm chứng bằng cách gọi thật:
> `view_detail` không kèm `dwell_time_ms` → **400 INVALID_REQUEST**; có kèm → **201**.
> Ai chỉ đọc `schemas.py` sẽ kết luận nhầm là không bắt buộc.

### 11.3. Chi tiết quán NÊN mở dạng panel trong cùng ngữ cảnh tìm kiếm

Vì `dwell_time_ms` đo bằng khoảng thời gian panel mở:

```
mở panel → bắt đầu đếm → người dùng đọc → đóng panel → dừng đếm → POST /interactions
```

Về kỹ thuật, mở trang mới rồi đo bằng timestamp lúc đi/lúc quay lại **vẫn khả thi**.
Nhưng panel là lựa chọn tốt hơn vì hai lý do: giữ nguyên ngữ cảnh tìm kiếm (danh sách,
bản đồ, vị trí cuộn), và đo `dwell_time` **nhất quán** hơn — không phụ thuộc điều hướng,
nút Back hay việc người dùng đóng tab.

Nói cho chính xác: **đây là lựa chọn UX được khuyến nghị mạnh, không phải ràng buộc kiến
trúc bắt buộc.** Muốn dùng trang riêng thì phải chứng minh đo được `dwell_time` đáng tin.

> ⚠️ **`dwell_time` KHÔNG phải bằng chứng người dùng thích quán.** Họ có thể ở lâu vì
> mạng chậm, vì bị phân tâm, vì đang đọc kỹ để loại. Backend đã coi nó là tín hiệu YẾU:
> `MIN_POSITIVE_DWELL_MS = 3000` — dưới 3 giây thì không tính là tích cực, trên 3 giây
> cũng chỉ là *tín hiệu hành vi*, không ngang hàng với `explicit_positive`.

### 11.4. Nguyên tắc thiết kế nút phản hồi

- **Đừng biến thẻ quán thành bảng nút.** Ưu tiên: `Xem` và `Lưu` hiện sẵn; `Hợp / Không hợp`
  xuất hiện **đúng lúc** — ví dụ sau khi người dùng đóng panel chi tiết.
- Phản hồi phải **một chạm**, không bắt điền form.
- Đã phản hồi thì phải thấy trạng thái đã ghi nhận (nút đổi hình).

### 11.5. ⛔ Chưa gửi được lên backend

| Ý tưởng | Vì sao chưa làm được |
|---|---|
| **Chọn lý do không phù hợp** (quá xa / sai món / sai mood / giá) | `InteractionRequest` **không có trường `reason`**. Thêm = đổi schema → BLOCKING DECISION |
| **Admin xem thống kê tương tác** | Chỉ có `POST /interactions`, **không có GET**. Cần endpoint mới |

Nếu vẫn muốn có, phải **duyệt thay đổi API trước**, không được làm UI rồi để dữ liệu rơi
vào hư không.

---

## 12. Giải thích đề xuất — USP, và giới hạn của nó

Mỗi kết quả phải trả lời được: **"vì sao quán này?"**

Nguồn duy nhất là `match_source` backend trả về (`"name+review"`, `"atmosphere+semantic"`…).
Nhiệm vụ của giao diện là **dịch mã đó sang câu người đọc hiểu**.

```
😌  Hợp với "quán lẩu ấm cúng gần đây"     ← khi match_source có atmosphere/mood
🔎  Khớp tên quán, đánh giá                ← khi có name/review/category/semantic
🍽  Lẩu nấm · khớp loại hình cụ thể        ← suggested_dish + confidence
```

> ⛔ **Không được bịa lý do.** Chỉ hiện những gì `match_source` thực sự nói. Không có
> `match_source` → không hiện dòng lý do nào. Không được thêm "Phù hợp thời tiết" nếu
> backend không báo, không được thêm "Đánh giá tốt" cho quán chưa có đánh giá.

---

## 13. Yêu cầu bảo mật ở tầng giao diện

| Yêu cầu | Chi tiết |
|---|---|
| **Token admin** | Lưu `sessionStorage` để **rút ngắn thời gian token tồn tại trên máy** (đóng tab là mất). ⚠️ Đây **KHÔNG phải biện pháp chống XSS** — mã độc chạy cùng origin vẫn đọc được `sessionStorage`. Muốn chống thật thì phải đổi kiến trúc xác thực, và đó là quyết định riêng |
| **Đăng xuất** | Xoá token phía client. ⚠️ Backend **chưa thu hồi token** — vẫn hợp lệ tới hết hạn (1 giờ). Giao diện không được hứa "đã đăng xuất hoàn toàn" |
| **Hết hạn** | Nhận 401 → về trang đăng nhập kèm câu "Phiên đã hết hạn", không hiện lỗi kỹ thuật |
| **Thông báo lỗi đăng nhập** | Chỉ "sai tài khoản hoặc mật khẩu". **Không** nói sai cái nào — tránh giúp người dò tài khoản |
| **Không render HTML thô** | Tuyệt đối không `dangerouslySetInnerHTML`. Review và tên quán là dữ liệu cào từ ngoài |
| **Không lộ dữ liệu nhạy cảm** | Không in token, hash, biến môi trường ra console hay DOM |
| **Nút phản hồi** | Chống bấm liên tục (debounce). `POST /interactions` **không yêu cầu xác thực** — giao diện không nên tạo điều kiện bơm nhãn hàng loạt |

---

## 14. ⛔ DESIGN GATE — thiết kế phải dựa trên fixture thật

**Cấm thiết kế hoặc đánh giá giao diện bằng dữ liệu lý tưởng.**

Dùng bộ mẫu: **`frontend/fixtures/restaurants.json`** — 100 quán **thật**, lấy từ chính
`POST /api/v1/search`, giữ đúng **độ phủ biên (marginal distribution)** của từng trường:

| | Bộ mẫu | Dataset thật |
|---|---|---|
| có ảnh | 22 | 21.5% |
| có đánh giá | 23 | 23.2% |
| có giá | 13 | 13.0% |
| đã phân cụm | 24 | 24.2% |

Bộ mẫu **cố ý** chứa các ca khó: 78 quán không ảnh · 77 không đánh giá · 87 không giá ·
76 chưa phân cụm · 11 món suy luận rộng · 3 tên rất dài · 22 địa chỉ rất dài.

> **Nói cho chính xác:** bộ mẫu khớp độ phủ của TỪNG trường riêng lẻ, **chưa phải bản sao
> thống kê đầy đủ** của dataset. Ví dụ thực tế "có ảnh" thường đi kèm "có rating" (cùng
> đến từ Apify), nhưng bộ mẫu không đảm bảo giữ đúng tương quan đó. Với mục đích kiểm thử
> giao diện thì như vậy đã đủ — không cần biến bộ mẫu thành một bài toán thống kê.

`RestaurantCard` phải trông ổn ở **mọi tổ hợp**:

```
[có ảnh / không ảnh] × [có sao / không sao] × [có giá / không giá]
× [món cụ thể / món suy luận rộng] × [đã phân cụm / chưa] × [tên ngắn / tên dài]
```

**Cưỡng chế bằng máy** — giống `verify.py` là gate của code:

```
python scripts/make_fixture.py     # sinh lại bộ mẫu
python scripts/verify_ui_data.py   # kiểm: schema · kiểu · tỉ lệ ±5đ · đủ trạng thái
python scripts/verify.py           # mục 9 chạy tự động
```

> Lỗi này **đã xảy ra**: bản fixture đầu tiên có 54% quán kèm ảnh (thật 21.5%) vì xếp hạng
> ưu tiên quán giàu dữ liệu. Nếu thiết kế trên bộ đó, giao diện sẽ đẹp lúc demo và vỡ khi
> cắm dữ liệu thật. Script mục 9 sinh ra chính là để chặn việc đó tái diễn.

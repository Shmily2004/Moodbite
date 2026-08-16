# Đánh giá mức sẵn sàng Frontend + Phương án kiến trúc

> **Trạng thái:** CHỜ BẠN CHỌN KIẾN TRÚC. Chưa triển khai frontend mới.

---

## PHẦN 1 — Mức sẵn sàng (dựa trên khảo sát thực tế, không phải phỏng đoán)

### Kết luận

| Frontend | Trạng thái | Lý do một câu |
|---|---|---|
| **Client / User** | ✅ **READY** | API đủ, hợp đồng ổn định, dữ liệu đủ cho tìm kiếm + bản đồ |
| **Admin** | ❌ **NOT READY** | Không có xác thực, không có CRUD, không có endpoint quản trị nào |

**Tổng thể: PARTIALLY READY — sẵn sàng cho Client, chưa sẵn sàng cho Admin.**

---

### 1.1. Bề mặt API hiện có (khảo sát từ OpenAPI schema)

```
GET    /api/v1/health                      trạng thái từng nguồn dữ liệu
GET    /api/v1/moods                       4 mood cho nút bấm nhanh
POST   /api/v1/search                      tìm kiếm + xếp hạng  ← endpoint chính
GET    /api/v1/restaurants/{id}            chi tiết quán
POST   /api/v1/interactions                ghi tương tác người dùng
GET    /health                             probe hạ tầng
```

**Xác thực: KHÔNG CÓ.** `securitySchemes` rỗng.

---

### 1.2. Client Frontend — vì sao READY

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Ổn định API | ✅ | Có version `/api/v1`, envelope `{data}`/`{error}` cố định |
| Hợp đồng request/response | ✅ | Pydantic schema sinh OpenAPI tự động, `snake_case` nhất quán |
| Xử lý lỗi | ✅ | Bảng mã lỗi thống nhất, 400/404/503/500 phân biệt rõ |
| Dữ liệu cho tìm kiếm | ✅ | 100% quán có tên + toạ độ + loại hình |
| Dữ liệu cho bản đồ | ✅ | 100% quán có lat/lng |
| Chất lượng gợi ý | ✅ | `predicted_score` + `match_source` giải thích được vì sao |
| Gợi ý món | ✅ | Lồng sẵn trong từng kết quả, kèm `confidence` |
| Ghi nhận tương tác | ✅ | `POST /interactions` đã chạy |
| Xác thực | ✅ Không cần | SRS mục 8: tài khoản người dùng là Won't-have |
| Test | ✅ | 129+ test, có test HTTP thật |

**Client có thể bắt đầu NGAY.** Không có gì chặn.

---

### 1.3. Admin Frontend — vì sao NOT READY

Đây là những thứ **chưa tồn tại**, không phải "chưa hoàn thiện":

| Cần cho Admin | Trạng thái | Ghi chú |
|---|---|---|
| Xác thực (login) | ❌ **Chưa có** | Không có user, password, session, token |
| Phân quyền (role) | ❌ **Chưa có** | Không có khái niệm admin vs viewer |
| CRUD nhà hàng | ❌ **Chưa có** | Chỉ có GET; không POST/PUT/DELETE |
| Soft-delete qua API | ❌ **Chưa có** | Entity có `is_active` nhưng không sửa được từ ngoài |
| Quản lý nguồn dữ liệu | 🟡 Có CLI, chưa có API | `python -m data_pipeline.harvest` |
| Giám sát chất lượng dữ liệu | 🟡 Có CLI, chưa có API | `python scripts/data_report.py` |
| Quản lý knowledge base món | ❌ **Chưa có** | Sửa tay file JSON |
| Cấu hình trọng số xếp hạng | ❌ **Chưa có** | Hằng số hard-code trong `search_ranking.py` |
| Xem tương tác người dùng | 🟡 Có file JSONL, chưa có API | |
| Sức khoẻ hệ thống | ✅ **Đã có** | `GET /api/v1/health` |
| Xem log/lỗi | ❌ **Chưa có** | Chỉ log ra stdout |
| Lưu trữ ghi được | ❌ **CSV chỉ đọc** | Sửa dữ liệu cần DB thật |

#### Chặn lớn nhất: lưu trữ hiện tại CHỈ ĐỌC

Backend đọc CSV vào RAM một lần lúc khởi động. Admin cần **ghi**: sửa quán, ẩn quán,
thêm món. CSV không làm được việc này an toàn (không có transaction, không có khoá ghi,
2 người sửa cùng lúc là mất dữ liệu).

→ **Admin bắt buộc phải có database thật trước.** SQLite là đủ cho quy mô đồ án và
không cần cài server.

---

### 1.4. Việc phải làm TRƯỚC khi bắt đầu Admin

Theo thứ tự phụ thuộc:

1. **Chuyển lưu trữ sang SQLite** (~1-2 ngày)
   Viết `SqliteRestaurantRepository` thoả port đã có. Use case KHÔNG đổi một dòng.
2. **Thêm xác thực** (~1 ngày)
   Đơn giản nhất phù hợp đồ án: 1 tài khoản admin + JWT ngắn hạn.
   ⚠️ Đây là ngoại lệ so với SRS ("không có tài khoản NGƯỜI DÙNG CUỐI") — tài khoản
   quản trị là chuyện khác, cần ghi rõ trong tài liệu để không mâu thuẫn.
3. **Thêm endpoint quản trị** (~2 ngày)
   `/api/v1/admin/restaurants` (CRUD + soft-delete), `/admin/dishes`, `/admin/data-quality`,
   `/admin/interactions`.
4. **Chỉ khi đó mới dựng Admin UI.**

### 1.5. Việc làm SONG SONG được ngay

- Client frontend (không phụ thuộc gì ở trên)
- Bản đồ Google Maps
- Cải thiện dữ liệu (đang làm)
- Thiết kế UI/UX cho Admin (thiết kế thôi, chưa nối API)

---

## PHẦN 2 — Phương án công nghệ

### Phương án 1: React + JavaScript (giữ nguyên hiện tại)

**Kiến trúc:** feature-based, đúng như frontend đang chạy.

```
src/
├── domain/       formatters, session       (thuần JS, không React)
├── services/     httpClient, moodbiteApi   (nơi DUY NHẤT gọi fetch)
├── features/
│   ├── search/   useSearch, SearchPage, RestaurantCard
│   └── map/      useUserLocation, RestaurantMap
└── components/ui/  Button, Spinner, EmptyState
```

| Tiêu chí | Đánh giá |
|---|---|
| Bảo trì | 🟡 Khá — nhưng không có gì chặn gõ sai tên field |
| Học | ✅ Không phải học thêm |
| Debug | 🟡 Lỗi kiểu chỉ lộ ra lúc chạy |
| Hiệu năng | ✅ Tốt |
| Mở rộng | 🟡 Càng nhiều tính năng càng dễ lệch hợp đồng API |
| Test | ✅ Vitest chạy được ngay |
| Phụ thuộc | ✅ Ít nhất |
| Triển khai | ✅ Đơn giản (static build) |
| Hợp đồ án | 🟡 Chạy được nhưng khó gây ấn tượng kỹ thuật |
| Hợp cho Admin | ❌ Admin nhiều form + bảng → thiếu kiểu dữ liệu rất dễ sai |
| **Rủi ro lại thành mớ hỗn độn** | 🟡 Trung bình |

---

### Phương án 2: React + TypeScript + feature-based ⭐

**Kiến trúc:** giống P1 nhưng có kiểu dữ liệu, và **sinh type tự động từ OpenAPI**.

```bash
npx openapi-typescript http://localhost:8001/openapi.json -o src/shared/api/schema.d.ts
```

```
src/
├── shared/
│   ├── api/          schema.d.ts (SINH TỰ ĐỘNG), httpClient.ts, endpoints.ts
│   ├── ui/           Button, Table, Modal, Spinner
│   └── lib/          formatters, session
├── features/
│   ├── search/       api.ts · model.ts · ui/ · index.ts
│   ├── restaurant/
│   ├── recommendation/
│   ├── map/
│   └── interaction/
└── app/              router, providers, layout
```

| Tiêu chí | Đánh giá |
|---|---|
| Bảo trì | ✅ Rất tốt |
| Học | 🟡 Cần vài ngày làm quen |
| Debug | ✅ **Sai tên field lộ ra ngay khi gõ**, không cần chạy |
| Hiệu năng | ✅ Tốt (TS chỉ ảnh hưởng lúc build) |
| Mở rộng | ✅ Rất tốt |
| Test | ✅ Vitest + Testing Library |
| Phụ thuộc | ✅ Chỉ thêm typescript |
| Triển khai | ✅ Vẫn là static build |
| Hợp đồ án | ✅ **Thể hiện được năng lực kỹ thuật khi bảo vệ** |
| Hợp cho Admin | ✅ Form/bảng phức tạp cần kiểu dữ liệu nhất |
| **Rủi ro lại thành mớ hỗn độn** | ✅ Thấp |

**Điểm mạnh quyết định:** backend đã sinh OpenAPI. Đổi field ở `schemas.py` → chạy lại
lệnh sinh type → TypeScript **chỉ thẳng ra mọi chỗ frontend phải sửa**. Đây chính là thứ
ngăn tái diễn cảnh "sửa backend, frontend vỡ mà không ai biết".

---

### Phương án 3: Next.js (App Router)

| Tiêu chí | Đánh giá |
|---|---|
| Bảo trì | ✅ Tốt |
| Học | ❌ Phải hiểu server vs client component |
| Debug | 🟡 Lỗi hydration rất khó lần |
| Hiệu năng | ✅ SSR tốt cho SEO |
| Mở rộng | ✅ Tốt |
| Triển khai | ❌ Cần Node server chạy thường trực |
| Hợp đồ án | 🟡 Phức tạp hơn nhu cầu |
| **Rủi ro** | ❌ **Next.js có API routes → rất dễ vô tình tạo backend thứ hai**, đúng cái vừa dọn xong |

**Không khuyến nghị.** Bản đồ bắt buộc là client component nên mất phần lớn lợi thế SSR;
mà lại thêm một runtime server nữa.

---

### Phương án 4: Vue 3 / SvelteKit

Đều tốt về kỹ thuật, nhưng **vứt bỏ toàn bộ code React đang chạy** và phải học lại từ đầu.
Không có lợi ích nào đủ lớn để bù. **Không khuyến nghị.**

---

## PHẦN 3 — Tách Client và Admin thế nào

### Option A — Một app, tách theo route/feature

```
src/features/{search,restaurant,map}/   ← client
src/features/admin/{dashboard,...}/     ← admin
src/app/routes: /  và  /admin/*
```

| Ưu | Nhược |
|---|---|
| Dựng nhanh nhất, 1 lần build, 1 lần deploy | **Code admin bị tải về máy người dùng cuối** (dù có route guard) |
| Chia sẻ component/type tự nhiên | Bundle to hơn cho người dùng thường |
| Chỉ 1 pipeline CI | Ranh giới quyền dễ bị xói mòn theo thời gian |

---

### Option B — Hai app hoàn toàn độc lập

| Ưu | Nhược |
|---|---|
| Tách bạch tuyệt đối, không lộ code admin | **Trùng lặp code** (httpClient, type, UI) |
| Deploy riêng, phân quyền rõ | Sửa 1 lỗi phải sửa 2 nơi |
| Bundle client nhỏ gọn | 2 pipeline CI |

---

### Option C — Monorepo: app riêng + package dùng chung ⭐

```
frontend/
├── packages/
│   ├── api-client/     ← type sinh từ OpenAPI + httpClient  (DÙNG CHUNG)
│   └── ui/             ← Button, Table, Modal               (DÙNG CHUNG)
└── apps/
    ├── client/         ← app người dùng
    └── admin/          ← app quản trị
```

| Ưu | Nhược |
|---|---|
| **Không trùng code** — type và UI viết 1 lần | Cần cấu hình workspace (npm workspaces là đủ) |
| **Không lộ code admin** cho người dùng cuối | Build phức tạp hơn Option A một chút |
| Deploy độc lập, phân quyền rõ ràng | Người mới cần hiểu cấu trúc monorepo |
| Đổi API 1 lần → cả 2 app cùng biết | |
| Dễ trả lời khi bảo vệ: "vì sao tách?" | |

---

### Option D — Admin nhúng vào công cụ có sẵn (Retool/Directus...)

Nhanh nhưng phụ thuộc dịch vụ ngoài và **gần như không có giá trị học thuật**.
Không khuyến nghị cho đồ án tốt nghiệp.

---

## PHẦN 4 — Khuyến nghị

> ### Chọn **Phương án 2 (React + TypeScript + feature-based)** với **Option C (monorepo)**

**Lý do:**

1. **Chống lặp lại sai lầm cũ.** Vấn đề lớn nhất của dự án này từng là hai backend song
   song không ai biết. Monorepo có `packages/api-client` dùng chung là cách cấu trúc
   khiến việc đó **không thể xảy ra** ở frontend.
2. **Type sinh tự động từ OpenAPI.** Backend đã có sẵn. Đây là thứ trực tiếp giải quyết
   yêu cầu *"không muốn một lỗi nhỏ mà phải quét cả dự án"*.
3. **Admin không lộ ra ngoài.** Người dùng cuối không tải về code quản trị.
4. **Nâng cấp dần được.** Frontend hiện tại đã đúng cấu trúc feature-based; chuyển sang
   TypeScript chủ yếu là đổi đuôi file và thêm kiểu, không phải viết lại.

**Lộ trình đề xuất:**

| Giai đoạn | Nội dung | Điều kiện |
|---|---|---|
| **1** | Dựng monorepo + `api-client` + chuyển client hiện tại sang TS | Làm ngay được |
| **2** | Bản đồ Google Maps vào app client | Cần API key |
| **3** | Backend: SQLite + auth + endpoint admin | **Chặn giai đoạn 4** |
| **4** | Dựng app admin | Sau giai đoạn 3 |

**Điểm bắt đầu:** giai đoạn 1 — cụ thể là `packages/api-client` sinh từ OpenAPI, vì mọi
thứ khác đều phụ thuộc vào nó.

---

## Câu hỏi cần bạn quyết

1. **Công nghệ:** Phương án 1 / 2 / 3 / 4?
2. **Tách Client-Admin:** Option A / B / C / D?
3. **Admin:** có đồng ý chuyển sang SQLite + thêm auth trước không? (bắt buộc để làm Admin)

Trả lời xong tôi mới bắt đầu code frontend.

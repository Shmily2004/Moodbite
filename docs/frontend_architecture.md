# Kiến trúc Frontend MoodBite — giải thích đầy đủ

**Cập nhật:** 2026-08-17 · **Trạng thái:** đang chạy, đã kiểm chứng bằng `python scripts/verify.py`

> Bản cũ (frontend JavaScript, "Phương án A") nằm ở
> `archive/frontend-v1/frontend_architecture_v1.md`. Giữ lại để biết vì sao hồi đó chọn
> JavaScript — **không còn mô tả đúng code hiện tại**.

---

## 0. Trả lời trong 30 giây

Câu hỏi hay gặp nhất: *"Frontend này có đủ Model — View — Controller không?"*

**CÓ ĐỦ CẢ BA.** Chỉ là ba tầng đó **nằm vắt qua ranh giới HTTP**, chứ không nằm gọn
trong một thư mục:

| Thuật ngữ cổ điển | Trong MoodBite nó là gì | File thật |
|---|---|---|
| **Model** (nghiệp vụ) | Backend Clean Architecture | `src/domain/`, `src/application/` |
| **Data Access** | Repository sau Port | `src/infrastructure/repositories/` |
| **Controller** | Hook React (ViewModel) | `features/*/model/use*.ts` |
| **View** | Component React | `features/*/ui/*.tsx`, `widgets/`, `pages/` |

React không có Controller kiểu MVC server-render (nơi Controller nhận HTTP request rồi
render HTML). Trong React, vai trò đó do **hook** đảm nhiệm: nó nhận sự kiện từ View,
gọi API, giữ state, rồi đưa dữ liệu ngược lại cho View. Đây là **lựa chọn có chủ đích**,
không phải thiếu sót — và nó có tên riêng: **MVVM** (Model–View–ViewModel).

Vì thế frontend dùng **FSD + MVVM**, backend dùng **Clean Architecture**. Hai kiến trúc
khác nhau vì hai bài toán khác nhau, nhưng **chung một nguyên tắc gốc: phụ thuộc chỉ đi
MỘT CHIỀU và phải cưỡng chế được bằng máy.**

---

## 1. Sơ đồ tổng thể

```
        NGƯỜI DÙNG gõ "quán yên tĩnh để làm việc" rồi bấm Tìm
                              │
╔═════════════════════════════▼═══════════════════════════════════════════╗
║  FRONTEND — React + TypeScript          Kiến trúc: FSD + MVVM           ║
║  Việc: TRÌNH BÀY + TƯƠNG TÁC. KHÔNG có quy tắc nghiệp vụ.               ║
║                                                                          ║
║   app/       khởi tạo, layout          ← App.tsx                        ║
║     │                                                                    ║
║   pages/     một route = một page      ← SearchPage.tsx  [ghép mọi thứ] ║
║     │                                                                    ║
║   widgets/   khối UI ghép sẵn          ← RestaurantList, RestaurantMap  ║
║     │                                                                    ║
║   features/  MỘT hành động người dùng                                   ║
║     │        ├── ui/     VIEW      chỉ JSX, không gọi API               ║
║     │        └── model/  VIEWMODEL hook: state + điều phối  ★CONTROLLER ║
║     │                                                                    ║
║   entities/  khái niệm nghiệp vụ       ← restaurant (card + format)     ║
║     │                                                                    ║
║   shared/    api client, config, lib   ← nơi duy nhất biết URL backend  ║
╚═════════════════════════════│═══════════════════════════════════════════╝
                              │  HTTP  POST /api/v1/search   (JSON)
                              │  envelope {"data": …} / {"error": …}
╔═════════════════════════════▼═══════════════════════════════════════════╗
║  BACKEND — Python + FastAPI            Kiến trúc: Clean Architecture     ║
║  Việc: NGHIỆP VỤ + DỮ LIỆU. Đây là nơi DUY NHẤT có quy tắc nghiệp vụ.   ║
║                                                                          ║
║   presentation/  router, schema, mã lỗi                                 ║
║          │                                                               ║
║   application/   use case (điều phối)                                   ║
║          │                                                               ║
║   domain/        ★ CÔNG THỨC XẾP HẠNG, bảng điểm mood, suy luận món     ║
║          ▲                                                               ║
║   infrastructure/ repository CSV/SQLite, TF-IDF, thời tiết               ║
╚══════════════════════════════════════════════════════════════════════════╝
```

**Luật import ở frontend: CHỈ ĐƯỢC ĐI XUỐNG.**
`app → pages → widgets → features → entities → shared`

Cấm đi ngược lên. Cấm import ngang giữa hai feature. Vi phạm là **CI đỏ** —
`npx steiger ./apps/client/src` kiểm tự động, đây là bản tương đương của
`scripts/check_architecture.py` bên backend.

---

## 2. Sáu tầng FSD — mỗi tầng làm gì

Đọc từ **dưới lên** sẽ dễ hiểu hơn, vì tầng dưới không biết gì về tầng trên.

### `shared/` — thứ mà ai cũng dùng được, không thuộc về nghiệp vụ nào

```
shared/
├── api/index.ts        dựng API client từ package dùng chung
├── config/env.ts       URL backend, bán kính mặc định, số kết quả
└── lib/session.ts      sinh & nhớ session_id (UUID) cho ghi tương tác
```

Không biết "nhà hàng" là gì. Đổi toàn bộ nghiệp vụ đi thì tầng này vẫn dùng lại được.

### `entities/` — khái niệm nghiệp vụ, ở đây là "nhà hàng"

```
entities/restaurant/
├── model/format.ts          quy tắc HIỂN THỊ (không phải nghiệp vụ!)
└── ui/RestaurantCard.tsx    một thẻ quán trông thế nào
```

⚠️ **Chỗ dễ hiểu nhầm nhất của cả dự án.** `format.ts` chứa những hàm như
`formatDistance`, `formatRating`, `describeDishConfidence`. Trông giống business logic
nhưng **không phải**. Phân biệt:

| Đây là HIỂN THỊ (được để frontend) | Đây là NGHIỆP VỤ (bắt buộc ở backend) |
|---|---|
| 1500 m → `"1.5 km"` | Quán cách bao xa thì bị loại khỏi kết quả |
| `rating = null` → `"chưa có đánh giá"` | Rating chiếm bao nhiêu % điểm xếp hạng |
| `"specific"` → `"khớp loại hình cụ thể"` | Món nào được suy ra từ tên quán nào |
| `null` → `"Đang cập nhật"` | Quán chưa phân cụm được chấm bao nhiêu điểm |

**Cách tự kiểm:** hỏi *"đổi dòng này thì THỨ TỰ kết quả có đổi không?"*
Đổi thứ tự → nghiệp vụ → phải ở backend. Chỉ đổi chữ trên màn hình → hiển thị → ở đây.

### `features/` — MỘT hành động của người dùng = MỘT feature

```
features/
├── search-restaurants/       "tôi muốn tìm quán"
│   ├── model/useSearch.ts    ★ VIEWMODEL — state, gọi API, xử lý lỗi
│   └── ui/SearchForm.tsx       VIEW — chỉ JSX, nhận mọi thứ qua props
├── pick-location/            "lấy vị trí của tôi"
├── view-restaurant-detail/   "xem chi tiết quán này"
└── log-interaction/          "ghi lại là tôi đã bấm vào"
```

Đây là chỗ **MVVM hiện ra rõ nhất**, và là câu trả lời cho "Controller ở đâu":

```
ui/SearchForm.tsx          model/useSearch.ts              Backend
   (VIEW)                    (VIEWMODEL/Controller)
      │                             │                          │
      │ người dùng bấm "Tìm"        │                          │
      ├────────── onSubmit() ──────►│                          │
      │                             │ setLoading(true)          │
      │                             ├──── POST /api/v1/search ─►│
      │                             │                          │ ★ xếp hạng
      │                             │◄──── {data: {results}} ───┤   ở ĐÂY
      │                             │ setResults(...)           │
      │◄──── props: results ────────┤                          │
      │ vẽ lại màn hình             │                          │
```

**Luật cứng:** `ui/` không được `fetch`, không được giữ state phức tạp. `model/` không
được chứa JSX. Tách như vậy thì test được ViewModel mà không cần dựng DOM, và đổi giao
diện không phải đụng vào logic điều phối.

### `widgets/` — khối UI ghép sẵn, dùng lại được

`RestaurantList` (danh sách thẻ quán) và `RestaurantMap` (bản đồ Leaflet). Chúng ghép
nhiều entity lại nhưng **không tự gọi API** — dữ liệu nhận qua props.

### `pages/` — một route = một page

`SearchPage.tsx` là component "thông minh" DUY NHẤT của luồng tìm kiếm: nó gọi các hook,
giữ state điều phối (`openNow`, `showMap`), rồi truyền xuống. Mọi thứ bên dưới nhận props.

### `app/` — khởi tạo

`App.tsx` + `styles.css`. Hiện chỉ có 1 trang nên chưa cần router.

---

## 3. Đi theo MỘT lượt tìm kiếm, qua từng file thật

Người dùng gõ *"quán yên tĩnh để làm việc"* rồi bấm **Tìm**:

| # | File | Việc |
|---|---|---|
| 1 | `features/search-restaurants/ui/SearchForm.tsx` | Bắt sự kiện bấm, gọi `onSubmit()` |
| 2 | `pages/search/ui/SearchPage.tsx` | `runSearch()` → gọi `search.run({ openNow })` |
| 3 | `features/search-restaurants/model/useSearch.ts` | **Huỷ request cũ** (`AbortController`), `setLoading(true)`, gom tham số |
| 4 | `shared/api/index.ts` | Client đã dựng sẵn với `API_BASE` |
| 5 | `packages/api-client/src/endpoints.ts` | Biết đường dẫn `/search` và kiểu dữ liệu |
| 6 | `packages/api-client/src/http.ts` | `fetch`, **bóc envelope `{data}`**, lỗi → `ApiError` |
| 7 | — HTTP — | `POST /api/v1/search` |
| 8 | **Backend `domain/services/search_ranking.py`** | ★ **XẾP HẠNG XẢY RA Ở ĐÂY** |
| 9 | `useSearch.ts` | `setResults(data.results)`, `setWarnings(...)` |
| 10 | `SearchPage.tsx` | Truyền xuống `RestaurantList` / `RestaurantMap` |
| 11 | `entities/restaurant/ui/RestaurantCard.tsx` | Vẽ thẻ, dùng `format.ts` để đổi số thành chữ |

**Điểm cần thấy:** giữa bước 1 và 11 **không có chỗ nào frontend quyết định quán nào
đứng trước quán nào.** Nó chỉ hỏi, rồi vẽ đúng thứ tự backend trả về.

---

## 4. Vì sao business logic KHÔNG được để ở frontend

Đây không phải sở thích. Đây là bài học đã trả giá — chép lại từ `CLAUDE.md` mục 1b:

> Dự án này từng suýt chết vì có HAI nơi chứa nghiệp vụ (hai backend song song nằm xen
> kẽ trong cùng thư mục `src/`). Thêm "business layer" ở frontend là tái phạm đúng sai
> lầm đó — sửa công thức xếp hạng sẽ phải sửa 2 chỗ, và chắc chắn sẽ có lúc quên một chỗ.

Cụ thể, frontend **KHÔNG** được chứa: công thức xếp hạng · bảng điểm mood · quy tắc suy
luận món · ngưỡng lọc · bất kỳ quy tắc nghiệp vụ nào.

Nếu cần bảo vệ điểm này trước hội đồng: **hệ thống có đủ 3 lớp kinh điển**
(Presentation / Business / Data Access), chỉ khác là lớp Business và Data Access nằm ở
tiến trình backend chứ không nằm trong bundle JavaScript. Đây là kiến trúc **client–server
3 lớp tiêu chuẩn**, không phải kiến trúc thiếu tầng.

---

## 5. Muốn sửa gì thì vào đâu

| Muốn làm | Sửa file |
|---|---|
| Đổi cách hiển thị khoảng cách / giá / nhãn tin cậy | `entities/restaurant/model/format.ts` |
| Đổi giao diện thẻ quán | `entities/restaurant/ui/RestaurantCard.tsx` |
| Đổi ô tìm kiếm, thêm bộ lọc mới trên giao diện | `features/search-restaurants/ui/SearchForm.tsx` |
| Đổi cách gọi API khi tìm kiếm | `features/search-restaurants/model/useSearch.ts` |
| Đổi URL backend | `shared/config/env.ts` |
| Thêm endpoint mới | `packages/api-client/src/endpoints.ts` |
| Đổi cách bóc envelope / dịch mã lỗi | `packages/api-client/src/http.ts` |
| **Đổi công thức xếp hạng** | **`src/domain/services/search_ranking.py` (BACKEND)** |
| **Đổi bảng điểm mood** | **`src/domain/value_objects/mood.py` (BACKEND)** |

### Thêm một feature mới — thứ tự bắt buộc

1. Tạo `features/<ten-hanh-dong>/` (tên là **HÀNH ĐỘNG**, không phải danh từ:
   `filter-by-price`, không phải `price`).
2. `model/use<Ten>.ts` — hook giữ state + gọi API.
3. `ui/<Ten>.tsx` — chỉ JSX, nhận props.
4. `index.ts` — chỉ export thứ bên ngoài được dùng (public API của slice).
5. Ghép vào `pages/`.
6. Chạy `npm run lint:arch` để chắc chắn không phá luật import.

---

## 6. Cưỡng chế bằng máy — không dựa vào trí nhớ

| Kiểm | Lệnh | Bắt được gì |
|---|---|---|
| Luật import FSD | `npm run lint:arch` | import ngược lên, import ngang giữa 2 feature |
| Kiểu TypeScript toàn monorepo | `npm run typecheck` | sai tên field API (sau khi `npm run gen:api`) |
| Build | `npm run build` | gồm cả `tsc --noEmit` |
| Test | `npm run test --workspace @moodbite/client` | 21 test |
| **Tất cả, kể cả backend** | **`python scripts/verify.py`** | 8 mục |

### Cơ chế chống "sửa backend, frontend vỡ mà không ai biết"

`packages/api-client/src/schema.d.ts` được **SINH TỰ ĐỘNG** từ OpenAPI của backend —
**không sửa tay**. Khi backend đổi API:

```powershell
# 1. Xuất spec mới (chạy ở thư mục gốc dự án)
python -c "import json; from src.presentation.api.main import create_app; open('frontend/openapi.json','w',encoding='utf-8').write(json.dumps(create_app().openapi(),ensure_ascii=False,indent=2))"

# 2. Sinh lại kiểu
cd frontend
npm run gen:api

# 3. TypeScript chỉ THẲNG ra mọi chỗ phải sửa
npm run typecheck
```

Đây là lý do chọn TypeScript thay vì JavaScript: đổi tên một field ở backend sẽ làm CI
đỏ ngay, thay vì đợi người dùng gặp `undefined` trên màn hình.

---

## 7. Cấu trúc thư mục đầy đủ

```
frontend/                          monorepo npm workspaces
├── tsconfig.base.json             tuỳ chọn TS dùng chung
├── tsconfig.json                  project cho packages/ + file cấu hình gốc
├── steiger.config.ts              luật FSD
├── openapi.json                   spec backend (nguồn để sinh kiểu)
│
├── packages/                      DÙNG CHUNG cho client + admin
│   ├── api-client/src/
│   │   ├── schema.d.ts            SINH TỰ ĐỘNG — không sửa tay
│   │   ├── http.ts                nơi DUY NHẤT biết envelope {data}/{error}
│   │   ├── endpoints.ts           các endpoint, gắn kiểu từ schema
│   │   └── index.ts
│   └── ui/src/index.ts            cố ý còn rỗng — chờ apps/admin
│
└── apps/client/src/
    ├── app/                       App.tsx, styles.css
    ├── pages/search/ui/           SearchPage.tsx      ← component "thông minh"
    ├── widgets/
    │   ├── restaurant-list/ui/    RestaurantList.tsx
    │   └── restaurant-map/ui/     RestaurantMap.tsx   (Leaflet + OpenStreetMap)
    ├── features/
    │   ├── search-restaurants/    model/useSearch.ts ★ + ui/SearchForm.tsx
    │   ├── pick-location/         model/useUserLocation.ts
    │   ├── view-restaurant-detail/model/useRestaurantDetail.ts
    │   └── log-interaction/       model/useInteractionLogger.ts
    ├── entities/restaurant/       model/format.ts ★ + ui/RestaurantCard.tsx
    └── shared/                    api/, config/env.ts, lib/session.ts
```

★ = nên đọc đầu tiên khi quay lại dự án.

---

## 8. Những quyết định đã chốt (đừng đổi nếu chưa bàn lại)

| Quyết định | Lý do |
|---|---|
| FSD + MVVM, **không** phải MVC theo tên thư mục | React không có Controller kiểu server-render; hook đúng là ViewModel |
| Business logic **chỉ** ở backend | Hai nguồn sự thật = sửa 2 chỗ = chắc chắn có lúc quên |
| TypeScript, không phải JavaScript | Đổi field backend → CI đỏ ngay, không đợi người dùng gặp lỗi |
| Monorepo `packages/` + `apps/` | `api-client` sẽ dùng lại nguyên vẹn cho `apps/admin` |
| Leaflet + OpenStreetMap, không Google Maps | Google Maps bắt bật thanh toán mới dùng được; chủ dự án không có thẻ |
| `schema.d.ts` sinh tự động | Ngăn frontend và backend trôi khác nhau |

# Kiến trúc Frontend — đề xuất và so sánh

> ## ✅ ĐÃ CHỌN: **Phương án A** (feature-based, giữ JavaScript) — đã triển khai
>
> Cấu trúc hiện tại nằm ở `frontend/src/` đúng theo mục 3.A. Các lỗi #1-#7 ở mục 1 đã sửa.
> Phần còn lại: bản đồ (mục 6, bước 8) — xem `docs/google_maps_integration.md`.
>
> Tài liệu này giữ nguyên phần so sánh để giải thích **vì sao chọn A**, và để khi nào cần
> nâng lên B (TypeScript) thì đã có sẵn phân tích.

**Trạng thái các lỗi đã nêu ở mục 1:**

| # | Lỗi | Trạng thái |
|---|---|---|
| 1 | 1 file làm 4 việc | ✅ tách thành `SearchPage` / `RestaurantCard` / `useSearch` |
| 2 | Style inline | ✅ chuyển hết sang `styles.css` |
| 3 | Không có tầng model | ✅ `services/moodbiteApi.js` ánh xạ JSON → model |
| 4 | Gọi 2 API tuần tự | ✅ backend gộp còn 1 lượt `/search` |
| 5 | Không huỷ request cũ | ✅ `AbortController` trong `useSearch` |
| 6 | Không test, không TypeScript | 🟡 vẫn chưa có test frontend |
| 7 | Code chết | ✅ đã xoá / chuyển vào `archive/frontend-legacy/` |
| 8 | Điều hướng bằng `useState` | 🟡 chưa cần — hiện chỉ có 1 trang |

---

## 1. Frontend hiện tại đang như thế nào

353 dòng, 7 file:

```
frontend/src/
├── main.jsx                       10 dòng   điểm vào
├── App.jsx                        33 dòng   điều hướng bằng useState('home')
├── styles.css                               CSS rời
├── components/
│   ├── Recommend.jsx               3 dòng   chỉ re-export RecommendView (thừa)
│   ├── RecommendView.jsx         152 dòng   TOÀN BỘ giao diện nằm ở đây
│   └── UploadFloorplan.jsx        98 dòng   tính năng đã tạm dừng, không ai gọi
├── hooks/useRecommend.js          36 dòng   state + gọi API
└── services/recommendationApi.js  21 dòng   fetch
```

**Điểm tốt (giữ lại):** đã tách `services/` (gọi API) và `hooks/` (state) khỏi component —
đây đúng là mầm mống của kiến trúc phân tầng, chỉ chưa làm tới nơi.

**Vấn đề cụ thể:**

| # | Vấn đề | Hệ quả |
|---|---|---|
| 1 | `RecommendView.jsx` làm 4 việc: chọn mood, hiện quán, hiện món, tải chi tiết | Sửa 1 chỗ dễ hỏng 3 chỗ |
| 2 | Style viết inline trong JSX | Không tái sử dụng, không đổi theme được |
| 3 | Không có tầng "model" — component đọc thẳng JSON của API | Backend đổi tên field là vỡ giao diện, không có nơi nào bắt lỗi |
| 4 | `useRecommend` gọi 2 API **tuần tự** | Chậm gấp đôi mức cần thiết |
| 5 | Không huỷ request cũ | Bấm nhanh 2 lần → kết quả cũ ghi đè kết quả mới |
| 6 | Không có test, không có TypeScript | Không có lưới an toàn nào |
| 7 | `Recommend.jsx` chỉ re-export; `UploadFloorplan.jsx` không ai dùng | Code chết gây rối |
| 8 | Điều hướng bằng `useState` | Không có URL riêng, không share link được |

**Lỗi #4 và #5 là lỗi thật, tái hiện được** — không phải chuyện lý thuyết.

---

## 2. Nguyên tắc chung (áp dụng cho mọi phương án)

Đây là cách chiếu 4 tầng của backend sang frontend:

| Backend | Frontend tương ứng | Trách nhiệm |
|---|---|---|
| `domain/` | `src/domain/` | Kiểu dữ liệu + quy tắc hiển thị thuần tuý (định dạng giá, khoảng cách). Không import React |
| `application/` | `src/features/*/hooks` | Điều phối: gọi API, quản lý state |
| `infrastructure/` | `src/services/` | `fetch`, Google Maps, localStorage |
| `presentation/` | `src/components/` | Chỉ hiển thị. Nhận props, trả JSX |

**Bốn luật bắt buộc, không phụ thuộc phương án nào:**

1. **Component không được gọi `fetch` trực tiếp.** Luôn đi qua `services/`.
2. **Phải có tầng mapper** biến JSON của API thành model của frontend. Đây là nơi *duy nhất*
   biết field tên `placeId` — đổi tên field ở backend chỉ phải sửa 1 file.
3. **Component "thông minh" (có state) tách khỏi component "ngu" (chỉ hiển thị).**
   Component ngu dễ test và tái sử dụng.
4. **Mọi lệnh gọi API phải xử lý đủ 3 trạng thái:** đang tải / lỗi / rỗng.
   Hiện tại trạng thái "rỗng" đang bị bỏ quên.

---

## 3. Ba phương án

### Phương án A — Feature-based, giữ JavaScript ⭐ **khuyến nghị**

Giữ React + Vite + JS. Sắp xếp lại theo **tính năng**, thêm tầng model/mapper.

```
frontend/src/
├── domain/
│   ├── mood.js                # 4 mood + nhãn tiếng Việt + emoji
│   └── formatters.js          # formatDistance, formatPrice, formatRating
├── services/
│   ├── httpClient.js          # fetch + timeout + huỷ request + lỗi thống nhất
│   └── moodbiteApi.js         # gọi endpoint, TRẢ VỀ MODEL (không phải JSON thô)
├── features/
│   ├── recommend/
│   │   ├── useRecommend.js        # state + gọi song song 2 API
│   │   ├── MoodPicker.jsx         # component ngu
│   │   ├── RestaurantCard.jsx     # component ngu
│   │   └── RecommendPage.jsx      # component thông minh
│   ├── dishes/
│   │   ├── DishCard.jsx
│   │   └── DishList.jsx
│   └── map/
│       ├── useUserLocation.js     # Geolocation API (miễn phí)
│       └── RestaurantMap.jsx      # Google Maps
├── components/ui/             # Button, Spinner, ErrorMessage, EmptyState
└── styles/                    # CSS Modules hoặc 1 file biến CSS
```

**Ưu điểm**
- Ít rủi ro nhất — không đổi ngôn ngữ, không đổi công cụ build
- Mỗi tính năng nằm gọn 1 thư mục: sửa phần gợi ý món không đụng phần bản đồ
- Chiếu 1-1 sang kiến trúc backend → dễ giải thích khi bảo vệ đồ án
- Làm được trong 1-2 buổi
- Thêm bản đồ chỉ là thêm `features/map/`, không đụng code cũ

**Nhược điểm**
- Không có kiểm tra kiểu → vẫn có thể gõ sai `r.placeid` mà không ai báo
- Mapper phải tự viết tay và tự giữ đồng bộ với backend
- Không tự động bắt được breaking change từ backend

**Phù hợp khi:** muốn sản phẩm chạy tốt, nhanh, không muốn học thêm công cụ mới.

---

### Phương án B — Feature-based + TypeScript

Giống A, nhưng chuyển sang `.ts`/`.tsx` và định nghĩa kiểu cho toàn bộ response API.

```
frontend/src/
├── domain/types.ts        # Restaurant, Dish, Mood — khớp với schemas.py
├── services/moodbiteApi.ts
└── features/...
```

**Ưu điểm**
- Trình soạn thảo bắt lỗi ngay khi gõ sai tên field
- Đổi field ở backend → TypeScript chỉ ra **chính xác** mọi chỗ phải sửa
- Tự động gợi ý code, đọc lại dễ hiểu hơn nhiều
- Có thể **sinh kiểu tự động từ OpenAPI** của FastAPI:
  ```bash
  npx openapi-typescript http://localhost:8001/openapi.json -o src/domain/api-types.ts
  ```
  → hợp đồng frontend/backend **không bao giờ lệch nhau nữa**
- Dự án vốn đã có kinh nghiệm TypeScript (backend TS cũ, nay ở `archive/`)

**Nhược điểm**
- Phải chuyển đổi 353 dòng code hiện có
- Thêm bước build, thêm `tsconfig.json`, dựng lại CI cho frontend
- Lúc đầu hay vướng lỗi kiểu, dễ nản nếu chưa quen
- Chậm hơn A khoảng 1 buổi

**Phù hợp khi:** chấp nhận chậm hơn một chút để đổi lấy an toàn lâu dài, và muốn hợp đồng
API tự đồng bộ.

---

### Phương án C — Next.js (App Router)

Thay Vite bằng Next.js, dùng server component + routing theo thư mục.

**Ưu điểm**
- Routing thật theo URL (`/recommend?mood=sad`) → chia sẻ link được
- SEO tốt (có ý nghĩa nếu sau này muốn Google index các quán)
- Sẵn tối ưu ảnh — hữu ích vì dữ liệu có `imageUrls`
- Có thể gọi API phía server, giấu Google Maps key khỏi trình duyệt

**Nhược điểm**
- **Viết lại gần như toàn bộ frontend**
- Nặng và phức tạp hơn hẳn nhu cầu hiện tại
- Phải học server component vs client component — dễ sai
- Bản đồ Google Maps buộc phải là client component → mất phần lớn lợi thế của Next
- Có 2 "backend" (FastAPI + Next server) → **đúng cái sai vừa mới dọn xong ở backend**
- Triển khai phức tạp hơn nhiều

**Phù hợp khi:** định biến MoodBite thành sản phẩm công khai cần SEO. **Chưa phải lúc này.**

---

## 4. So sánh nhanh

| Tiêu chí | A (JS) | B (TS) | C (Next.js) |
|---|---|---|---|
| Công sức | 1-2 buổi | 2-3 buổi | 1-2 tuần |
| Rủi ro | Thấp | Trung bình | Cao |
| An toàn kiểu dữ liệu | ❌ | ✅ | ✅ |
| Hợp đồng API tự đồng bộ | ❌ | ✅ | ✅ |
| Chia sẻ link được | ❌ | ❌ | ✅ |
| Cần học thêm | Không | Ít | Nhiều |
| Hợp với kiến trúc backend | ✅ | ✅ | 🟡 |
| Dễ thêm bản đồ | ✅ | ✅ | 🟡 |

---

## 5. Khuyến nghị

**Chọn A ngay bây giờ, mở đường sẵn để lên B sau.**

Lý do:
1. Việc gấp nhất là **bản đồ + vị trí thật** — cả 3 phương án đều làm được, nhưng A nhanh nhất.
2. Frontend mới 353 dòng, chuyển sang TypeScript sau này rẻ hơn nhiều so với chuyển bây giờ.
3. Backend vừa dọn xong; ổn định frontend trước rồi hãy đổi ngôn ngữ.
4. Cấu trúc thư mục của A và B **giống hệt nhau** → nâng cấp sau chỉ là đổi đuôi file và
   thêm kiểu, không phải sắp xếp lại.

Nếu ưu tiên "không bao giờ lệch hợp đồng API" hơn tốc độ → chọn **B**, và sinh kiểu tự động
từ `openapi.json`.

**Chưa nên chọn C** cho tới khi thực sự cần SEO hoặc chia sẻ link công khai.

---

## 6. Việc cần làm khi đã chọn (áp dụng cho A hoặc B)

1. Dựng khung thư mục như trên
2. Viết `httpClient` có huỷ request (`AbortController`) — sửa lỗi #5
3. Viết mapper JSON → model — sửa lỗi #3
4. Gọi 2 API **song song** bằng `Promise.all` — sửa lỗi #4
5. Tách `RecommendView.jsx` thành `MoodPicker` + `RestaurantCard` + `DishList` — sửa lỗi #1
6. Xoá `Recommend.jsx`, chuyển `UploadFloorplan.jsx` vào `archive/` — sửa lỗi #7
7. Chuyển style inline sang CSS Modules — sửa lỗi #2
8. Thêm `features/map/` (xem `docs/google_maps_integration.md`)
9. Hiển thị `dish_confidence` để nói thật với người dùng về độ tin cậy của món

---

## 7. Điều tuyệt đối không được làm

- ❌ Gọi `fetch` thẳng trong component
- ❌ Đọc field JSON thô rải rác khắp component (`r.placeId` chỉ được xuất hiện trong mapper)
- ❌ Đặt API key vào code — dùng `.env` với tiền tố `VITE_`
- ❌ Coi `null` là `0` (giá/rating) — `null` nghĩa là **chưa có dữ liệu**
- ❌ Hiện món ăn mà giấu `dish_confidence` — món là suy luận, không phải menu thật

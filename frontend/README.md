# MoodBite Frontend

Monorepo: **React + TypeScript + Feature-Sliced Design**.

## Chạy

```powershell
npm install
npm run dev          # app người dùng  -> http://localhost:5173
```

Backend phải chạy trước ở `http://localhost:8001` (xem README ở gốc dự án).

### Bật trang quản trị

Trang quản trị **fail-closed**: chưa cấu hình thì mọi endpoint `/api/v1/admin/*` trả 503.
Ba bước, chạy ở thư mục gốc dự án:

```powershell
python scripts/build_sqlite.py        # 1. dựng CSDL ghi được (CSV chỉ đọc)
python scripts/make_admin_user.py     # 2. tạo tài khoản admin (bảng users) + ghi secret vào .env.local
$env:MOODBITE_STORAGE = "sqlite"      # 3. bật kho SQLite rồi khởi động lại backend
```

## HAI ỨNG DỤNG, MỘT TẦNG DÙNG CHUNG

Đây là điểm quan trọng nhất của cấu trúc này:

| | `apps/client` | `packages/admin` (khu `/quan-tri`) |
|---|---|---|
| Dành cho | người đi ăn | người quản lý dữ liệu |
| Cổng dev | 5173 | 5173 (cùng app, đường dẫn `/quan-tri`) |
| Đăng nhập | ❌ không có | ✅ đăng nhập chung ở `/login`, admin vào `/quan-tri` (token 1 giờ) |
| Gọi API bằng | `createApi()` | `createAdminApi()` |
| Thấy quán đã ẩn | ❌ không bao giờ | ✅ có, để bỏ ẩn lại được |
| Sửa dữ liệu | ❌ | ✅ tên/loại hình/địa chỉ/giá/điện thoại/website |

**Ranh giới được cưỡng chế bằng KIỂU DỮ LIỆU, không phải bằng lời dặn.**
`createApi()` trả về lớp `MoodbiteApi` — lớp đó **không hề có** method quản trị, nên
`apps/client` không thể gọi nhầm dù muốn. Ngược lại `createAdminApi()` **bắt buộc** phải
truyền hàm lấy token, quên là TypeScript báo lỗi ngay lúc biên dịch.

```
frontend/
├── packages/                    ← DÙNG CHUNG cho cả hai app
│   ├── api-client/src/
│   │   ├── schema.d.ts          SINH TỰ ĐỘNG từ OpenAPI - KHÔNG sửa tay
│   │   ├── http.ts              nơi DUY NHẤT biết envelope {data}/{error}
│   │   ├── endpoints.ts         API của NGƯỜI DÙNG CUỐI
│   │   └── admin.ts             API QUẢN TRỊ - tách hẳn, cần token
│   └── ui/                      component dùng chung (còn rỗng)
└── apps/
    ├── client/src/              app người dùng cuối
    │   ├── app/                 khởi tạo, bố cục
    │   ├── pages/               một route = một page
    │   ├── widgets/             khối UI ghép sẵn
    │   ├── features/            MỘT hành động người dùng = một feature
    │   │   └── <ten>/
    │   │       ├── ui/          VIEW    — chỉ JSX
    │   │       └── model/       VIEWMODEL — hook: state + điều phối
    │   ├── entities/            khái niệm nghiệp vụ (restaurant)
    │   └── shared/              api, lib, config
    └── (packages/admin/src/)    khu quản trị - CÙNG cấu trúc FSD, gắn vào app người dùng ở /quan-tri
        ├── app/                 App.tsx, styles.css (tông màu khác client)
        ├── pages/restaurants/   trang quản lý quán
        ├── features/
        │   ├── admin-login/     đăng nhập
        │   └── manage-restaurants/  sửa, ẩn, bỏ ẩn
        └── shared/              api (createAdminApi), config, lib (lưu token)
```

**Luật import: chỉ đi XUỐNG** `pages → widgets → features → entities → shared`.
Cưỡng chế bằng `npm run lint:arch` (chạy trong CI, kiểm cả hai app).

---

## Layout và route

Cả hai app dùng **react-router v6**. Khung giao diện (header/nav/footer) nằm ở tầng
`app/layout/`, các trang cắm vào qua `<Outlet />` — thêm trang mới KHÔNG phải chép lại khung.

```
apps/<app>/src/app/
├── App.tsx            dựng router, không chứa giao diện
├── routes.tsx         ĐĂNG KÝ ROUTE - nơi duy nhất khai "đường dẫn nào ra trang nào"
└── layout/            khung dùng chung
```

### Cây route

Đối chiếu `apps/*/src/app/routes.tsx` + `apps/*/src/shared/config/routes.ts` ngày 2026-10-06.

**App người dùng (client)** — mọi trang nằm trong `RootLayout`. Đăng nhập là TUỲ CHỌN:
không có route guard chung; riêng trang `/account` tự chuyển về `/login` khi chưa đăng nhập.

| Đường dẫn | Trang | Ghi chú |
|---|---|---|
| `/` | `pages/home` | luồng chính: chọn bộ lọc → lưới MÓN |
| `/dishes/:dishId` | `pages/dish` | giới thiệu món + bản đồ + quán gần đây (tải sau) |
| `/search` | `pages/search` | lối vào thứ hai: tìm quán bằng câu tự do (tải sau) |
| `/recommend` | `pages/recommend` | kết quả gợi ý món, bộ lọc nằm trên query string (tải sau) |
| `/login` | `pages/login` | |
| `/register` | `pages/register` | |
| `/forgot-password` | `pages/forgot-password` | |
| `/reset-password` | `pages/reset-password` | link nằm trong thư — đổi đường dẫn phải đổi cả backend |
| `/verify-email` | `pages/verify-email` | link nằm trong thư — như trên |
| `/account` | `pages/account` | trang tài khoản (tải sau) |
| `*` | `pages/not-found` | |

Đường dẫn CŨ tiếng Việt (`/mon/:dishId`, `/tim-kiem`, `/dang-nhap`, `/dang-ky`,
`/quen-mat-khau`, `/dat-lai-mat-khau`) tự chuyển hướng sang đường mới, giữ nguyên query
string — xem `DUONG_DAN_CU`.

**App quản trị (admin)**

| Đường dẫn | Trang | Ghi chú |
|---|---|---|
| `/login` | `pages/login` | công khai |
| `/` | `pages/overview` | Tổng quan — sau `RequireAuth` → `AdminLayout` (như mọi dòng dưới) |
| `/quan-an` | `pages/restaurants` | danh sách quán |
| `/mon-an` | `pages/dishes` | danh mục món |
| `/mon-an/:dishId` | `pages/dish-detail` | chi tiết một món |
| `/chat-luong` | `pages/quality` | chất lượng dữ liệu |
| `/can-xu-ly` | `pages/issues` | việc cần xử lý |
| `/goi-y` | `pages/recommendation` | năm lớp mô hình |
| `/nhat-ky` | `pages/activity` | nhật ký hoạt động |
| `/cai-dat` | `pages/system` | cấu hình (chỉ đọc) |
| `*` | `pages/not-found` | vẫn trong `AdminLayout` |

Riêng app admin lồng thêm hai lớp:

```
AdminSessionProvider   phiên đăng nhập, dùng chung mọi route
├── /login             công khai
└── RequireAuth        chưa đăng nhập -> đá về /login
    └── AdminLayout    thanh trên + điều hướng + nút đăng xuất
        └── các trang
```

`RequireAuth` đặt ở tầng NGOÀI nên **thêm trang mới là tự động được bảo vệ, không thể
quên** — bản song song của việc backend gắn xác thực ở cấp router.

> ⚠️ `RequireAuth` chỉ là lớp phòng vệ cho trải nghiệm. Chốt chặn THẬT ở backend:
> không có token thì mọi `/api/v1/admin/*` trả 401, dù giao diện vẽ ra gì đi nữa.

### Thêm một trang mới

1. Tạo `pages/<ten-trang>/` gồm `ui/<Ten>Page.tsx` và `index.ts`
2. Thêm đường dẫn vào `shared/config/routes.ts` (cả hai app đều có file này)
3. Thêm một dòng vào `children` trong `app/routes.tsx`
4. Muốn hiện trên thanh điều hướng thì thêm `<NavLink>` vào `AdminLayout` (admin) hoặc
   khung trong `app/layout/` (client)

Hằng số đường dẫn để ở `shared/config/` chứ không ở `app/`, vì cả `app/` lẫn `pages/`
đều cần — mà luật FSD cấm `pages/` import ngược lên `app/`.

## Lệnh

| Lệnh | Việc |
|---|---|
| `npm run dev` | dev server app người dùng (5173) |
| `npm run build` | build CẢ HAI app (đã gồm kiểm kiểu) |
| `npm run typecheck` | kiểm kiểu toàn monorepo |
| `npm run test` | test app người dùng (gồm cả khu quản trị) |
| `npm run lint:arch` | luật import FSD cho CẢ HAI app |
| `npm run gen:api` | **sinh lại kiểu từ OpenAPI** |

## Khi backend đổi API

```powershell
# 1. Xuất spec mới (chạy ở thư mục gốc dự án)
python scripts/export_openapi.py

# 2. Sinh lại kiểu
cd frontend
npm run gen:api

# 3. TypeScript sẽ chỉ THẲNG ra mọi chỗ phải sửa
npm run typecheck
```

Đây là cơ chế ngăn "sửa backend, frontend vỡ mà không ai biết".

## Bản đồ

Dùng **Leaflet + OpenStreetMap** — miễn phí, không cần API key, không cần thẻ thanh toán.
Xem `docs/google_maps_integration.md` để biết vì sao không dùng Google Maps.

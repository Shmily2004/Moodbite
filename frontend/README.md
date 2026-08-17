# MoodBite Frontend

Monorepo: **React + TypeScript + Feature-Sliced Design**.

## Chạy

```powershell
npm install
npm run dev          # app người dùng  -> http://localhost:5173
npm run dev:admin    # app quản trị    -> http://localhost:5174
```

Backend phải chạy trước ở `http://localhost:8001` (xem README ở gốc dự án).

### Bật trang quản trị

Trang quản trị **fail-closed**: chưa cấu hình thì mọi endpoint `/api/v1/admin/*` trả 503.
Ba bước, chạy ở thư mục gốc dự án:

```powershell
python scripts/build_sqlite.py        # 1. dựng CSDL ghi được (CSV chỉ đọc)
python scripts/make_admin_password.py # 2. sinh 3 biến môi trường, làm theo hướng dẫn in ra
$env:MOODBITE_STORAGE = "sqlite"      # 3. bật kho SQLite rồi khởi động lại backend
```

## HAI ỨNG DỤNG, MỘT TẦNG DÙNG CHUNG

Đây là điểm quan trọng nhất của cấu trúc này:

| | `apps/client` | `apps/admin` |
|---|---|---|
| Dành cho | người đi ăn | người quản lý dữ liệu |
| Cổng dev | 5173 | 5174 |
| Đăng nhập | ❌ không có | ✅ 1 tài khoản + token 1 giờ |
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
    └── admin/src/               app quản trị - CÙNG cấu trúc FSD
        ├── app/                 App.tsx, styles.css (tông màu khác client)
        ├── pages/restaurants/   trang quản lý quán
        ├── features/
        │   ├── admin-login/     đăng nhập
        │   └── manage-restaurants/  sửa, ẩn, bỏ ẩn
        └── shared/              api (createAdminApi), config, lib (lưu token)
```

**Luật import: chỉ đi XUỐNG** `pages → widgets → features → entities → shared`.
Cưỡng chế bằng `npx steiger ./apps/client/src` (chạy trong CI).

## Lệnh

| Lệnh | Việc |
|---|---|
| `npm run dev` | dev server app người dùng (5173) |
| `npm run dev:admin` | dev server app quản trị (5174) |
| `npm run build` | build CẢ HAI app (đã gồm kiểm kiểu) |
| `npm run typecheck` | kiểm kiểu toàn monorepo |
| `npm run test` | test app client |
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

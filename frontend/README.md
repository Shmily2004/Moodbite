# MoodBite Frontend

Monorepo: **React + TypeScript + Feature-Sliced Design**.

## Chạy

```powershell
npm install
npm run dev        # http://localhost:5173
```

Backend phải chạy trước ở `http://localhost:8001` (xem README ở gốc dự án).

## Cấu trúc

```
frontend/
├── packages/
│   ├── api-client/    ← DÙNG CHUNG cho client + admin
│   │   └── src/
│   │       ├── schema.d.ts   SINH TỰ ĐỘNG từ OpenAPI - KHÔNG sửa tay
│   │       ├── http.ts       nơi DUY NHẤT biết envelope {data}/{error}
│   │       └── endpoints.ts  các endpoint, gắn kiểu từ schema
│   └── ui/            ← component dùng chung (sẽ dùng khi có admin)
└── apps/
    └── client/src/
        ├── app/        khởi tạo, bố cục
        ├── pages/      một route = một page
        ├── widgets/    khối UI ghép sẵn
        ├── features/   MỘT hành động người dùng = một feature
        │   └── <ten>/
        │       ├── ui/     VIEW    — chỉ JSX
        │       └── model/  VIEWMODEL — hook: state + điều phối
        ├── entities/   khái niệm nghiệp vụ (restaurant)
        └── shared/     api, lib, config
```

**Luật import: chỉ đi XUỐNG** `pages → widgets → features → entities → shared`.
Cưỡng chế bằng `npx steiger ./apps/client/src` (chạy trong CI).

## Lệnh

| Lệnh | Việc |
|---|---|
| `npm run dev` | chạy dev server |
| `npm run build` | kiểm tra kiểu + build |
| `npm run test --workspace @moodbite/client` | chạy test |
| `npm run lint:arch` | kiểm tra luật import FSD |
| `npm run gen:api` | **sinh lại kiểu từ OpenAPI** |

## Khi backend đổi API

```powershell
# 1. Xuất spec mới (chạy ở thư mục gốc dự án)
python -c "import json; from src.presentation.api.main import create_app; open('frontend/openapi.json','w',encoding='utf-8').write(json.dumps(create_app().openapi(),ensure_ascii=False,indent=2))"

# 2. Sinh lại kiểu
cd frontend
npm run gen:api

# 3. TypeScript sẽ chỉ THẲNG ra mọi chỗ phải sửa
npm run build
```

Đây là cơ chế ngăn "sửa backend, frontend vỡ mà không ai biết".

## Bản đồ

Dùng **Leaflet + OpenStreetMap** — miễn phí, không cần API key, không cần thẻ thanh toán.
Xem `docs/google_maps_integration.md` để biết vì sao không dùng Google Maps.

# Frontend v1 (JavaScript, feature-based) — ĐÃ THAY THẾ

Giữ lại để tham khảo. **Không chạy, không khôi phục nếu chưa bàn lại.**

Thay bằng `frontend/apps/client` — TypeScript + Feature-Sliced Design, theo quyết định
kiến trúc ghi ở [`CLAUDE.md`](../../CLAUDE.md) mục 1b.

## Vì sao thay

| v1 (JavaScript) | v2 (TypeScript + FSD) |
|---|---|
| Gõ sai tên field chỉ lộ ra lúc chạy | TypeScript bắt ngay khi gõ |
| Kiểu dữ liệu API tự viết tay, dễ lệch backend | Sinh tự động từ OpenAPI (`npm run gen:api`) |
| 0 test | 21 test |
| Không có công cụ cưỡng chế cấu trúc | `steiger` chạy trong CI |
| Không dùng chung được với app admin | `packages/api-client` dùng chung |

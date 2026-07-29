# API RULES (QUY CHUẨN GIAO TIẾP REST VÀ ĐIỀU PHỐI)

## 1. QUY TẮC KIẾN TRÚC TRONG API (PRESENTATION LAYER)
- **Ranh giới:** REST Controllers chỉ được phép nhận request, gọi Use Case (tầng Application) và trả kết quả[cite: 4, 5].
- **Cấm tuyệt đối:** Controller KHÔNG ĐƯỢC chứa logic nghiệp vụ, logic xếp hạng hoặc xử lý dữ liệu trực tiếp[cite: 4, 5]. Tuyệt đối không gọi thẳng xuống Infrastructure (ví dụ: gọi trực tiếp Repository từ Controller là vi phạm ranh giới)[cite: 2, 4, 5].

## 2. QUY CHUẨN ĐỊNH DẠNG & ĐƯỜNG DẪN
- **Base URL & Versioning:** Mọi endpoint phải có tiền tố version tường minh, bắt đầu bằng `/api/v1`[cite: 2].
- **Định dạng dữ liệu:** Sử dụng JSON (`Content-Type: application/json`) cho cả request và response[cite: 2].
- **Quy ước đặt tên (Naming Convention):** Sử dụng `snake_case` cho tên trường (khớp trực tiếp với tên cột trong DB) để giảm thiểu một tầng ánh xạ DTO thủ công ở quy mô một người phát triển[cite: 2].
- **Thời gian:** Mọi trường thời gian BẮT BUỘC dùng chuẩn ISO-8601 UTC (ví dụ: `2026-07-27T09:00:00Z`). Việc quy đổi múi giờ hiển thị là trách nhiệm của frontend, không phải API[cite: 2].

## 3. CẤU TRÚC PHẢN HỒI (RESPONSE ENVELOPE)
Mọi phản hồi phải được bọc trong một Envelope nhất quán, giúp client xử lý bằng một điều kiện duy nhất (kiểm tra có `error` hay không) thay vì đoán qua HTTP status[cite: 2]:
- **Thành công:** Bọc trong trường `data` (Ví dụ: `{ "data": { ... } }`)[cite: 2].
- **Lỗi:** Bọc trong trường `error` với cấu trúc chuẩn: `{ "error": { "code": "...", "message": "...", "details": { } } }`[cite: 2].

## 4. QUẢN LÝ PHIÊN & BẢO MẬT
- **Không xác thực người dùng (Auth):** Không áp dụng hệ thống tài khoản cá nhân đăng nhập ở Giai đoạn MVP[cite: 2].
- **Định danh phiên (Session):** Sử dụng `session_id` (UUID v4) do client tự sinh, lưu cục bộ và gửi kèm trong mọi request có ghi dữ liệu. Dữ liệu này là ẩn danh và không gắn với thông tin định danh cá nhân[cite: 2].

## 5. MÃ LỖI (ERROR CODES) CHUẨN
Bắt buộc sử dụng các HTTP Status và `error.code` dùng chung sau[cite: 2]:
- `400` - `INVALID_REQUEST`: Thiếu hoặc sai định dạng trường bắt buộc.
- `404` - `RESTAURANT_NOT_FOUND` / `SEARCH_RESULT_ITEM_NOT_FOUND`: Khi ID không tồn tại hoặc dữ liệu đã bị soft-delete (`is_active = false`). Lưu ý trả 404 thay vì 410 để không làm lộ trạng thái nội bộ.
- `503` - `EXTERNAL_SERVICE_UNAVAILABLE`: Khi API bên thứ ba (Maps, Traffic) lỗi và không có fallback.
- `500` - `INTERNAL_ERROR`: Lỗi máy chủ không xác định.
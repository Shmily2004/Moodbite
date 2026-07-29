# DATABASE RULES (QUY TẮC CƠ SỞ DỮ LIỆU)

## 1. CÔNG NGHỆ & LƯU TRỮ
- **Hệ quản trị CSDL:** Bắt buộc sử dụng PostgreSQL[cite: 3].
- **Tìm kiếm ngữ nghĩa:** Sử dụng extension `pgvector` với chuẩn `VECTOR(768)` cho trường `description_embedding` của nhà hàng[cite: 3].
- **Kiểu dữ liệu thời gian:** Mọi mốc thời gian phải dùng `TIMESTAMPTZ` (chuẩn ISO-8601 UTC)[cite: 2, 3]. Việc quy đổi múi giờ chỉ thực hiện ở tầng frontend[cite: 3].

## 2. QUY TẮC SOFT-DELETE (CỰC KỲ QUAN TRỌNG)
- **Tuyệt đối cấm:** KHÔNG BAO GIỜ xóa cứng dữ liệu (`DELETE`) trên các bảng gốc như `restaurants` và `dishes`[cite: 3].
- **Cơ chế:** Sử dụng cờ `is_active = false` kết hợp ghi nhận `deleted_at`[cite: 3].
- **Ràng buộc nhất quán:** Bắt buộc có check constraint `CHECK (deleted_at IS NULL OR is_active = false)` để tránh trạng thái mâu thuẫn[cite: 3].
- **Truy vấn bắt buộc:** MỌI truy vấn phục vụ người dùng cuối (tìm kiếm, chi tiết nhà hàng/món ăn) BẮT BUỘC phải đính kèm điều kiện `WHERE is_active = true`[cite: 3]. Các truy vấn huấn luyện mô hình offline không cần lọc điều kiện này[cite: 3].

## 3. RÀNG BUỘC KHÓA NGOẠI (FOREIGN KEYS)
- **Mặc định:** Sử dụng chiến lược `ON DELETE RESTRICT` cho mọi khóa ngoại để chặn việc xóa cứng ngoài ý muốn và ép hệ thống phải dùng soft-delete[cite: 3].
- **Ngoại lệ:** Chỉ dùng `ON DELETE SET NULL` cho các quan hệ tùy chọn mà việc mất tham chiếu không làm hỏng ý nghĩa bản ghi (ví dụ: `suggested_dish_id` trong `search_result_items`)[cite: 3].
- **Tuyệt đối cấm:** KHÔNG dùng `CASCADE` cho thao tác DELETE ở bất kỳ quan hệ nào trong hệ thống, vì mọi bảng con đều chứa dữ liệu lịch sử/huấn luyện có giá trị[cite: 3].

## 4. QUY TẮC CẬP NHẬT & XỬ LÝ TRÙNG LẶP (UPSERT)
- **Cấm tạo mới nếu đã tồn tại:** Khi crawler thu thập dữ liệu, BẮT BUỘC dùng lệnh UPSERT theo `external_place_id` (với ràng buộc UNIQUE đầy đủ, không dùng partial index). Nếu nhà hàng đã tồn tại (kể cả khi `is_active = false`), chỉ cập nhật thông tin và bật lại `is_active = true`, tuyệt đối không `INSERT` mới[cite: 3].
- **Audit trail:** Khi cập nhật các bảng `restaurants` và `dishes`, bắt buộc ghi nhận nguồn gốc qua trường `updated_by` với các giá trị hợp lệ: `'crawler'`, `'batch_pipeline'`, hoặc `'manual'`[cite: 3].

## 5. PHÂN LOẠI 4 NHÓM DỮ LIỆU
Hệ thống quản lý 4 nhóm dữ liệu với đặc tính vận hành riêng biệt[cite: 3]:
1. **Dữ liệu gốc (Master Data):** `restaurants`, `dishes`, `reviews`. Là nguồn sự thật do crawler ghi chính.
2. **Dữ liệu suy diễn (Derived Data):** `review_summaries` (lưu append-only theo phiên bản), `restaurant_experience_features` (vector đặc trưng đầu vào, chỉ giữ bản mới nhất).
3. **Dữ liệu giao dịch (Transactional):** `search_queries`, `search_result_items`, `interaction_events`. Ghi liên tục (append-only), không sửa/xóa sau khi ghi.
4. **Artifact mô hình & Phiên bản:** `dataset_snapshots`, `cluster_model_versions`, `ranking_model_versions`. Mỗi lần chạy là một bản ghi mới, chỉ bật cờ `is_active = true` cho duy nhất một phiên bản tại một thời điểm.
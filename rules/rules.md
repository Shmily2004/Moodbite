# MOODBITE - ROOT RULES (HIẾN PHÁP DỰ ÁN)

## 1. NGUỒN SỰ THẬT (SOURCE OF TRUTH)
Mọi thiết kế, quyết định kiến trúc và mã nguồn BẮT BUỘC phải tuân thủ tuyệt đối các tài liệu nguồn. Không được phép suy diễn ngoài các tài liệu sau:
- `MoodBite_Kien_Truc_Ky_Thuat`[cite: 4]
- `MoodBite_So_Do_Kien_Truc`[cite: 5]
- `MoodBite_Data_Dictionary_ERD`[cite: 3]
- `MoodBite_ADR_Assumption_Scope`[cite: 1]
- `MoodBite_SRS_v1.2`[cite: 6]
- `MoodBite_WBS_v1.6`[cite: 7]
- `MoodBite_Dac_Ta_API`[cite: 2]

## 2. QUY TRÌNH THỰC THI BẮT BUỘC CHO AI (AI AGENT INSTRUCTIONS)
Bất cứ khi nào Agent nhận lệnh sinh code, phân tích logic, hoặc sửa lỗi, **BẮT BUỘC phải đọc file Rule tương ứng trong thư mục `rules/` TRƯỚC KHI sinh ra bất kỳ dòng code nào**:

- **Cấu trúc 4 lớp & Luồng dữ liệu (Clean Architecture):** -> Yêu cầu đọc `rules/architecture.md`
- **Nghiệp vụ lõi (Entity, Value Object):** -> Yêu cầu đọc `rules/domain.md`
- **Giao thức REST, Endpoint & DTO:** -> Yêu cầu đọc `rules/api.md`
- **PostgreSQL, Schema, Soft-delete & Truy vấn:** -> Yêu cầu đọc `rules/database.md`
- **Thuật toán, Xếp hạng (Heuristic) & Cold Start:** -> Yêu cầu đọc `rules/ranking.md`

## 3. CÁC CHỐT CHẶN KỸ THUẬT TỐI THƯỢNG (BLOCKING GATES)
Agent BẮT BUỘC phải dừng lại (STOP) và báo cáo nếu yêu cầu của người dùng vi phạm một trong các điều sau:

1. **Phá vỡ Hướng phụ thuộc:** Presentation và Infrastructure KHÔNG BAO GIỜ được gọi lẫn nhau. Mọi giao tiếp đi qua Application. Domain không phụ thuộc vào bất kỳ framework nào[cite: 4, 5].
2. **Xóa cứng dữ liệu (Hard Delete):** Mọi thao tác xóa trên các bảng gốc (`restaurants`, `dishes`) BẮT BUỘC phải dùng soft-delete (`is_active = false`). Mọi truy vấn người dùng cuối BẮT BUỘC có `WHERE is_active = true`[cite: 3].
3. **Vi phạm Quy tắc Cold Start (Phụ lục A.12):** Khi một nhà hàng chưa có `experience_cluster_id`, tuyệt đối KHÔNG ĐƯỢC gán giá trị NULL hoặc 0 cho `cluster_score` trong công thức tính toán. Bắt buộc phải dùng "điểm trung bình toàn hệ thống" làm giá trị trung lập[cite: 1, 3].
4. **Sai lệch Phiên bản (Version Drift):** Khi truy vấn cụm (`experience_cluster_id`), bắt buộc phải đối chiếu với `cluster_model_versions` đang active, vì trị số cụm không có ý nghĩa cố định giữa các lần huấn luyện[cite: 3, 4].
5. **Suy diễn Module/Repository ngoài tài liệu:** Không tự ý tạo thêm các lớp như `SearchRepository` hay `InteractionRepository` trừ khi chúng được định nghĩa rõ trong Data Dictionary hoặc sơ đồ kiến trúc[cite: 3, 5].

## 4. NGUYÊN TẮC CHỐNG ẢO GIÁC (ANTI-HALLUCINATION)
- **TỪ CHỐI SUY DIỄN:** Nếu tài liệu nguồn ghi "Ngoài phạm vi" (ví dụ: Tài khoản người dùng, Collaborative Filtering ở Giai đoạn 0-1)[cite: 1], Agent KHÔNG ĐƯỢC tự ý sinh code cho các tính năng này.
- **BÁO CÁO THIẾU SÓT:** Nếu một Use Case cần thiết nhưng chưa được định nghĩa Port/Adapter trong tài liệu kiến trúc, Agent phải lập tức cảnh báo thay vì tự chế ra giải pháp.
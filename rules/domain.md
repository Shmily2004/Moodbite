# DOMAIN RULES (QUY TẮC NGHIỆP VỤ LÕI)

## 1. SỰ THUẦN KHIẾT (PURITY)
- **Độc lập công nghệ:** Lớp Domain chứa các thực thể nghiệp vụ thuần túy và tuyệt đối không phụ thuộc vào bất kỳ framework, thư viện học máy, hay công nghệ web nào[cite: 4]. 
- **Không chứa logic hạ tầng:** Lớp Domain là lớp duy nhất không import bất cứ thứ gì từ ba lớp còn lại[cite: 4]. Tuyệt đối KHÔNG sử dụng các annotation của ORM (ví dụ: `@Entity`, `@Table`, `@Column`) bên trong các lớp Entity của Domain.

## 2. THỰC THỂ (ENTITIES) & ĐỐI TƯỢNG GIÁ TRỊ (VALUE OBJECTS)
- **Entities cốt lõi:** Bao gồm `Restaurant`, `Dish`, `UserContext`, và `ExperienceCluster`[cite: 4].
- **Value Objects:** Các khái niệm như `Location`, `PriceRange`, `ContextVector` được thiết kế dưới dạng Value Objects[cite: 4]. Các tín hiệu ngữ cảnh tại thời điểm tìm kiếm (`ContextSignal`, `ContextVector`, `UserContext`) là dữ liệu tính toán tại runtime, không lưu trữ lâu dài và không cần bảng cơ sở dữ liệu riêng[cite: 3].

## 3. NGUYÊN TẮC MỞ RỘNG (EXTENSIBILITY)
- **Thêm mới, không sửa đổi:** Khi các giai đoạn sau cần thêm dữ liệu (ví dụ: điểm độ ồn, cụm trải nghiệm, nhận xét tổng hợp), trường mới bắt buộc phải được thêm dưới dạng tùy chọn (optional) vào Entity đã có[cite: 4].
- **Bảo toàn cấu trúc cũ:** Tuyệt đối không thay đổi kiểu dữ liệu hay xóa các trường cũ đã được định nghĩa từ các giai đoạn trước[cite: 4]. 
- **Sử dụng Value Object mới:** Nếu một trường thực sự cần đổi kiểu dữ liệu triệt để, phải tạo Value Object mới bọc quanh thay vì sửa trực tiếp trường cũ[cite: 4].
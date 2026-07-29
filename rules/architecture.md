# ARCHITECTURE RULES (QUY TẮC KIẾN TRÚC)

## 1. MÔ HÌNH 4 LỚP (CLEAN ARCHITECTURE)
Hệ thống tuân thủ nghiêm ngặt kiến trúc 4 lớp đồng tâm[cite: 4, 5]:
1. **Domain (Trong cùng):** Chứa các thực thể nghiệp vụ thuần túy (Restaurant, Dish, UserContext). Không phụ thuộc vào bất kỳ framework, công nghệ web hay thư viện học máy nào[cite: 4, 5].
2. **Application:** Chứa Use Cases và Ports (Interfaces). Chỉ gọi vào Port, không biết Port được cài đặt bằng công nghệ gì[cite: 4, 5].
3. **Infrastructure:** Chứa Adapters cài đặt các Port (ví dụ: PostgresRestaurantRepository, SemanticSearchAdapter) và các Batch Jobs (Crawler, KMeansTrainingJob)[cite: 4, 5].
4. **Presentation (Ngoài cùng):** Chứa REST API Controllers và Web UI. Chỉ chứa logic điều phối, không chứa logic nghiệp vụ[cite: 4, 5].

## 2. QUY TẮC PHỤ THUỘC ĐẢO NGƯỢC (DEPENDENCY RULE)
- **Luồng phụ thuộc:** Mọi phụ thuộc mã nguồn CHỈ được phép đi từ ngoài vào trong: `Presentation -> Application -> Domain` và `Infrastructure -> Application`[cite: 4, 5].
- **Cấm tuyệt đối:** Lớp bên trong gọi ngược ra lớp bên ngoài, hoặc `Presentation` gọi thẳng xuống `Infrastructure`[cite: 4, 5]. Lớp Domain là lớp duy nhất không import bất cứ thứ gì từ 3 lớp còn lại[cite: 4].

## 3. PORTS & ADAPTERS (ANTI-CORRUPTION LAYER)
- **Thiết kế Port:** Chữ ký của Port phải sử dụng ngôn ngữ nghiệp vụ, TUYỆT ĐỐI KHÔNG rò rỉ chi tiết công nghệ (ví dụ: không truyền tham số riêng của CSDL vector vào `ISearchPort`)[cite: 4].
- **Vai trò Adapter:** Đóng vai trò lớp chống tham nhũng (Anti-Corruption Layer), tự dịch ngôn ngữ nghiệp vụ sang chi tiết kỹ thuật bên trong, bảo vệ Use Case khỏi thay đổi công nghệ[cite: 4].

## 4. CẤU HÌNH VÀ DEPENDENCY INJECTION (DI)
- Việc quyết định sử dụng Adapter nào cho Port tương ứng CHỈ được thực hiện tại một nơi duy nhất: `config/di_container` khi khởi động ứng dụng[cite: 4, 5].
- Các thông tin cấu hình nhạy cảm (chuỗi kết nối DB, API Keys) chỉ được đọc tại `di_container` và truyền vào Adapter qua Constructor Injection[cite: 4]. Adapter không tự đọc file cấu hình hay hardcode thông tin này[cite: 4].

## 5. NGUYÊN TẮC BẢO TOÀN QUA CÁC GIAI ĐOẠN (PHASES)
- **Mở rộng thay vì sửa đổi:** Khi thêm tính năng ở giai đoạn sau, CHỈ viết thêm Adapter mới để cài đặt Port cũ, tuyệt đối không sửa đổi chữ ký của Port đã có[cite: 4].
- **Giữ lại Adapter cũ:** Các Adapter của Giai đoạn 0 (ví dụ `HeuristicRankingAdapter`, `CsvRestaurantRepository`) phải được giữ lại trong mã nguồn làm phương án dự phòng/rollback, không được xóa bỏ[cite: 4].

## 6. TÁCH BIỆT OFFLINE VÀ ONLINE (RUNTIME)
- Các tác vụ nặng như cào dữ liệu (Crawling) hay huấn luyện mô hình phân cụm (KMeans) là các batch job chạy offline hoàn toàn độc lập, ghi kết quả trực tiếp vào DB[cite: 1, 4, 5].
- Luồng Runtime (phục vụ API người dùng cuối) không bao giờ gọi các tác vụ huấn luyện này. Nó chỉ đọc các kết quả đã được tính toán sẵn (ví dụ: đọc `experience_cluster_id` trực tiếp từ Entity)[cite: 1, 4, 5].
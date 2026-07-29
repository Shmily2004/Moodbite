# Ranking Rules

Add ranking-related rules here.
# RANKING & ALGORITHM RULES (QUY TẮC XẾP HẠNG VÀ THUẬT TOÁN)

## 1. THUẬT TOÁN GIAI ĐOẠN 0-1 (HEURISTIC)
- **Công nghệ:** Sử dụng `HeuristicRankingAdapter` với công thức cộng có trọng số (dựa trên khoảng cách, mức giá, rating, và ngữ cảnh)[cite: 1, 4].
- **Cấm tuyệt đối:** KHÔNG được phép sử dụng bất kỳ thư viện Machine Learning nào (như scikit-learn, TensorFlow) hoặc mô hình học có giám sát trong Giai đoạn 0 và 1[cite: 1, 4].

## 2. QUY TẮC COLD START (RẤT QUAN TRỌNG)
Nhà hàng mới chưa được phân cụm (ví dụ: `experience_cluster_id IS NULL`) phải tuân thủ nghiêm ngặt quy tắc sau để không bị chìm nghỉm[cite: 3, 4]:
- **Cấm truyền NULL hoặc 0:** Tuyệt đối KHÔNG được coi giá trị NULL này là 0 hay để nó lan truyền làm hỏng công thức tính điểm (predicted_score = NULL)[cite: 3].
- **Quy tắc thay thế:** BẮT BUỘC thay thế `cluster_score` bằng **điểm trung bình toàn hệ thống** (giá trị trung lập) trong công thức tính toán[cite: 3]. 

## 3. TRÁNH RÒ RỈ DỮ LIỆU (DATA LEAKAGE)
- **Tách biệt tập dữ liệu:** Quá trình tinh chỉnh (tuning) các trọng số (w1, w2...) BẮT BUỘC phải thực hiện trên tập `Development Set`[cite: 4].
- **Bảo vệ Evaluation Set:** Tập `Evaluation Set` tuyệt đối chỉ được dùng để đánh giá chính thức một lần cuối cùng. Tuyệt đối không dựa vào kết quả của `Evaluation Set` để quay lại điều chỉnh trọng số thuật toán[cite: 4].

## 4. QUY TẮC LỌC KHI XẾP HẠNG MÓN ĂN (DISH RECOMMENDATION)
- Pipeline đề xuất món ăn BẮT BUỘC phải lọc điều kiện `is_active = true` trên tập ứng viên **TRƯỚC KHI** đưa vào bước xếp hạng[cite: 3]. 
- **Tuyệt đối cấm:** Lọc sau khi đã xếp hạng, vì mô hình có thể chấm điểm cao cho một món đã ngừng bán rồi mới loại bỏ nó, làm sai lệch danh sách Top K[cite: 3].

## 5. ĐIỀU KIỆN NÂNG CẤP HỌC MÁY (ML RANKING)
Giai đoạn 3 chỉ được chuyển sang mô hình học có giám sát (`MLRankingAdapter`) khi và chỉ khi thỏa mãn đồng thời[cite: 1]:
1. Đã tích lũy đủ tối thiểu 5.000 `InteractionEvent` hợp lệ[cite: 1].
2. `MLRankingAdapter` phải vượt `HeuristicRankingAdapter` về chỉ số Precision@5 trên cùng một `Evaluation Set`[cite: 1].
- **Cơ chế thay thế:** Nếu đạt, chỉ thay đổi cấu hình DI để trỏ về `MLRankingAdapter`, tuyệt đối không sửa đổi mã nguồn của `HeuristicRankingAdapter` (để dùng làm fallback)[cite: 4].
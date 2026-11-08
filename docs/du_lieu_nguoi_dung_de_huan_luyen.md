# Dữ liệu người dùng để huấn luyện mô hình — khảo sát 2026-11-07

**Câu hỏi:** lấy dữ liệu *người dùng* (ai chọn quán/món nào, trong ngữ cảnh nào) ở đâu để
huấn luyện Lớp 3 (xếp hạng quán) và Lớp 5 (gợi ý món)?

## 1. Hiện trạng trong repo (đo 2026-11-07)

| Nguồn | Số bản ghi | Dùng được để huấn luyện? |
|---|---|---|
| `data_pipeline/data_cleaned/interactions.jsonl` (THẬT) | **6 dòng**, phần lớn do kiểm thử (`session_id` = `t`, `kiem-thu`) | Không |
| `data_pipeline/data_synthetic/` (GIẢ LẬP, `scripts/gia_lap_nguoi_dung.py`) | 3.574 tương tác, 1.984 phiên | Chỉ để thử quy trình. Nhãn sinh từ `persona.restaurant_utility` (khoảng cách + khẩu vị + rating + giá), nên mô hình học trên đó sẽ học lại đúng công thức giả lập |
| Lượt hiển thị (impression) | **Không ghi** | Đây là chỗ chặn, xem mục 4 |

## 2. Bộ dữ liệu công khai có thể dùng

Chia theo mục đích. **Không bộ nào thay được dữ liệu người dùng MoodBite thật**: khác thành
phố, khác thời kỳ, khác giao diện. Dùng chúng để *(a)* thử và chọn thuật toán, *(b)* tiền
huấn luyện / so sánh, *(c)* viết phần thực nghiệm trong báo cáo.

### 2a. Xếp hạng quán có ngữ cảnh (Lớp 3)

| Bộ dữ liệu | Có gì | Giấy phép / điều kiện | Hợp với MoodBite ở điểm nào |
|---|---|---|---|
| **Google Local Reviews** (McAuley Lab, UCSD) | 11,4 triệu review · 4,5 triệu user · 3,1 triệu địa điểm toàn cầu; có GPS, giờ mở cửa, category, user_id, thời gian | Không ghi giấy phép; yêu cầu trích dẫn 2 bài (He, Kang, McAuley RecSys 2017; Pasricha & McAuley RecSys 2018). Dữ liệu cũ (thời Google+, khoảng 2014). Host cũ `jmcauley.ucsd.edu` đã chết, bản đang chạy ở `mcauleylab.ucsd.edu/public_datasets/data/googlelocal/` | **Có thể chứa quán ở Hà Nội.** Số đo: xem mục 3 |
| **Yelp Open Dataset** | Doanh nghiệp + review + user + check-in, một số thành phố Bắc Mỹ | Chỉ dùng học thuật / phi thương mại, phải đồng ý Dataset Agreement của Yelp, không được phân phối lại | Bộ chuẩn nhất để thử LTR, ngữ cảnh thời gian, cold start. Không có Việt Nam |
| **UCI Restaurant & Consumer Data** | 138 user, ~1.161 rating; **có hồ sơ người dùng** (ngân sách, hút thuốc, đồ uống, ẩm thực ưa thích) và thuộc tính quán | **CC BY 4.0** (DOI 10.24432/C5DP41) | Nhỏ nhưng sạch, giấy phép rõ, đúng bài toán *context-aware restaurant recommendation*. Hợp để minh hoạ trong báo cáo |
| **Foursquare Global-scale Check-in** (Dingqi Yang, TIST 2015) | 33 triệu check-in · 267 nghìn user · 415 thành phố / 77 nước (2012–2013); bản mở rộng LBSN2Vec++ có thêm mạng bạn bè | Bản LBSN2Vec++ trên 4TU: **CC BY 4.0**; bản gốc: yêu cầu trích dẫn | Có giờ check-in nên học được tín hiệu "giờ ăn". **Chưa kiểm chứng có Hà Nội không** (phải tải 775 MB) |

### 2b. Gợi ý món / đơn hàng đồ ăn (Lớp 5)

| Bộ dữ liệu | Có gì | Giấy phép | Ghi chú |
|---|---|---|---|
| **Delivery Hero Recommendation Dataset (DHRD)**, RecSys 2023 | Hơn 1 triệu đơn giao đồ ăn thật ở 3 thành phố (các bài sau dùng tập Singapore, Stockholm), có vendor, sản phẩm, thời gian, vị trí | **MIT** (theo README GitHub `deliveryhero/dh-reco-dataset`) | Gần nhất với "người dùng chọn món gì, lúc nào, ở đâu". Có tập Singapore ở Đông Nam Á. Các con số kích thước giữa các nguồn chưa khớp nhau, cần đọc README khi tải |

### 2c. Review tiếng Việt (Lớp 4, không phải dữ liệu hành vi)

| Bộ dữ liệu | Có gì | Điều kiện |
|---|---|---|
| **VLSP 2018 ABSA — miền nhà hàng** | Review nhà hàng tiếng Việt gán nhãn khía cạnh (FOOD#QUALITY, SERVICE#GENERAL, RESTAURANT#PRICES…) và cảm xúc | Dùng cho nghiên cứu, đăng ký qua vlsp.org.vn/resources |

### 2d. Không dùng

ShopeeFood, Foody, GrabFood, TripAdvisor, Facebook: ToS cấm thu thập tự động (CLAUDE.md mục 4b).
Áp dụng cả với các bộ "đã có người cào sẵn" đăng trên Kaggle/GitHub: nguồn gốc vẫn là vi
phạm ToS, nên không đưa vào đồ án tốt nghiệp.

## 3. Đo thật: Google Local có bao nhiêu địa điểm ở Hà Nội?

Script đọc luồng `places.clean.json.gz` (277 MB), đếm địa điểm nằm trong bbox Hà Nội của dự án
(lat 20,72–21,41; lng 105,41–106,06).

| Đại lượng | Giá trị |
|---|---|
| Tổng địa điểm trong file | 3.114.353 |
| Nằm trong bbox Hà Nội | **2.787** (0,09%) |
| Có `categories` | **0 / 2.787** |
| Ví dụ | Hanoi Posh Hotel, Bibo Mart Nguyễn Văn Cừ, tiệm tóc Hàng Tre, Hanoitour Taxi, Trung tâm HL thể thao Nhổn |

**Kết luận: giá trị thấp cho MoodBite.** 2.787 địa điểm đủ mọi loại hình (khách sạn, siêu
thị, dịch vụ), không có category để lọc ra quán ăn. Muốn biết bao nhiêu quán ăn, bao nhiêu
review và user thì phải khớp tên/toạ độ với dataset 52.871 quán, rồi tải thêm
`reviews.clean.json.gz` (1,4 GB). **Chưa làm.** Thêm vào đó, dữ liệu là của thời Google+
(khoảng 2014), cũ hơn dataset hiện tại gần 12 năm. Chỉ nên làm tiếp nếu muốn có một con số
"thử nghiệm trên dữ liệu thật ở Hà Nội" cho báo cáo, và chấp nhận mẫu nhỏ.

## 4. Việc phải làm TRƯỚC khi thu dữ liệu người dùng thật

Thứ tự quan trọng. Bước 1 và 2 không làm thì mọi tương tác thu được đều phí.

1. **Ghi lượt hiển thị (impression log).** Mỗi lần `/search` hoặc `/dishes/{id}/restaurants`
   trả kết quả, ghi một bản: `search_query_id`, thời điểm, ngữ cảnh (giờ ăn, thời tiết),
   vị trí đã làm tròn, và **danh sách quán theo thứ hạng kèm các điểm thành phần**
   (`text_score`, `semantic_score`, `mood_score`, `cluster_score`, khoảng cách, rating).
   Đây chính là ma trận đặc trưng cho LTR; mẫu âm = quán đã hiện mà không bấm.
   ⚠️ Thay đổi lược đồ dữ liệu, cần chủ dự án duyệt. Cần tính dung lượng (10 quán × ~10 số
   mỗi lượt) và quyền riêng tư (làm tròn toạ độ, không lưu IP).
2. **Siết kiểm hợp lệ cho nhãn:** trần cho `dwell_time_ms`, `max_length` cho `session_id`,
   đối chiếu `search_query_id` với impression đã ghi.
3. **Sửa giới hạn tần suất khi chạy sau proxy / chung Wi-Fi** (`--proxy-headers`), nếu
   không thì buổi mời người thử sẽ hỏng ở bước đăng ký (QA Q2).
4. **Mời 20–30 người dùng thử**, mỗi người 15 phút, theo kịch bản có nhiệm vụ cụ thể (ví dụ
   "tìm chỗ ăn tối trời mưa gần trường"). Mục tiêu ≥ 500 tương tác thật (PROJECT_CHECKLIST).
5. **Huấn luyện:** chia train/test theo PHIÊN (không chia theo dòng, tránh rò rỉ), mô hình
   nhẹ (Logistic Regression → LightGBM LambdaMART), so với công thức trọng số hiện tại bằng
   NDCG@10. Hiệu chỉnh thiên lệch vị trí (người dùng hay bấm hạng 1 bất kể quán nào).

## Nguồn

- Delivery Hero DHRD: https://github.com/deliveryhero/dh-reco-dataset · https://arxiv.org/pdf/2402.14440
- Google Local: https://mcauleylab.ucsd.edu/public_datasets/data/datasets.html
- UCI Restaurant & consumer data: https://archive.ics.uci.edu/dataset/232/restaurant+consumer+data
- Foursquare (Dingqi Yang): https://sites.google.com/site/yangdingqi/home/foursquare-dataset · https://doi.org/10.4121/15112308
- Yelp Open Dataset: https://www.yelp.com/dataset (điều khoản: Dataset User Agreement)
- VLSP 2018 ABSA: https://vlsp.org.vn/resources · https://github.com/ds4v/absa-vlsp-2018

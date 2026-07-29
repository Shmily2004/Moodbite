# MoodBite_WBS_v1.6

TÀI LIỆU CẤU TRÚC PHÂN RÃ CÔNG VIỆC

(Work Breakdown Structure – WBS)

MoodBite

Nền tảng Web Gợi ý Nhà hàng & Món ăn theo Ngữ cảnh Thời gian thực

Phiên bản 1.6

Ngày ban hành: 22/07/2026 (cập nhật v1.6 — bổ sung Intra-List Diversity@5 vào tiêu chí M2)

Tài liệu nguồn: MoodBite – Đề án ý tưởng (v1) & Tài liệu Đặc tả Yêu cầu Phần mềm (SRS v1.2)

Mục lục

1. Giới thiệu

1.1. Mục đích tài liệu

Tài liệu này phân rã toàn bộ phạm vi công việc cần thực hiện để xây dựng MoodBite thành các gói công việc (work package) cụ thể, có thể giao việc, ước lượng và theo dõi tiến độ. Cấu trúc phân rã bám sát hai tài liệu nguồn: “MoodBite – Đề án ý tưởng” (định hướng kiến trúc/sản phẩm) và “Tài liệu Đặc tả Yêu cầu Phần mềm – SRS v1.2” (các yêu cầu chức năng FR và phi chức năng NFR chi tiết). Mỗi gói công việc trong WBS được truy vết ngược về đúng mã FR/NFR tương ứng, đảm bảo không có yêu cầu nào trong SRS bị bỏ sót khi lập kế hoạch, và không có công việc nào trong kế hoạch nằm ngoài phạm vi đã đặc tả. Phiên bản 1.2 này tiếp thu phản biện từ hai lượt rà soát độc lập và áp dụng trực tiếp vào cấu trúc: bổ sung bước phân tích khám phá dữ liệu (EDA) và tạo tập nhãn thủ công phục vụ đánh giá mô hình (mục 2.2), gắn nhãn hạng mục bàn giao (deliverable) tiếng Anh cho từng nhóm cấp 1 để đúng bản chất deliverable-based WBS, đổi tên hạng mục lịch chạy batch thành điều phối luồng dữ liệu (mục 2.7), bổ sung công cụ quản lý phiên bản dữ liệu/mô hình vào 1.2, và chèn các mốc dự phòng lặp lại (buffer) trực tiếp vào lộ trình tuần tự thay vì chỉ cộng thêm phần trăm vào tổng effort (mục 4).

1.2. Nguyên tắc phân rã

Phân rã theo chức năng/mô-đun, bám theo đúng các nhóm mô-đun đã dùng trong SRS (mục 3.1–3.9), để một người đọc cả hai tài liệu có thể đối chiếu trực tiếp mà không cần học một cách tổ chức mới. Mỗi nhóm cấp 1 tương ứng một hạng mục bàn giao (deliverable) cụ thể — tên tiếng Anh trong ngoặc ở tiêu đề mỗi nhóm (ví dụ “Offline Data Pipeline”, “Recommendation Engine”) thể hiện đúng gói bàn giao đó, còn các dòng bên trong là các công việc/artifact cụ thể để tạo ra bàn giao ấy — không phải một danh sách việc rời rạc không có sản phẩm đầu ra.

Mỗi gói công việc (work package) ở cấp thấp nhất được viết ở mức đủ nhỏ để một cá nhân/cặp có thể đảm nhiệm và báo cáo hoàn thành trong vài ngày đến khoảng một tuần.

Mức ưu tiên của từng gói công việc kế thừa trực tiếp từ phân loại MoSCoW ở SRS mục 8, không đánh giá lại — đảm bảo kế hoạch triển khai nhất quán với phạm vi MVP đã thống nhất.

Cột “Effort*” là ước lượng số ngày công tham khảo cho một cá nhân có kinh nghiệm trung bình, phục vụ lập lịch sơ bộ ở quy mô đồ án/dự án nhỏ; cần hiệu chỉnh lại theo năng lực thực tế của nhóm thực hiện.

Cột “Phụ thuộc” liệt kê các mã công việc cần hoàn thành trước (hoặc hoàn thành song song có điều phối) — dùng làm cơ sở sắp lịch, không hàm ý thứ tự thực hiện tuyệt đối trong mọi trường hợp.

1.3. Cách đọc bảng phân rã

Mỗi nhóm công việc lớn (cấp 1) tương ứng một chương trong SRS mục 3, được đánh số 1–8. Trong mỗi nhóm, các gói công việc cấp 2 được đánh số dạng X.Y (ví dụ 2.5). Bảng liệt kê đầy đủ 7 cột: mã, tên công việc, đầu ra chính (deliverable), FR/NFR liên quan trong SRS, mức ưu tiên MoSCoW, effort ước tính, và các công việc phụ thuộc trước.

2. Cấu trúc phân rã công việc

2.1. Nhóm 1 — Quản lý & Khởi tạo dự án (Project Setup)

Mã

Công việc

Đầu ra chính

FR/NFR liên quan

Ưu tiên

Effort*

Phụ thuộc

1.1

Lập kế hoạch cá nhân (lịch làm việc, mốc kiểm tra)

Kế hoạch dự án, lộ trình tuần tự (mục 4)

—

Bắt buộc

3

—

1.2

Thiết lập môi trường phát triển & quản lý phiên bản

Repository, quy ước code, pipeline CI cơ bản, công cụ versioning cho dữ liệu/mô hình (ví dụ DVC) để đảm bảo khả năng tái lập thực nghiệm

NFR-5

Bắt buộc

4

1.1

1.3

Thiết kế kiến trúc hệ thống tổng thể

Sơ đồ kiến trúc 5 lớp, tài liệu thiết kế hệ thống

SRS mục 2–3

Bắt buộc

4

1.1

1.4

Thiết kế cơ sở dữ liệu chi tiết + ghi chú thiết kế kỹ thuật

ERD chi tiết, script khởi tạo CSDL, ghi chú thiết kế module/API gộp chung (thay cho một tài liệu SDD riêng)

SRS mục 6

Bắt buộc

5

1.3

2.2. Nhóm 2 — Thu thập & Xử lý dữ liệu (Offline Data Pipeline)

Tương ứng mô-đun 3.7 trong SRS. Đây là nhóm công việc nền tảng — hầu hết các nhóm 3, 4 phía sau đều phụ thuộc vào dữ liệu đã qua xử lý của nhóm này. Không có gói riêng cho “trang quản trị dữ liệu” (FR-7.5): với một người vận hành, việc theo dõi/can thiệp dữ liệu thực hiện trực tiếp qua công cụ quản trị cơ sở dữ liệu có sẵn (ví dụ pgAdmin) thay vì tự xây giao diện riêng.

Mã

Công việc

Đầu ra chính

FR/NFR liên quan

Ưu tiên

Effort*

Phụ thuộc

2.1

Crawl dữ liệu nhà hàng (Google Maps/Places)

Bộ dữ liệu Restaurant thô

FR-7.1

Bắt buộc

5

1.4

2.2

Thu thập review đa nguồn (văn bản)

Bộ dữ liệu Review thô

FR-7.2

Bắt buộc

5

1.4

2.3

Phân tích khám phá dữ liệu (EDA)

Báo cáo phân phối dữ liệu thô: tỷ lệ thiếu, trùng lặp, phân bố rating/giá/độ dài review — làm căn cứ số liệu hoá cho quy tắc ở 2.5 và 2.8

FR-7.3, FR-7.7

Bắt buộc*

4

2.1, 2.2

2.4

Trích xuất transcript từ video review (ASR)

Transcript văn bản từ video TikTok

FR-7.6

Có thể có

6

2.2

2.5

Làm sạch & khử trùng lặp dữ liệu

Dữ liệu đã chuẩn hoá, báo cáo chất lượng

FR-7.3

Bắt buộc

4

2.3

2.6

Tạo tập nhãn thủ công (ground truth) cho đánh giá

Mẫu nhà hàng/review được người thực hiện tự gán nhãn không gian/độ ồn, chia tỷ lệ cứng ngay từ đầu (ví dụ 50% Dev-set dùng để tinh chỉnh từ điển/quy tắc ở 2.7, 50% Test-set giữ ẩn, chỉ dùng một lần ở 6.4) để tránh rò rỉ dữ liệu (data leakage) làm sai lệch kết quả Cohen's Kappa

SRS mục 7

Nên có

4

2.5

2.7

Trích xuất đặc trưng trải nghiệm (aspect extraction)

RestaurantExperienceFeature (điểm thô)

FR-7.7

Nên có

6

2.5, 2.4

2.8

Xử lý đặc trưng thiếu/độ tin cậy thấp

Quy tắc impute, cờ độ tin cậy

FR-7.8

Nên có

3

2.7

2.9

Chuẩn hoá đặc trưng trước phân cụm (Z-score)

Đặc trưng đã chuẩn hoá, tham số versioned

FR-7.9

Nên có

3

2.8

2.10

Sinh & cập nhật vector embedding

Embedding lưu trong CSDL, chỉ mục ANN

FR-7.4

Bắt buộc**

4

2.5

* EDA được nâng lên Bắt buộc dù không gắn trực tiếp với một FR nào: không thể định ra quy tắc làm sạch (2.5, Bắt buộc) hay quy tắc điền khuyết đặc trưng (2.8) một cách có căn cứ nếu chưa khảo sát phân phối dữ liệu thô — thiếu bước này khiến các quyết định xử lý nhiễu ở phần sau không có số liệu hỗ trợ khi trình bày phương pháp.

** 2.10 nâng lên Bắt buộc vì FR-4.2 (Bắt buộc) không thể vận hành nếu chưa có embedding — mức ưu tiên của một công việc không được thấp hơn mức ưu tiên của công việc phụ thuộc vào nó.

2.3. Nhóm 3 — Xây dựng mô hình lõi (Recommendation Engine)

Mã

Công việc

Đầu ra chính

FR/NFR liên quan

Ưu tiên

Effort*

Phụ thuộc

3.1

Phân cụm trải nghiệm nhà hàng (KMeans)

Mô hình cụm, nhãn cụm cho từng nhà hàng

FR-4.1

Nên có

5

2.9

3.2

Tìm kiếm ngữ nghĩa (semantic similarity)

Module tính độ tương đồng, API truy vấn

FR-4.2

Bắt buộc

5

2.10

3.3

Bộ lọc ràng buộc cứng

Module lọc ngân sách/giờ mở cửa/dị ứng

FR-4.3

Bắt buộc

3

1.4

3.4

Mô hình xếp hạng heuristic (công thức trọng số)

Công thức tính điểm phù hợp (có quy định trọng số mặc định/fallback cho nhà hàng mới hoặc thiếu dữ liệu trải nghiệm — dựa trên cờ độ tin cậy từ 2.8, tránh vừa loại oan vừa tính điểm sai lệch bằng giá trị impute như dữ liệu thật) + tài liệu tham số

FR-4.4 (MVP)

Bắt buộc

6

3.2, 3.3 (bắt buộc); 3.1 bổ sung sau

3.5

Tổng hợp đánh giá tự động (review summarization)

ReviewSummary cho từng nhà hàng

FR-5.1

Nên có

5

2.5

3.6

Ánh xạ tâm trạng sang đặc trưng món ăn

Bảng ánh xạ + module so khớp ngữ nghĩa

FR-6.1, FR-6.2

Có thể có

6

3.2

3.7

Xếp hạng món ăn trong phạm vi quán đề xuất

Module xếp hạng món

FR-6.3

Có thể có

4

3.4, 3.6

3.8

(Định hướng) Nâng cấp xếp hạng học có giám sát

Mô hình GBDT/Logistic Regression từ InteractionEvent

FR-4.4 (nâng cấp)

Chưa triển khai

—

4.4 + tích luỹ dữ liệu

* Ở Giai đoạn 1, công thức FR-4.4 chạy ở bản rút gọn — không có tín hiệu “cụm trải nghiệm” vì 3.1 (Nên có) chưa hoàn thành ở giai đoạn này. Khi 3.1 hoàn thành ở Giai đoạn 2, công thức được bổ sung thêm tín hiệu cụm mà không cần đổi kiến trúc — đây là cách tránh việc phải kéo 3.1 lên Bắt buộc chỉ vì FR-4.4 nhắc đến nó trong SRS.

2.4. Nhóm 4 — Backend & API (Application Backend)

Mã

Công việc

Đầu ra chính

FR/NFR liên quan

Ưu tiên

Effort*

Phụ thuộc

4.1

Xây dựng REST API tìm kiếm & xếp hạng

Endpoint tìm kiếm, trả kết quả đã xếp hạng

FR-2.1, FR-4.5

Bắt buộc

5

3.4

4.2

Tích hợp API bản đồ/thời tiết/giao thông

Module gọi API bên thứ ba (có cơ chế mock/cache dữ liệu cho môi trường local/dev, tránh gọi API thật liên tục — và tốn phí/cạn rate limit — trong lúc code và test giao diện ở 5.1, 5.2) + xử lý lỗi/fallback

FR-1.1, FR-3.1–3.3, NFR-2

Bắt buộc

5

1.3

4.3

API chi tiết nhà hàng & món ăn gợi ý

Endpoint chi tiết, tích hợp gợi ý món

FR-5.2, FR-6.4

Nên có

4

3.5, 3.7

4.4

API ghi nhận sự kiện tương tác (InteractionEvent)

Endpoint logging, entity SearchResultItem

FR-9.1–9.3

Bắt buộc

4

4.1

4.5

API phản hồi tường minh (explicit feedback)

Endpoint lưu phản hồi “phù hợp/không phù hợp”

FR-9.4

Có thể có

2

4.4

Không có gói “API phục vụ trang quản trị dữ liệu” riêng: theo dõi/can thiệp dữ liệu (FR-7.5) thực hiện trực tiếp qua công cụ quản trị CSDL có sẵn (mục 2.2), không cần lớp API riêng cho việc này ở quy mô một người.

2.5. Nhóm 5 — Frontend / Giao diện người dùng (Web Application)

Mã

Công việc

Đầu ra chính

FR/NFR liên quan

Ưu tiên

Effort*

Phụ thuộc

5.1

Trang chủ: tìm kiếm ngôn ngữ tự nhiên + bản đồ nền

Giao diện tìm kiếm, bản đồ tương tác

FR-1.3, FR-2.1, FR-2.3

Bắt buộc

6

4.1, 4.2

5.2

Trang kết quả: danh sách + marker đồng bộ

Danh sách xếp hạng, marker bản đồ, nhận xét tổng hợp

FR-4.5, FR-5.2

Bắt buộc

6

5.1

5.3

Hiển thị món ăn gợi ý kèm quán

UI hiển thị món gợi ý trên thẻ kết quả

FR-6.4

Có thể có

3

5.2, 4.3

5.4

Trang chi tiết nhà hàng

Trang chi tiết, tuyến đường, review tổng hợp

FR-1.5, FR-5.2

Nên có

4

5.2

5.7

Tích hợp ghi nhận tương tác phía client

Gọi API log khi người dùng thao tác kết quả

FR-9.1

Bắt buộc

3

4.4, 5.2

Không có “trang phân tích dữ liệu” (FR-8.1/8.2) và “trang quản trị nội bộ” (FR-7.5) riêng: số liệu phục vụ báo cáo đồ án lấy trực tiếp bằng truy vấn SQL khi cần, thay vì dựng hẳn hai trang web chỉ để xem số liệu — tiết kiệm effort đáng kể mà không mất chức năng thực chất.

2.6. Nhóm 6 — Tích hợp & Kiểm thử (Quality Assurance)

Mã

Công việc

Đầu ra chính

FR/NFR liên quan

Ưu tiên

Effort*

Phụ thuộc

6.1

Viết & chạy unit test cho từng mô-đun

Bộ test tự động, báo cáo coverage

Toàn bộ FR

Bắt buộc

Liên tục

Song song 2–5

6.2

Kiểm thử tích hợp pipeline offline → online

Kịch bản kiểm thử end-to-end

SRS mục 2–4

Bắt buộc

4

Nhóm 2–4 hoàn tất

6.3

Đánh giá chất lượng phân cụm & tìm kiếm ngữ nghĩa

Silhouette Score, đánh giá relevance thủ công

SRS mục 7

Nên có

4

3.1, 3.2

6.4

Đánh giá aspect extraction (Cohen's Kappa)

Báo cáo đối chiếu với nhãn thủ công

SRS mục 7

Nên có

3

2.6, 2.7

6.5

Kiểm thử hiệu năng (thời gian phản hồi)

Báo cáo benchmark đối chiếu NFR-1

NFR-1

Bắt buộc

3

4.1

6.6

Kiểm thử bảo mật & quyền riêng tư

Checklist NFR-3: HTTPS, ẩn danh session

NFR-3

Bắt buộc

3

4.4

6.7

Kiểm thử người dùng dạng checklist nhẹ (thay UAT hình thức)

Checklist kiểm thử thủ công, không cần bộ test tự động riêng

Toàn bộ

Nên có

2

6.2

2.7. Nhóm 7 — Triển khai & Vận hành (Deployment & Operations)

Mã

Công việc

Đầu ra chính

FR/NFR liên quan

Ưu tiên

Effort*

Phụ thuộc

7.1

Triển khai môi trường staging

Hệ thống chạy thử trên môi trường gần production

NFR-4

Bắt buộc

3

6.2

7.2

Thiết lập lịch chạy batch cho pipeline offline

Cron job/scheduler cho FR-7.1–7.9, có cơ chế retry & đánh dấu trạng thái từng bước (idempotent) để xử lý trường hợp một bước thất bại giữa chừng (ví dụ crawl xong nhưng sinh embedding lỗi) mà không phải chạy lại toàn bộ pipeline

NFR-5

Nên có

4

Nhóm 2 hoàn tất

7.3

Giám sát & ghi log vận hành

Dashboard giám sát lỗi/hiệu năng

NFR-2

Nên có

3

7.1

7.4

Triển khai môi trường production/demo

Bản demo công khai phục vụ báo cáo đồ án

—

Bắt buộc

3

7.1–7.3

Không dùng một framework điều phối luồng dữ liệu đầy đủ (ví dụ Airflow): ở quy mô một pipeline theo lô, một người vận hành, chi phí học và triển khai framework đó lớn hơn giá trị mang lại. Yêu cầu retry/idempotent được xử lý trực tiếp trong 7.2 là đủ cho quy mô này.

2.8. Nhóm 8 — Tài liệu & Báo cáo đồ án (Project Documentation)

Mã

Công việc

Đầu ra chính

FR/NFR liên quan

Ưu tiên

Effort*

Phụ thuộc

8.1

Hoàn thiện đề án ý tưởng

MoodBite – Đề án ý tưởng

—

Bắt buộc

—

Đã hoàn thành

8.2

Hoàn thiện tài liệu SRS

MoodBite – SRS v1.2

—

Bắt buộc

—

Đã hoàn thành

8.4

Báo cáo đồ án & slide bảo vệ

Báo cáo tổng kết, bộ slide trình bày

Toàn bộ

Bắt buộc

5

Nhóm 6, 7

8.5

Video/bản demo trực tiếp

Video demo hoặc phiên bản chạy thử trực tiếp

Toàn bộ

Nên có

3

7.4

Không có gói “tài liệu thiết kế kỹ thuật (SDD)” riêng: nội dung này đã gộp vào đầu ra của 1.3–1.4 (sơ đồ kiến trúc + ERD + ghi chú thiết kế module/API), tránh trùng lặp công sức với một tài liệu độc lập.

* Effort đã tính cho bối cảnh một người tự thực hiện toàn bộ (bao gồm thời gian làm quen công nghệ ngoài chuyên môn chính, tự kiểm tra không có người review chéo); các mục đánh dấu “Liên tục” hoặc “—” không ước lượng theo ngày công cố định.

2.9. Nhóm 0 — Bộ khung chạy được (Walking Skeleton, bổ sung v1.1)

Đây là nhóm công việc chèn thêm trước Nhóm 1–8 gốc, dùng để kiểm chứng sớm phần rủi ro kỹ thuật lớn nhất (mô hình + tích hợp giao diện web), tách khỏi rủi ro tốn thời gian nhưng cơ chế đã rõ (crawl dữ liệu quy mô lớn, sinh embedding). Không thay thế Nhóm 2 và 3.2 (semantic search) ở SRS mục 2.7 — chỉ là bản rút gọn tạm thời chạy trước, dữ liệu và mô-đun ở nhóm này sẽ được thay thế dần bằng dữ liệu thật và embedding thực sự khi bước vào Giai đoạn 1.

0.1 — Thu thập tay 50–100 nhà hàng mẫu (tên, toạ độ, mức giá, loại món, giờ mở cửa) vào một bảng tính/CSDL đơn giản, không crawl tự động. Effort tham khảo: 2 ngày.

0.2 — Viết bộ lọc ràng buộc cứng + công thức xếp hạng heuristic rút gọn (không có tín hiệu cụm/embedding, chỉ dùng thuộc tính có cấu trúc và so khớp từ khoá đơn giản cho câu tìm kiếm tự do). Effort tham khảo: 4 ngày.

0.3 — Dựng API tìm kiếm tối thiểu trả kết quả đã xếp hạng từ bộ dữ liệu mẫu. Effort tham khảo: 3 ngày.

0.4 — Dựng giao diện web tối thiểu: ô tìm kiếm + bản đồ hiển thị marker kết quả (có thể dùng bản đồ tĩnh/thư viện có sẵn, chưa cần tuyến đường/thời gian di chuyển thực tế). Effort tham khảo: 5 ngày.

0.5 — Chạy thử end-to-end trên trình duyệt, ghi nhận vướng mắc kỹ thuật thực tế (không phải chỉ trên giấy) trước khi đầu tư effort vào Nhóm 2 (crawl thật) và Nhóm 3 (embedding/semantic search). Effort tham khảo: 2 ngày.

Tổng effort Nhóm 0 tham khảo: khoảng 16 ngày công, được cộng vào trước lộ trình tuần tự ở mục 4 (xem mục 4, bước 0).

3. Ánh xạ theo giai đoạn triển khai

Bảng dưới đây nhóm các gói công việc ở mục 2 thành bốn giai đoạn triển khai, nhất quán với phân loại MoSCoW của SRS mục 8, giúp nhóm phát triển biết chính xác “làm xong đến đâu thì có một bản demo chạy được” thay vì phải hoàn thành toàn bộ WBS mới có sản phẩm.

Giai đoạn

Mục tiêu

Các gói công việc chính

Tiêu chí hoàn thành

Giai đoạn 1 — MVP (Bắt buộc)

Có một bản demo chạy được luồng lõi: tìm kiếm → xếp hạng heuristic → hiển thị kết quả trên bản đồ

1.1–1.4; 2.1, 2.2, 2.3(EDA), 2.5, 2.10; 3.2–3.4; 4.1, 4.2, 4.4; 5.1, 5.2, 5.7; 6.1, 6.2, 6.5, 6.6; 7.1, 7.4; 8.4

Người dùng nhập câu tìm kiếm tự do, nhận được danh sách nhà hàng xếp hạng kèm bản đồ, trong thời gian đáp ứng NFR-1; InteractionEvent được ghi nhận đầy đủ

Giai đoạn 2 — Mở rộng dữ liệu & trải nghiệm (Nên có)

Nâng chất lượng dữ liệu đầu vào và bổ sung trải nghiệm tra cứu sâu hơn

2.6–2.9; 3.1, 3.5; 4.3; 5.4; 6.3, 6.4, 6.7; 7.2, 7.3

Phân cụm trải nghiệm chạy trên đặc trưng đã trích xuất/chuẩn hoá; có nhận xét tổng hợp và trang chi tiết nhà hàng hoạt động

Giai đoạn 3 — Tính năng nâng cao (Có thể có)

Bổ sung các tính năng làm giàu trải nghiệm, không ảnh hưởng luồng lõi nếu chưa kịp hoàn thành

2.4(ASR); 3.6, 3.7; 4.5; 5.3; 8.5

Có gợi ý món ăn theo tâm trạng đi kèm quán; xử lý được một phần dữ liệu video review

Giai đoạn 4 — Định hướng tương lai (Chưa triển khai)

Ghi nhận rõ trong kế hoạch nhưng nằm ngoài phạm vi thực hiện hiện tại

3.8 và các hạng mục Won't-have khác ở SRS mục 8 (tài khoản người dùng, đặt chỗ trực tiếp...)

Chỉ triển khai khi đã tích luỹ đủ dữ liệu InteractionEvent và có nhu cầu mở rộng sản phẩm rõ ràng

4. Lộ trình thực hiện tuần tự cho cá nhân

Vì dự án do một người thực hiện, mục “phân công vai trò” không còn ý nghĩa — toàn bộ công việc phải làm tuần tự thay vì chạy song song giữa các vai trò như bản kế hoạch nhóm. Khác biệt quan trọng nhất là: effort của một kế hoạch nhóm được tính theo nhánh chậm nhất chạy song song, còn effort của một người phải cộng dồn toàn bộ các gói công việc lại với nhau. Bảng dưới đây sắp xếp lại các gói công việc Giai đoạn 1 (Bắt buộc) theo đúng thứ tự phụ thuộc, kèm effort cộng dồn, để dùng trực tiếp làm lịch làm việc cá nhân.

Thứ tự

Mã

Công việc

Effort (ngày)

Cộng dồn (ngày)

0

0.1–0.5

Bộ khung chạy được (Nhóm 0): dữ liệu mẫu tay + lọc/xếp hạng rút gọn + API tối thiểu + giao diện tối thiểu + chạy thử end-to-end

16

16

1

1.1–1.2

Lập kế hoạch cá nhân & thiết lập môi trường (kèm quy ước versioning nhẹ)

7

23

2

1.3–1.4

Thiết kế kiến trúc hệ thống & cơ sở dữ liệu (gộp SDD)

9

32

3

2.1–2.2

Crawl dữ liệu nhà hàng & thu thập review

10

42

4

2.3

Phân tích khám phá dữ liệu (EDA)

4

46

5

2.5

Làm sạch & khử trùng lặp dữ liệu (theo căn cứ từ EDA)

4

50

6

2.10

Sinh & cập nhật vector embedding

4

54

7

3.3

Bộ lọc ràng buộc cứng

3

57

8

3.2

Tìm kiếm ngữ nghĩa (semantic similarity)

5

62

9

3.4

Mô hình xếp hạng heuristic (bản rút gọn)

6

68

10

—

Điểm kiểm tra chất lượng mô hình lõi & dự phòng lặp lại (nếu embedding/ranking chưa đạt)

6

74

11

4.2

Tích hợp API bản đồ/thời tiết/giao thông

5

79

12

4.1

REST API tìm kiếm & xếp hạng

5

84

13

4.4

API ghi nhận sự kiện tương tác

4

88

14

5.1–5.2

Trang chủ tìm kiếm & trang kết quả (danh sách + bản đồ)

12

100

15

5.7

Tích hợp ghi nhận tương tác phía client

3

103

16

6.2, 6.5, 6.6

Kiểm thử tích hợp, hiệu năng, bảo mật

10

113

17

—

Dự phòng sửa lỗi tích hợp phát sinh

4

117

18

7.1, 7.4

Triển khai staging & bản demo

6

123

19

8.4

Báo cáo đồ án & slide bảo vệ

5

128

Ghi chú: 6.1 (viết unit test) không xuất hiện thành một dòng riêng vì được làm rải rác song song với từng gói công việc phía trên (viết test ngay khi vừa code xong một phần, không dồn lại cuối). Hai dòng “—” là điểm dự phòng tường minh, đặt đúng sau hai vị trí rủi ro cao nhất (mô hình lõi chưa chắc đạt chất lượng ngay lần đầu; tích hợp nhiều thành phần lần đầu chạy chung dễ phát sinh lỗi) — khác với việc cộng đều buffer vào mọi con số, cách này giữ cho từng effort riêng lẻ phản ánh đúng khối lượng việc thật, còn rủi ro lặp lại được xử lý riêng, tại đúng chỗ có khả năng xảy ra.

Effort cộng dồn cho Giai đoạn 1 (đã gồm Nhóm 0 bổ sung) là 128 ngày công. Quy đổi lịch làm việc: nếu làm toàn thời gian (8 giờ/ngày, 5 ngày/tuần), 128 ngày công tương đương khoảng 6–6,5 tháng liên tục; nếu làm bán thời gian (~15 giờ/tuần), cùng khối lượng đó kéo dài khoảng 15–16 tháng theo lịch thực.

Mốc hoàn thành (milestones)

Mốc

Sau bước

Cộng dồn (ngày)

Trạng thái đạt được

M0 — Bộ khung chạy được (Nhóm 0)

Bước 0

16

Đã chứng minh luồng tìm kiếm → mô hình rút gọn → hiển thị bản đồ chạy được trên trình duyệt, với dữ liệu mẫu nhỏ; chưa có dữ liệu thật/embedding

M1 — Dữ liệu offline sẵn sàng

Bước 6

54

Có dữ liệu nhà hàng/review đã làm sạch, đã khảo sát phân phối (EDA), đã sinh embedding — nền tảng cho toàn bộ phần còn lại

M2 — Mô hình lõi hoạt động

Bước 10

74

Tìm kiếm ngữ nghĩa và công thức xếp hạng heuristic chạy được, đã qua một vòng kiểm tra chất lượng sơ bộ

M3 — Backend hoàn chỉnh

Bước 13

88

API tìm kiếm, tích hợp bản đồ/thời tiết, ghi nhận tương tác đều sẵn sàng để nối giao diện

M4 — Demo end-to-end trên trình duyệt

Bước 15

103

Người dùng thao tác được từ tìm kiếm đến xem kết quả trên bản đồ, chưa qua kiểm thử đầy đủ

M5 — Sẵn sàng báo cáo

Bước 19

128

Đã kiểm thử, đã triển khai bản demo công khai, có báo cáo/slide bảo vệ

Tiêu chí nghiệm thu chi tiết theo mốc

Bảng mốc ở trên cho biết "đạt đến bước nào thì có gì", nhưng chưa nói rõ đạt đến mức nào mới được coi là xong. Bảng dưới đây bổ sung tiêu chí đo được cho từng mốc và điều kiện cụ thể để được phép chuyển sang bước/phase kế tiếp — nếu chưa đạt, không chuyển, kể cả khi đã hết effort dự kiến của bước đó.

Mốc

Tiêu chí nghiệm thu (đo được)

Điều kiện chuyển sang phase/bước tiếp theo

M0

Người dùng nhập được câu tìm kiếm/lựa chọn khảo sát và nhận được danh sách nhà hàng đã xếp hạng hiển thị trên bản đồ, không lỗi qua ít nhất 10 lượt thử thủ công với dữ liệu mẫu.

Chạy được ổn định trên trình duyệt (desktop) → bắt đầu Giai đoạn 1 (crawl dữ liệu thật).

M1

Dataset có tối thiểu vài trăm bản ghi, tỷ lệ thiếu dữ liệu ở các trường bắt buộc dưới 10%, không còn bản ghi trùng lặp giữa các nguồn.

Dữ liệu đã qua kiểm soát chất lượng (SRS mục 2) → cho phép Adapter thật thay Adapter mẫu qua cấu hình DI.

M2

Silhouette Score của KMeans đạt ngưỡng tối thiểu đã chọn trước khi huấn luyện (ví dụ ≥ 0,3, tự điều chỉnh theo dữ liệu thực tế); tìm kiếm ngữ nghĩa trả kết quả liên quan cho ít nhất 70% câu hỏi trong tập câu mẫu kiểm tra thủ công. Silhouette chỉ đo chất lượng phân cụm, không đo việc gợi ý có hữu ích hay không, nên bắt buộc có thêm một tiêu chí nghiệp vụ độc lập: Precision@5 (hoặc tỷ lệ chấp nhận Top-5) trên tập Evaluation Set riêng (xem Kiến trúc Kỹ thuật mục 9.3) đạt tối thiểu 60%, đánh giá bằng một thang đo (grading rubric) cố định, không để cảm tính người chấm quyết định: một gợi ý được tính True Positive khi và chỉ khi thoả cả hai điều kiện — (1) khớp hoàn toàn mọi ràng buộc cứng trong truy vấn (ngân sách, giờ mở cửa, chế độ ăn), và (2) yêu cầu ngữ nghĩa trong câu tìm kiếm (ví dụ "không gian yên tĩnh") có bằng chứng cụ thể trong review/review_summary của nhà hàng đó, không chỉ dựa vào điểm tương đồng embedding một cách trừu tượng. Đồng thời đo thêm Intra-List Diversity@5 (tỷ lệ cặp nhà hàng trong Top-5 thuộc các cụm trải nghiệm khác nhau) đạt tối thiểu 60%, để tránh trường hợp Precision@5 cao nhưng Top-5 toàn nhà hàng cùng một kiểu (xem ADR/Assumption/Scope mục 8).

Mô hình đạt ngưỡng → được đặt làm active qua config/di_container (xem Kiến trúc Kỹ thuật mục 9); không đạt thì giữ nguyên bản heuristic, không chuyển bước.

M3

Toàn bộ endpoint API trả đúng dữ liệu cho các kịch bản kiểm thử đã liệt kê; thời gian phản hồi trung bình dưới ngưỡng chấp nhận được cho một demo trực tiếp.

API ổn định qua kiểm thử thủ công lặp lại → tích hợp vào giao diện web hoàn chỉnh.

M4

Người dùng thao tác được trọn luồng (tìm kiếm → xem kết quả → xem trên bản đồ) không gặp lỗi chặn luồng, qua ít nhất 10 kịch bản thử nghiệm khác nhau.

Demo chạy ổn định → chuyển sang hoàn thiện kiểm thử và tài liệu báo cáo.

M5

Toàn bộ yêu cầu mức Bắt buộc (Must have) ở SRS mục 8 đã triển khai và nghiệm thu theo tiêu chí tương ứng ở trên; đã diễn tập thuyết trình/demo ít nhất một lần.

Đạt đủ tiêu chí → coi là hoàn thành Giai đoạn 1, các phần còn lại (Giai đoạn 2–3) là mở rộng thêm nếu còn thời gian.

Kế hoạch sao lưu và rollback dữ liệu, mô hình

Kiến trúc rollback qua Dependency Injection (đổi Adapter bằng một dòng cấu hình) chỉ giải quyết phần mã nguồn. Dữ liệu và mô hình đã huấn luyện cũng cần một cơ chế khôi phục riêng, được trình bày chi tiết ở tài liệu Kiến trúc Kỹ thuật mục 9. Tóm tắt áp dụng cho lộ trình WBS này:

Mỗi lần crawl làm mới dữ liệu (bước 2.1–2.2) tạo một bản snapshot có version riêng, không ghi đè bản cũ; snapshot mới chỉ thay thế dữ liệu đang phục vụ sau khi qua lại bước kiểm soát chất lượng (bước 2.3/EDA).

Mỗi lần huấn luyện lại KMeans hoặc mô hình xếp hạng (bước 3.x, 6.x) tạo một artifact mô hình có version kèm chỉ số đánh giá; chỉ đặt làm active nếu đạt tiêu chí nghiệm thu tương ứng ở bảng trên, nếu không đạt thì giữ nguyên mô hình đang dùng.

Nhờ đó nếu một lần retrain thất bại hoặc dữ liệu mới có vấn đề, việc khôi phục chỉ là quay về snapshot/artifact phiên bản trước — không cần làm lại từ đầu, không ảnh hưởng đến effort đã tính ở mục 4.

Nguồn gốc trọng số công thức xếp hạng heuristic

Trọng số w1…w5 của công thức xếp hạng (đề án ý tưởng, mục Recommendation Engine) không phải số tuỳ ý: khởi tạo ban đầu bằng phán đoán chuyên gia (Expert Judgment — dựa trên mức độ quan trọng cảm nhận của từng tiêu chí theo từng ngữ cảnh khảo sát), sau đó chạy vòng lặp thử-sai thủ công (grid search thủ công trên một lưới giá trị nhỏ) trên Development Set để chọn bộ trọng số cho kết quả hợp lý nhất theo cảm quan; bộ trọng số chỉ được khoá lại và đưa vào đánh giá chính thức trên Evaluation Set sau bước này, không chỉnh thêm dựa trên kết quả Evaluation Set (xem mục tách dev/eval ở trên).

Cold Start và tách bạch dữ liệu tuning/đánh giá

Hai điểm này được trình bày chi tiết ở tài liệu Kiến trúc Kỹ thuật (mục 9.3 và mục 10) nên không lặp lại toàn bộ ở đây, chỉ nhắc để không bỏ sót khi lập kế hoạch: (1) Cold Start có hai dạng độc lập — nhà hàng mới chưa có cluster_id/tổng hợp review, và người dùng mới chưa có lịch sử tương tác cho mô hình xếp hạng học có giám sát — mỗi dạng cần một cơ chế dự phòng riêng, không dùng chung một giải pháp; (2) tập dữ liệu dùng để tinh chỉnh (Development Set) và tập dùng để đánh giá chính thức (Evaluation Set) phải tách biệt ngay từ đầu, Evaluation Set không được quay lại phục vụ tuning — nếu không, các chỉ số ở bảng tiêu chí nghiệm thu phía trên sẽ lạc quan giả tạo.

Đối chiếu với hạn chót tháng 12/2026

Tài liệu này được ban hành ngày 21/07/2026, còn khoảng 5–5,5 tháng theo lịch (đến cuối tháng 12/2026). So với effort 128 ngày công của Giai đoạn 1 (đã gồm Nhóm 0): nếu làm toàn thời gian, 128 ngày công (~6–6,5 tháng liên tục) vẫn vượt quỹ thời gian còn lại một chút; nếu làm bán thời gian như hầu hết trường hợp một người vừa học/làm vừa tự triển khai, quỹ effort này (~15–16 tháng) vượt hạn chót rất nhiều.

Vì vậy, mục tiêu thực tế cho tháng 12/2026 không nên là hoàn thành toàn bộ Giai đoạn 1 như liệt kê ở mục 2, mà là: hoàn thành Nhóm 0 (bộ khung chạy được) trong 2–3 tuần đầu, sau đó ưu tiên tuyệt đối các bước 1–14 của lộ trình ở trên (đến hết Trang chủ & trang kết quả, mốc M4 rút gọn) bằng một tập dữ liệu vừa phải (vài trăm nhà hàng, crawl một lần bằng Google Places API, không cần đa nguồn TikTok/ASR), và dùng bản tìm kiếm ngữ nghĩa rút gọn (so khớp từ khoá/thuộc tính) thay cho embedding đầy đủ nếu thời gian không cho phép — đúng theo chiến lược đã nêu ở SRS mục 2.7. Các bước 15–19 (kiểm thử đầy đủ, triển khai production, embedding/tìm kiếm ngữ nghĩa hoàn chỉnh) và toàn bộ Giai đoạn 2–3 (phân cụm, tổng hợp đánh giá, gợi ý món ăn, ASR) nên được xem là mục tiêu "làm thêm nếu còn thời gian" chứ không phải điều kiện bắt buộc để có một bản demo trình bày được vào tháng 12.

Nói cách khác: có một bản demo chạy được với dữ liệu và mô hình rút gọn nhưng đúng hạn, có giá trị hơn một kiến trúc đầy đủ nhưng dang dở khi đến hạn.

5. Phụ lục — Sơ đồ cây WBS (dạng rút gọn)

Danh sách dưới đây trình bày lại toàn bộ cấu trúc phân rã ở mục 2 dưới dạng cây thụt lề, phục vụ tra cứu nhanh hoặc đưa vào slide báo cáo.

1. Quản lý & Khởi tạo dự án

1.1 Lập kế hoạch cá nhân (lịch làm việc, mốc kiểm tra)

1.2 Thiết lập môi trường phát triển

1.3 Thiết kế kiến trúc hệ thống tổng thể

1.4 Thiết kế cơ sở dữ liệu chi tiết

2. Thu thập & Xử lý dữ liệu

2.1 Crawl dữ liệu nhà hàng

2.2 Thu thập review đa nguồn

2.3 Phân tích khám phá dữ liệu (EDA)

2.4 Trích xuất transcript từ video (ASR)

2.5 Làm sạch & khử trùng lặp

2.6 Tạo tập nhãn thủ công (ground truth)

2.7 Trích xuất đặc trưng trải nghiệm (aspect extraction)

2.8 Xử lý đặc trưng thiếu/độ tin cậy thấp

2.9 Chuẩn hoá đặc trưng trước phân cụm

2.10 Sinh & cập nhật embedding

3. Xây dựng mô hình lõi

3.1 Phân cụm trải nghiệm (KMeans)

3.2 Tìm kiếm ngữ nghĩa

3.3 Bộ lọc ràng buộc cứng

3.4 Mô hình xếp hạng heuristic

3.5 Tổng hợp đánh giá tự động

3.6 Ánh xạ tâm trạng sang món ăn

3.7 Xếp hạng món ăn trong quán đề xuất

3.8 (Tương lai) Xếp hạng học có giám sát

4. Backend & API

4.1 API tìm kiếm & xếp hạng

4.2 Tích hợp API bản đồ/thời tiết/giao thông

4.3 API chi tiết nhà hàng & món gợi ý

4.4 API ghi nhận tương tác

4.5 API phản hồi tường minh

5. Frontend / Giao diện người dùng

5.1 Trang chủ: tìm kiếm + bản đồ

5.2 Trang kết quả: danh sách + marker

5.3 Hiển thị món ăn gợi ý

5.4 Trang chi tiết nhà hàng

5.7 Ghi nhận tương tác phía client

6. Tích hợp & Kiểm thử

6.1 Unit test

6.2 Kiểm thử tích hợp end-to-end

6.3 Đánh giá phân cụm & tìm kiếm ngữ nghĩa

6.4 Đánh giá aspect extraction

6.5 Kiểm thử hiệu năng

6.6 Kiểm thử bảo mật

6.7 UAT

7. Triển khai & Vận hành

7.1 Triển khai staging

7.2 Lịch chạy batch offline

7.3 Giám sát vận hành

7.4 Triển khai production/demo

8. Tài liệu & Báo cáo

8.1 Đề án ý tưởng

8.2 Tài liệu SRS

8.4 Báo cáo & slide bảo vệ

8.5 Video/bản demo


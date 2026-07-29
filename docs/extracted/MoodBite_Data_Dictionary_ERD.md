# MoodBite_Data_Dictionary_ERD

DATA DICTIONARY & ERD CHI TIẾT

(Từ điển dữ liệu & Sơ đồ Thực thể – Quan hệ)

MoodBite

Phiên bản 1.5

Ngày ban hành: 23/07/2026

Tài liệu nguồn: MoodBite – SRS v1.2, WBS v1.6, Kiến trúc Kỹ thuật v1.1, ADR/Assumption/Scope v1.2

Lịch sử thay đổi tài liệu

Phiên bản

Ngày

Mô tả thay đổi

1.0

23/07/2026

Khởi tạo Data Dictionary & ERD hợp nhất từ SRS, WBS, Kiến trúc Kỹ thuật, ADR.

1.1

23/07/2026

Thêm soft-delete (is_active/deleted_at), đổi review_summaries sang append-only, chốt VECTOR(768).

1.2

24/07/2026

Bổ sung ON DELETE/UPDATE cho toàn bộ FK, index còn thiếu, quy tắc Cold Start, truy vết dataset↔cluster↔ranking; từ chối Partial Unique Index và đổi 7.2 (WBS) sang orchestration framework.

1.3

24/07/2026

Chuẩn hoá cú pháp CHECK, đồng bộ deleted_at cho dishes, làm rõ lý do no-FK cho experience_cluster_id, thêm mục Data Ownership.

1.4

24/07/2026

Vẽ lại ERD: thêm Subject Area, sửa cardinality 1–n → 1–0..N, thể hiện FK tuỳ chọn 0..1, đồng bộ lại ranking_model_versions trên sơ đồ.

1.5

25/07/2026

Chuyển mục “Vấn đề phát hiện” sang Phụ lục A (tách hiện trạng khỏi lịch sử quyết định); thêm Glossary (mục 1.3); thêm Type ngắn gọn vào ERD; thêm bảng lịch sử này.

Mục lục

1. Giới thiệu

1.1. Mục đích tài liệu

Bốn tài liệu đã có (SRS, WBS, Kiến trúc Kỹ thuật, ADR/Assumption/Scope) đều nhắc đến các thực thể dữ liệu, nhưng mỗi tài liệu chỉ mô tả ở mức đủ dùng cho mục đích riêng của nó — SRS liệt kê thuộc tính tiêu biểu, Kiến trúc Kỹ thuật nói tên Entity theo Domain, WBS và ADR nhắc tới các trường/khái niệm phát sinh khi giải quyết vấn đề kỹ thuật cụ thể (cluster_id, centroid, version, session_id...). Tài liệu này hợp nhất toàn bộ thành một nguồn duy nhất, đủ chi tiết để dùng trực tiếp viết migration/schema thật — kiểu dữ liệu, ràng buộc, khoá chính/khoá ngoại cho từng trường, không chỉ tên thực thể.

Trong quá trình hợp nhất, tài liệu này phát hiện và xử lý một số điểm chưa nhất quán giữa các tài liệu nguồn — liệt kê đầy đủ ở Phụ lục A.

1.2. Giả định công nghệ

Các tài liệu nguồn không chỉ định rõ hệ quản trị cơ sở dữ liệu, nhưng Kiến trúc Kỹ thuật đặt tên Adapter là PostgresRestaurantRepository (mục 4.3, 6.2), nên tài liệu này giả định PostgreSQL, có phần mở rộng hỗ trợ kiểu dữ liệu vector (ví dụ pgvector) để lưu embedding — nhất quán với ISearchPort/SemanticSearchAdapter đã thiết kế. Nếu công nghệ nền thay đổi, chỉ cần đổi cột kiểu vector và chỉ mục ANN tương ứng, không ảnh hưởng phần còn lại của từ điển dữ liệu này.

1.3. Thuật ngữ (Glossary)

Chỉ liệt kê thuật ngữ đặc thù của dự án — không đưa các khái niệm CSDL phổ thông (PK, FK, UUID...) vào đây.

Thuật ngữ

Định nghĩa

Experience Feature

restaurant_experience_features — vector đặc trưng ĐẦU VÀO (điểm không gian, độ ồn suy ra từ review) dùng để phân cụm. Không phải kết quả phân cụm.

Experience Cluster

Khái niệm miền (Domain Entity ExperienceCluster ở Kiến trúc Kỹ thuật) biểu diễn một NHÓM/PHÂN KHÚC nhà hàng — là kết quả ĐẦU RA của phân cụm, lưu ở restaurants.experience_cluster_id (nhãn) và cluster_model_versions.centroids (định nghĩa tâm cụm theo từng version). Dễ nhầm với Experience Feature ở trên vì tên gần giống nhau — hai khái niệm này KHÔNG đồng nhất: Feature là đầu vào, Cluster là đầu ra.

Cold Start

Tình huống nhà hàng/hạng mục mới chưa có đủ dữ liệu (chưa được phân cụm, chưa có review) để tính điểm theo cách thông thường; cần quy tắc dự phòng riêng thay vì để NULL/0 mặc định — chi tiết ở Phụ lục A.12.

Embedding

Vector số học biểu diễn ngữ nghĩa văn bản, dùng cho tìm kiếm/so khớp ngữ nghĩa (mô hình multilingual-e5-base, 768 chiều — mục 4, Phụ lục A.15).

ANN (Approximate Nearest Neighbor)

Kỹ thuật lập chỉ mục tìm kiếm gần đúng láng giềng gần nhất trên vector embedding, tránh so sánh vét cạn (mục 6).

Dataset Snapshot

Một phiên bản đóng băng của toàn bộ dữ liệu nhà hàng/review tại một thời điểm crawl, dùng làm nền huấn luyện/đánh giá có thể tái lập (bảng dataset_snapshots, mục 4).

Source of Truth

Hệ thống/nguồn dữ liệu được coi là đúng tuyệt đối cho một bảng — dùng để phân xử khi có nhiều nguồn cùng ghi (mục 2.3).

Owner

Hệ thống/vai trò có quyền ghi vào một bảng Dữ liệu gốc (mục 2.3). Authority (phân quyền chi tiết theo từng trường khi có xung đột Manual/Crawler) được ghi ở ADR, không lặp lại ở đây.

Soft Delete

Đánh dấu bản ghi ngừng hoạt động qua cờ is_active thay vì xoá cứng (DELETE), giữ nguyên toàn vẹn khoá ngoại và lịch sử liên quan (mục 4, Phụ lục A.5).

Subject Area

Nhóm hiển thị các bảng có liên quan trên ERD (Dữ liệu gốc / Suy diễn / Giao dịch / Artifact mô hình) — chỉ là cách trình bày sơ đồ, không phải schema PostgreSQL thật (mục 3).

Version Drift

Rủi ro các artifact có phụ thuộc lẫn nhau (dataset, cluster, ranking model) bị lệch phiên bản khi publish không đồng bộ — ghi nhận ở mục 2.3, xử lý chi tiết thuộc phạm vi ADR.

2. Nguyên tắc thiết kế dữ liệu

2.1. Quy ước đặt tên

Tên bảng: số nhiều, snake_case (ví dụ restaurants, search_result_items).

Khoá chính: id (UUID hoặc BIGSERIAL tuỳ bảng) trừ các bảng có khoá tự nhiên là version_tag (dataset_snapshots, cluster_model_versions, ranking_model_versions) hoặc khoá ngoại kiêm khoá chính (restaurant_experience_features — quan hệ 1-1 với restaurants). review_summaries dùng id riêng vì thiết kế append-only theo phiên bản (mục 4).

Khoá ngoại: <tên_bảng_số_ít>_id (ví dụ restaurant_id, search_query_id).

Thời điểm: hậu tố _at, kiểu TIMESTAMPTZ (có múi giờ), tránh nhầm lẫn khi vận hành nhiều môi trường.

2.2. Bốn nhóm dữ liệu

Việc phân nhóm này quyết định cách vận hành khác nhau cho từng loại dữ liệu — không phải phân loại hình thức:

Nhóm

Đặc điểm vận hành

Bảng thuộc nhóm

Dữ liệu gốc (Master Data)

Thu thập theo đợt (batch), là nguồn sự thật (source of truth) cho các nhóm còn lại tham chiếu tới.

restaurants, dishes, reviews

Dữ liệu suy diễn (Derived Data)

Tính toán lại toàn bộ mỗi khi pipeline offline chạy lại (SRS mục 6.2); không nhập tay, không phải nguồn sự thật độc lập. review_summaries lưu append-only theo phiên bản (mục 4); restaurant_experience_features chỉ giữ bản mới nhất vì là input trực tiếp cho phân cụm, không cần lịch sử.

review_summaries, restaurant_experience_features

Dữ liệu giao dịch/vận hành (Transactional)

Ghi liên tục theo thời gian thực khi người dùng thao tác; không sửa/xoá sau khi ghi (append-only), phục vụ huấn luyện mô hình sau này.

search_queries, search_result_items, interaction_events

Artifact mô hình & phiên bản (Model/Versioning)

Mỗi lần crawl lại/huấn luyện lại tạo một bản ghi version mới, không ghi đè; chỉ một bản được đánh dấu is_active tại một thời điểm (Kiến trúc Kỹ thuật mục 9).

dataset_snapshots, cluster_model_versions, ranking_model_versions

2.3. Data Ownership (Source of Truth & Owner)

Bổ sung theo góp ý MDM (Master Data Management): mỗi bảng Dữ liệu gốc cần trả lời rõ “ai/hệ thống nào có quyền ghi vào bảng này”, tránh tình huống hai nguồn ghi đè lẫn nhau không kiểm soát (ví dụ crawler ghi đè một chỉnh sửa thủ công). Bảng dưới đây dừng ở mức bảng (table-level); ma trận Authority chi tiết theo từng trường (ví dụ rating do Google quyết định, display_name có thể bị ghi đè thủ công) và quy tắc xử lý xung đột Manual vs Crawler được khuyến nghị ghi ở ADR/Assumption/Scope, không lặp lại chi tiết ở đây — tách hai tài liệu để tránh chính tài liệu chống trùng lặp dữ liệu lại tự trùng lặp chính sách với ADR.

Bảng

Source of Truth

Owner (được phép ghi)

restaurants

Google Places API (trường cốt lõi: tên, toạ độ, rating, giờ mở cửa); cho phép ghi đè thủ công có kiểm soát qua updated_by = 'manual'

Crawler Service (ghi chính); quản trị viên (ghi đè có giới hạn)

dishes

Thực đơn công khai của nhà hàng (crawl) hoặc trích xuất từ review khi không có thực đơn cấu trúc (FR-6.1)

Crawler Service

reviews

Nội dung gốc từ từng nguồn (Google Places, TikTok...) — không chỉnh sửa nội dung sau khi thu thập

Crawler Service (chỉ ghi/thêm, không sửa nội dung đã có)

review_summaries

Không có Source of Truth độc lập — là dữ liệu suy diễn từ reviews

Batch Pipeline (ReviewSummarizationUseCase)

Ba nội dung liên quan khác được khuyến nghị ghi vào ADR/Assumption/Scope thay vì Data Dictionary: (1) quy ước lưu thời điểm theo UTC và quy tắc quy đổi múi giờ chỉ ở tầng hiển thị (frontend), không lặp lại ở từng bảng; (2) quy tắc giải quyết xung đột khi Manual override và Crawler cùng ghi một trường; (3) yêu cầu publish đồng bộ (transactional) giữa các artifact có phụ thuộc lẫn nhau — ví dụ dataset_snapshot mới chỉ nên kéo theo cluster_model_version và ranking_model_version mới cùng lúc nếu có phụ thuộc, tránh tình trạng version drift giữa các artifact.

3. Sơ đồ Thực thể – Quan hệ (ERD)

Sơ đồ dưới đây chỉ hiển thị khoá chính/khoá ngoại kèm kiểu dữ liệu ngắn gọn (không ghi độ dài/precision — ví dụ chỉ ghi VARCHAR chứ không VARCHAR(255)) để giữ bố cục dễ đọc; toàn bộ chi tiết đầy đủ (CHECK, DEFAULT, Owner, precision chính xác...) nằm trong Data Dictionary ở mục 2.3 và mục 4 — có chủ đích không nhồi các chi tiết đó vào ERD. Trường không có nhãn (opt) đều là NOT NULL; có (opt) là nullable — dùng quy ước này thay vì ghi lặp lại chữ NOT NULL ở từng dòng. Bốn khung viền màu là Subject Area (nhóm hiển thị theo mục 2.2, chỉ để đọc sơ đồ dễ hơn) — không phải schema PostgreSQL thật; toàn bộ 11 bảng vẫn nằm trong một schema public duy nhất. Nhãn số ở hai đầu mỗi quan hệ là cardinality kiểu crow's-foot (1 = bắt buộc đúng một; 0..1 = tuỳ chọn tối đa một; 0..N = từ không đến nhiều) — toàn bộ đều dùng 0..N thay vì N vì không có bảng con nào chắc chắn có sẵn bản ghi ngay khi bảng cha vừa được tạo (nhất quán với thiết kế Cold Start ở Phụ lục A.12). Đường nét đứt biểu thị quan hệ tham chiếu phiên bản (không phải ràng buộc theo thời gian thực). Nhãn ⚠ mới trong Data Dictionary mục 4 đánh dấu bảng phát sinh khi hợp nhất (giải thích ở Phụ lục A); không lặp lại nhãn đó trên sơ đồ để đỡ rối.

Hình 1 — Chú giải màu: xanh navy = Dữ liệu gốc; xanh lá = Dữ liệu suy diễn; cam = Dữ liệu giao dịch/vận hành; tím = Artifact mô hình & phiên bản.

4. Data Dictionary chi tiết

restaurants — Dữ liệu gốc

Nguồn: SRS mục 6.1 (Restaurant); Kiến trúc Kỹ thuật mục 4.1, 6.1, 6.3 (trường experience_cluster_id thêm ở Giai đoạn 2, dạng optional, không đổi cấu trúc cũ).

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

id

UUID

PK

Định danh nhà hàng.

name

VARCHAR(255)

NOT NULL

Tên nhà hàng.

address

TEXT

NULLABLE

Địa chỉ dạng văn bản.

latitude

DOUBLE PRECISION

NOT NULL, CHECK (latitude BETWEEN -90 AND 90)

Vĩ độ.

longitude

DOUBLE PRECISION

NOT NULL, CHECK (longitude BETWEEN -180 AND 180)

Kinh độ.

opening_hours

JSONB

NULLABLE

Giờ mở cửa theo từng ngày trong tuần.

price_range

SMALLINT

CHECK (price_range BETWEEN 1 AND 4)

Mức giá quy đổi theo thang price_level của Google Places (ADR-05).

rating

NUMERIC(2,1)

CHECK (rating BETWEEN 0 AND 5)

Điểm đánh giá trung bình từ nguồn gốc.

user_ratings_total

INTEGER

NULLABLE

Số lượng đánh giá — dùng để giảm trọng số rating có ít đánh giá (Assumption Register, ADR mục 3).

description_embedding

VECTOR(768)

NULLABLE

Embedding mô tả/review tổng hợp bằng mô hình multilingual-e5-base. Xem chiến lược nâng cấp không downtime ở Phụ lục A.15.

is_active

BOOLEAN

NOT NULL DEFAULT true

Cờ soft-delete — false khi nhà hàng đóng cửa/ngừng hoạt động. Không hard-delete để không phá FK từ reviews, dishes, search_result_items, interaction_events. ON DELETE của mọi FK trỏ tới bảng này là RESTRICT — xem mục 5.

deleted_at

TIMESTAMPTZ

NULLABLE

Thời điểm đánh dấu ngừng hoạt động. CHECK (deleted_at IS NULL OR is_active = false) — không cho phép trạng thái mâu thuẫn (còn hoạt động nhưng lại có mốc ngừng hoạt động).

experience_cluster_id

SMALLINT

NULLABLE, không FK cứng — xem lý do

Nhãn cụm được gán bởi KMeansTrainingJob theo lô (Kiến trúc Kỹ thuật mục 6.3). KHÔNG dùng khoá ngoại tới cluster_model_versions: bản thân trị số cluster_id (0..k-1) không có ngữ nghĩa độc lập — KMeans không đảm bảo cùng một số hiệu cụm mang ý nghĩa giống nhau giữa các lần huấn luyện, nên “cụm 3” ở version này và version khác có thể là hai nhóm nhà hàng hoàn toàn khác nhau. Ràng buộc đúng nghĩa cần khoá phức hợp (cluster_model_version, cluster_id) trỏ tới bảng ánh xạ centroid — vượt quá nhu cầu thực tế ở quy mô hiện tại, nên chấp nhận đánh đổi: chỉ diễn giải đúng khi đối chiếu với cluster_model_versions đang active. Quy tắc xử lý khi NULL (Cold Start): công thức xếp hạng KHÔNG được coi NULL này như 0 hay để nó lan truyền NULL; phải thay bằng điểm trung bình toàn hệ thống làm giá trị trung lập — chi tiết đầy đủ ở Phụ lục A.12.

source

VARCHAR(50)

NOT NULL

Nguồn dữ liệu, ví dụ 'google_places'.

external_place_id

VARCHAR(255)

UNIQUE (đầy đủ, không phải partial — xem Phụ lục A.14)

ID gốc từ nguồn. Pipeline thu thập (FR-7.1/7.3) bắt buộc UPSERT theo trường này, không bao giờ INSERT khi đã tồn tại kể cả lúc is_active = false.

updated_by

VARCHAR(20)

NOT NULL, CHECK (updated_by IN ('crawler','batch_pipeline','manual'))

Nguồn gốc lần cập nhật gần nhất — phục vụ audit khi cần truy vết vì sao một trường bị đổi (Phụ lục A.17).

created_at

TIMESTAMPTZ

NOT NULL

Bất biến — không cập nhật lại sau khi tạo.

updated_at

TIMESTAMPTZ

NOT NULL

Tự cập nhật mỗi lần bản ghi thay đổi (trigger hoặc tầng ứng dụng).

dishes — Dữ liệu gốc

Nguồn: SRS mục 6.1 (Dish); FR-6.1.

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

id

BIGSERIAL

PK

Định danh món ăn.

restaurant_id

UUID

FK → restaurants(id) ON DELETE RESTRICT ON UPDATE CASCADE, NOT NULL

Nhà hàng sở hữu món ăn.

name

VARCHAR(255)

NOT NULL

Tên món.

category

VARCHAR(100)

NULLABLE

Nhóm món (canh/nước, khô, tráng miệng...) — cố ý để tự do (không CHECK), khác temperature/portion_size — xem lý do ở Phụ lục A.17.

spice_level

SMALLINT

CHECK (spice_level BETWEEN 0 AND 5)

Mức độ cay.

temperature

VARCHAR(20)

CHECK (temperature IN ('hot','cold','neutral'))

Nóng/lạnh/trung tính.

portion_size

VARCHAR(20)

CHECK (portion_size IN ('light','regular','heavy'))

Độ no.

mood_keywords

TEXT[]

NULLABLE

Từ khoá cảm xúc liên quan, dùng cho FR-6.2.

price

NUMERIC(12,0)

NULLABLE

Giá món, nếu công khai.

is_active

BOOLEAN

NOT NULL DEFAULT true

Cờ soft-delete — false khi món ngừng bán. Bắt buộc: pipeline đề xuất món (FR-6.4) phải lọc is_active = true trên tập ứng viên TRƯỚC khi xếp hạng, không lọc sau — tránh sinh ra suggested_dish_id trỏ tới món đã ngừng bán (Phụ lục A.16).

deleted_at

TIMESTAMPTZ

NULLABLE, CHECK (deleted_at IS NULL OR is_active = false)

Thời điểm ngừng bán — đồng bộ đúng quy tắc với restaurants.deleted_at (mục 4), tránh hai bảng cùng dùng soft-delete nhưng có cấu trúc lệch nhau.

updated_by

VARCHAR(20)

NOT NULL, CHECK (updated_by IN ('crawler','batch_pipeline','manual'))

Nguồn gốc lần cập nhật gần nhất.

created_at, updated_at

TIMESTAMPTZ

NOT NULL

Thời điểm tạo/cập nhật.

reviews — Dữ liệu gốc

Nguồn: SRS mục 6.1 (Review); FR-7.2, FR-7.6.

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

id

BIGSERIAL

PK

Định danh review.

restaurant_id

UUID

FK → restaurants(id) ON DELETE RESTRICT ON UPDATE CASCADE, NOT NULL

Nhà hàng được đánh giá.

source

VARCHAR(50)

NOT NULL

Nguồn thu thập (google_places, tiktok...).

source_review_id

VARCHAR(255)

NULLABLE, UNIQUE cùng source

ID gốc — dùng khử trùng lặp giữa các lần thu thập.

content

TEXT

NOT NULL

Nội dung văn bản (review chữ, hoặc transcript từ ASR — FR-7.6).

content_type

VARCHAR(20)

CHECK (content_type IN ('text','video_transcript'))

Phân biệt review chữ và transcript video, phục vụ theo dõi độ tin cậy riêng cho từng loại.

rating_given

SMALLINT

NULLABLE

Điểm đánh giá kèm theo review, nếu nguồn có cung cấp.

reviewed_at

TIMESTAMPTZ

NULLABLE

Thời điểm review gốc được đăng, nếu xác định được.

collected_at

TIMESTAMPTZ

NOT NULL

Thời điểm hệ thống thu thập — dùng làm trọng số độ mới khi tổng hợp (FR-7.7).

review_summaries — Dữ liệu suy diễn

Nguồn: SRS mục 6.1 (ReviewSummary); FR-5.1. Thiết kế lại theo hướng chèn thêm (append), không ghi đè: mỗi lần pipeline offline chạy lại tự động tạo một bản ghi lịch sử mới, không cần cơ chế archive riêng — dữ liệu dùng để hiển thị luôn là bản ghi có generated_at lớn nhất.

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

id

BIGSERIAL

PK

Định danh bản tổng hợp — mỗi lần tính lại là một dòng mới.

restaurant_id

UUID

FK → restaurants(id) ON DELETE RESTRICT, NOT NULL

Nhà hàng được tổng hợp.

strengths

TEXT

NULLABLE

Điểm mạnh tổng hợp.

weaknesses

TEXT

NULLABLE

Điểm yếu tổng hợp.

suited_for

TEXT[]

NULLABLE

Nhóm người dùng phù hợp.

based_on_review_count

INTEGER

NOT NULL

Số review dùng để tổng hợp — cần hiển thị cho minh bạch (Explainability, ADR mục 9).

generated_at

TIMESTAMPTZ

NOT NULL

Thời điểm sinh bản tổng hợp — kết hợp UNIQUE(restaurant_id, generated_at); truy vấn hiển thị luôn lấy MAX(generated_at) theo restaurant_id (xem chỉ mục ở mục 6).

restaurant_experience_features — Dữ liệu suy diễn

Nguồn: SRS mục 6.1 (RestaurantExperienceFeature); FR-7.7, FR-7.8. Đây là vector đặc trưng đầu vào cho phân cụm — khác với experience_cluster_id trên restaurants là kết quả đầu ra của phân cụm (xem phân biệt ở Phụ lục A.3).

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

restaurant_id

UUID

PK, FK → restaurants(id) ON DELETE RESTRICT

Quan hệ 1-1 theo phiên bản đặc trưng mới nhất.

ambience_score_raw

NUMERIC(3,2)

NULLABLE

Điểm không gian suy ra từ văn bản, trước chuẩn hoá.

ambience_score_normalized

NUMERIC(5,4)

NULLABLE

Điểm không gian sau Z-score, dùng làm đầu vào KMeans.

noise_score_raw

NUMERIC(3,2)

NULLABLE

Điểm độ ồn suy ra từ văn bản, trước chuẩn hoá.

noise_score_normalized

NUMERIC(5,4)

NULLABLE

Điểm độ ồn sau Z-score.

ambience_review_count

INTEGER

NOT NULL DEFAULT 0

Số review đề cập khía cạnh không gian — căn cứ tính cờ độ tin cậy.

noise_review_count

INTEGER

NOT NULL DEFAULT 0

Số review đề cập khía cạnh độ ồn.

confidence_flag

VARCHAR(20)

CHECK (confidence_flag IN ('low','sufficient'))

Cờ độ tin cậy theo FR-7.8 — 'low' khi số review dưới ngưỡng tối thiểu quy định.

search_queries — Dữ liệu giao dịch

Nguồn: SRS mục 6.1 (SearchQuery). Không còn cột “danh sách kết quả trả về” như bản mô tả tóm tắt ở SRS — tách sang search_result_items (xem Phụ lục A.1).

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

id

UUID

PK

Định danh lượt tìm kiếm.

session_id

VARCHAR(100)

NOT NULL

Định danh phiên ẩn danh (NFR-3), không gắn thông tin cá nhân.

query_text

TEXT

NULLABLE

Câu tìm kiếm tự do (FR-2.1); có thể rỗng nếu người dùng chỉ dùng bộ lọc.

latitude, longitude

DOUBLE PRECISION

NOT NULL, CHECK cùng ràng buộc biên độ như restaurants (mục 4)

Vị trí tìm kiếm tại thời điểm truy vấn.

budget_constraint

NUMERIC(12,0)

NULLABLE

Ràng buộc ngân sách (FR-2.3).

dietary_constraint

TEXT[]

NULLABLE

Ràng buộc dị ứng/kiêng khem.

hours_constraint

VARCHAR(50)

NULLABLE

Ràng buộc giờ mở cửa mong muốn.

searched_at

TIMESTAMPTZ

NOT NULL

Thời điểm tìm kiếm — dùng để tra ContextSignal tại đúng thời điểm đó (xem mục 6).

search_result_items ⚠ bảng mới, xem Phụ lục A.1 — Dữ liệu giao dịch

Không có trong bốn tài liệu nguồn dưới dạng một entity đầy đủ — chỉ được nhắc tên một lần ở WBS mục 2.4 (“entity SearchResultItem”) mà chưa từng thiết kế trường. Tài liệu này thiết kế đầy đủ để lấp khoảng trống đó.

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

id

BIGSERIAL

PK

Định danh một dòng kết quả.

search_query_id

UUID

FK → search_queries(id) ON DELETE RESTRICT, NOT NULL

Lượt tìm kiếm sinh ra kết quả này.

restaurant_id

UUID

FK → restaurants(id) ON DELETE RESTRICT, NOT NULL

Nhà hàng xuất hiện trong kết quả.

rank_position

SMALLINT

NOT NULL

Vị trí trong danh sách hiển thị — cần cho tính NDCG/Precision@K và hiệu chỉnh position bias khi huấn luyện mô hình học có giám sát.

predicted_score

NUMERIC(6,4)

NOT NULL

Điểm phù hợp do RankingUseCase tính ra tại thời điểm đó.

suggested_dish_id

BIGINT

FK → dishes(id) ON DELETE SET NULL, NULLABLE

Món ăn gợi ý kèm theo (FR-6.4). SET NULL (khác RESTRICT) vì mất gợi ý món không làm hỏng ý nghĩa của cả dòng kết quả nhà hàng — chỉ RESTRICT cho các FK mà việc mất tham chiếu làm dữ liệu vô nghĩa.

ranking_model_version

VARCHAR(50)

FK → ranking_model_versions(version_tag) ON DELETE RESTRICT, NOT NULL

Ghi lại đúng phiên bản mô hình/công thức đã tạo ra điểm số này — bắt buộc cho Ablation Study (ADR mục 10) và truy vết khi so sánh Baseline/Proposed.

interaction_events — Dữ liệu giao dịch

Nguồn: SRS mục 6.1 (InteractionEvent); FR-9.1–9.3. Trường tham chiếu đổi từ (search_query_id + restaurant_id + vị trí) sang một khoá duy nhất search_result_item_id để không lặp lại dữ liệu đã có sẵn ở bảng trên (chuẩn hoá quan hệ — xem Phụ lục A.1).

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

id

BIGSERIAL

PK

Định danh sự kiện.

search_result_item_id

BIGINT

FK → search_result_items(id) ON DELETE RESTRICT, NOT NULL

Dòng kết quả mà người dùng tương tác.

action_type

VARCHAR(30)

CHECK (action_type IN ('view_detail','get_directions','save','explicit_positive','explicit_negative'))

Loại hành động (FR-9.1, FR-9.4).

dwell_time_ms

INTEGER

NULLABLE

Thời gian ở lại (nếu action_type = view_detail), dùng để lọc click nhầm.

is_positive_signal

BOOLEAN

NOT NULL

Kết quả áp dụng quy tắc phân loại tín hiệu dương (FR-9.3) — tính sẵn tại thời điểm ghi, không tính lại mỗi lần truy vấn.

occurred_at

TIMESTAMPTZ

NOT NULL

Thời điểm xảy ra sự kiện.

session_id

VARCHAR(100)

NOT NULL

Trùng với session_id của search_queries tương ứng (qua search_result_item_id), tách riêng để truy vấn nhanh không cần join.

dataset_snapshots — Artifact mô hình & phiên bản

Nguồn: Kiến trúc Kỹ thuật mục 9.1 (mô tả bằng lời, chưa có bảng); WBS mục Lộ trình (kế hoạch sao lưu).

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

version_tag

VARCHAR(50)

PK

Ví dụ 'dataset_2026_07' — theo đúng quy ước đặt tên ở Kiến trúc Kỹ thuật mục 9.1.

source_pipeline_run_at

TIMESTAMPTZ

NOT NULL

Thời điểm pipeline crawl/làm sạch chạy xong.

restaurant_count, review_count

INTEGER

NOT NULL

Quy mô snapshot — đối chiếu ngưỡng tối thiểu ở Assumption Register (ADR mục 3, ≥300 bản ghi).

quality_check_passed

BOOLEAN

NOT NULL

Kết quả bước kiểm soát chất lượng (SRS mục 2, FR-7.3).

quality_report

JSONB

NULLABLE

Chi tiết tỷ lệ thiếu/trùng lặp — dùng cho báo cáo.

is_active

BOOLEAN

NOT NULL DEFAULT false

Chỉ một snapshot active tại một thời điểm; snapshot mới chỉ bật cờ này sau khi quality_check_passed = true (Kiến trúc Kỹ thuật mục 9.1).

created_at

TIMESTAMPTZ

NOT NULL

Thời điểm tạo bản ghi version.

cluster_model_versions — Artifact mô hình & phiên bản

Nguồn: Kiến trúc Kỹ thuật mục 6.3, 9.2 (centroid + cluster_id phải cùng version, không tách rời).

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

version_tag

VARCHAR(50)

PK

Ví dụ 'cluster_model_v2'.

trained_at

TIMESTAMPTZ

NOT NULL

Thời điểm KMeansTrainingJob chạy xong.

k_clusters

SMALLINT

NOT NULL

Số cụm k đã chọn (ADR-01, qua Elbow + Silhouette).

silhouette_score

NUMERIC(4,3)

NOT NULL

Đối chiếu ngưỡng tối thiểu và Review Trigger ở ADR-01.

centroids

JSONB

NOT NULL

Toạ độ tâm cụm — lưu cùng version với cluster_id đã gán, không tách rời (Kiến trúc Kỹ thuật mục 6.3, 9.2).

dataset_snapshot_version

VARCHAR(50)

FK → dataset_snapshots(version_tag) ON DELETE RESTRICT, NOT NULL

Snapshot dữ liệu dùng để huấn luyện phiên bản cụm này.

is_active

BOOLEAN

NOT NULL DEFAULT false

Chỉ bật sau khi đạt ngưỡng nghiệm thu (WBS, bảng tiêu chí theo mốc M2).

ranking_model_versions — Artifact mô hình & phiên bản

Nguồn: Kiến trúc Kỹ thuật mục 9.2, 9.3 (Development/Evaluation Set); WBS mục “Nguồn gốc trọng số công thức xếp hạng”; ADR-06.

Trường

Kiểu dữ liệu

Ràng buộc

Mô tả

version_tag

VARCHAR(50)

PK

Ví dụ 'ranking_model_v3'.

model_type

VARCHAR(20)

CHECK (model_type IN ('heuristic','ml_supervised'))

Phân biệt HeuristicRankingAdapter và MLRankingAdapter (Kiến trúc Kỹ thuật mục 4.3).

weights_or_artifact_path

JSONB

NOT NULL

Trọng số w1…w5 (nếu heuristic) hoặc đường dẫn artifact .pkl (nếu ml_supervised).

dataset_snapshot_version

VARCHAR(50)

FK → dataset_snapshots(version_tag) ON DELETE RESTRICT, NOT NULL

Snapshot dữ liệu nền mà phiên bản xếp hạng này được tinh chỉnh/huấn luyện trên đó.

cluster_model_version

VARCHAR(50)

FK → cluster_model_versions(version_tag) ON DELETE RESTRICT, NULLABLE

Phiên bản cụm dùng làm tín hiệu đầu vào (nếu công thức có dùng cluster_score) — bắt buộc phải cùng một cặp dataset/cluster nhất quán, tránh tình huống Cluster huấn luyện từ Dataset 1 nhưng Ranking lại dùng Dataset 2 (xem Phụ lục A.13).

dev_set_version

VARCHAR(50)

NOT NULL

Định danh Development Set dùng để tinh chỉnh — không được trùng với eval_set_version (Kiến trúc Kỹ thuật mục 9.3).

eval_set_version

VARCHAR(50)

NOT NULL

Định danh Evaluation Set dùng để đánh giá chính thức, chỉ dùng một lần mỗi lượt đánh giá.

precision_at_5

NUMERIC(4,3)

NULLABLE

Tiêu chí nghiệm thu chính (WBS, mốc M2; ADR mục 10, 11).

intra_list_diversity_at_5

NUMERIC(4,3)

NULLABLE

Bổ sung theo ADR mục 8 — đo cùng lúc với precision_at_5, không thay thế nhau.

ndcg

NUMERIC(4,3)

NULLABLE

Dùng khi đã có đủ InteractionEvent để tính (SRS mục 7).

is_active

BOOLEAN

NOT NULL DEFAULT false

Đổi qua config/di_container khi promote (Kiến trúc Kỹ thuật mục 9.2).

Ghi chú: ContextSignal / ContextVector / UserContext — không phải bảng dữ liệu

SRS mục 6.1 liệt kê ContextSignal (thời tiết, giao thông, thời điểm) và Kiến trúc Kỹ thuật nhắc ContextVector, UserContext như các khái niệm Domain. Cả ba đều là dữ liệu tính toán tại thời điểm truy vấn (runtime), không lưu trữ lâu dài (SRS mục 6.2) — về bản chất là Value Object/DTO truyền giữa các lớp trong Clean Architecture, không cần bảng CSDL riêng. UserContext tương ứng với nội dung của một bản ghi search_queries tại thời điểm request; ContextVector là biểu diễn vector tạm thời của UserContext, không persist.

5. Bảng tóm tắt quan hệ

Cột “Bản chất” dùng ký hiệu crow's-foot: 1 = bắt buộc đúng một; 0..1 = tuỳ chọn tối đa một; 0..N = từ không đến nhiều. Toàn bộ quan hệ 1-nhiều trong hệ thống đều ghi 0..N ở đầu “nhiều” (không dùng N/nhiều không kèm cận dưới) vì không có bảng con nào chắc chắn đã có bản ghi ngay khi bảng cha vừa được tạo — sửa lại so với bản trước để phản ánh đúng nghiệp vụ (một nhà hàng mới crawl có thể chưa có review/dish/kết quả tìm kiếm nào).

Quan hệ

Bản chất

ON DELETE

Ghi chú

restaurants → dishes

1 — 0..N

RESTRICT

Một nhà hàng có thể chưa có món nào (mới crawl thực đơn chưa xong); xoá cứng nhà hàng bị chặn, dùng is_active.

restaurants → reviews

1 — 0..N

RESTRICT

Một nhà hàng mới có thể chưa có review nào.

restaurants → review_summaries

1 — 0..N

RESTRICT

Append-only theo phiên bản (mục 2.2, 4); có thể là 0 nếu pipeline tổng hợp chưa từng chạy cho nhà hàng đó.

restaurants → restaurant_experience_features

1 — 0..1

RESTRICT

Đúng 1-1 khi đã có, nhưng tối đa một bản (không phải append-only) và có thể chưa tồn tại — 0..1, không phải 1–1 bắt buộc.

search_queries → search_result_items

1 — 0..N

RESTRICT

Một lượt tìm kiếm có thể trả về 0 kết quả nếu ràng buộc cứng loại hết ứng viên.

restaurants → search_result_items

1 — 0..N

RESTRICT

Một nhà hàng mới có thể chưa từng xuất hiện trong lượt tìm kiếm nào.

dishes → search_result_items

0..1 — 0..N

SET NULL

Đầu dishes cũng là 0..1 (không phải 1) vì suggested_dish_id nullable — một dòng kết quả có thể không gợi ý món nào. Chỉ có khi module Dish Recommendation kích hoạt (Giai đoạn 3).

ranking_model_versions → search_result_items

1 — 0..N

RESTRICT

Một phiên bản mô hình có thể chưa từng tạo ra kết quả nào nếu chưa is_active.

search_result_items → interaction_events

1 — 0..N

RESTRICT

Một dòng kết quả có thể không nhận được tương tác nào (người dùng lướt qua).

dataset_snapshots → cluster_model_versions

1 — 0..N

RESTRICT

Một snapshot có thể chưa từng được dùng để huấn luyện cụm.

dataset_snapshots → ranking_model_versions

1 — 0..N

RESTRICT

Truy vết dataset nền cho từng phiên bản xếp hạng — bổ sung mới, xem Phụ lục A.13.

cluster_model_versions → ranking_model_versions

0..1 — 0..N

RESTRICT

Đầu cluster_model_versions là 0..1 vì cluster_model_version trên ranking_model_versions nullable (không phải công thức nào cũng dùng tín hiệu cụm) — xem Phụ lục A.13.

restaurants → cluster_model_versions

n–1 (gián tiếp qua experience_cluster_id)

— (không phải FK cứng)

cluster_id trên restaurants chỉ có ý nghĩa khi đối chiếu đúng version cluster_model_versions đang active (Kiến trúc Kỹ thuật mục 6.3, rủi ro lệch version).

Nguyên tắc chọn RESTRICT làm mặc định: vì phần lớn bảng gốc (restaurants, dishes) đã có soft-delete, hard-delete lẽ ra không bao giờ xảy ra trong vận hành bình thường — RESTRICT đóng vai trò hàng rào chặn thao tác xoá cứng ngoài ý muốn ở tầng CSDL, không phó mặc hoàn toàn cho kỷ luật của tầng ứng dụng. CASCADE không được dùng ở bất kỳ quan hệ nào trong hệ thống này, vì mọi bảng con đều là dữ liệu có giá trị lịch sử/huấn luyện — xoá lan truyền sẽ luôn là mất mát không mong muốn.

6. Chỉ mục & ràng buộc khuyến nghị

Bảng / cột

Loại chỉ mục

Lý do

restaurants.description_embedding

ANN (HNSW, pgvector)

Truy vấn tương đồng ngữ nghĩa (FR-4.2) không thể quét toàn bộ bảng khi số nhà hàng lớn. Ưu tiên HNSW hơn IVFFlat cho quy mô dữ liệu vài nghìn dòng — build nhanh hơn, không cần bước 'train' như IVFFlat.

restaurants (latitude, longitude)

Cột geography(Point,4326) + chỉ mục GiST (PostGIS)

Lọc theo bán kính/tâm bản đồ (FR-1.4) chạy mỗi lượt tìm kiếm. Nếu không muốn cài đặt PostGIS đầy đủ, phương án nhẹ hơn là extension cube + earthdistance với chỉ mục GiST tương ứng — độ chính xác thấp hơn nhưng đủ dùng cho phạm vi một thành phố.

restaurants.external_place_id

UNIQUE B-tree (đầy đủ, không phải partial)

Chặn trùng lặp ngay ở tầng CSDL — xem lý do giữ nguyên UNIQUE đầy đủ ở Phụ lục A.14.

restaurants.is_active, dishes.is_active

Partial index WHERE is_active = true

Toàn bộ truy vấn tìm kiếm/xếp hạng (FR-4.x) phải lọc is_active — điều kiện WHERE xuất hiện ở gần như mọi câu truy vấn người dùng cuối.

reviews.restaurant_id

B-tree (FK index)

Join thường xuyên khi tổng hợp review theo nhà hàng (FR-5.1, FR-7.7) — chưa có ở bản v1.0, bổ sung ở Phụ lục A.11.

reviews (restaurant_id, collected_at DESC)

Composite B-tree

Pipeline tổng hợp luôn cần lấy review theo nhà hàng, sắp theo độ mới (FR-7.7 trọng số theo thời gian) — truy vấn thực tế, không chỉ tra cứu đơn lẻ.

reviews (restaurant_id, source, source_review_id)

UNIQUE composite

Khử trùng lặp review khi crawl lại cùng nguồn (FR-7.3).

search_result_items.search_query_id

B-tree (FK index)

Chưa có ở bản v1.0 — cần cho mọi truy vấn 'lấy lại kết quả của một lượt tìm kiếm'.

search_result_items.restaurant_id

B-tree (FK index)

Chưa có ở bản v1.0 — cần khi truy vấn lịch sử một nhà hàng từng xuất hiện ở những lượt tìm kiếm nào.

search_result_items (search_query_id, rank_position)

Composite B-tree

Truy vấn lại toàn bộ kết quả theo đúng thứ tự hiển thị của một lượt tìm kiếm.

interaction_events.search_result_item_id

B-tree (FK index)

Join thường xuyên khi tổng hợp dữ liệu huấn luyện mô hình xếp hạng.

search_queries (session_id, searched_at)

Composite B-tree

Thống kê hành vi theo phiên (FR-8.2) và truy vấn 'các lượt tìm kiếm gần nhất của một phiên'.

*_model_versions.is_active

Partial index WHERE is_active = true

Truy vấn “phiên bản đang dùng” là truy vấn nóng nhất trên các bảng version, cần nhanh dù bảng có nhiều bản ghi lịch sử.

review_summaries (restaurant_id, generated_at DESC)

UNIQUE composite

Bảng append-only theo mục 4 — cần tra nhanh bản mới nhất theo từng nhà hàng.

Nguyên tắc bắt buộc đi kèm soft-delete: mọi truy vấn phục vụ người dùng cuối (tìm kiếm, xếp hạng, chi tiết nhà hàng/món ăn) phải có điều kiện WHERE is_active = true; các truy vấn phục vụ phân tích/huấn luyện mô hình (đọc lại interaction_events, search_result_items lịch sử) thì không lọc, vì nhà hàng đã ngừng hoạt động vẫn là dữ liệu hợp lệ cho mục đích huấn luyện.

6.1. View cho review_summaries (khuyến nghị, không bắt buộc ở MVP)

Truy vấn MAX(generated_at) rồi join lại để lấy bản tóm tắt mới nhất là đúng nhưng lặp lại logic này ở nhiều nơi (API chi tiết, API danh sách kết quả) dễ sai sót và tốn chi phí tính toán nếu bảng lớn. Khuyến nghị tạo một View (hoặc Materialized View nếu đo được độ trễ đáng kể ở giai đoạn sau) tên latest_review_summary, định nghĩa bằng DISTINCT ON (restaurant_id) ... ORDER BY restaurant_id, generated_at DESC — cách này hiệu quả hơn subquery MAX() kết hợp self-join trong PostgreSQL. Đây là cải tiến hiệu năng, không phải yêu cầu bắt buộc ở quy mô MVP — có thể triển khai sau khi đã đo được truy vấn này thực sự chậm.

Phụ lục A — Nhật ký quyết định thiết kế (Design Decision Log)

Phần này ghi lại lý do đằng sau từng quyết định thiết kế qua các vòng rà soát — kể cả những đề xuất đã cân nhắc rồi từ chối. Đây KHÔNG phải một phần của đặc tả schema (mục 1–6 ở trên là hiện trạng chính thức, đủ để viết migration); mục đích của phụ lục là chuẩn bị trả lời câu hỏi “tại sao không làm theo cách khác” khi bảo vệ đồ án, và giữ lại ngữ cảnh cho người đọc sau này khi cần thay đổi thiết kế.

A.1. search_result_items chưa từng được thiết kế đầy đủ

SRS mục 6.1 mô tả SearchQuery có thuộc tính “danh sách kết quả trả về (có thứ tự)” — tức lưu kết quả dạng mảng lồng trong chính bản ghi tìm kiếm. Trong khi đó, WBS mục 2.4 (API ghi nhận sự kiện tương tác) lại nhắc tới “entity SearchResultItem” như một bảng riêng, nhưng không tài liệu nào định nghĩa trường của nó. Hai cách mô tả này mâu thuẫn nhau: lưu mảng lồng trong SearchQuery khiến InteractionEvent không có một khoá ngoại rõ ràng để trỏ tới đúng “vị trí kết quả” đã tương tác mà không phải giải nén JSON. Tài liệu này chọn theo hướng WBS (bảng trung gian chuẩn hoá) và thiết kế đầy đủ trường ở mục 4 — khuyến nghị SRS và Kiến trúc Kỹ thuật cập nhật lại mục 6.1 và sơ đồ để nhất quán.

A.2. WBS tham chiếu FR-7.9 nhưng SRS không có mã này

WBS mục 2.2, dòng 2.9 (“Chuẩn hoá đặc trưng trước phân cụm — Z-score”) ghi rõ FR/NFR liên quan là FR-7.9. Tuy nhiên SRS v1.2 (bản đã tải lên) mục 3.7 chỉ liệt kê đến FR-7.8, không có FR-7.9. Đây là một khoảng trống truy vết (traceability gap): một công việc trong WBS không có yêu cầu chức năng tương ứng để truy ngược. Tài liệu này không tự ý thêm FR-7.9 vào SRS (nằm ngoài phạm vi Data Dictionary) — chỉ ghi nhận và khuyến nghị bổ sung FR-7.9 vào lần cập nhật SRS kế tiếp, mô tả đúng nội dung chuẩn hoá Z-score đã thiết kế trong restaurant_experience_features ở mục 4.

A.3. Phân biệt chưa rõ giữa đặc trưng đầu vào và nhãn cụm đầu ra

Cả bốn tài liệu nguồn đều nhắc “cụm trải nghiệm” nhưng không luôn phân biệt rạch ròi hai khái niệm khác nhau: (a) restaurant_experience_features — vector đặc trưng đầu vào cho KMeans (không gian, độ ồn), và (b) restaurants.experience_cluster_id — nhãn cụm đầu ra sau khi KMeans chạy xong. Tài liệu này tách rõ hai bảng, đúng theo mô tả kỹ hơn ở Kiến trúc Kỹ thuật mục 6.3 (huấn luyện offline ghi cluster_id vào Restaurant qua Repository, tách khỏi vector đặc trưng dùng làm đầu vào).

A.4. Artifact mô hình/dữ liệu được mô tả bằng lời nhưng chưa từng là bảng dữ liệu

Kiến trúc Kỹ thuật mục 9 mô tả khá chi tiết nguyên tắc versioning cho dataset và mô hình (snapshot có tên, không ghi đè, chỉ một bản active...) nhưng trình bày dưới dạng quy ước vận hành bằng lời, không phải như một entity có thể lưu trong CSDL và truy vấn được (ví dụ: “phiên bản mô hình đang active là gì, huấn luyện lúc nào, đạt Precision@5 bao nhiêu” — nếu không có bảng, câu trả lời phải tìm trong tên file/thư mục thủ công). Tài liệu này hình thức hoá thành ba bảng (dataset_snapshots, cluster_model_versions, ranking_model_versions) ở mục 4, giữ nguyên đúng nguyên tắc đã mô tả, chỉ thêm cấu trúc lưu trữ truy vấn được.

Bốn điểm trên không phải lỗi nghiêm trọng của các tài liệu nguồn — chúng là hệ quả tự nhiên của việc bốn tài liệu được viết ở bốn thời điểm, cho bốn mục đích khác nhau (yêu cầu, kiến trúc, công việc, quyết định), không tài liệu nào có vai trò “nguồn sự thật duy nhất” cho lược đồ dữ liệu. Đây chính là lý do tài liệu Data Dictionary này cần tồn tại như một tài liệu độc lập, không gộp lại vào SRS hay Kiến trúc Kỹ thuật.

A.5. Thiếu cơ chế soft-delete (đã sửa)

Bản v1.0 chưa có trường quản lý trạng thái hoạt động trên restaurants, dishes — hard-delete trong thực tế vận hành (nhà hàng đóng cửa, món ngừng bán) sẽ phá vỡ khoá ngoại từ reviews, search_result_items, interaction_events, làm hỏng dữ liệu huấn luyện mô hình xếp hạng. Đã bổ sung is_active + deleted_at cho cả hai bảng ở mục 4, kèm nguyên tắc bắt buộc lọc is_active ở mục 6.

A.6. review_summaries ghi đè làm mất khả năng theo dõi thay đổi theo thời gian (đã sửa)

Bản v1.0 dùng restaurant_id làm khoá chính (quan hệ 1-1, ghi đè mỗi lần tính lại). Dữ liệu gốc (reviews) không mất vì là append-only, nhưng bản tóm tắt tại một thời điểm cụ thể trong quá khứ thì không truy lại trực tiếp được. Đã đổi sang id riêng + UNIQUE(restaurant_id, generated_at), mỗi lần pipeline chạy lại tạo một bản ghi mới thay vì ghi đè — chi phí gần như bằng không (không cần bảng archive riêng như đề xuất ban đầu) vì việc này xảy ra tự nhiên theo đúng tần suất pipeline offline đã chạy sẵn.

A.7. Vector dimension chưa xác định (đã sửa)

Cột description_embedding ở bản v1.0 để VECTOR(n) — chưa chọn mô hình embedding nên không thể sinh script tạo bảng thật. Đã chốt VECTOR(768) dùng multilingual-e5-base (hỗ trợ tiếng Việt, tự host, không phụ thuộc API trả phí — nhất quán với cách xử lý API bản đồ/thời tiết đã quyết định trước đó trong dự án). Đây là quyết định kiến trúc đủ quan trọng để cần một mục ADR riêng trong tài liệu ADR/Assumption/Scope, không chỉ dừng ở Data Dictionary — khuyến nghị bổ sung ở lần cập nhật kế tiếp.

A.8. Đề xuất tách dữ liệu giao dịch sang Kafka/Data Warehouse — cân nhắc nhưng không áp dụng

Có ý kiến đề xuất định tuyến search_queries, search_result_items, interaction_events qua message queue và lưu dài hạn ở data warehouse riêng, với lý do dữ liệu append-only sẽ phình to và ảnh hưởng hiệu năng đọc/ghi của dữ liệu gốc. Nguyên tắc tách bạch dữ liệu giao dịch khỏi dữ liệu gốc là đúng (đã thể hiện ở việc phân nhóm tại mục 2.2), nhưng giải pháp cụ thể không tương xứng với quy mô dự án: ở phạm vi thí điểm một thành phố, ước tính khối lượng interaction_events chỉ ở mức hàng triệu dòng/năm trong kịch bản lạc quan — PostgreSQL xử lý tốt ở quy mô này với chỉ mục phù hợp (mục 6), chưa đến ngưỡng cần hạ tầng streaming/warehouse riêng. Quyết định này để ngỏ, không đóng: nếu khối lượng thực tế vượt xa ước tính, hướng xử lý trước tiên nên là partition interaction_events theo tháng trong cùng PostgreSQL, rồi mới cân nhắc tách hạ tầng riêng khi có bằng chứng cụ thể về nghẽn hiệu năng — không nên đầu tư trước khi có nhu cầu thật (nguyên tắc đã áp dụng nhất quán khi từ chối Airflow cho pipeline offline ở WBS).

A.9. CHECK constraint tĩnh cho temperature/portion_size/action_type — cân nhắc nhưng giữ nguyên

Có ý kiến đề xuất chuyển các giá trị liệt kê cố định (dishes.temperature, dishes.portion_size, interaction_events.action_type) sang lookup table hoặc quản lý ở tầng ứng dụng, với lý do CHECK constraint đòi hỏi migration mỗi khi thêm giá trị mới. Giữ nguyên CHECK constraint vì cả ba trường đều được tham chiếu trực tiếp trong logic nghiệp vụ (FR-6.2 dùng temperature/portion_size để ánh xạ tâm trạng; FR-9.3 dùng action_type để phân loại tín hiệu dương) — thêm một giá trị mới luôn đòi hỏi sửa code nghiệp vụ tương ứng, nên migration constraint đi kèm không phải chi phí phát sinh thêm. Lookup table chỉ phù hợp cho dữ liệu mô tả không gắn logic cứng và đổi thường xuyên mà không cần sửa code — ví dụ dishes.category ở mục 4 đã để dạng tự do (không CHECK) đúng theo tinh thần này.

A.10. Thiếu chiến lược ON DELETE/ON UPDATE cho toàn bộ khoá ngoại (đã sửa)

Bản v1.0 chỉ ghi FK → bảng(cột) mà không quy định điều gì xảy ra khi bản ghi cha bị xoá — để ngỏ cho lập trình viên tự quyết ở tầng ứng dụng, trong khi đây phải là quy tắc CSDL. Đã bổ sung ON DELETE cho toàn bộ khoá ngoại ở mục 4, tổng hợp lại ở mục 5. Nguyên tắc áp dụng: RESTRICT làm mặc định (chặn xoá cứng, ép phải dùng soft-delete), SET NULL chỉ cho quan hệ tuỳ chọn mà mất tham chiếu không làm hỏng ý nghĩa bản ghi con (suggested_dish_id), không dùng CASCADE ở bất kỳ đâu vì mọi bảng con đều là dữ liệu lịch sử/huấn luyện có giá trị.

A.11. Thiếu chỉ mục tường minh cho một số khoá ngoại và các truy vấn tổng hợp thực tế (đã sửa)

Bản v1.0 chỉ liệt kê ANN, GiST, UNIQUE và một vài B-tree — bỏ sót chỉ mục cho reviews.restaurant_id, search_result_items.search_query_id, search_result_items.restaurant_id (đều là FK được join thường xuyên), và chưa có composite index cho các truy vấn tổng hợp thực tế của pipeline (reviews theo restaurant_id + collected_at DESC; search_queries theo session_id + searched_at). Đã bổ sung đầy đủ ở mục 6, đồng thời làm rõ lựa chọn PostGIS geography+GiST (hoặc earthdistance nếu muốn nhẹ hơn) thay vì nói chung chung “GiST hoặc tương đương” — tránh câu hỏi “truy vấn bán kính chạy kiểu gì” không có câu trả lời cụ thể.

A.12. Cold Start chưa xử lý triệt để trong công thức xếp hạng (đã sửa)

Bản v1.0 chỉ dừng ở việc gắn cờ NULL cho experience_cluster_id khi nhà hàng chưa qua huấn luyện, chưa quy định công thức xếp hạng phải xử lý NULL đó như thế nào — nguy cơ NULL lan truyền làm predicted_score thành NULL, hoặc vô tình mặc định = 0 khiến nhà hàng mới luôn bị điểm thấp nhất một cách không có căn cứ. Quy tắc bắt buộc bổ sung: khi experience_cluster_id IS NULL, cluster_score dùng trong công thức phải được thay bằng điểm trung bình toàn hệ thống (giá trị trung lập, không phải 0 và không phải NULL). Ngoài ra, chỉ trung lập hoá điểm số là chưa đủ để tránh nhà hàng mới bị chìm nghỉm vĩnh viễn — vì không được hiển thị đủ nhiều nên không bao giờ tích luỹ đủ review để thoát khỏi trạng thái cold-start. Khuyến nghị bổ sung một hệ số ưu tiên khám phá tạm thời cho nhà hàng mới, áp dụng một kỹ thuật exploration phù hợp (ví dụ: epsilon-greedy — không chốt cứng một thuật toán cụ thể ở tài liệu dữ liệu này, việc chọn kỹ thuật thuộc phạm vi thiết kế mô hình/ADR), giới hạn theo số lượt hiển thị hoặc thời gian cụ thể — không áp dụng vô thời hạn để tránh trở thành nhiễu (noise) lâu dài trong kết quả. Quy tắc số hoá công thức đầy đủ (giá trị δ, ngưỡng số lượt hiển thị, thuật toán exploration cụ thể) thuộc phạm vi ADR/thiết kế mô hình, không phải Data Dictionary — nhưng ràng buộc dữ liệu (cluster_score không được NULL/0 mặc định) được ghi nhận trực tiếp tại trường experience_cluster_id ở mục 4.

A.13. Thiếu truy vết đầy đủ giữa phiên bản xếp hạng và dataset/cluster đã dùng (đã sửa, mở rộng hơn góp ý gốc)

Bản v1.0 đã có dataset_snapshot_version trên cluster_model_versions (nguồn dữ liệu train cụm), nhưng ranking_model_versions chưa có liên kết tương tự — không trả lời được câu hỏi “phiên bản xếp hạng này được tinh chỉnh trên nền dataset/cluster nào”, dẫn tới rủi ro Cluster huấn luyện từ Dataset 1 nhưng Ranking lại dùng Dataset 2 mà không ai biết. Đã bổ sung dataset_snapshot_version và cluster_model_version (FK, nullable vì không phải công thức nào cũng dùng tín hiệu cụm) trực tiếp vào ranking_model_versions ở mục 4 — khép kín chuỗi truy vết dataset → cluster → ranking cho Ablation Study.

A.14. Đề xuất Partial Unique Index cho external_place_id — không áp dụng

Có ý kiến (và được nhắc lại ở lượt góp ý tiếp theo) đề xuất đổi UNIQUE trên external_place_id thành Partial Unique Index (WHERE is_active = true), lý do: nhà hàng đóng cửa rồi mở lại/crawl lại đúng place_id cũ sẽ khiến INSERT vi phạm UNIQUE. Không áp dụng đề xuất này vì nó tự mâu thuẫn với mục đích của chính soft-delete: cho phép INSERT một bản ghi mới với external_place_id đã tồn tại nghĩa là cùng một địa điểm vật lý có hai id khác nhau trong hệ thống — bản ghi cũ (giữ toàn bộ review/InteractionEvent lịch sử) và bản ghi mới (rỗng) — đúng kiểu đứt gãy dữ liệu mà soft-delete được thiết kế để ngăn, chỉ dịch chuyển thời điểm xảy ra. external_place_id là định danh Google Places gán cho một địa điểm vật lý, không đổi theo trạng thái mở/đóng cửa, nên về bản chất luôn là một thực thể duy nhất. Cách xử lý đúng nằm ở tầng logic ứng dụng: pipeline thu thập (FR-7.1/FR-7.3) phải UPSERT theo external_place_id — nếu đã tồn tại (kể cả is_active = false), cập nhật lại thông tin và bật is_active = true, không bao giờ INSERT mới. Giữ nguyên UNIQUE đầy đủ (không phải partial) đóng vai trò hàng rào CSDL ngăn crawler vô tình vi phạm đúng nguyên tắc này.

A.15. Vector dimension “cứng” gây rủi ro khi đổi mô hình embedding — ghi nhận, bổ sung chiến lược di chuyển

Có ý kiến lo ngại việc chốt VECTOR(768) trói buộc CSDL vào một phiên bản mô hình cụ thể, đổi sang mô hình khác (ví dụ 1024 chiều) sẽ cần ALTER TABLE nặng nề trên bảng Master. Về bản chất kỹ thuật, chi phí thật không nằm ở câu lệnh ALTER TABLE (đơn giản), mà ở việc phải sinh lại toàn bộ embedding cho mọi nhà hàng — chi phí này luôn xảy ra khi đổi mô hình bất kể có hardcode số chiều hay không, vì embedding của mô hình cũ và mới không tương thích nhau về mặt ngữ nghĩa dù cùng số chiều hay khác số chiều. Điểm cần bổ sung thực sự là chiến lược cắt chuyển không downtime: khi thử nghiệm/nâng cấp mô hình embedding mới, tạo cột mới (ví dụ description_embedding_v2 VECTOR(m)) hoặc bảng embedding riêng theo phiên bản thay vì ALTER TABLE tại chỗ, chạy pipeline offline điền dữ liệu cột mới, xây chỉ mục ANN mới song song, rồi mới cắt chuyển endpoint đọc sang cột mới — cho phép A/B test hai mô hình cùng lúc và rollback tức thời nếu mô hình mới kém hơn. Đồng ý với khuyến nghị ghi Review Trigger cho quyết định embedding model vào ADR (Phụ lục A.7) — bổ sung thêm chiến lược cắt chuyển này vào cùng mục ADR đó.

A.16. Dish Recommendation phải lọc is_active trước khi xếp hạng (đã sửa)

Cả hai lượt góp ý đều chỉ ra: nếu pipeline đề xuất món (FR-6.4) không lọc is_active = true trên tập ứng viên trước khi xếp hạng, có thể sinh ra suggested_dish_id trỏ tới món đã ngừng bán — người dùng bấm vào sẽ gặp lỗi không tìm thấy món. Đã ghi quy tắc bắt buộc trực tiếp vào trường dishes.is_active ở mục 4: lọc is_active = true PHẢI thực hiện trên tập ứng viên trước bước xếp hạng, không lọc sau — vì lọc sau vẫn để mô hình xếp hạng “thấy” và có thể chọn nhầm món đã ngừng bán trước khi bị loại. Quy tắc hiển thị cụ thể ở giao diện (ví dụ gắn nhãn “tạm ngừng phục vụ” hay ẩn hẳn khỏi danh sách) là quyết định UI/API, nằm ngoài phạm vi Data Dictionary — thuộc tài liệu Đặc tả API/giao diện khi được xây dựng.

A.17. Các quy tắc vận hành bổ sung — ghi nhận quyết định, chưa cần cơ chế triển khai ngay

Bốn điểm sau đều là quyết định cần ghi nhận rõ ràng để tránh câu hỏi bỏ ngỏ khi bảo vệ, nhưng không đòi hỏi xây dựng cơ chế phức tạp ngay ở quy mô MVP — nhất quán với nguyên tắc “ghi nhận quyết định, triển khai khi có bằng chứng cần thiết” đã áp dụng cho Phụ lục A.8:

Audit trail: đã bổ sung cột updated_by (crawler / batch_pipeline / manual) cho restaurants và dishes ở mục 4, trả lời được câu hỏi “ai/cái gì cập nhật lần cuối” mà không cần dựng hẳn một hệ thống audit log riêng.

Timestamp: created_at bất biến, updated_at tự cập nhật, deleted_at ràng buộc CHECK (deleted_at IS NULL OR is_active = false) — áp dụng đồng bộ cho cả restaurants và dishes ở mục 4 (đã đồng bộ, không còn lệch giữa hai bảng).

Transaction boundary khi crawl: một lượt crawl một nhà hàng (kèm dishes, reviews phát sinh cùng lượt) nên nằm trong một transaction duy nhất — thất bại ở bước ghi review không để lại một restaurant/dish mồ côi không có review nào dù thực tế có. Đây là quy tắc vận hành pipeline, ghi nhận ở đây, mô tả chi tiết hơn thuộc phạm vi ADR/thiết kế use case CrawlRestaurantsUseCase.

Data Retention Policy cho interaction_events: chưa xác định thời hạn lưu trữ hay chiến lược partition/archive khi bảng đủ lớn. Ghi nhận là quyết định để ngỏ có chủ đích (tương tự Phụ lục A.8) — tại quy mô MVP/thí điểm, chưa cần retention policy; sẽ xác định ngưỡng cụ thể (theo số dòng hoặc theo năm) khi có dữ liệu vận hành thực tế để ước lượng đúng, tránh đặt một con số tuỳ tiện không có căn cứ ngay từ bây giờ.

A.18. Chuẩn hoá & bổ sung nhỏ theo góp ý vòng 3 (đã sửa)

Chuẩn hoá toàn bộ cú pháp CHECK về một dạng thống nhất CHECK (cột ...) thay vì trộn lẫn ký hiệu rút gọn (0–5) và cú pháp đầy đủ ở các bảng khác nhau.

Đồng bộ deleted_at + CHECK (deleted_at IS NULL OR is_active = false) cho dishes, trước đó chỉ có ở restaurants dù cả hai bảng cùng dùng cơ chế soft-delete — điểm thiếu nhất quán đã sửa ở mục 4.

Bổ sung lý do kỹ thuật đầy đủ cho việc experience_cluster_id không dùng khoá ngoại cứng (trị số cụm không có ngữ nghĩa độc lập giữa các phiên bản huấn luyện) — trực tiếp tại trường ở mục 4, không chỉ ở bảng quan hệ mục 5.

Đổi cách diễn đạt exploration boost cho cold-start thành ví dụ minh hoạ kỹ thuật (epsilon-greedy là một ví dụ, không phải quyết định chốt cứng) — tránh Data Dictionary vô tình khoá một lựa chọn thuật toán thuộc phạm vi ADR/thiết kế mô hình.

Bổ sung mục 2.3 — Data Ownership (Source of Truth + Owner ở mức bảng cho toàn bộ Dữ liệu gốc); Authority chi tiết theo từng trường và quy tắc giải quyết xung đột Manual/Crawler được trỏ sang ADR thay vì lặp lại ở đây.

A.19. Vẽ lại ERD theo góp ý vòng 4 (đã sửa)

Bổ sung Subject Area (4 khung nhóm bảng theo đúng phân loại đã có ở mục 2.2) trực tiếp lên ERD; ghi rõ đây là nhóm hiển thị, không phải schema PostgreSQL thật — tránh hiểu nhầm thành yêu cầu tạo schema master/search/ml khi toàn bộ hệ thống chỉ dùng một schema public.

Sửa toàn bộ cardinality từ 1–n sang 1–0..N (và 1–1 thành 1–0..1 ở quan hệ thực sự tối đa một) — lỗi có thật, không phải góp ý phong cách: không bảng con nào chắc chắn có bản ghi ngay khi bảng cha vừa tạo, nhất quán với thiết kế Cold Start đã có ở Phụ lục A.12. Áp dụng cho toàn bộ 13 dòng ở bảng quan hệ mục 5 và toàn bộ nhãn trên ERD.

Thể hiện rõ FK tuỳ chọn (0..1) ở hai quan hệ trước đó chỉ ghi chú bằng lời: dishes → search_result_items (suggested_dish_id nullable) và cluster_model_versions → ranking_model_versions (cluster_model_version nullable).

Cập nhật ERD để khớp lại với Data Dictionary: ranking_model_versions trên sơ đồ trước đó chỉ có version_tag, thiếu hẳn dataset_snapshot_version và cluster_model_version dù hai trường này đã có trong bảng dữ liệu từ Phụ lục A.13 — ERD bị lạc hậu so với văn bản, nay đã đồng bộ lại.

Rà soát naming convention toàn bộ 21 trường dạng _id/_at/is_*/embedding — xác nhận đã nhất quán 100% từ trước, không có trường nào cần đổi tên (restaurant_id không lẫn restaurants_id, mọi mốc thời gian đều đúng hậu tố _at, mọi cờ boolean đều đúng tiền tố is_).

A.20. Tách hiện trạng khỏi lịch sử quyết định, bổ sung Glossary (đã sửa)

Chuyển toàn bộ mục “Vấn đề phát hiện & đã xử lý” (trước đây là mục 7, A.1–A.19) thành Phụ lục A độc lập ở cuối tài liệu — mục 1–6 giờ chỉ còn hiện trạng schema (đúng tinh thần “Data Dictionary là bản vẽ kỹ thuật, chỉ chứa sự thật hiện tại”). Không chuyển sang file ADR riêng vì không có toàn văn ADR hiện tại trong tay để đối chiếu an toàn — giữ trong cùng tài liệu dưới dạng phụ lục đạt cùng mục tiêu mà không có rủi ro lệch nội dung chéo file.

Bổ sung mục 1.3 — Glossary, chỉ gồm thuật ngữ đặc thù dự án (Experience Feature, Experience Cluster, Cold Start, Embedding, ANN, Dataset Snapshot, Source of Truth, Owner, Soft Delete, Subject Area, Version Drift), không đưa khái niệm CSDL phổ thông (PK/FK/UUID). Đặc biệt làm rõ Experience Feature và Experience Cluster KHÔNG phải cùng một khái niệm dù tên gần giống — đây là điểm dễ gây nhầm lẫn nhất khi đối chiếu thuật ngữ giữa Data Dictionary và Kiến trúc Kỹ thuật.

ERD bổ sung kiểu dữ liệu ngắn gọn (không precision) cho các trường PK/FK đã hiển thị — cân bằng giữa yêu cầu “ERD cần thể hiện Type” và nguyên tắc “giữ ERD gọn, chi tiết đầy đủ ở Data Dictionary” đã thống nhất từ trước; không mở rộng thêm cột dữ liệu nào ngoài PK/FK sẵn có.

Bổ sung bảng Lịch sử thay đổi tài liệu ở đầu (đồng bộ với SRS/WBS đã có bảng này từ trước — Data Dictionary trước đó là tài liệu duy nhất trong bộ chưa có).

Không vẽ thêm Use Case Diagram hay Sequence Diagram bổ sung: SRS đã có bảng UC-01–UC-08 dạng văn bản (không yêu cầu chuyển thành UML), và Sequence hiện có (Sơ đồ Kiến trúc, Hình 2) đã mô tả đúng luồng quan trọng nhất — thêm artifact mới không phục vụ mục tiêu “chỉ xác minh, không bổ sung nội dung” của vòng rà soát này.


# MoodBite_Dac_Ta_API

ĐẶC TẢ API

(API Specification)

MoodBite

Phiên bản 1.0

Ngày ban hành: 27/07/2026

Tài liệu nguồn: SRS v1.2, Kiến trúc Kỹ thuật v1.1, Sơ đồ Kiến trúc v1.0, Data Dictionary & ERD v1.5

Lịch sử thay đổi tài liệu

Phiên bản

Ngày

Mô tả thay đổi

1.0

27/07/2026

Khởi tạo đặc tả API — 5 endpoint MVP (Giai đoạn 1), phát hiện và lấp một khoảng trống Use Case trong Kiến trúc Kỹ thuật (mục 5).

Mục lục

1. Giới thiệu

1.1. Mục đích & phạm vi

Tài liệu này đặc tả tầng presentation/api (REST controllers) của MoodBite ở mức endpoint — method, path, request/response schema, mã lỗi — đủ chi tiết để cài đặt hoặc mock mà không cần đoán thêm. Phạm vi chỉ gồm API phục vụ người dùng cuối qua trình duyệt (Giai đoạn 1 — MVP theo WBS); các job offline (crawl, huấn luyện mô hình) không lộ qua REST API công khai, đã có ở Sơ đồ Kiến trúc mục 5 (Deployment), không lặp lại ở đây.

Mỗi endpoint được truy vết ngược về đúng Use Case/Port trong Kiến trúc Kỹ thuật và mã FR trong SRS — giữ nguyên nguyên tắc truy vết đã áp dụng xuyên suốt bộ tài liệu.

1.2. Base URL & versioning

Base URL: /api/v1 — tiền tố version tường minh ngay từ đầu dù chỉ có một phiên bản, để không phải đổi toàn bộ đường dẫn client khi công thức xếp hạng hoặc response schema thay đổi ở Giai đoạn 3 (ví dụ khi RankRestaurantsUseCase chuyển từ HeuristicRankingAdapter sang MLRankingAdapter — response có thể thêm trường mới, envelope version giúp client cũ không vỡ).

1.3. Quy ước chung

Định dạng: JSON (Content-Type: application/json) cho cả request và response.

Thời điểm: mọi trường thời gian dùng ISO-8601 UTC (ví dụ 2026-07-27T09:00:00Z) — nhất quán với quy ước TIMESTAMPTZ ở Data Dictionary mục 2.1; quy đổi múi giờ hiển thị thực hiện ở tầng frontend, không phải API.

Tên trường: giữ nguyên snake_case khớp trực tiếp với tên cột trong Data Dictionary (ví dụ restaurant_id, predicted_score) — quyết định có chủ đích để giảm một tầng ánh xạ DTO ở quy mô một người phát triển, đổi lại là API không theo convention camelCase phổ biến của JSON; chấp nhận đánh đổi này.

Định danh phiên: session_id (UUID v4) do client tự sinh và lưu cục bộ (localStorage), gửi kèm mọi request có ghi dữ liệu — không có khái niệm tài khoản người dùng (SRS mục 8, Won't-have).

1.4. Authentication

Không áp dụng xác thực người dùng ở phạm vi tài liệu này — nhất quán với quyết định SRS “tài khoản người dùng và cá nhân hoá dài hạn” thuộc Won't-have. Endpoint công khai, không yêu cầu API key phía client. Nếu triển khai công khai ngoài phạm vi đồ án, cần bổ sung rate limiting ở tầng hạ tầng (không thuộc phạm vi đặc tả API này).

1.5. Response Envelope

Toàn bộ response thành công bọc trong trường data; lỗi bọc trong trường error — giúp client xử lý nhất quán bằng một điều kiện duy nhất (kiểm tra có error hay không) thay vì suy đoán qua HTTP status.

// Thành công

{ "data": { ... } }

// Lỗi

{ "error": { "code": "RESTAURANT_NOT_FOUND", "message": "...", "details": { } } }

1.6. Bảng mã lỗi dùng chung

HTTP Status

error.code

Khi nào xảy ra

400

INVALID_REQUEST

Thiếu trường bắt buộc (ví dụ latitude/longitude) hoặc giá trị không hợp lệ (action_type lạ).

404

RESTAURANT_NOT_FOUND

restaurant_id không tồn tại, hoặc is_active = false (ẩn khỏi công khai — trả 404 thay vì 410 để không lộ trạng thái nội bộ).

404

SEARCH_RESULT_ITEM_NOT_FOUND

search_result_item_id trong POST /interactions không tồn tại (ví dụ dữ liệu đã quá cũ hoặc client gửi id giả).

429

RATE_LIMITED

Dự phòng khai báo trước; MVP hiện chưa bật rate limiting theo mục 1.4.

503

EXTERNAL_SERVICE_UNAVAILABLE

API bên thứ ba (Maps/Traffic) lỗi và không có cache/fallback hợp lệ tại thời điểm gọi.

500

INTERNAL_ERROR

Lỗi không xác định phía server.

2. Bản đồ Endpoint × Module × Use Case

Đối chiếu trực tiếp với Ma trận Module × Lớp ở Sơ đồ Kiến trúc mục 3 — mỗi endpoint gọi đúng một Use Case ở tầng Application, không có endpoint nào gọi thẳng xuống Infrastructure (vi phạm Dependency Rule).

Endpoint

Module

Use Case

FR liên quan

POST /search

3. Search & Ranking

SearchRestaurantsUseCase

FR-2.1, FR-2.3, FR-4.2–4.5, FR-6.3, FR-6.4, FR-5.2

GET /restaurants/{id}

1. Restaurant & Dish Catalog

GetRestaurantDetailUseCase ⚠ mới — xem mục 6

FR-5.2, FR-1.5 (khi kèm origin)

GET /restaurants/{id}/directions

4. External Context Signals

GetRestaurantDetailUseCase (nhánh route)

FR-1.5

POST /interactions

9. Interaction Logging

LogInteractionUseCase

FR-9.1, FR-9.2, FR-9.3, FR-9.4

GET /health

— (hệ thống)

— (không qua Use Case, đọc trực tiếp *_model_versions.is_active)

—

Ba module không có endpoint riêng — có chủ đích, không phải thiếu sót: Review Synthesis (5) trả kèm trong GET /restaurants/{id}, không tách endpoint vì luôn được đọc cùng lúc với chi tiết nhà hàng; Dish Recommendation (6) trả kèm trong từng phần tử kết quả của POST /search (đúng thiết kế suggested_dish_id nằm ngay trên search_result_items ở Data Dictionary, không phải bảng độc lập cần tra riêng); Data Analytics (8) không có endpoint theo quyết định đã chốt ở WBS — số liệu báo cáo lấy trực tiếp bằng SQL, không xây trang/API chỉ để xem số liệu.

3. Chi tiết Endpoint

3.1. Tìm kiếm & Xếp hạng

POST /api/v1/search

Nhận nhu cầu tìm kiếm bằng ngôn ngữ tự nhiên kèm ràng buộc cứng, trả danh sách nhà hàng đã xếp hạng. Tác dụng phụ (side effect): tự động ghi một bản ghi search_queries và một bản ghi search_result_items cho mỗi kết quả trả về — client không cần gọi thêm request nào để “log lượt hiển thị”.

Request body

{

"session_id": "3f9a...", // bắt buộc, UUID v4 do client sinh

"query_text": "chỗ yên tĩnh để làm việc", // tuỳ chọn

"latitude": 21.0278, // bắt buộc

"longitude": 105.8342, // bắt buộc

"budget_max": 150000, // tuỳ chọn (VND)

"dietary_restrictions": ["vegetarian"], // tuỳ chọn

"opening_hours_constraint": "now" // tuỳ chọn: "now" | "HH:mm"

}

Response 200

{

"data": {

"search_query_id": "a1b2...",

"results": [

{

"search_result_item_id": 8831,

"restaurant_id": "c4d5...",

"name": "Quán Ấm",

"address": "12 Trúc Bạch, Ba Đình",

"latitude": 21.041, "longitude": 105.836,

"distance_m": 1240, // đường chim bay, không gọi Traffic API — xem mục 3.2

"price_range": 2, "rating": 4.5, "user_ratings_total": 132,

"experience_cluster_label": "Yên tĩnh, phù hợp làm việc", // null nếu Cold Start

"review_summary": { "strengths": "...", "weaknesses": "...", "suited_for": ["làm việc"] },

"suggested_dish": { "dish_id": 501, "name": "Trà đào", "reason": "phù hợp ngồi lâu" }, // null nếu chưa kích hoạt Giai đoạn 3

"rank_position": 1,

"predicted_score": 0.8721

}

],

"ranking_model_version": "ranking_model_v3" // chỉ trả khi request có header X-Debug: true

}

}

Cột experience_cluster_label là null khi nhà hàng đang ở trạng thái Cold Start (experience_cluster_id chưa gán) — client hiển thị “Đang cập nhật” thay vì để trống hoặc báo lỗi, đúng quy tắc trung lập hoá đã thống nhất ở Data Dictionary Phụ lục A.12. ranking_model_version mặc định KHÔNG trả ở production (tránh lộ chi tiết cài đặt nội bộ cho người dùng cuối); chỉ trả khi request có header X-Debug: true, phục vụ kiểm thử/Ablation Study nội bộ.

Mã lỗi

HTTP

Điều kiện

INVALID_REQUEST

400

Thiếu latitude/longitude, hoặc session_id không phải UUID hợp lệ.

EXTERNAL_SERVICE_UNAVAILABLE

503

SemanticSearchAdapter hoặc embedding service lỗi — không có kết quả tìm kiếm ngữ nghĩa để trả.

3.2. Chi tiết nhà hàng

GET /api/v1/restaurants/{restaurant_id}

Trả thông tin đầy đủ một nhà hàng, kèm review_summary mới nhất và danh sách món đang bán (is_active = true). Query param origin_lat, origin_lng tuỳ chọn — nếu có, trả thêm distance_m đường chim bay (không gọi Traffic API ở endpoint này, xem mục 3.3 khi cần thời gian di chuyển thực tế).

Response 200

{

"data": {

"restaurant_id": "c4d5...", "name": "Quán Ấm", "address": "...",

"price_range": 2, "rating": 4.5,

"experience_cluster_label": "Yên tĩnh, phù hợp làm việc",

"review_summary": { "strengths": "...", "weaknesses": "...", "suited_for": ["..."], "based_on_review_count": 47 },

"dishes": [ { "dish_id": 501, "name": "Trà đào", "category": "Đồ uống", "price": 35000 } ]

}

}

Mã lỗi

HTTP

Điều kiện

RESTAURANT_NOT_FOUND

404

Không tồn tại hoặc is_active = false.

3.3. Tuyến đường & thời gian di chuyển thực tế

GET /api/v1/restaurants/{restaurant_id}/directions?origin_lat=&origin_lng=

Tách riêng khỏi mục 3.2 có chủ đích: nếu tính thời gian di chuyển traffic-aware cho TẤT CẢ kết quả ngay trong POST /search, số lượt gọi Traffic API sẽ nhân theo số kết quả mỗi lượt tìm kiếm — đúng rủi ro rate limit/chi phí đã cảnh báo ở WBS mục 4.2 (lý do dùng mock/cache khi phát triển). Endpoint này chỉ gọi Traffic API thật khi người dùng thực sự chọn xem một nhà hàng cụ thể — đây cũng chính là thời điểm hợp lý để ghi InteractionEvent action_type = get_directions (mục 3.4).

Response 200

{ "data": { "distance_m": 1580, "duration_s": 480, "duration_in_traffic_s": 610 } }

Mã lỗi

HTTP

Điều kiện

INVALID_REQUEST

400

Thiếu origin_lat/origin_lng.

RESTAURANT_NOT_FOUND

404

restaurant_id không tồn tại hoặc is_active = false.

EXTERNAL_SERVICE_UNAVAILABLE

503

GoogleMapsAdapter/TrafficApiAdapter lỗi.

3.4. Ghi nhận tương tác

POST /api/v1/interactions

Ghi một InteractionEvent gắn với một SearchResultItem cụ thể — nguồn dữ liệu nhãn cho mô hình xếp hạng học có giám sát ở giai đoạn nâng cấp (SRS mục 3.9). is_positive_signal tính sẵn phía server theo đúng bảng phân loại tín hiệu ở SRS FR-9.3, không tính ở client.

Request body

{

"search_result_item_id": 8831,

"action_type": "get_directions", // view_detail | get_directions | save | explicit_positive | explicit_negative

"dwell_time_ms": 6200, // bắt buộc nếu action_type = view_detail, bỏ qua với loại khác

"session_id": "3f9a..."

}

Response 201

{ "data": { "interaction_event_id": 91234, "is_positive_signal": true } }

Client KHÔNG dùng is_positive_signal để đổi giao diện — trường này chỉ trả về để phục vụ debug/kiểm thử, tránh client tự suy luận sai quy tắc phân loại (giữ đúng một nguồn sự thật duy nhất ở server, theo tinh thần Source of Truth đã áp dụng cho dữ liệu ở Data Dictionary mục 1.3).

Mã lỗi

HTTP

Điều kiện

INVALID_REQUEST

400

action_type không thuộc danh sách hợp lệ, hoặc thiếu dwell_time_ms khi action_type = view_detail.

SEARCH_RESULT_ITEM_NOT_FOUND

404

search_result_item_id không tồn tại.

3.5. Kiểm tra tình trạng hệ thống

GET /api/v1/health

Phục vụ kiểm thử/giám sát vận hành (WBS mục Kiểm thử hiệu năng, Triển khai demo) — không qua Use Case, đọc trực tiếp is_active của các bảng version để xác nhận hệ thống có đúng một phiên bản mô hình đang hoạt động.

{ "data": { "status": "ok", "api_version": "v1",

"database": "UP",

"active_ranking_model_version": "ranking_model_v3",

"active_cluster_model_version": "cluster_model_v2" } }

Trường database chỉ trả “UP”/“DOWN” — một lượt kiểm tra kết nối đơn giản (ví dụ SELECT 1), không phải dashboard giám sát hạ tầng đầy đủ (không có độ trễ, connection pool, dung lượng...) — giữ đúng tinh thần endpoint này chỉ phục vụ kiểm thử/demo, không thay thế công cụ giám sát vận hành thật.

4. Module không có Endpoint riêng — theo chủ đích

Module

Lý do không tách endpoint

5. Review Synthesis

review_summary luôn được đọc cùng lúc với chi tiết nhà hàng (mục 3.2) hoặc cùng danh sách kết quả tìm kiếm (mục 3.1) — tách endpoint riêng chỉ tạo thêm một round-trip không cần thiết cho một dữ liệu luôn đi kèm.

6. Dish Recommendation

suggested_dish_id là một trường trên search_result_items (Data Dictionary mục 4), không phải một thực thể độc lập cần tra cứu riêng — trả kèm trong mục 3.1 là đúng đường dữ liệu đã thiết kế.

8. Data Analytics

Theo quyết định đã chốt ở WBS (cắt trang phân tích dữ liệu riêng): số liệu báo cáo lấy trực tiếp bằng truy vấn SQL khi cần cho báo cáo đồ án, không xây dựng và duy trì một API/trang web chỉ để xem số liệu ở quy mô một người phát triển.

7. Data Ingestion

Job offline (crawl, sinh embedding, huấn luyện mô hình) không phải API phục vụ người dùng cuối — đã đặc tả ở Sơ đồ Kiến trúc mục 5 (Deployment), thuộc phạm vi vận hành nội bộ, không lộ qua REST công khai.

5. Phát hiện: Module Restaurant & Dish Catalog thiếu tầng Application

Khi đặc tả endpoint GET /restaurants/{id}, đối chiếu lại Ma trận Module × Lớp ở Sơ đồ Kiến trúc mục 3 phát hiện: Module 1 (Restaurant & Dish Catalog) chỉ đánh dấu có mặt ở Domain và Infrastructure — KHÔNG có ở Application. Theo đúng Dependency Rule đã thống nhất (Kiến trúc Kỹ thuật mục 2.1, Sơ đồ Kiến trúc mục 2), Presentation chỉ được phép gọi vào Application, không bao giờ gọi thẳng xuống Infrastructure. Nếu giữ nguyên hiện trạng, RestaurantController muốn lấy chi tiết một nhà hàng sẽ không có đường gọi hợp lệ — gọi thẳng PostgresRestaurantRepository là vi phạm chính nguyên tắc kiến trúc đã đặt ra, còn nếu nhét logic đó vào SearchRestaurantsUseCase thì use case đó phình to sai trách nhiệm (Single Responsibility).

Tài liệu này bổ sung một Use Case mới để lấp khoảng trống: GetRestaurantDetailUseCase (Application), dùng lại đúng IRestaurantRepository đã có sẵn (không cần Port mới) — chỉ thêm một use case mỏng, không đổi Infrastructure. Khuyến nghị đồng bộ ngược lại hai tài liệu:

Tài liệu cần cập nhật

Nội dung cập nhật

Kiến trúc Kỹ thuật mục 5 (Phân rã Module)

Dòng Module 1 (Restaurant & Dish Catalog): thêm cột Application, ghi GetRestaurantDetailUseCase.

Sơ đồ Kiến trúc mục 3 (Ma trận Module × Lớp)

Thêm dấu chấm (●) ở giao Module 1 × Application; cập nhật Hình 1 (sơ đồ 4 lớp) thêm GetRestaurantDetailUseCase vào danh sách Use Cases của khối APPLICATION.

Đây là phát hiện cùng loại với module Interaction Logging đã bổ sung trước đó (Sơ đồ Kiến trúc mục 7) — cả hai đều lộ ra khi đặc tả ở mức đủ chi tiết (API, luồng gọi cụ thể) chứ không xuất hiện khi mô tả kiến trúc ở mức khái quát. Đây là lý do thực tế cho thấy việc viết Đặc tả API không chỉ là tài liệu hoá cái đã có, mà còn là một bước kiểm chứng kiến trúc.


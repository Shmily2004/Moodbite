# MoodBite_Kien_Truc_Ky_Thuat

MoodBite

Tài liệu Kiến trúc Kỹ thuật & Phân rã Chức năng theo Clean Architecture

Phiên bản 1.1

Ngày ban hành: 22/07/2026 (bổ sung centroid versioning, tách dev/eval set, Cold Start)

Tài liệu nguồn: MoodBite – SRS v1.2, WBS v1.2

1. Mục đích tài liệu

Tài liệu này bổ sung cho SRS và WBS đã có, tập trung riêng vào cách tổ chức mã nguồn để đáp ứng hai yêu cầu: mọi chức năng đều được xây dựng theo Clean Architecture, tách rõ các lớp và chỉ phụ thuộc đúng một chiều; đồng thời mỗi phase triển khai (Giai đoạn 0 → 4 theo WBS v1.2) chỉ được phép thêm mã nguồn mới, hạn chế tối đa việc sửa lại mã nguồn của các phase trước.

Nhờ ràng buộc này, một người phát triển đơn lẻ có thể hoàn thành từng phase một cách độc lập, kiểm thử xong phase nào là yên tâm với phase đó, không phải lo việc thêm tính năng mới ở giai đoạn sau làm hỏng phần đã chạy ổn định trước đó.

2. Nguyên tắc kiến trúc

2.1. Clean Architecture và Quy tắc phụ thuộc

Hệ thống được chia thành bốn lớp đồng tâm, tuân theo Quy tắc phụ thuộc (Dependency Rule): mã nguồn ở lớp trong không được biết đến sự tồn tại của lớp ngoài; mọi phụ thuộc giữa các lớp luôn hướng vào trong, không bao giờ ngược lại.

Domain (trong cùng): các thực thể nghiệp vụ thuần tuý — Nhà hàng, Món ăn, Ngữ cảnh người dùng, Cụm trải nghiệm... — không phụ thuộc vào bất kỳ framework, thư viện học máy hay công nghệ web nào.

Application: các use case điều phối nghiệp vụ (Tìm kiếm & Xếp hạng, Tổng hợp đánh giá, Gợi ý món ăn...) và các cổng giao tiếp (port/interface) mà use case cần dùng để nói chuyện với thế giới bên ngoài — nhưng chưa biết cổng đó được cài đặt bằng công nghệ gì.

Infrastructure: cài đặt cụ thể cho từng cổng ở trên — cơ sở dữ liệu, mô hình KMeans, embedding, API bản đồ/thời tiết/giao thông, bộ crawler.

Presentation: giao diện web và API điều phối, chỉ được phép gọi vào Application, không chứa logic nghiệp vụ bên trong.

Sơ đồ phụ thuộc: Presentation → Application → Domain, và Infrastructure → Application (cài đặt các Port do Application định nghĩa). Domain không phụ thuộc vào bất kỳ lớp nào khác — đây là lớp duy nhất không import bất cứ thứ gì từ ba lớp còn lại.

2.2. Nguyên tắc giữ ổn định qua các phase

Để phase sau hạn chế sửa phase trước, toàn bộ giao tiếp giữa các lớp đi qua interface (port) được định nghĩa sớm, ổn định, và không đổi chữ ký khi thêm cài đặt mới:

Ports & Adapters: mỗi khả năng bên ngoài (tìm kiếm ngữ nghĩa, xếp hạng, thời tiết, giao thông, tổng hợp review...) được khai báo thành một interface trong Application ngay từ Giai đoạn 0, dù cài đặt ban đầu rất đơn giản. Giai đoạn sau chỉ viết thêm một Adapter mới cài đặt cùng interface đó, không sửa interface đã có.

Strategy Pattern qua Dependency Injection: việc chọn cài đặt nào cho mỗi Port (ví dụ xếp hạng heuristic của Giai đoạn 0 hay mô hình học máy của Giai đoạn 3) được quyết định tại một nơi cấu hình duy nhất khi khởi động ứng dụng, không nằm rải rác trong code nghiệp vụ.

Mở rộng Entity bằng trường tuỳ chọn, không sửa cấu trúc cũ: khi giai đoạn sau cần thêm dữ liệu (ví dụ điểm độ ồn suy ra từ review), trường mới được thêm dưới dạng optional vào Entity đã có, không đổi kiểu hay xoá trường cũ.

Versioning khi buộc phải đổi hợp đồng: nếu một Port thực sự cần đổi chữ ký, tạo interface phiên bản mới (ví dụ IRankingPortV2) thay vì sửa trực tiếp, giữ song song đến khi mọi nơi gọi đã chuyển xong.

2.3. Nguyên tắc thiết kế Port (tránh rò rỉ chi tiết công nghệ)

Một Port chỉ thực sự bảo vệ được các phase sau nếu chữ ký của nó được diễn đạt bằng ngôn ngữ nghiệp vụ, không lộ chi tiết kỹ thuật của một công nghệ cụ thể:

Chữ ký Port dùng khái niệm nghiệp vụ: ví dụ ISearchPort.search(query: SearchQuery) trả về List<RankedRestaurant>, không khai báo các tham số đặc thù công nghệ như cosine_similarity_threshold, số chiều vector, hay cú pháp truy vấn riêng của một hệ quản trị CSDL vector cụ thể.

Adapter chịu trách nhiệm dịch giữa ngôn ngữ nghiệp vụ và chi tiết kỹ thuật bên trong nó (đóng vai trò một anti-corruption layer): SemanticSearchAdapter tự quyết định cách tính độ tương đồng, tự chọn công nghệ lưu vector — Application không biết và không cần biết.

Nhờ vậy, đổi công nghệ nền (ví dụ đổi CSDL vector, đổi mô hình embedding) chỉ cần viết lại nội dung bên trong Adapter, không đổi chữ ký Port, không đổi use case gọi nó.

Toàn bộ thông tin cấu hình nhạy cảm (chuỗi kết nối cơ sở dữ liệu, khoá API bản đồ/thời tiết/giao thông) chỉ được đọc và khởi tạo tại config/di_container (ví dụ từ biến môi trường); Adapter nhận các giá trị này qua constructor injection, không tự đọc file cấu hình hay hardcode ở bất kỳ nơi nào khác trong Domain/Application/Infrastructure.

3. Phase Tổng quan

Bảng dưới đây tổng hợp toàn bộ lộ trình ở một chỗ — bức tranh toàn cảnh để đối chiếu nhanh — trước khi đi vào chi tiết từng phase ở mục 6. Cách chia và tên gọi các giai đoạn nhất quán với WBS v1.2.

Phase

Mục tiêu chính

Lớp/Module bị tác động

Port mới xuất hiện

Cam kết với phase trước

Giai đoạn 0 (Bộ khung chạy được)

Chứng minh kiến trúc 4 lớp chạy được end-to-end với dữ liệu mẫu nhỏ

Domain (khung Entity); Application (use case Tìm kiếm & Xếp hạng rút gọn); Infrastructure (repository CSV/in-memory); Presentation (web tối thiểu)

ISearchPort, IRankingPort, IRestaurantRepository

Không có phase trước — đây là nền móng; các Port định nghĩa ở đây phải đủ tổng quát cho mọi phase sau

Giai đoạn 1 (MVP)

Thay dữ liệu mẫu bằng dữ liệu thật quy mô vừa phải, thêm tìm kiếm ngữ nghĩa và bản đồ thật

Infrastructure (repository DB thật, crawler); Application (use case ngữ nghĩa dùng lại ISearchPort)

ISemanticSearchAdapter (cài đặt mới của ISearchPort), IMapPort

Chỉ thêm Adapter mới cho Port đã có ở Giai đoạn 0; không sửa Entity hay use case cũ, chỉ đổi cấu hình DI

Giai đoạn 2 (Mở rộng dữ liệu & trải nghiệm)

Thêm phân cụm trải nghiệm KMeans (huấn luyện offline), tổng hợp đánh giá, làm giàu đặc trưng

Infrastructure (batch job huấn luyện KMeans, ghi cluster_id thẳng vào dữ liệu qua IRestaurantRepository); Application (SummarizeReviews mới; RankingUseCase đọc cluster_id có sẵn trên Entity, không gọi Port tính cụm lúc truy vấn)

ISummarizationPort, IClusterAssignmentPort (chỉ dùng để so khớp vector ngữ cảnh người dùng với tâm cụm đã lưu — nhẹ, không phải huấn luyện lại)

RankingUseCase chỉ đọc thêm trường có sẵn trên Entity; Entity Nhà hàng chỉ thêm trường mở rộng, không đổi trường cũ

Giai đoạn 3 (Tính năng nâng cao)

Gợi ý món ăn, tín hiệu thời tiết/giao thông thời gian thực, nâng cấp mô hình xếp hạng lên học có giám sát

Application (use case mới RecommendDish); Infrastructure (IWeatherPort, ITrafficPort, adapter học máy mới cho IRankingPort)

IWeatherPort, ITrafficPort, adapter mới của IRankingPort

Adapter học máy cài đặt lại IRankingPort đã có từ Giai đoạn 0; không đổi cách use case gọi ra ngoài

Giai đoạn 4 (Định hướng tương lai)

Ghi nhận hướng mở rộng chưa triển khai (Collaborative Filtering, ASR đầy đủ, tài khoản người dùng...)

Chỉ ghi nhận dưới dạng Port dự kiến, chưa cài đặt

(dự kiến) IUserAccountPort, ICollaborativeFilteringPort

Chỉ là ghi chú định hướng — không code, không ảnh hưởng các phase trước

4. Kiến trúc bốn lớp

4.1. Domain

Chứa các Entity và Value Object mô tả nghiệp vụ độc lập với công nghệ: Restaurant, Dish, UserContext (kết quả khảo sát + câu tìm kiếm tự do + vị trí), ExperienceCluster, ContextVector. Lớp này không import bất kỳ thư viện nào từ Application, Infrastructure hay Presentation — có thể copy sang một dự án hoàn toàn khác mà vẫn chạy được vì không phụ thuộc framework.

4.2. Application

Chứa các use case điều phối nghiệp vụ và các Port (interface) mà use case cần: SearchRestaurantsUseCase, SummarizeReviewsUseCase, RecommendDishUseCase. Mỗi use case chỉ gọi vào Port, không biết Port được cài đặt bằng công nghệ gì — nhờ vậy test được use case mà không cần chạy thật cơ sở dữ liệu hay mô hình ML (dùng bản giả lập/mock của Port).

4.3. Infrastructure

Chứa các Adapter — cài đặt cụ thể cho từng Port: CsvRestaurantRepository rồi PostgresRestaurantRepository (cùng cài đặt IRestaurantRepository); HeuristicRankingAdapter rồi MLRankingAdapter (cùng cài đặt IRankingPort); GoogleMapsAdapter, WeatherApiAdapter, TrafficApiAdapter. Cũng chứa các job crawl dữ liệu, chạy tách biệt hoàn toàn khỏi luồng phục vụ người dùng.

4.4. Presentation

Chứa API điều phối (nhận request, gọi use case, trả kết quả) và giao diện web (ô tìm kiếm, bản đồ, trang phân tích). Lớp này chỉ được phép gọi vào Application, tuyệt đối không chứa logic xếp hạng hay xử lý dữ liệu trực tiếp.

5. Phân rã Module

Module

Thuộc lớp

Trách nhiệm

Xuất hiện từ Phase

Restaurant & Dish Catalog

Domain + Infrastructure

Định nghĩa và lưu trữ thông tin nhà hàng, món ăn

Giai đoạn 0 (khung) → Giai đoạn 1 (dữ liệu thật) → Giai đoạn 3 (chi tiết món ăn)

User Context

Domain

Biểu diễn nhu cầu người dùng: khảo sát, câu tìm kiếm tự do, vị trí hiện tại

Giai đoạn 0

Search & Ranking

Application + Infrastructure

Điều phối tìm kiếm, lọc ràng buộc cứng, tính điểm xếp hạng; đọc nhãn cụm đã được huấn luyện offline (không tính cụm lúc truy vấn)

Giai đoạn 0 (heuristic) → 1 (ngữ nghĩa) → 2 (đọc nhãn cụm) → 3 (học máy)

External Context Signals

Application (port) + Infrastructure (adapter)

Bản đồ, thời tiết, giao thông thời gian thực

Giai đoạn 1 (bản đồ) → Giai đoạn 3 (thời tiết/giao thông)

Review Synthesis

Application + Infrastructure

Tổng hợp review thành nhận xét ngắn gọn (ưu điểm/nhược điểm)

Giai đoạn 2

Dish Recommendation

Application

Gợi ý món ăn phù hợp theo ngữ cảnh

Giai đoạn 3

Data Ingestion

Infrastructure (độc lập với runtime)

Crawl dữ liệu theo lô (Google Places, TikTok...), không chạy trong luồng thời gian thực

Giai đoạn 1 trở đi

Presentation/Web

Presentation

Giao diện web và API điều phối gọi Application

Giai đoạn 0 (tối thiểu), mở rộng dần

6. Chi tiết theo từng Phase

6.1. Giai đoạn 0 — Bộ khung chạy được

Domain: định nghĩa Restaurant, UserContext, ContextVector ở mức tối thiểu nhưng đủ trường để không phải đổi cấu trúc ở các phase sau.

Application: SearchRestaurantsUseCase gọi IRestaurantRepository (lọc ràng buộc cứng) và IRankingPort (heuristic đơn giản: rating, khoảng cách, ngân sách).

Infrastructure: CsvRestaurantRepository đọc 50–100 bản ghi nhập tay; HeuristicRankingAdapter cài đặt IRankingPort bằng công thức cộng có trọng số cố định.

Presentation: một trang web tối thiểu — ô tìm kiếm dạng lọc cơ bản + bản đồ hiển thị marker kết quả.

Cam kết: các Port khai báo ở đây (IRestaurantRepository, IRankingPort, ISearchPort) là hợp đồng gốc — mọi phase sau chỉ thêm Adapter mới, không sửa chữ ký các Port này.

6.2. Giai đoạn 1 — MVP

Infrastructure: thêm PostgresRestaurantRepository (cài đặt lại IRestaurantRepository với dữ liệu thật đã crawl), thêm job crawl độc lập (module Data Ingestion), thêm GoogleMapsAdapter (cài đặt IMapPort mới).

Application: thêm SemanticSearchAdapter cài đặt ISearchPort bằng embedding, dùng song song với bản heuristic của Giai đoạn 0 (chọn qua cấu hình DI).

Presentation: nâng cấp giao diện — ô tìm kiếm nhận câu tự do, bản đồ hiển thị tuyến đường thật.

Cam kết: CsvRestaurantRepository và HeuristicRankingAdapter của Giai đoạn 0 được giữ nguyên trong mã nguồn (không xoá) để dùng làm môi trường test nhanh/offline, không phải sửa lại khi chuyển sang Adapter thật.

6.3. Giai đoạn 2 — Mở rộng dữ liệu và trải nghiệm

Huấn luyện cụm là một job offline độc lập, không phải một Port được RankingUseCase gọi lúc truy vấn: một script trong infrastructure/training đọc toàn bộ đặc trưng nhà hàng, fit KMeans theo lô, rồi ghi thẳng experience_cluster_id vào từng bản ghi qua IRestaurantRepository. Việc này chạy định kỳ (ví dụ mỗi khi có dữ liệu mới đáng kể), hoàn toàn tách khỏi luồng phục vụ người dùng.

Runtime (Application): RankingUseCase chỉ đọc trường experience_cluster_id đã có sẵn trên Restaurant Entity (qua IRestaurantRepository, không cần một Port riêng) để so khớp với cụm của người dùng. Việc so khớp vector ngữ cảnh của người dùng với tâm cụm gần nhất là một phép tính khoảng cách nhẹ (không phải huấn luyện lại), có thể đặt trong một Port riêng, nhỏ và rẻ: IClusterAssignmentPort.

Application: thêm SummarizeReviewsUseCase (dùng ISummarizationPort); RankingUseCase nhận thêm một tham số tuỳ chọn "cluster_signal", không đổi chữ ký các tham số đã có.

Infrastructure: KMeansTrainingJob (offline, không phải Adapter của một Port trong Application) ghi cluster_id vào dữ liệu; ClusterCentroidAssignmentAdapter cài đặt IClusterAssignmentPort bằng cách nạp sẵn toạ độ tâm cụm đã lưu; TextSummarizationAdapter cài đặt ISummarizationPort.

Centroid được version cùng một lần với model artifact, không tách rời: mỗi lần KMeansTrainingJob chạy xong tạo ra một cặp (cluster_id đã gán cho dữ liệu, file toạ độ tâm cụm) cùng chung một version, ví dụ cluster_model_v2/. ClusterCentroidAssignmentAdapter luôn nạp centroid từ đúng version model đang active theo config/di_container, tuyệt đối không tự đọc lại centroid tính rời từ dataset hiện tại — nếu không, một lần retrain xong nhưng chưa promote sẽ khiến cluster_id trên dữ liệu (version cũ) và centroid dùng để so khớp (nếu đọc nhầm bản mới) bị lệch nhau.

Domain: Restaurant được thêm các trường optional (experience_cluster_id, review_summary) — không đổi các trường đã dùng ở Giai đoạn 0–1.

Cam kết: mọi lời gọi RankingUseCase từ Giai đoạn 1 vẫn chạy đúng vì tham số mới là tuỳ chọn, có giá trị mặc định khi không truyền; đồng thời việc tách bạch huấn luyện (offline) khỏi truy vấn (online) đảm bảo hiệu năng tìm kiếm không phụ thuộc vào thời gian chạy KMeans.

6.4. Giai đoạn 3 — Tính năng nâng cao

Application: thêm RecommendDishUseCase (module Dish Recommendation), độc lập với SearchRestaurantsUseCase, gọi sang khi cần.

Infrastructure: WeatherApiAdapter, TrafficApiAdapter (cài đặt IWeatherPort, ITrafficPort mới); MLRankingAdapter cài đặt lại IRankingPort bằng mô hình học có giám sát, thay thế HeuristicRankingAdapter qua cấu hình DI — không sửa mã của HeuristicRankingAdapter, chỉ đổi Adapter nào được chọn.

Cam kết: nếu MLRankingAdapter phát sinh lỗi khi vận hành, có thể rollback tức thời về HeuristicRankingAdapter chỉ bằng một dòng cấu hình, vì cả hai vẫn cùng tồn tại và cùng cài đặt một Port.

6.5. Giai đoạn 4 — Định hướng tương lai (chưa triển khai)

Chỉ ghi nhận các Port dự kiến cho hướng mở rộng xa hơn: IUserAccountPort (tài khoản người dùng, lưu lịch sử), ICollaborativeFilteringPort (gợi ý dựa trên hành vi nhiều người dùng khi đã tích luỹ đủ dữ liệu tương tác).

Không viết code ở giai đoạn này; mục đích duy nhất là để khi thực sự cần, người phát triển (hoặc người kế nhiệm) biết nên mở ở đâu trong kiến trúc mà không phải thiết kế lại từ đầu.

7. Cấu trúc thư mục đề xuất

Cấu trúc dưới đây áp dụng cho toàn bộ vòng đời dự án; các thư mục được tạo dần theo từng phase, không cần dựng sẵn toàn bộ từ Giai đoạn 0.

src/ domain/ entities/ Restaurant, Dish, UserContext, ExperienceCluster value_objects/ Location, PriceRange, ContextVector application/ use_cases/ SearchRestaurants, RecommendDish, SummarizeReviews ports/ ISearchPort, IRankingPort, IRestaurantRepository, IWeatherPort, ITrafficPort, IMapPort, IClusterAssignmentPort, ISummarizationPort infrastructure/ repositories/ CsvRestaurantRepository, PostgresRestaurantRepository adapters/ search/ KeywordSearchAdapter, SemanticSearchAdapter ranking/ HeuristicRankingAdapter, MLRankingAdapter clustering/ ClusterCentroidAssignmentAdapter (đọc tâm cụm, nhẹ, runtime) external/ GoogleMapsAdapter, WeatherApiAdapter, TrafficApiAdapter ingestion/ crawler jobs — chạy độc lập, ngoài runtime phục vụ người dùng training/ KMeansTrainingJob, RankingModelTrainingJob — batch offline, mỗi lần chạy ghi ra một version gồm cả centroid + cluster_id (không tách rời), không phải Port của Application presentation/ api/ REST controllers gọi use case web/ ô tìm kiếm, bản đồ, kết quả, trang phân tích config/ di_container nơi duy nhất quyết định Adapter nào dùng cho mỗi Port, thay đổi theo từng phase

8. Quy ước thực thi để giữ cam kết "phase sau không sửa phase trước"

Mọi Port trong application/ports là hợp đồng ổn định: không xoá phương thức đã có, chỉ được thêm phương thức mới hoặc tham số có giá trị mặc định.

Mọi Adapter mới đặt trong infrastructure/adapters/<port>/, được chọn dùng qua config/di_container; Adapter cũ được giữ lại làm phương án dự phòng/rollback, không bị xoá khi có Adapter mới.

Entity trong domain/entities chỉ được mở rộng thêm trường optional; nếu một trường cần đổi kiểu dữ liệu triệt để, tạo Value Object mới bọc quanh thay vì sửa trực tiếp trường cũ.

Mỗi phase kết thúc bằng một lượt kiểm thử hồi quy tối thiểu — chạy lại luồng end-to-end của (các) phase trước — để xác nhận không có gì bị hỏng trước khi bắt đầu phase kế tiếp.

Toàn bộ chuỗi kết nối cơ sở dữ liệu và khoá API chỉ được đọc tại config/di_container (ví dụ từ biến môi trường); không hardcode hay đọc lại cấu hình ở bất kỳ Adapter hay use case nào khác.

9. Sao lưu và rollback dữ liệu, mô hình

Mục 2.2 và mục 6 đã mô tả cơ chế rollback cho mã nguồn (giữ lại Adapter cũ, đổi qua cấu hình DI). Mục này mở rộng cùng nguyên tắc đó sang dữ liệu và mô hình đã huấn luyện — hai thứ không nằm trong mã nguồn nhưng vẫn có thể hỏng và cần khôi phục được.

9.1. Sao lưu dữ liệu (dataset)

Mỗi lần crawl/làm mới dữ liệu tạo ra một bản snapshot có gắn version (ví dụ dataset_2026_07, dataset_2026_08...), không ghi đè lên bản snapshot trước đó.

Giữ lại tối thiểu 2–3 snapshot gần nhất; snapshot cũ hơn có thể xoá sau khi snapshot mới đã được xác nhận ổn định qua một khoảng thời gian sử dụng thực tế.

Snapshot mới chỉ được áp dụng vào cơ sở dữ liệu phục vụ người dùng sau khi chạy lại bước kiểm soát chất lượng dữ liệu (đã mô tả ở SRS mục 2 — dữ liệu thiếu, trùng lặp, mất cân bằng); nếu không đạt, hệ thống tiếp tục phục vụ bằng snapshot đang hoạt động, không tự động chuyển.

9.2. Sao lưu và rollback mô hình (KMeans, mô hình xếp hạng)

Mỗi lần huấn luyện lại (offline, theo mục 6.3 và 6.4) tạo ra một artifact mô hình có version riêng (ví dụ ranking_model_v3.pkl), kèm theo các chỉ số đánh giá ghi lại tại thời điểm huấn luyện (Silhouette Score, NDCG... theo tiêu chí nghiệm thu ở WBS).

Mô hình mới chỉ được đặt làm "active" — tức được config/di_container trỏ tới — sau khi các chỉ số này đạt ngưỡng tối thiểu đã định trước; nếu không đạt, mô hình đang active trước đó tiếp tục được dùng, artifact mới bị giữ lại để xem xét chứ không tự động thay thế.

Vì Adapter cũ (HeuristicRankingAdapter, hoặc artifact mô hình phiên bản trước) luôn được giữ lại trong hệ thống theo nguyên tắc ở mục 8, việc rollback khi retrain thất bại chỉ là đổi một dòng cấu hình trỏ về artifact/Adapter phiên bản trước — không cần deploy lại mã nguồn, không cần huấn luyện lại.

Với riêng mô hình phân cụm, artifact luôn gồm cả cặp (cluster_id đã gán, toạ độ tâm cụm) cùng version — không lưu và rollback tách rời hai phần này, để tránh tình huống dữ liệu đang dùng centroid của một version còn cluster_id trên Entity lại thuộc version khác (xem chi tiết ở mục 6.3).

Với quy mô một dự án cá nhân, các bước 9.1–9.2 có thể thực hiện thủ công (sao chép file, đổi tên có version, sửa một dòng cấu hình) thay vì xây dựng một pipeline CI/CD tự động — miễn là quy ước đặt tên/versioning được tuân thủ nhất quán để không bị nhầm giữa các phiên bản.

9.3. Tách bạch tập dữ liệu tuning và đánh giá (tránh Data Leakage)

Để các chỉ số ở mục nghiệm thu (WBS) đáng tin cậy, tập dữ liệu dùng để chỉnh tham số/luật và tập dùng để đánh giá cuối cùng phải tách biệt và không được trộn lẫn:

Development Set: dùng để tinh chỉnh trọng số công thức xếp hạng heuristic, chọn số cụm k, thử nghiệm ngưỡng từ khoá cho tìm kiếm ngữ nghĩa rút gọn, và mọi vòng lặp thử-sai khác trong lúc phát triển.

Evaluation Set: một tập câu hỏi/kịch bản mẫu tách riêng ngay từ đầu, chỉ dùng đúng một lần cho mỗi lần đánh giá chính thức (ví dụ trước khi promote một model artifact lên active, hoặc khi báo cáo tiêu chí nghiệm thu ở milestone). Evaluation Set tuyệt đối không được đưa ngược lại vào quá trình tuning — nếu một model không đạt và cần chỉnh lại, việc chỉnh phải dựa trên Development Set, rồi mới đánh giá lại bằng Evaluation Set ở lượt sau.

Vi phạm nguyên tắc này (tinh chỉnh trực tiếp dựa trên phản hồi từ Evaluation Set) khiến chỉ số nghiệm thu trở nên lạc quan giả tạo — hệ thống trông như đạt ngưỡng nhưng thực chất chỉ đang học thuộc tập đánh giá, không phản ánh khả năng phục vụ người dùng mới.

10. Xử lý Cold Start

Cold Start không chỉ có một dạng. Hệ thống có hai tình huống độc lập, cần cơ chế dự phòng riêng cho từng loại, không dùng chung một giải pháp:

Trước khi thiết kế cơ chế xử lý, cần trả lời câu hỏi ở góc độ sản phẩm: mục này có thực sự cần giải quyết trong phạm vi tới tháng 12/2026 không? Câu trả lời là không — vì lý do kiến trúc, không phải vì bỏ qua rủi ro. Dữ liệu nhà hàng ở Giai đoạn 0–1 được nạp trọn vẹn theo lô trước khi hệ thống phục vụ người dùng (không có kịch bản "thêm nhà hàng mới khi đang chạy"), và MLRankingAdapter (nơi Cold Start người dùng mới thực sự gây rủi ro) chỉ thuộc Giai đoạn 3 — nằm ngoài phạm vi cắt giảm đã chốt (xem tài liệu ADR/Assumption/Scope mục 6). Vì vậy, mục 10.1–10.2 dưới đây được ghi lại như một thiết kế dự phòng sẵn có nhờ kiến trúc Ports & Adapters (gần như miễn phí, không tốn thêm effort riêng), chứ không phải một hạng mục công việc cần ưu tiên cho bản demo tháng 12.

10.1. Cold Start — Nhà hàng mới

Một nhà hàng vừa được crawl/thêm vào hệ thống chưa có cluster_id (vì KMeansTrainingJob chạy theo lô, chưa đến lượt xử lý bản ghi mới) và có thể chưa đủ review để tính các đặc trưng suy ra từ văn bản (độ ồn, review_summary).

Cơ chế dự phòng: RankingUseCase vẫn xếp hạng được nhà hàng này bằng các tín hiệu luôn có sẵn ngay khi crawl xong (rating ban đầu nếu có, khoảng cách, mức giá, loại món), coi tín hiệu cụm và tổng hợp review là tuỳ chọn (đã thiết kế optional từ mục 6.3) — nhà hàng mới không bị loại khỏi kết quả, chỉ tạm thời thiếu một phần tín hiệu cho đến lần huấn luyện theo lô kế tiếp.

10.2. Cold Start — Người dùng mới

Một người dùng lần đầu sử dụng chưa có lịch sử tương tác (InteractionEvent) để mô hình xếp hạng học có giám sát (MLRankingAdapter, Giai đoạn 3) suy luận trọng số cá nhân hoá.

Cơ chế dự phòng: vì HeuristicRankingAdapter của Giai đoạn 0 luôn được giữ lại trong hệ thống (mục 8), người dùng mới có thể được phục vụ bằng Adapter heuristic (trọng số cố định theo ngữ cảnh khảo sát, không cần dữ liệu tương tác) cho đến khi tích luỹ đủ lịch sử tương tác tối thiểu; MLRankingAdapter chỉ áp dụng từ lượt tìm kiếm đủ điều kiện dữ liệu trở đi. Việc chuyển đổi này diễn ra tự nhiên nhờ cả hai Adapter cùng cài đặt một IRankingPort, không cần logic đặc biệt ở use case.


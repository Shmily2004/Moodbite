# MoodBite_ADR_Assumption_Scope

MoodBite

Nhật ký Quyết định (ADR) · Assumption Register · Ngoài phạm vi · Định nghĩa Thành công

Phiên bản 1.2

Ngày ban hành: 22/07/2026 (bổ sung Review Trigger, Validation, Exit Criteria, Falsification Criteria)

Tài liệu nguồn: MoodBite – SRS v1.2, WBS v1.4, Kiến trúc Kỹ thuật v1.1

1. Mục đích tài liệu

Ba tài liệu đã có (SRS, WBS, Kiến trúc Kỹ thuật) trả lời câu hỏi "hệ thống làm gì và làm như thế nào". Tài liệu này trả lời bốn câu hỏi khác mà một hội đồng hoặc một Tech Lead thường hỏi thêm, và rất ít đồ án chuẩn bị sẵn: vì sao chọn phương án này mà không chọn phương án khác (Decision Log), hệ thống đang ngầm tin vào điều gì (Assumption Register), hệ thống chủ động không làm gì (Out of Scope), và thành công thực sự nghĩa là gì ngoài các chỉ số kỹ thuật (Definition of Success).

2. Nhật ký Quyết định Kiến trúc (ADR)

Mỗi quyết định được ghi theo bốn phần: Bối cảnh, Quyết định, Phương án đã cân nhắc và lý do không chọn, Hệ quả — đủ ngắn để đọc trong một buổi bảo vệ, đủ chi tiết để trả lời câu hỏi "vì sao không chọn X".

ADR-01 — Chọn KMeans cho phân cụm trải nghiệm, không chọn DBSCAN/Hierarchical/GMM

Bối cảnh: Cần nhóm nhà hàng theo đặc trưng trải nghiệm (không gian, mức độ ồn, mức giá) làm một tín hiệu đầu vào cho xếp hạng.

Quyết định: Dùng KMeans, số cụm k chọn qua Elbow + Silhouette Score.

DBSCAN — không chọn vì nhạy với mật độ không đồng đều giữa khu vực trung tâm (dày đặc quán ăn) và khu vực ngoại thành (thưa), dễ gộp nhầm hoặc bỏ sót cụm với dữ liệu một thành phố.

Phân cụm phân cấp (Hierarchical) — không chọn vì chi phí tính toán tăng nhanh theo số lượng nhà hàng, khó mở rộng khi dữ liệu lớn dần qua các phase.

Gaussian Mixture Model — không chọn vì giả định phân phối Gauss cho từng đặc trưng, trong khi nhiều đặc trưng ở đây có nguồn gốc categorical/suy diễn từ văn bản, khó thoả điều kiện này nếu không xử lý thêm.

Hệ quả: KMeans đơn giản, rẻ, tâm cụm dễ diễn giải (phục vụ Cluster Profile ở Analytics Dashboard) — đánh đổi là giả định cụm có dạng hình cầu (spherical), chấp nhận được ở quy mô dữ liệu và mục tiêu diễn giải của đồ án.

Điều kiện xem xét lại (Review Trigger / Exit Criteria): Dataset vượt quá 100.000 nhà hàng (chi phí KMeans tăng nhanh, đáng cân nhắc thuật toán khác); hoặc Silhouette Score dưới 0,2 liên tục qua từ hai lần huấn luyện lại trở lên; hoặc Cluster Profile không thể diễn giải được bằng ngôn ngữ tự nhiên (không tìm được đặc trưng nổi bật chung cho một cụm) — bất kỳ điều nào xảy ra đều là tín hiệu cần xem lại ADR-01, theo quy trình ở mục 7.1.

ADR-02 — Kiến trúc lai (Clustering + Semantic Search + Ranking) thay vì thuần rule-based hoặc thuần Machine Learning end-to-end

Bối cảnh: Bài toán vừa cần lọc ràng buộc chắc chắn đúng/sai (ngân sách, dị ứng, giờ mở cửa) vừa cần hiểu ngữ nghĩa câu tìm kiếm tự do và tính điểm phù hợp tổng hợp.

Quyết định: Chia thành lớp: Business Rules (rule-based, cho ràng buộc cứng) + Semantic Search (embedding, cho hiểu ngôn ngữ tự nhiên) + Ranking (heuristic rồi ML, cho tổng hợp điểm số).

Thuần rule-based toàn bộ — không chọn vì không thể biểu diễn được các câu tìm kiếm tự do đa dạng bằng luật if-else hữu hạn, và không tận dụng được tín hiệu ngữ nghĩa từ review.

Thuần Machine Learning end-to-end (một mô hình học mọi thứ từ dữ liệu) — không chọn vì rủi ro: dữ liệu tương tác người dùng chưa tồn tại ở giai đoạn đầu (cold start toàn hệ thống), và các ràng buộc cứng như dị ứng/giờ mở cửa cần đúng tuyệt đối, không nên phó thác cho một mô hình xác suất có thể sai.

Hệ quả: Tăng độ phức tạp kiến trúc (nhiều lớp hơn một mô hình duy nhất), nhưng đổi lại mỗi lớp có thể kiểm chứng độc lập và đúng đắn hơn cho từng loại bài toán con — đây cũng là điều kiện tiên quyết để áp dụng Clean Architecture ở ADR-03.

Điều kiện xem xét lại (Review Trigger / Exit Criteria): Ablation Study (mục 10) cho thấy một lớp trong kiến trúc lai (ví dụ tín hiệu cụm) không đóng góp giá trị đo được — khi đó xem xét bỏ hẳn lớp đó khỏi kiến trúc thay vì giữ lại như một tính năng hình thức.

ADR-03 — Áp dụng Clean Architecture (Ports & Adapters) thay vì kiến trúc phân lớp truyền thống gộp logic vào Controller

Bối cảnh: Một người phát triển đơn lẻ cần thêm tính năng qua nhiều phase (Giai đoạn 0 → 3) mà không phá vỡ phần đã chạy ổn định.

Quyết định: Tách bốn lớp Domain/Application/Infrastructure/Presentation, giao tiếp qua Port; mỗi phase chỉ thêm Adapter mới.

Kiến trúc phân lớp truyền thống (Controller gọi thẳng Service gọi thẳng ORM) — không chọn vì logic nghiệp vụ (công thức xếp hạng, quy tắc lọc) dễ bị lẫn vào code framework, khó thay đổi công nghệ (ví dụ đổi CSDL vector) mà không sửa nhiều nơi.

Microservices — không chọn vì vượt quá nhu cầu thực tế của một dự án một người, chi phí vận hành (triển khai, giám sát nhiều service) không tương xứng với lợi ích ở quy mô này.

Hệ quả: Chi phí thiết kế ban đầu cao hơn (phải định nghĩa Port trước khi viết Adapter), nhưng giảm rủi ro phải viết lại khi đổi công nghệ hoặc mở rộng tính năng ở các phase sau.

Điều kiện xem xét lại (Review Trigger / Exit Criteria): Dự án mở rộng thành một nhóm nhiều người phát triển đồng thời, hoặc quy mô người dùng thực tế đủ lớn để chi phí vận hành microservices trở nên hợp lý — khi đó xem xét tách một số Infrastructure adapter thành service độc lập.

ADR-04 — Huấn luyện KMeans offline theo lô, không gọi như một Port thời gian thực

Bối cảnh: Ban đầu tài liệu để chung một IClusteringPort mơ hồ, dễ hiểu nhầm là gọi huấn luyện lại lúc truy vấn.

Quyết định: Tách rõ: huấn luyện là batch job offline ghi kết quả vào dữ liệu; runtime chỉ đọc cluster_id có sẵn và dùng một Port riêng, nhẹ (IClusterAssignmentPort) để so khớp vector người dùng với tâm cụm đã lưu.

Gọi huấn luyện lại KMeans mỗi lần có truy vấn — không chọn vì chi phí tính toán không tương xứng với một thao tác cần phản hồi nhanh, và kết quả cụm sẽ không ổn định giữa các lần truy vấn liên tiếp.

Hệ quả: Yêu cầu quản lý version cho cặp (cluster_id, centroid) như đã mô tả ở Kiến trúc Kỹ thuật mục 6.3 và 9.2, để tránh lệch phiên bản giữa dữ liệu và centroid đang dùng.

Điều kiện xem xét lại (Review Trigger / Exit Criteria): Tần suất thêm nhà hàng mới trở nên rất cao (ví dụ cần cập nhật cụm gần thời gian thực thay vì theo lô định kỳ) — khi đó xem xét chuyển sang huấn luyện tăng dần (incremental clustering) thay vì batch job cố định.

ADR-05 — Nguồn dữ liệu chính là Google Places API, không phụ thuộc crawl đa nguồn TikTok cho phạm vi đến tháng 12/2026

Bối cảnh: Cần dữ liệu nhà hàng đủ lớn và hợp pháp trong thời gian hạn chế của một người.

Quyết định: Dùng Google Places API làm nguồn duy nhất cho Giai đoạn 0–1; nội dung đa phương tiện (TikTok, ASR) chuyển hẳn sang Giai đoạn 3/Ngoài phạm vi cho đến tháng 12 (xem mục 4).

Crawl đa nguồn (Google Maps + TikTok + Foody...) ngay từ đầu — không chọn cho mốc tháng 12 vì rủi ro pháp lý (điều khoản dịch vụ), rủi ro kỹ thuật (ASR tiếng Việt) và effort không tương xứng với quỹ thời gian còn lại (xem WBS mục đối chiếu hạn chót).

Hệ quả: Một số đặc trưng suy ra từ review đa nguồn (ví dụ độ phong phú thực đơn) sẽ kém chi tiết hơn so với kế hoạch đầy đủ ban đầu — chấp nhận được vì không phải yêu cầu Bắt buộc của SRS.

Điều kiện xem xét lại (Review Trigger / Exit Criteria): Chi phí Google Places API vượt hạn mức miễn phí đáng kể khi mở rộng quy mô; hoặc phát hiện độ phủ dữ liệu thiếu nghiêm trọng (nhiều nhà hàng quan trọng trong khu vực khảo sát không có trên Google Places) — khi đó xem xét bổ sung nguồn thứ hai có kiểm soát rủi ro pháp lý rõ ràng.

ADR-06 — Giai đoạn 0–1 dùng xếp hạng heuristic có trọng số tinh chỉnh thủ công, chưa dùng mô hình học có giám sát

Bối cảnh: Mô hình xếp hạng học có giám sát (MLRankingAdapter) cần dữ liệu tương tác người dùng (InteractionEvent) mà một hệ thống chưa ra mắt không thể có.

Quyết định: Dùng công thức cộng có trọng số, khởi tạo bằng phán đoán chuyên gia, tinh chỉnh qua Development Set, chỉ khoá lại sau khi kiểm tra trên Evaluation Set (xem mục 5 và Kiến trúc Kỹ thuật mục 9.3). Heuristic được chọn vì đây là lựa chọn đúng với giai đoạn phát triển hiện tại — dữ liệu tương tác chưa tồn tại — không phải vì heuristic được cho là tốt hơn học máy về bản chất; đây là một quyết định tạm thời có điều kiện thoát rõ ràng, không phải một lập trường kỹ thuật cố định.

Huấn luyện mô hình học có giám sát ngay từ Giai đoạn 0/1 bằng dữ liệu giả lập hoặc quá ít mẫu thật — không chọn vì một mô hình huấn luyện trên dữ liệu không đại diện dễ tạo cảm giác "có vẻ khoa học" nhưng thực chất không đáng tin hơn một công thức heuristic được tinh chỉnh có phương pháp.

Hệ quả: MLRankingAdapter (Giai đoạn 3) chỉ được kích hoạt khi đã tích luỹ đủ InteractionEvent và đạt tiêu chí nghiệm thu tương ứng — không phải một yêu cầu bắt buộc để coi MVP là hoàn thành.

Điều kiện xem xét lại (Review Trigger / Exit Criteria): Chuyển từ HeuristicRankingAdapter sang MLRankingAdapter (dạng Learning to Rank) khi đồng thời thoả: (1) đã tích luỹ tối thiểu 5.000 InteractionEvent hợp lệ; (2) có đủ tín hiệu implicit feedback phân biệt được (ví dụ tỷ lệ người dùng bấm xem chi tiết/chọn quán trong Top-5 đủ chênh lệch giữa các vị trí xếp hạng, không phải nhiễu ngẫu nhiên); (3) MLRankingAdapter thử nghiệm vượt HeuristicRankingAdapter trên cùng Evaluation Set theo Precision@5 — nếu không vượt, tiếp tục dùng heuristic dù đã đủ dữ liệu, vì khi đó heuristic vẫn là lựa chọn đúng.

3. Assumption Register

Toàn bộ thiết kế đang đứng trên một số giả định chưa được kiểm chứng. Bảng dưới đây ghi rõ giả định, hậu quả nếu giả định sai, và biện pháp giảm thiểu — để không bị động nếu bị chất vấn hoặc nếu thực tế lệch khỏi kỳ vọng.

Giả định

Tác động nếu sai

Validation (cách kiểm chứng)

Biện pháp giảm thiểu

Ghi chú

Dataset thu thập được đủ lớn (vài trăm bản ghi trở lên) để KMeans phân cụm có ý nghĩa thống kê

Cụm không tách biệt rõ (Silhouette thấp), Cluster Profile không diễn giải được, làm yếu phần học thuật

Ngay sau khi crawl xong (mốc M1), đếm số bản ghi hợp lệ; nếu dưới 300 bản ghi thì coi là chưa đạt

Đặt ngưỡng tối thiểu về số bản ghi trước khi huấn luyện; nếu không đạt, báo cáo trung thực và dùng heuristic thuần cho bản demo thay vì ép phân cụm trên dữ liệu quá ít

Kiểm tra ngay sau bước crawl (M1), không đợi đến M2 mới phát hiện

Rating trên Google Places phản ánh đúng chất lượng thực tế, không bị thao túng/spam có hệ thống

Xếp hạng heuristic bị lệch theo rating sai, gợi ý kém tin cậy dù thuật toán đúng

Lấy mẫu 50 nhà hàng, so sánh rating với số lượng đánh giá (user_ratings_total); nếu rating cao (>4,5) nhưng số đánh giá rất thấp (<5) ở trên 30% mẫu, coi giả định là yếu

Không dùng rating làm tín hiệu duy nhất; kết hợp với số lượng đánh giá để giảm trọng số cho quán có ít đánh giá

Rủi ro chấp nhận được ở quy mô đồ án, không có ngân sách kiểm chứng chéo nhiều nguồn

Người dùng trả lời khảo sát (mood, đi với ai, ngân sách...) trung thực, không chọn ngẫu nhiên khi thử nghiệm

Dữ liệu tương tác thu được (nếu dùng để đánh giá) không phản ánh nhu cầu thật, làm sai lệch đánh giá trải nghiệm

Trong buổi thử nghiệm thật, so sánh câu trả lời khảo sát với câu tìm kiếm tự do của cùng người dùng; nếu mâu thuẫn rõ rệt (ví dụ chọn ngân sách thấp nhưng gõ tìm quán sang trọng) ở nhiều người, coi giả định là yếu

Khi thử nghiệm với người dùng thật, ưu tiên kịch bản có bối cảnh cụ thể ("giả sử bạn đang...") thay vì để người thử tự do và có thể trả lời qua loa

Chủ yếu ảnh hưởng đến đánh giá Definition of Success (mục 5), không ảnh hưởng đến kiến trúc

Nội dung review phản ánh đúng trải nghiệm không gian/độ ồn thực tế, đủ để suy ra đặc trưng qua text mining

Đặc trưng độ ồn/không gian suy ra sai, cụm trải nghiệm không phản ánh đúng thực tế

Lấy mẫu 100 review, cho một người đánh giá thủ công gắn nhãn độ ồn, so sánh với nhãn suy ra tự động qua text mining; nếu độ khớp dưới 70% thì coi giả định là yếu

Chỉ tính đặc trưng này cho nhà hàng có đủ số lượng review tối thiểu đề cập từ khoá liên quan; nếu Validation dưới ngưỡng, để trống đặc trưng (optional), không suy diễn ép

Đã có sẵn cơ chế optional field cho trường hợp này (Kiến trúc Kỹ thuật mục 6.3)

Người dùng đồng ý chia sẻ vị trí GPS chính xác qua trình duyệt

Không xác định được vị trí trung tâm tìm kiếm, tính năng bản đồ/khoảng cách mất tác dụng

Trong buổi thử nghiệm, ghi nhận tỷ lệ người dùng từ chối chia sẻ vị trí trên tổng số người thử; nếu trên 20% từ chối, coi giả định là yếu

Có phương án dự phòng nhập địa chỉ thủ công khi từ chối chia sẻ vị trí (đã ghi ở SRS mục 2.6)

Đã có phương án dự phòng, không phải rủi ro mới

4. Ngoài phạm vi (Out of Scope)

Danh sách dưới đây liệt kê rõ những gì hệ thống chủ động KHÔNG giải quyết trong toàn bộ vòng đời dự án hiện tại (không chỉ riêng mốc tháng 12), để tránh bị hỏi lan man về những hướng chưa từng được cam kết:

Gợi ý cập nhật theo thời gian thực dựa trên hành vi click/lướt xem trong phiên (real-time behavioral recommendation) — hệ thống chỉ dùng ngữ cảnh khai báo tường minh (khảo sát, câu tìm kiếm) cho mỗi lượt tìm kiếm.

Collaborative Filtering (gợi ý dựa trên hành vi của những người dùng khác tương tự) — cần khối lượng người dùng và lịch sử tương tác vượt xa quy mô một đồ án; chỉ ghi nhận là hướng mở (Kiến trúc Kỹ thuật mục 6.5, Giai đoạn 4).

Online Learning (mô hình tự cập nhật liên tục theo từng tương tác mới) — mọi việc huấn luyện lại đều là batch offline có kiểm soát (ADR-04, ADR-06), không có vòng lặp học tự động không giám sát.

Multi-city optimization (tối ưu đồng thời cho nhiều thành phố với đặc điểm giao thông/văn hoá ẩm thực khác nhau) — phạm vi dữ liệu và đánh giá giới hạn ở một thành phố duy nhất.

Tài khoản người dùng, lưu lịch sử tìm kiếm nhiều phiên, cá nhân hoá dài hạn — mỗi lượt tìm kiếm độc lập, không có khái niệm hồ sơ người dùng lâu dài.

Đặt bàn, thanh toán, hoặc bất kỳ giao dịch nào trong ứng dụng — hệ thống dừng lại ở việc gợi ý và dẫn hướng, không đóng vai trò nền tảng giao dịch.

5. Định nghĩa Thành công (Definition of Success)

Các chỉ số ở WBS (Silhouette Score, Precision@5...) là điều kiện kỹ thuật để một cấu phần được coi là hoạt động đúng — chúng không tự động chứng minh sản phẩm có giá trị. Câu hỏi lớn hơn, ở mức sản phẩm, là: dự án này thành công nghĩa là gì?

Người dùng thử nghiệm chọn được một nhà hàng cụ thể để đi trong vòng dưới 2 phút kể từ khi mở ứng dụng và nhập nhu cầu — đo bằng quan sát trực tiếp trong một buổi thử nghiệm nhỏ, không cần công cụ đo phức tạp.

Tối thiểu 70% người dùng thử nghiệm đánh giá gợi ý đầu tiên nhận được là "hữu ích" hoặc tốt hơn so với việc họ tự duyệt Google Maps/Foody như thường lệ — hỏi trực tiếp sau khi thử, một câu hỏi có/không hoặc thang 1–5.

Người xem (hội đồng, người dùng thử) có thể tự giải thích lại được vì sao một gợi ý xuất hiện, chỉ dựa vào lý do hiển thị kèm theo — đây là cách đo Explainability một cách thực tế, không chỉ là một mục tiêu trừu tượng ở SRS mục 2.

Ba tiêu chí trên là Definition of Success ở mức sản phẩm. Chúng khác về bản chất so với tiêu chí nghiệm thu kỹ thuật ở WBS: một hệ thống có thể đạt Precision@5 tốt nhưng vẫn thất bại ở tiêu chí "chọn được quán trong dưới 2 phút" nếu giao diện rối hoặc luồng thao tác quá nhiều bước — vì vậy cả hai nhóm tiêu chí cần được theo dõi song song, không thay thế cho nhau.

6. Nếu phải cắt 40% phạm vi, giữ 90% giá trị học thuật và sản phẩm

Đây là bài kiểm tra quan trọng nhất cho một kiến trúc: không phải thiết kế được nhiều, mà biết bỏ đúng thứ. Nguyên tắc chọn: cắt những gì có chi phí triển khai cao nhưng không phải là giả thuyết cốt lõi đang được kiểm chứng (context/mood-aware + tìm kiếm ngữ nghĩa + minh bạch lý do gợi ý), và những gì phụ thuộc vào dữ liệu/điều kiện chưa chắc có ở thời điểm tháng 12.

Cắt bỏ hẳn khỏi phạm vi đến tháng 12 (không phải "làm thêm nếu còn thời gian")

Mô hình xếp hạng học có giám sát (MLRankingAdapter, Giai đoạn 3) — cắt. Lý do: cần InteractionEvent chưa tồn tại ở một hệ thống chưa ra mắt; cố huấn luyện trên dữ liệu giả lập/quá ít vừa tốn effort vừa tạo rủi ro học thuật (trông có vẻ khoa học nhưng không đáng tin — xem ADR-06). Ranking heuristic đã tinh chỉnh có phương pháp (Development/Evaluation Set) vẫn là một đóng góp học thuật hợp lệ, không cần ML để hợp lệ.

Tín hiệu thời tiết/giao thông thời gian thực (IWeatherPort, ITrafficPort) — cắt. Lý do: đây là một lớp "gia vị" cho trải nghiệm, không phải giả thuyết cốt lõi; kéo theo hai tích hợp API bên thứ ba mới (thêm rủi ro quota/lỗi) trong khi giá trị chứng minh được lại nhỏ so với việc chứng minh core loop (ngữ cảnh + ngữ nghĩa + bản đồ) hoạt động tốt.

Crawl đa nguồn TikTok/ASR — cắt, giữ đúng như ADR-05. Lý do: rủi ro pháp lý và kỹ thuật cao nhất trong toàn bộ danh sách, trong khi Google Places API một mình đã đủ dữ liệu để chứng minh toàn bộ pipeline.

Gợi ý món ăn (Dish Recommendation) — cắt. Lý do: đòi hỏi một chiều dữ liệu mới (thực đơn/món ăn theo từng quán) không có sẵn và không đảm bảo crawl được đầy đủ; đây luôn là một tính năng "thêm vào" theo yêu cầu sau này, không phải ý tưởng gốc của MoodBite — cắt nó không làm suy yếu giả thuyết cốt lõi.

Tổng hợp đánh giá bằng mô hình tóm tắt riêng (ISummarizationPort đầy đủ) — thu gọn, không cắt hẳn. Thay một mô hình tóm tắt sinh (abstractive) bằng đúng kỹ thuật trích xuất từ khoá đã thiết kế sẵn cho "độ ồn" (đếm tần suất, chọn câu review đại diện) — vẫn giữ được lời hứa Explainability trong Definition of Success mà không cần một hệ con NLP thứ hai.

Giữ lại (đóng góp 90% giá trị còn lại)

KMeans + đánh giá cụm đúng phương pháp (Silhouette, Elbow) — vẫn là xương sống học thuật của đồ án.

Semantic Search bằng embedding — đây là giả thuyết sản phẩm trung tâm (tìm theo ý nghĩa, không chỉ từ khoá) và là điểm khác biệt lớn nhất so với Google Maps/Foody; không thể cắt mà không đánh mất luận điểm chính của đề tài.

Kiến trúc Clean Architecture + Ports & Adapters — chi phí thiết kế đã trả gần hết (đã có trong ba tài liệu), giữ lại gần như miễn phí và là nơi thể hiện tư duy kỹ thuật rõ nhất.

Ứng dụng web có bản đồ, định vị người dùng — đây là lý do dự án được yêu cầu chuyển từ dạng khảo sát sang web; cắt phần này coi như quay lại đề án cũ, không chấp nhận được.

Business Rules (lọc ràng buộc cứng: ngân sách, dị ứng, giờ mở cửa) — chi phí triển khai thấp, nhưng là phần chứng minh rõ nhất tư duy "AI không nên quyết định mọi thứ" mà hội đồng đã đánh giá cao ngay từ vòng đầu.

Tổng lại: phần bị cắt đều là các lớp tín hiệu "bổ sung" (weather/traffic, dish, ML ranking, đa nguồn dữ liệu) được thiết kế từ đầu như các Adapter độc lập, tuỳ chọn (mục 8, Kiến trúc Kỹ thuật) — nên việc cắt không đòi hỏi thiết kế lại, chỉ đơn giản là không viết Adapter đó trước tháng 12. Đây chính là lý do kiến trúc Ports & Adapters được chọn ngay từ ADR-03: để một quyết định cắt giảm phạm vi sau này không phải là một cuộc đại phẫu.

7. Chiến lược khi giả thuyết kỹ thuật thất bại (Failure Strategy)

Toàn bộ tài liệu trước đây ngầm giả định các cấu phần chính sẽ hoạt động tốt. Mục này ghi rõ: nếu không, làm gì tiếp — để không bị động và để việc "thất bại một phần" không có nghĩa là dừng dự án.

7.1. Nếu KMeans không tạo ra cụm có ý nghĩa (Silhouette Score thấp, ví dụ ≈ 0,12)

Bước 1 — Đổi số cụm k: thử lại Elbow/Silhouette trên một dải k khác (kể cả k nhỏ hơn nhiều so với dự kiến ban đầu); nhiều khi dữ liệu chỉ tách biệt tự nhiên ở một số ít cụm lớn.

Bước 2 — Đổi/thêm đặc trưng: xem lại các đặc trưng đầu vào (mức giá, độ ồn suy ra từ review...) có thực sự phân tách nhà hàng hay không; loại bỏ đặc trưng nhiễu, chuẩn hoá lại nếu thang đo lệch.

Bước 3 — Đổi thuật toán: quay lại bảng so sánh ở ADR-01, thử DBSCAN hoặc Hierarchical trên chính dữ liệu thật (không chỉ tin vào lý do lý thuyết đã chọn KMeans trước đó) nếu bước 1–2 không cải thiện.

Bước 4 — Chấp nhận không dùng tín hiệu cụm: nếu cả ba bước trên đều không đạt ngưỡng tối thiểu, tắt hẳn tín hiệu cụm trong RankingUseCase (tham số tuỳ chọn, đã thiết kế sẵn — xem Kiến trúc Kỹ thuật mục 6.3) và báo cáo trung thực rằng phân cụm không mang lại giá trị trên bộ dữ liệu này — đây vẫn là một kết luận hợp lệ, không phải một thất bại của toàn bộ đồ án (xem mục 10).

7.2. Nếu chất lượng embedding tiếng Việt không tốt (tìm kiếm ngữ nghĩa trả kết quả không liên quan)

Fallback đã có sẵn trong kiến trúc, không cần thiết kế thêm: KeywordSearchAdapter của Giai đoạn 0 (so khớp từ khoá/thuộc tính có cấu trúc) và SemanticSearchAdapter của Giai đoạn 1 cùng cài đặt một ISearchPort — nếu độ liên quan của tìm kiếm ngữ nghĩa đo được (mục tiêu chí nghiệm thu M2, WBS) không đạt ngưỡng, config/di_container trỏ ISearchPort về lại KeywordSearchAdapter, không cần deploy lại gì khác.

Trước khi kết luận embedding "không tốt", thử thay mô hình embedding khác (nhiều lựa chọn embedding tiếng Việt/đa ngôn ngữ hiện có) như một bước trung gian, trước khi hạ cấp về fallback từ khoá.

8. Đa dạng hoá kết quả (Diversity), không chỉ độ liên quan

Precision@5 chỉ đo việc từng kết quả có phù hợp hay không, không đo việc 5 kết quả đó có khác nhau đủ để có ý nghĩa lựa chọn hay không. Một hệ thống có thể đạt Precision@5 tuyệt đối nhưng vẫn vô dụng nếu cả 5 gợi ý đều là quán cà phê gần giống nhau.

Bổ sung chỉ số Intra-List Diversity@5: tỷ lệ cặp nhà hàng trong Top-5 thuộc các cụm trải nghiệm (experience_cluster_id) khác nhau, trên tổng số cặp có thể có (10 cặp với Top-5). Ngưỡng tối thiểu tham khảo: trên 60% số cặp thuộc cụm khác nhau.

Đây chính là câu trả lời cụ thể cho câu hỏi "KMeans đóng góp gì" ở mục 10: vai trò thực tế của tín hiệu cụm không chỉ là "đo độ giống trải nghiệm" một cách trừu tượng, mà được dùng để tránh Top-5 bị dồn vào một nhóm nhà hàng đơn điệu — một vai trò mà riêng Business Rules và Semantic Search không tự nhiên có được.

9. Đo lường Explainability cụ thể hơn

Mục 5 (Definition of Success) đã nêu Explainability là một tiêu chí thành công, nhưng "người dùng nói họ hiểu" là một phép đo yếu — người dùng có thể tự nhận là hiểu dù không thực sự hiểu đúng lý do. Cách đo chặt hơn:

Sau khi hiển thị một gợi ý kèm lý do (ví dụ: "Yên tĩnh · Phù hợp đi một mình · Trong bán kính 2km · Ngân sách phù hợp"), che lý do đi và hỏi người dùng thử nghiệm diễn giải lại bằng lời của họ vì sao họ nghĩ nhà hàng này được gợi ý.

Người đánh giá đối chiếu câu trả lời của người dùng với danh sách lý do thực tế đã hiển thị: tính là "hiểu đúng" nếu người dùng nêu được ít nhất 2 trong số các lý do chính, không cần nêu đủ toàn bộ.

Tỷ lệ "hiểu đúng" trên tổng số người dùng thử nghiệm là con số cụ thể thay thế cho phát biểu chung chung "hệ thống có Explainability".

10. Ablation Study và tính khả bác bỏ (Falsifiability)

Giả thuyết trung tâm của MoodBite là: thêm tín hiệu phân cụm trải nghiệm (KMeans) vào một hệ thống đã có Business Rules và Semantic Search sẽ cải thiện kết quả gợi ý. Đây là một giả thuyết cần được kiểm chứng, không phải một điều hiển nhiên đúng — và cần chuẩn bị sẵn cho câu hỏi phản biện mạnh nhất: "Nếu bỏ hẳn KMeans, hệ thống còn hoạt động không? Nếu có, KMeans đóng góp gì?"

10.1. Thiết kế thí nghiệm

Baseline (B): Business Rules (lọc ràng buộc cứng) + Semantic Search (embedding) + xếp hạng chỉ theo rating/khoảng cách/mức giá — hoàn toàn không dùng tín hiệu cụm. Hệ thống này chạy được độc lập, không phụ thuộc KMeans — đúng như câu hỏi phản biện giả định.

Proposed (P): giống Baseline, cộng thêm tín hiệu cụm trong bước xếp hạng/đa dạng hoá (đúng phần đã mô tả ở mục 8). Vì cluster_signal là tham số tuỳ chọn có sẵn trong RankingUseCase (Kiến trúc Kỹ thuật mục 6.3), việc bật/tắt để so sánh B và P không cần viết thêm code, chỉ cần gọi use case với hai cấu hình tham số khác nhau trên cùng một Evaluation Set.

So sánh B và P trên cùng Evaluation Set theo hai chỉ số: Precision@5 (giả thuyết: P không được kém hơn B đáng kể) và Intra-List Diversity@5 (giả thuyết: P cao hơn B rõ rệt).

10.2. Điều kiện để giả thuyết bị bác bỏ, và vì sao điều đó vẫn có giá trị

Nếu P không cải thiện Diversity so với B (chênh lệch không đáng kể), hoặc P làm giảm Precision@5 nhiều hơn mức chấp nhận được, giả thuyết trung tâm bị bác bỏ trong bối cảnh dữ liệu và bài toán này.

Kết luận đó vẫn là một kết quả nghiên cứu hợp lệ, không phải một thất bại cần che giấu: "trong bối cảnh dữ liệu và quy mô của đồ án này, tín hiệu phân cụm KMeans không mang lại cải thiện đáng kể so với việc chỉ dùng Business Rules và Semantic Search" là một phát biểu khoa học rõ ràng, có thể trình bày thẳng thắn trước hội đồng, và vẫn thể hiện được năng lực thiết kế thí nghiệm đúng phương pháp — điều này có giá trị học thuật ngang bằng, thậm chí cao hơn, so với việc chỉ báo cáo một con số Precision@5 đơn lẻ mà không có baseline đối chứng.

Nói cách khác, KMeans không được coi là một thành phần "phải đúng" để đồ án thành công — nó là một giả thuyết đang được kiểm chứng bằng một thí nghiệm có đối chứng, và bản thân việc thiết kế được thí nghiệm đó (thay vì chỉ khẳng định) mới là điều cần bảo vệ trước hội đồng.

11. Điều kiện để kết luận một giả thuyết bị bác bỏ (Falsification Criteria)

Mục 10 đã thiết kế ablation study cho riêng giả thuyết phân cụm. Mục này mở rộng cùng nguyên tắc cho toàn bộ các giả thuyết cốt lõi của đề tài — định nghĩa trước, bằng số cụ thể, điều gì sẽ khiến kết luận "giả thuyết này không đúng trong bối cảnh đề tài", thay vì chỉ định nghĩa thành công.

Giả thuyết phân cụm: KMeans không cải thiện Intra-List Diversity@5 so với Baseline (chênh lệch không có ý nghĩa thống kê rõ ràng trên Evaluation Set), hoặc làm giảm Precision@5 nhiều hơn mức chấp nhận được → giả thuyết phân cụm bị bác bỏ (xem mục 10).

Giả thuyết tìm kiếm ngữ nghĩa: SemanticSearchAdapter không cho Precision@5 tốt hơn rõ rệt so với KeywordSearchAdapter (baseline từ khoá) trên cùng Evaluation Set → giả thuyết ngữ nghĩa bị bác bỏ; hệ thống vẫn hoạt động bình thường bằng fallback từ khoá (mục 7.2), không cần huỷ bỏ dự án.

Giả thuyết giá trị sản phẩm: người dùng thử nghiệm không giảm được thời gian ra quyết định so với duyệt thủ công, và/hoặc dưới 40% người dùng đánh giá gợi ý là hữu ích (thấp hơn hẳn ngưỡng kỳ vọng 70% ở Định nghĩa Thành công, mục 5) → giả thuyết giá trị sản phẩm bị bác bỏ ở mức trải nghiệm, dù các cấu phần kỹ thuật riêng lẻ vẫn hoạt động đúng.

Cần phân biệt hai mức độ: một giả thuyết con bị bác bỏ (ví dụ phân cụm không giúp ích) là một kết quả nghiên cứu bình thường, không đồng nghĩa đề tài thất bại — hệ thống vẫn chạy được nhờ kiến trúc Adapter cho phép tắt thành phần đó. Đề tài chỉ thực sự được coi là thất bại nếu cả ba giả thuyết ở trên đều bị bác bỏ đồng thời, hoặc nếu ngay cả Baseline (Business Rules + Semantic Search/Keyword Search) cũng không tạo ra được một sản phẩm dùng được — tức là vấn đề nằm ở chính tiền đề bài toán (dữ liệu không thu thập được, hoặc nhu cầu người dùng không tồn tại như giả định), không phải ở một kỹ thuật cụ thể nào.


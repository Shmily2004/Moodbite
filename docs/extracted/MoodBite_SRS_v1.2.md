# MoodBite_SRS_v1.2

TÀI LIỆU ĐẶC TẢ YÊU CẦU PHẦN MỀM

(Software Requirements Specification – SRS)

MoodBite

Nền tảng Web Gợi ý Nhà hàng & Món ăn theo Ngữ cảnh Thời gian thực

Phiên bản 1.2

Ngày ban hành: 21/07/2026 (cập nhật v1.2)

Tài liệu nguồn: MoodBite – Đề án ý tưởng

Lịch sử thay đổi tài liệu

Phiên bản

Ngày

Mô tả thay đổi

Người thực hiện

1.0

16/07/2026

Khởi tạo tài liệu SRS dựa trên đề án ý tưởng MoodBite

Nhóm phát triển

1.1

16/07/2026

Bổ sung xử lý video review (ASR), mô-đun trích xuất đặc trưng trải nghiệm từ văn bản phi cấu trúc (aspect extraction) cho FR-4.1, thực thể InteractionEvent và mô-đun ghi nhận hành vi người dùng phục vụ nâng cấp mô hình xếp hạng có giám sát; cập nhật MoSCoW, tiêu chí nghiệm thu và mô hình dữ liệu tương ứng

Nhóm phát triển

1.2

21/07/2026

Bổ sung mục 2.7 — chiến lược triển khai theo hạn chót tháng 12/2026 cho dự án cá nhân: tách Giai đoạn 0 (bộ khung chạy được, dữ liệu nhỏ + so khớp đơn giản) trước Giai đoạn 1 (MVP đầy đủ với embedding/tìm kiếm ngữ nghĩa), nhằm kiểm chứng sớm phần tích hợp mô hình–giao diện web trước khi đầu tư thời gian vào crawl/embedding quy mô lớn

Nhóm phát triển

Mục lục

1. Giới thiệu

1.1. Mục đích tài liệu

Tài liệu này đặc tả các yêu cầu chức năng và phi chức năng của hệ thống MoodBite — nền tảng web gợi ý nhà hàng và món ăn theo ngữ cảnh thời gian thực — nhằm làm cơ sở thống nhất giữa các bên liên quan (nhóm phát triển, giảng viên hướng dẫn/khách hàng, người kiểm thử) về phạm vi và hành vi mong đợi của hệ thống trước khi bước vào giai đoạn thiết kế và cài đặt. Tài liệu được xây dựng dựa trên nội dung của tài liệu “MoodBite – Đề án ý tưởng”.

1.2. Phạm vi sản phẩm

MoodBite là một ứng dụng web cho phép người dùng nhập nhu cầu ăn uống bằng ngôn ngữ tự nhiên (ví dụ: “muốn tìm quán yên tĩnh, có chỗ đậu xe, gần đây, hợp để nói chuyện”) và nhận về danh sách nhà hàng cùng món ăn được xếp hạng theo mức độ phù hợp, có tính đến vị trí hiện tại, thời tiết, tình trạng giao thông và thời điểm tìm kiếm. Hệ thống bao gồm:

Giao diện bản đồ tương tác để tìm kiếm và hiển thị kết quả.

Bộ máy xử lý ngữ nghĩa và xếp hạng nhà hàng theo ngữ cảnh động.

Mô-đun tổng hợp đánh giá (review synthesis) tự động.

Mô-đun đề xuất món ăn theo tâm trạng/ngữ cảnh.

Hệ thống thu thập, làm sạch và cập nhật dữ liệu nhà hàng theo đợt (offline).

Phạm vi của phiên bản đầu (MVP) giới hạn trong một khu vực/thành phố thí điểm và tập trung vào luồng tìm kiếm – xem gợi ý; các tính năng tài khoản người dùng, cá nhân hoá theo lịch sử dài hạn, hoặc đặt chỗ/đặt món trực tiếp với nhà hàng không thuộc phạm vi phiên bản này (xem mục 2.6 và 8).

1.3. Đối tượng sử dụng tài liệu

Nhóm phát triển: dùng làm cơ sở thiết kế kiến trúc, cơ sở dữ liệu và cài đặt.

Giảng viên hướng dẫn / người đánh giá đồ án: dùng để đối chiếu phạm vi triển khai với đề án ý tưởng.

Người kiểm thử (tester): dùng làm cơ sở xây dựng ca kiểm thử (test case).

1.4. Định nghĩa, từ viết tắt

Thuật ngữ

Giải thích

SRS

Software Requirements Specification – Tài liệu đặc tả yêu cầu phần mềm.

FR

Functional Requirement – Yêu cầu chức năng.

NFR

Non-Functional Requirement – Yêu cầu phi chức năng.

MVP

Minimum Viable Product – Phiên bản tối thiểu khả dụng.

Embedding

Vector số học biểu diễn ngữ nghĩa của văn bản, dùng cho tìm kiếm ngữ nghĩa.

Ranking model

Mô hình học máy dự đoán/xếp hạng mức độ phù hợp giữa nhu cầu người dùng và nhà hàng.

Tín hiệu ngữ cảnh

Các yếu tố thời điểm tìm kiếm: thời tiết, nhiệt độ, giao thông, thời điểm trong ngày.

Review synthesis

Tác vụ tóm tắt tự động nhiều review thành một nhận xét ngắn gọn.

ASR

Automatic Speech Recognition – nhận dạng giọng nói, chuyển audio thành văn bản (transcript).

Aspect extraction

Trích xuất khía cạnh — kỹ thuật xử lý ngôn ngữ tự nhiên nhằm suy ra điểm số theo từng khía cạnh cụ thể (ví dụ không gian, độ ồn) từ văn bản phi cấu trúc.

Implicit feedback

Tín hiệu hành vi gián tiếp thể hiện mức độ quan tâm của người dùng (xem chi tiết, bấm chỉ đường, lưu quán), dùng thay cho đánh giá tường minh khi huấn luyện mô hình.

1.5. Tài liệu tham khảo

MoodBite – Đề án ý tưởng (Real-time Context-Aware Restaurant Recommendation Platform), phiên bản cập nhật gần nhất.

2. Mô tả tổng quan hệ thống

2.1. Bối cảnh sản phẩm

Các nền tảng bản đồ/đánh giá hiện có (Google Maps, Foody, TikTok...) cung cấp dữ liệu nhà hàng phong phú nhưng không sắp xếp theo đúng nhu cầu thực tế của người dùng tại đúng thời điểm và vị trí. MoodBite không thay thế các nguồn dữ liệu này mà đóng vai trò lớp xử lý ở trên: tiếp nhận dữ liệu thô, tính toán lại mức độ phù hợp theo ngữ cảnh động (thời tiết, giao thông, tâm trạng diễn đạt tự do), và hiển thị kết quả đã xếp hạng trên nền bản đồ tương tác.

2.2. Tổng quan chức năng sản phẩm

Ở mức tổng quan, hệ thống cung cấp bốn nhóm chức năng chính, tương ứng với kiến trúc mô hình lai của đề án ý tưởng:

Nhập nhu cầu bằng ngôn ngữ tự nhiên và nhận gợi ý nhà hàng được xếp hạng theo mức độ phù hợp.

Xem nhận xét tổng hợp (điểm mạnh/điểm yếu) của từng nhà hàng thay vì đọc toàn bộ review.

Nhận gợi ý món ăn cụ thể theo tâm trạng/ngữ cảnh, trong phạm vi các quán được đề xuất.

Tương tác với bản đồ: xem vị trí, tuyến đường, thời gian di chuyển ước tính; đổi khu vực tìm kiếm.

2.3. Đối tượng người dùng

Nhóm người dùng

Mô tả

Mức độ tương tác kỹ thuật

Người dùng cuối (thực khách)

Người cần tìm quán ăn/món ăn phù hợp với hoàn cảnh hiện tại.

Không yêu cầu kiến thức kỹ thuật; thao tác qua giao diện web thông thường.

Quản trị viên dữ liệu

Theo dõi chất lượng dữ liệu crawl, xử lý trùng lặp, cập nhật danh mục nhà hàng.

Người vận hành nội bộ, dùng trang quản trị riêng.

Nhóm phát triển/vận hành mô hình

Huấn luyện, đánh giá và cập nhật mô hình xếp hạng, embedding, tóm tắt review.

Kỹ thuật, thao tác ngoài phạm vi giao diện người dùng cuối.

2.4. Môi trường vận hành

Ứng dụng web, truy cập qua trình duyệt trên máy tính và thiết bị di động (responsive).

Backend triển khai dạng dịch vụ web (web service) có khả năng gọi API bên thứ ba (thời tiết, bản đồ/giao thông).

Cơ sở dữ liệu lưu trữ dữ liệu tĩnh (nhà hàng, món ăn, embedding) tách biệt với tín hiệu động chỉ gọi tại thời điểm tìm kiếm.

2.5. Ràng buộc thiết kế

Phụ thuộc vào tính sẵn sàng và giới hạn truy vấn (rate limit) của các API bên thứ ba: bản đồ, thời tiết, giao thông.

Việc thu thập dữ liệu từ các nền tảng mạng xã hội (ví dụ TikTok) phải tuân thủ điều khoản dịch vụ của nền tảng nguồn; trong trường hợp không thể crawl trực tiếp, hệ thống cần phương án thay thế (nhập liệu thủ công/API chính thức nếu có).

Độ phủ dữ liệu món ăn (thực đơn) phụ thuộc vào việc nhà hàng có công khai thực đơn hay không; với nhà hàng không có thực đơn cấu trúc, chức năng đề xuất món chấp nhận độ phủ thấp hơn (trích xuất từ review).

Nội dung video review (TikTok...) là dữ liệu đa phương thức; ở phạm vi tài liệu này, hệ thống chỉ xử lý phần văn bản khai thác được từ video (caption có sẵn và transcript sinh ra qua ASR), không xử lý tín hiệu hình ảnh/âm thanh thô (nhận diện không gian qua thị giác máy tính, đo độ ồn thực tế qua phân tích âm lượng). Độ chính xác của ASR tiếng Việt (đặc biệt với giọng địa phương, tạp âm nền quán ăn) là một rủi ro cần chấp nhận và kiểm soát bằng lấy mẫu kiểm tra thủ công định kỳ.

Các khía cạnh mô tả trải nghiệm (không gian, mức độ ồn) không có sẵn dưới dạng số liệu — phải được suy ra từ văn bản phi cấu trúc (review/transcript) trước khi đưa vào mô hình phân cụm; độ tin cậy của các đặc trưng này phụ thuộc vào số lượng review đề cập đến từng khía cạnh cho mỗi nhà hàng (xem FR-7.7, FR-7.8).

2.6. Giả định và phụ thuộc

Giả định người dùng đồng ý chia sẻ vị trí hiện tại qua trình duyệt/thiết bị; nếu từ chối, hệ thống cần phương án dự phòng (nhập địa chỉ thủ công).

Giả định dữ liệu nhà hàng ban đầu được crawl và xử lý xong trước khi hệ thống phục vụ người dùng thật (pha offline hoàn tất trước pha online).

Phiên bản đầu không giả định có sẵn dữ liệu tương tác người dùng để huấn luyện mô hình xếp hạng có giám sát; mô hình xếp hạng ở MVP dùng công thức trọng số/heuristic, có thể nâng cấp thành mô hình học máy khi tích lũy đủ dữ liệu (xem mục 3.4 và mục 8).

Để rút ngắn thời gian tích luỹ dữ liệu huấn luyện cho giai đoạn nâng cấp nói trên, việc ghi nhận hành vi tương tác của người dùng (mục 3.9) được thực hiện ngay từ MVP, độc lập với thời điểm mô hình học có giám sát thực sự được xây dựng.

2.7. Chiến lược triển khai theo hạn chót (tháng 12/2026)

Vì dự án do một cá nhân thực hiện với hạn chót tháng 12/2026, phạm vi MVP ở mục 1.2 được tách thêm một bước con phía trước để giảm rủi ro kỹ thuật xuất hiện sớm, thay vì chỉ có một mốc MVP duy nhất:

Giai đoạn 0 — Bộ khung chạy được (Walking Skeleton), mục tiêu hoàn thành trong 2–3 tuần đầu: chứng minh toàn bộ luồng kỹ thuật hoạt động — từ nhập nhu cầu, qua xử lý mô hình, đến hiển thị kết quả trên bản đồ web — bằng một tập dữ liệu nhỏ (khoảng 50–100 nhà hàng nhập tay hoặc lấy mẫu nhanh từ một nguồn có sẵn), dùng cơ chế so khớp đơn giản (lọc theo từ khoá/thuộc tính có cấu trúc) thay cho tìm kiếm ngữ nghĩa dựa trên embedding. Việc cào dữ liệu quy mô lớn (FR-7.1, FR-7.2) và sinh embedding (FR-7.4) được lùi lại, không chặn việc chứng minh mô hình và giao diện web hoạt động được.

Giai đoạn 1 (MVP đầy đủ) giữ nguyên phạm vi như mục 1.2 và mục 8, nhưng chỉ bắt đầu triển khai dữ liệu quy mô lớn và tìm kiếm ngữ nghĩa sau khi Giai đoạn 0 đã chạy ổn định trên trình duyệt — đảm bảo rủi ro kỹ thuật lớn nhất (tích hợp mô hình với giao diện web, phần chưa từng làm) được kiểm chứng sớm, tách khỏi rủi ro dữ liệu (crawl, embedding — cơ chế đã rõ nhưng tốn thời gian thực hiện).

Theo cách tách này, FR-4.2 (Tìm kiếm ngữ nghĩa) được triển khai theo hai bước: bản rút gọn dùng so khớp từ khoá/thuộc tính có cấu trúc ở Giai đoạn 0, nâng cấp lên embedding thực sự ở Giai đoạn 1 khi đã có dữ liệu crawl. Mức ưu tiên Bắt buộc của FR-4.2 ở mục 8 vẫn giữ nguyên cho đích cuối (Giai đoạn 1); Giai đoạn 0 chỉ là một bản thay thế tạm thời phục vụ việc kiểm chứng kiến trúc sớm, không phải một yêu cầu SRS mới.

Chi tiết phân rã công việc và effort của Giai đoạn 0 được trình bày trong tài liệu WBS tương ứng (mục 3, 4).

3. Yêu cầu chức năng

Các yêu cầu chức năng được nhóm theo mô-đun, bám theo kiến trúc 5 lớp mô hình và các thành phần frontend/backend đã mô tả trong đề án ý tưởng. Mỗi yêu cầu có mã định danh (ID), mô tả, và mức ưu tiên (Bắt buộc / Nên có / Có thể có) theo MoSCoW, chi tiết mức ưu tiên tổng hợp tại mục 8.

3.1. Mô-đun Định vị & Bản đồ

ID

Tên chức năng

Mô tả

FR-1.1

Lấy vị trí hiện tại

Hệ thống lấy toạ độ vị trí hiện tại của người dùng qua định vị trình duyệt/thiết bị, dùng làm tâm điểm mặc định cho tìm kiếm.

FR-1.2

Nhập vị trí thủ công

Cho phép người dùng nhập/chọn địa chỉ thủ công khi từ chối chia sẻ vị trí hoặc muốn tìm quanh một vị trí khác.

FR-1.3

Hiển thị bản đồ tương tác

Hiển thị kết quả gợi ý dưới dạng điểm đánh dấu (marker) trên bản đồ tương tác, kèm thông tin tóm tắt khi chạm/hover vào marker.

FR-1.4

Đổi tâm tìm kiếm

Cho phép người dùng kéo/thu phóng bản đồ để đổi khu vực tìm kiếm; hệ thống tính lại toàn bộ tín hiệu ngữ cảnh theo tâm bản đồ mới.

FR-1.5

Hiển thị tuyến đường & thời gian di chuyển

Với mỗi nhà hàng trong kết quả, hiển thị tuyến đường ước tính và thời gian di chuyển thực tế từ vị trí hiện tại/tâm bản đồ.

3.2. Mô-đun Nhập nhu cầu

ID

Tên chức năng

Mô tả

FR-2.1

Ô tìm kiếm ngôn ngữ tự nhiên

Cho phép người dùng gõ trực tiếp nhu cầu bằng câu tự do (ví dụ: “chỗ yên tĩnh để làm việc”).

FR-2.2

Gợi ý câu tìm kiếm mẫu

Hiển thị một số gợi ý nhanh (chip) cho người dùng chưa biết diễn đạt nhu cầu (ví dụ: “Ấm bụng ngày mưa”, “Ăn nhẹ, ít thời gian”).

FR-2.3

Bộ lọc ràng buộc cứng

Cho phép nhập/chọn các ràng buộc cứng: ngân sách, dị ứng/kiêng khem, giờ mở cửa mong muốn.

3.3. Mô-đun Tín hiệu ngữ cảnh thời gian thực

ID

Tên chức năng

Mô tả

FR-3.1

Lấy dữ liệu thời tiết

Gọi API thời tiết theo vị trí tìm kiếm tại thời điểm truy vấn (tình trạng mưa/nắng, nhiệt độ).

FR-3.2

Lấy tình trạng giao thông

Gọi API bản đồ/giao thông để lấy thời gian di chuyển thực tế thay vì khoảng cách đường chim bay.

FR-3.3

Xác định đặc trưng thời điểm

Xác định giờ trong ngày và ngày trong tuần tại thời điểm tìm kiếm, dùng làm đặc trưng đầu vào cho mô-đun xếp hạng.

3.4. Mô-đun Đề xuất nhà hàng

ID

Tên chức năng

Mô tả

FR-4.1

Phân cụm trải nghiệm (offline)

Nhóm các nhà hàng có đặc trưng trải nghiệm tương tự thành các cụm, cập nhật định kỳ theo lô. Đầu vào là vector đặc trưng có cấu trúc (không gian, mức độ ồn đã được số hoá, mức giá) do mô-đun trích xuất đặc trưng (FR-7.7) tạo ra — Lớp này không xử lý trực tiếp văn bản thô.

FR-4.2

Tìm kiếm ngữ nghĩa

Chuyển câu tìm kiếm và mô tả/review nhà hàng thành vector embedding; tính độ tương đồng ngữ nghĩa (cosine similarity) để xác định mức độ khớp về ý nghĩa.

FR-4.3

Lọc theo ràng buộc cứng

Loại các nhà hàng không thoả ràng buộc cứng (ngân sách, dị ứng, giờ mở cửa) trước khi đưa vào xếp hạng.

FR-4.4

Tính điểm xếp hạng dự đoán

Tổng hợp các tín hiệu (cụm trải nghiệm, độ tương đồng ngữ nghĩa, thời gian di chuyển, mức giá, rating, tín hiệu ngữ cảnh) thành một điểm phù hợp cuối cùng cho từng nhà hàng. Ở MVP dùng công thức trọng số/heuristic; giai đoạn sau nâng cấp thành mô hình học có giám sát, huấn luyện trên dữ liệu InteractionEvent (mục 3.9, 6.1) ghi nhận từ MVP.

FR-4.5

Hiển thị danh sách kết quả

Hiển thị danh sách nhà hàng theo thứ tự điểm phù hợp giảm dần, kèm thông tin cơ bản (tên, khoảng cách, mức giá, rating, cụm trải nghiệm).

3.5. Mô-đun Tổng hợp đánh giá

ID

Tên chức năng

Mô tả

FR-5.1

Tóm tắt review (offline)

Với mỗi nhà hàng, sinh một nhận xét tổng hợp ngắn gọn từ toàn bộ review đã thu thập, lưu sẵn để phục vụ tra cứu nhanh.

FR-5.2

Hiển thị nhận xét tổng hợp

Hiển thị điểm mạnh, điểm yếu và nhóm người dùng phù hợp cho mỗi nhà hàng trong kết quả tìm kiếm.

3.6. Mô-đun Đề xuất món ăn

ID

Tên chức năng

Mô tả

FR-6.1

Gán nhãn đặc trưng món ăn (offline)

Gán các thuộc tính cho từng món ăn: nhóm món, mức độ cay, nóng/lạnh, độ no, từ khoá cảm xúc liên quan.

FR-6.2

Ánh xạ tâm trạng sang món ăn

Đối chiếu câu mô tả tâm trạng/ngữ cảnh của người dùng với đặc trưng món ăn bằng kết hợp luật (rule) và so khớp ngữ nghĩa.

FR-6.3

Xếp hạng món trong phạm vi quán đề xuất

Xếp hạng món ăn chỉ trong tập nhà hàng đã được mô-đun 3.4 đề xuất, theo độ khớp ngữ cảnh và mức độ phổ biến trong review.

FR-6.4

Hiển thị món gợi ý kèm quán

Hiển thị món ăn được gợi ý đi kèm mỗi nhà hàng trong danh sách/bản đồ kết quả.

3.7. Mô-đun Thu thập & Quản trị dữ liệu

ID

Tên chức năng

Mô tả

FR-7.1

Crawl dữ liệu nhà hàng theo đợt

Thu thập thông tin cơ bản, toạ độ, giờ mở cửa, rating từ Google Maps/Places theo lịch định kỳ (không kích hoạt theo mỗi lượt tìm kiếm).

FR-7.2

Thu thập review đa nguồn

Thu thập nội dung review dạng văn bản từ các nguồn được phép, phục vụ tìm kiếm ngữ nghĩa và tổng hợp đánh giá.

FR-7.3

Làm sạch & khử trùng lặp

Phát hiện dữ liệu thiếu, trùng lặp giữa các nguồn (cùng một nhà hàng trên nhiều nền tảng), và mất cân bằng khu vực/loại hình trước khi đưa vào xử lý tiếp theo.

FR-7.4

Sinh & cập nhật embedding

Sinh vector embedding cho mô tả/review nhà hàng và món ăn; cập nhật định kỳ khi có dữ liệu mới.

FR-7.5

Trang quản trị chất lượng dữ liệu

Cung cấp giao diện nội bộ để quản trị viên theo dõi số liệu thu thập, tỷ lệ trùng lặp/thiếu dữ liệu, và can thiệp thủ công khi cần.

FR-7.6

Trích xuất văn bản từ video review

Với các review dạng video (TikTok...), thu thập caption có sẵn và sinh transcript bằng ASR (nhận dạng giọng nói) từ audio của video; transcript được đưa vào cùng pipeline xử lý với review dạng văn bản (FR-7.2, FR-7.7). Không xử lý tín hiệu hình ảnh/âm thanh thô.

FR-7.7

Trích xuất đặc trưng trải nghiệm (aspect extraction)

Từ nội dung review/transcript, suy ra điểm số theo từng khía cạnh trải nghiệm (không gian, mức độ ồn...) bằng kết hợp từ điển từ khoá và so khớp ngữ nghĩa/mô hình ngôn ngữ; tổng hợp điểm theo từng nhà hàng (trung bình có trọng số theo độ mới của review) để tạo vector đặc trưng có cấu trúc, làm đầu vào cho FR-4.1.

FR-7.8

Xử lý đặc trưng thiếu/độ tin cậy thấp

Khi số lượng review đề cập một khía cạnh trải nghiệm dưới ngưỡng tối thiểu quy định, đánh dấu đặc trưng đó là độ tin cậy thấp; áp dụng giá trị impute (trung vị toàn hệ thống) hoặc loại khỏi vector đặc trưng cho tới khi đủ dữ liệu, tránh đưa nhà hàng ít dữ liệu vào cụm sai lệch.

3.8. Mô-đun Trang phân tích dữ liệu

ID

Tên chức năng

Mô tả

FR-8.1

Thống kê tổng quan

Hiển thị các số liệu tổng quan hệ thống: số lượng nhà hàng, phân bố theo cụm trải nghiệm, phân bố khu vực.

FR-8.2

Thống kê hành vi tìm kiếm

Hiển thị các chỉ số vận hành: tỷ lệ người dùng chọn kết quả trong top gợi ý, thời gian trung bình ra quyết định (phục vụ đánh giá ở mục 6).

3.9. Mô-đun Ghi nhận hành vi người dùng

Mục tiêu của mô-đun này không phải phục vụ trực tiếp người dùng cuối, mà nhằm tích luỹ dữ liệu nhãn (label) ngay từ giai đoạn MVP, làm nền cho việc nâng cấp FR-4.4 thành mô hình học có giám sát khi có đủ dữ liệu (xem mục 2.6, 6.1, 8).

ID

Tên chức năng

Mô tả

FR-9.1

Ghi nhận sự kiện tương tác với kết quả

Mỗi khi người dùng xem chi tiết, bấm chỉ đường, hoặc lưu một nhà hàng trong danh sách/bản đồ kết quả, hệ thống ghi lại một bản ghi InteractionEvent gồm: nhà hàng, loại hành động, vị trí (position) của nhà hàng đó trong danh sách hiển thị, và thời điểm.

FR-9.2

Liên kết sự kiện với lượt tìm kiếm gốc

Mỗi InteractionEvent tham chiếu tới SearchQuery đã sinh ra danh sách kết quả tương ứng, để tái tạo đầy đủ bộ ba (ngữ cảnh tìm kiếm, danh sách hiển thị, lựa chọn thực tế) phục vụ huấn luyện mô hình xếp hạng ở giai đoạn nâng cấp.

FR-9.3

Định nghĩa tín hiệu dương (implicit positive label)

Quy định rõ những loại hành động nào (ví dụ: bấm chỉ đường, xem chi tiết quá một ngưỡng thời gian) được coi là tín hiệu quan tâm thực sự, phân biệt với việc chỉ lướt qua kết quả.

4. Yêu cầu phi chức năng

Mã

Nhóm yêu cầu

Mô tả chi tiết

NFR-1

Hiệu năng

Thời gian phản hồi cho một lượt tìm kiếm (từ khi gửi truy vấn đến khi hiển thị danh sách xếp hạng) không vượt quá khoảng 3 giây trong điều kiện vận hành bình thường, không tính thời gian tải bản đồ nền.

NFR-2

Khả dụng

Hệ thống hoạt động ổn định trong giờ cao điểm sử dụng; có cơ chế dự phòng (fallback) khi API bên thứ ba (thời tiết/giao thông) tạm thời không phản hồi, để không làm gián đoạn toàn bộ luồng tìm kiếm.

NFR-3

Bảo mật & quyền riêng tư

Vị trí người dùng chỉ được sử dụng trong phiên tìm kiếm hiện tại, không lưu trữ lâu dài nếu không có sự đồng ý rõ ràng; kết nối giữa client và server sử dụng HTTPS. Dữ liệu InteractionEvent (mục 3.9) được gắn với session ẩn danh, không gắn với thông tin định danh cá nhân của người dùng.

NFR-4

Khả năng mở rộng

Kiến trúc cho phép mở rộng độc lập từng thành phần (đổi mô hình xếp hạng, đổi nhà cung cấp bản đồ/thời tiết, mở rộng sang khu vực/thành phố mới) mà không ảnh hưởng các phần còn lại.

NFR-5

Khả năng bảo trì

Tách bạch rõ ràng giữa pha xử lý offline (crawl, embedding, tóm tắt review) và pha phục vụ online (tìm kiếm, xếp hạng), giúp cập nhật một phần mà không cần triển khai lại toàn hệ thống.

NFR-6

Khả năng sử dụng (UX)

Giao diện responsive, sử dụng tốt trên cả máy tính và thiết bị di động; luồng thao tác từ nhập nhu cầu đến xem kết quả không quá 3 bước.

NFR-7

Tương thích

Hỗ trợ các trình duyệt phổ biến hiện hành (Chrome, Safari, Edge, Firefox phiên bản gần nhất).

NFR-8

Tuân thủ dữ liệu

Việc thu thập dữ liệu từ nguồn bên ngoài phải tuân thủ điều khoản dịch vụ của từng nền tảng nguồn; dữ liệu review hiển thị công khai không chứa thông tin định danh cá nhân của người viết review ngoài phạm vi đã công khai.

NFR-9

Khả năng theo dõi/đánh giá

Mỗi thành phần mô hình (phân cụm, tìm kiếm ngữ nghĩa, xếp hạng, tóm tắt review, đề xuất món ăn) phải có chỉ số đánh giá riêng, ghi log phục vụ phân tích sau này (xem mục 6).

5. Yêu cầu giao diện

5.1. Giao diện người dùng

Trang chủ: ô tìm kiếm ngôn ngữ tự nhiên + bản đồ tương tác làm nền chính.

Trang kết quả: danh sách nhà hàng xếp hạng (dạng thẻ) đồng bộ với marker trên bản đồ; mỗi thẻ hiển thị nhận xét tổng hợp và món ăn gợi ý.

Trang chi tiết nhà hàng: thông tin đầy đủ, tuyến đường, danh sách món gợi ý, nhận xét tổng hợp chi tiết.

Trang phân tích dữ liệu (nội bộ/công khai tuỳ quyết định triển khai): số liệu thống kê tổng quan hệ thống.

Trang quản trị dữ liệu (nội bộ): theo dõi chất lượng dữ liệu thu thập.

5.2. Giao diện phần cứng

Cảm biến định vị (GPS) của thiết bị người dùng, truy cập qua API định vị trình duyệt.

5.3. Giao diện phần mềm (API bên thứ ba)

Loại API

Mục đích sử dụng

API Bản đồ (ví dụ Google Maps Platform)

Hiển thị bản đồ, tính khoảng cách/tuyến đường, dữ liệu cơ sở nhà hàng (Places).

API Thời tiết

Lấy tình trạng thời tiết và nhiệt độ theo vị trí tìm kiếm tại thời điểm truy vấn.

API Giao thông

Lấy thời gian di chuyển thực tế theo tình trạng giao thông hiện tại.

Nguồn review bên ngoài

Thu thập nội dung review phục vụ tìm kiếm ngữ nghĩa và tổng hợp đánh giá, trong phạm vi được phép theo điều khoản dịch vụ.

5.4. Giao diện truyền thông

Giao tiếp giữa frontend và backend qua REST API dạng JSON.

Toàn bộ kết nối client–server và server–API bên thứ ba sử dụng giao thức HTTPS.

6. Yêu cầu dữ liệu

6.1. Các thực thể dữ liệu chính

Thực thể

Mô tả

Thuộc tính chính (tiêu biểu)

Restaurant (Nhà hàng)

Dữ liệu tĩnh về một nhà hàng, thu thập theo đợt.

id, tên, toạ độ, giờ mở cửa, mức giá, rating, cụm trải nghiệm, embedding mô tả.

Dish (Món ăn)

Món ăn thuộc một nhà hàng, dùng cho mô-đun đề xuất món.

id, restaurant_id, tên món, nhóm món, mức độ cay, nóng/lạnh, từ khoá cảm xúc.

Review

Đánh giá/nhận xét thu thập từ các nguồn bên ngoài.

id, restaurant_id, nguồn, nội dung, thời điểm thu thập.

ReviewSummary (Nhận xét tổng hợp)

Kết quả tóm tắt của Review theo từng nhà hàng, sinh sẵn offline.

restaurant_id, điểm mạnh, điểm yếu, nhóm phù hợp.

SearchQuery (Lượt tìm kiếm)

Ghi nhận một lượt tìm kiếm của người dùng, phục vụ đánh giá và huấn luyện mô hình sau này.

id, câu tìm kiếm, vị trí, thời điểm, các ràng buộc cứng, danh sách kết quả trả về (có thứ tự).

ContextSignal (Tín hiệu ngữ cảnh)

Tín hiệu động tại thời điểm tìm kiếm, không lưu trữ lâu dài.

thời tiết, nhiệt độ, tình trạng giao thông, thời điểm trong ngày/tuần.

RestaurantExperienceFeature (Đặc trưng trải nghiệm)

Vector đặc trưng có cấu trúc, suy ra từ review/transcript qua FR-7.7, dùng làm đầu vào cho phân cụm (FR-4.1). Tính lại mỗi đợt cập nhật dữ liệu, không phải dữ liệu do người dùng nhập.

restaurant_id, điểm không gian, điểm độ ồn, số review dùng để tính mỗi khía cạnh, cờ độ tin cậy (thấp/đủ tin cậy).

InteractionEvent (Sự kiện tương tác)

Ghi nhận hành vi thực tế của người dùng trên danh sách kết quả của một lượt tìm kiếm; là nguồn dữ liệu nhãn cho mô hình xếp hạng có giám sát ở giai đoạn nâng cấp.

id, search_query_id, restaurant_id, vị trí trong danh sách hiển thị, loại hành động, thời điểm, session_id (ẩn danh).

6.2. Nguyên tắc tổ chức dữ liệu

Dữ liệu tĩnh (Restaurant, Dish, Review, ReviewSummary, embedding) được lưu trữ lâu dài trong cơ sở dữ liệu chính, cập nhật theo đợt.

Tín hiệu động (ContextSignal) chỉ được truy vấn tại thời điểm tìm kiếm và không lưu trữ lâu dài, nhằm đảm bảo dữ liệu luôn phản ánh đúng thời điểm hiện tại.

SearchQuery được lưu lại (ở mức tối thiểu cần thiết, tuân thủ NFR-3) để làm dữ liệu huấn luyện cho mô hình xếp hạng ở giai đoạn nâng cấp sau MVP.

RestaurantExperienceFeature là dữ liệu suy diễn (derived), không nhập trực tiếp và không chỉnh sửa thủ công ngoài trang quản trị (FR-7.5); được tính lại toàn bộ mỗi khi pipeline offline (FR-7.6–7.8) chạy lại.

InteractionEvent được ghi liên tục ngay từ MVP dù mô hình học có giám sát chưa được xây dựng, nhằm rút ngắn thời gian tích luỹ dữ liệu nhãn cho giai đoạn nâng cấp; mỗi bản ghi tham chiếu tới đúng một SearchQuery để tái tạo được bối cảnh tại thời điểm hiển thị kết quả.

7. Tiêu chí đánh giá và nghiệm thu

Vì hệ thống có nhiều thành phần học máy/xử lý dữ liệu riêng biệt, tiêu chí nghiệm thu được xây dựng theo từng thành phần, tương ứng với các FR ở mục 3:

Thành phần

Tiêu chí nghiệm thu

Trích xuất đặc trưng trải nghiệm (FR-7.7)

Điểm số tự động (không gian, độ ồn) khớp với gán nhãn thủ công trên tập kiểm thử, đo bằng tỷ lệ đồng thuận hoặc hệ số Cohen's Kappa; báo cáo riêng tỷ lệ nhà hàng rơi vào nhóm “độ tin cậy thấp” (FR-7.8) trên tổng số nhà hàng.

Phân cụm trải nghiệm (FR-4.1)

Các cụm tách biệt có ý nghĩa thống kê, đo bằng Silhouette Score, Davies–Bouldin Index, Calinski–Harabasz Index.

Tìm kiếm ngữ nghĩa (FR-4.2)

Kết quả trả về khớp về mặt ý nghĩa với câu tìm kiếm mẫu, đánh giá thủ công trên tập câu kiểm thử (đo độ liên quan – relevance).

Xếp hạng nhà hàng (FR-4.4)

Ở giai đoạn có dữ liệu tương tác: đánh giá bằng NDCG hoặc Precision@K trên tập dữ liệu tương tác thực tế.

Tổng hợp đánh giá (FR-5.1)

Nhận xét tổng hợp phản ánh đúng nội dung review gốc, kiểm tra thủ công trên mẫu ngẫu nhiên các nhà hàng.

Đề xuất món ăn (FR-6.2, FR-6.3)

Cặp (ngữ cảnh, món được đề xuất) hợp lý khi kiểm tra thủ công; theo dõi tỷ lệ người dùng xem/lưu món gợi ý sau triển khai.

Ghi nhận hành vi người dùng (FR-9.1–9.3)

Tỷ lệ lượt tìm kiếm có ít nhất một InteractionEvent được ghi đầy đủ trường bắt buộc (search_query_id, restaurant_id, vị trí, loại hành động); không thất lạc sự kiện khi so với log phía client.

Trải nghiệm tổng thể

Tỷ lệ người dùng chọn một trong các gợi ý đầu (top-K); thời gian trung bình ra quyết định so với duyệt thủ công.

8. Ưu tiên triển khai (MoSCoW)

Do phạm vi kiến trúc tương đối lớn so với một chu kỳ phát triển đồ án/dự án ban đầu, các yêu cầu chức năng được phân loại mức ưu tiên để xác định phạm vi MVP, tách khỏi các phần mở rộng.

Mức ưu tiên

Nhóm chức năng

Bắt buộc (Must have) – MVP

FR-1.1, FR-1.3, FR-2.1, FR-2.3, FR-3.1, FR-3.2, FR-4.2, FR-4.3, FR-4.4 (bản heuristic), FR-4.5, FR-7.1, FR-7.2, FR-7.3, FR-9.1, FR-9.2, FR-9.3.

Nên có (Should have)

FR-1.2, FR-1.4, FR-1.5, FR-2.2, FR-3.3, FR-4.1, FR-5.1, FR-5.2, FR-7.4, FR-7.5, FR-7.7, FR-7.8.

Có thể có (Could have)

FR-6.1, FR-6.2, FR-6.3, FR-6.4 (đề xuất món ăn), FR-7.6 (transcript video qua ASR), FR-8.1, FR-8.2.

Chưa triển khai ở bản này (Won't have – for now)

Mô hình xếp hạng học có giám sát đầy đủ (nâng cấp từ FR-4.4 heuristic khi có đủ dữ liệu InteractionEvent); phân tích tín hiệu hình ảnh/âm thanh thô của video (thị giác máy tính, đo độ ồn thực tế); tài khoản người dùng và cá nhân hoá dài hạn; đặt chỗ/đặt món trực tiếp với nhà hàng.

Việc phân loại này cho phép nhóm phát triển chứng minh được một sản phẩm chạy được (working demo) trong phạm vi MVP, đồng thời vẫn thể hiện đầy đủ tầm nhìn kiến trúc của đề án ý tưởng thông qua các mục Nên có/Có thể có.

Lưu ý về thứ tự triển khai: FR-9.1–9.3 (ghi nhận hành vi) được xếp vào Must have dù mô hình học có giám sát mà nó phục vụ lại thuộc Won't have — vì đây là hành động ghi log có chi phí kỹ thuật thấp nhưng cần bắt đầu sớm để rút ngắn thời gian chờ tích luỹ dữ liệu ở giai đoạn sau. Tương tự, FR-7.7/FR-7.8 được xếp Should have vì FR-4.1 (Should have) không thể chạy có ý nghĩa nếu thiếu bước trích xuất đặc trưng này.

9. Phụ lục — Danh sách use case chính

Mã UC

Tên use case

Tác nhân chính

FR liên quan

UC-01

Tìm kiếm nhà hàng bằng ngôn ngữ tự nhiên

Người dùng cuối

FR-2.1, FR-3.1–3.3, FR-4.2–4.5

UC-02

Đổi khu vực tìm kiếm trên bản đồ

Người dùng cuối

FR-1.4

UC-03

Xem nhận xét tổng hợp của nhà hàng

Người dùng cuối

FR-5.2

UC-04

Xem món ăn gợi ý theo tâm trạng

Người dùng cuối

FR-6.2–6.4

UC-05

Cập nhật dữ liệu nhà hàng định kỳ

Quản trị viên dữ liệu

FR-7.1–7.4

UC-06

Theo dõi chất lượng dữ liệu

Quản trị viên dữ liệu

FR-7.5

UC-07

Trích xuất transcript và đặc trưng trải nghiệm từ review/video

Nhóm phát triển/vận hành mô hình

FR-7.6–7.8

UC-08

Ghi nhận tương tác của người dùng với kết quả gợi ý

Hệ thống (nền, tự động theo hành vi người dùng cuối)

FR-9.1–9.3


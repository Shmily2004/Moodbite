# MoodBite
### Nền tảng Web Gợi ý Nhà hàng theo Ngữ cảnh Thời gian thực
*(Real-time Context-Aware Restaurant Recommendation Platform)*

---

## 1. Bối cảnh và vấn đề

Khi cần chọn một quán ăn, người dùng thường rơi vào tình trạng có quá nhiều lựa chọn nhưng lại thiếu thông tin để quyết định nhanh. Vấn đề không nằm ở việc thiếu dữ liệu — các nền tảng bản đồ và đánh giá đã có sẵn hàng nghìn quán — mà nằm ở việc dữ liệu đó không được sắp xếp theo đúng nhu cầu thực tế của người dùng tại đúng thời điểm và đúng vị trí họ đang đứng.

Cụ thể, người dùng thường gặp phải:

- Không biết quán nào phù hợp với tâm trạng và hoàn cảnh hiện tại (đi với ai, muốn không khí gì, còn bao nhiêu thời gian).
- Không diễn đạt được nhu cầu của mình bằng các bộ lọc cứng (dropdown, checkbox), mà thường nghĩ bằng ngôn ngữ tự nhiên — ví dụ "muốn tìm quán yên tĩnh, có chỗ đậu xe, gần đây, hợp để nói chuyện".
- Không tính đến các yếu tố thời điểm: trời đang mưa, đang nắng nóng, hay giờ này đường có tắc không — những yếu tố ảnh hưởng trực tiếp đến việc quán nào là lựa chọn hợp lý *ngay lúc này*.
- Mất nhiều thời gian đọc hàng trăm review nhưng vẫn khó rút ra kết luận tổng quan quán đó có hợp với mình hay không.

Vì vậy, bài toán của MoodBite không phải là một bài toán phân loại đơn giản, mà là một **bài toán dự đoán và xếp hạng theo ngữ cảnh động** (context-aware ranking/prediction): tại một thời điểm cụ thể, tại một vị trí cụ thể, với một nhu cầu diễn đạt tự do của một người dùng cụ thể — quán nào nên được xếp lên đầu.

---

## 2. Ý tưởng cốt lõi

MoodBite được xây dựng dựa trên năm thay đổi tư duy so với các công cụ tìm kiếm nhà hàng hiện có:

**Thứ nhất**, thay vì chỉ dùng một thuật toán phân cụm đơn lẻ, hệ thống dùng một **kiến trúc mô hình lai**: phân cụm để nhóm nhà hàng theo "chất trải nghiệm", tìm kiếm ngữ nghĩa để hiểu nhu cầu diễn đạt tự do bằng ngôn ngữ tự nhiên, và một mô hình xếp hạng học được từ dữ liệu để tổng hợp tất cả tín hiệu thành một điểm số cuối cùng — vì bài toán này về bản chất là dự đoán "quán nào phù hợp nhất", không phải chỉ là phân nhóm.

**Thứ hai**, người dùng không chỉ khảo sát bằng các lựa chọn cố định (đi với ai, ngân sách bao nhiêu), mà có thể **gõ trực tiếp nhu cầu bằng câu tự nhiên**, hệ thống hiểu ý nghĩa câu đó và tự đối chiếu với mô tả, review của từng nhà hàng — thay vì ép người dùng phải tự quy đổi cảm nhận của mình thành các lựa chọn có sẵn.

**Thứ ba**, hệ thống không xem nhà hàng là một thực thể tĩnh (giá, rating, loại món cố định), mà kết hợp thêm các **tín hiệu thời gian thực** tại thời điểm tìm kiếm — thời tiết, nhiệt độ, tình trạng giao thông — vì cùng một quán có thể phù hợp vào lúc trời nắng nhưng không phù hợp vào lúc trời mưa, hoặc cùng một khoảng cách nhưng thời gian di chuyển thực tế lại rất khác nhau tuỳ giờ cao điểm.

**Thứ tư**, vị trí không phải là một lựa chọn trong khảo sát ("dưới 1km", "dưới 3km") mà được lấy trực tiếp từ vị trí hiện tại của người dùng thông qua bản đồ, và toàn bộ trải nghiệm tìm kiếm — từ nhập nhu cầu đến xem kết quả — diễn ra trên nền một bản đồ tương tác, không phải một danh sách rời rạc.

**Thứ năm**, hệ thống không dừng lại ở việc trả lời "nên đến quán nào", mà còn trả lời câu hỏi cụ thể hơn là "nên ăn món gì" — vì trong thực tế người dùng thường có tâm trạng hoặc nhu cầu rõ ràng về món ăn (ví dụ "trời lạnh muốn ăn gì đó nóng", "hôm nay mệt muốn ăn nhẹ") trước khi nghĩ đến việc chọn quán. Vì vậy, đề xuất món ăn (dish-level recommendation) được thiết kế như một lớp riêng, hoạt động song song và bổ trợ cho lớp đề xuất quán (mục 3.5).

---

## 3. Kiến trúc mô hình lai (xử lý dự đoán và xếp hạng)

Vì đây là bài toán dự đoán/xếp hạng chứ không đơn thuần là phân cụm, hệ thống xử lý theo bốn lớp mô hình phối hợp với nhau:

**Lớp 1 — Phân cụm trải nghiệm (KMeans):** vẫn giữ vai trò nhóm các nhà hàng có đặc trưng trải nghiệm tương tự nhau (không gian, mức độ ồn, mức giá) thành các cụm, dùng làm một tín hiệu đầu vào cho bước xếp hạng, không phải là bước ra quyết định cuối cùng.

**Lớp 2 — Tìm kiếm ngữ nghĩa (Semantic Search):** câu tìm kiếm tự do của người dùng và mô tả/review của từng nhà hàng được chuyển thành vector embedding bằng một mô hình biểu diễn văn bản (text embedding model). Độ tương đồng ngữ nghĩa giữa hai vector (cosine similarity) cho biết mức độ phù hợp về mặt ý nghĩa, chứ không chỉ khớp từ khoá — nhờ vậy câu "chỗ yên tĩnh để làm việc" vẫn khớp được với một quán được review là "không gian tĩnh lặng, phù hợp ngồi lâu" dù không chung từ nào.

**Lớp 3 — Mô hình xếp hạng theo ngữ cảnh (Contextual Ranking Model):** đây là lớp tổng hợp, đóng vai trò dự đoán mức độ phù hợp cuối cùng của từng nhà hàng. Thay vì một công thức cộng có trọng số cố định, lớp này là một **mô hình học có giám sát nhẹ** (ví dụ Gradient Boosting hoặc Logistic Regression) được huấn luyện trên dữ liệu tương tác (nhà hàng nào được người dùng chọn khi có tập tín hiệu đầu vào tương ứng), học cách phối hợp các tín hiệu: cụm trải nghiệm, độ tương đồng ngữ nghĩa, khoảng cách/thời gian di chuyển thực tế, mức giá, rating, và các tín hiệu thời điểm (mục 4). Việc dùng một mô hình học được thay vì trọng số cố định giúp hệ thống tự điều chỉnh khi có thêm dữ liệu phản hồi, đúng bản chất một bài toán dự đoán.

**Lớp 4 — Tổng hợp đánh giá (Review Synthesis Model):** với mỗi nhà hàng có hàng chục đến hàng trăm review, hệ thống cần một mô hình tóm tắt văn bản (tóm tắt trích rút hoặc tóm tắt sinh, tuỳ năng lực triển khai) để tổng hợp thành một nhận xét ngắn gọn: điểm mạnh, điểm yếu, và phù hợp với nhóm người dùng nào — thay vì bắt người dùng tự đọc toàn bộ review. Đây là một bài toán xử lý ngôn ngữ tự nhiên độc lập với phần xếp hạng, chạy tách rời và định kỳ cập nhật.

**Lớp 5 — Đề xuất món ăn theo tâm trạng và ngữ cảnh (Mood-to-Dish Recommendation):** đây là lớp bổ sung, xử lý song song với Lớp 3, nhằm trả lời câu hỏi cụ thể hơn "nên ăn món gì" thay vì chỉ "nên đến quán nào". Phương thức đề xuất được thiết kế theo hướng lai (hybrid), gồm ba bước:

1. **Trích xuất đặc trưng món ăn (offline, thực hiện một lần khi thu thập dữ liệu ở mục 7):** mỗi món ăn trong thực đơn/menu được gán các thuộc tính (tag) như nhóm món (canh/nước, khô, tráng miệng...), mức độ cay, nóng/lạnh, độ "nặng bụng" (nhẹ/no), và các từ khoá cảm xúc thường xuất hiện trong review nhắc đến món đó (ví dụ "ấm bụng", "giải nhiệt", "an ủi tinh thần"). Việc gán nhãn này có thể thực hiện bán tự động: dùng mô hình ngôn ngữ để gợi ý nhãn từ mô tả/review, sau đó kiểm duyệt thủ công một phần để đảm bảo chất lượng.
2. **Ánh xạ tâm trạng/ngữ cảnh sang đặc trưng món ăn (rule + semantic matching):** xây dựng một bảng ánh xạ nền (ví dụ trời mưa/lạnh → ưu tiên món nóng, nước; tâm trạng mệt/buồn → ưu tiên món "an ủi" quen thuộc; tâm trạng muốn ăn nhẹ → ưu tiên món ít dầu mỡ, khẩu phần nhỏ) kết hợp với việc so khớp ngữ nghĩa giữa câu mô tả tâm trạng của người dùng và các từ khoá cảm xúc đã gán ở bước 1, dùng cùng cơ chế embedding như Lớp 2 để không phải xây riêng một mô hình NLP khác.
3. **Xếp hạng món ăn trong phạm vi các quán đã được Lớp 3 đề xuất:** món ăn chỉ được xếp hạng trong tập nhà hàng đã qua lọc theo vị trí/ngân sách, tránh đề xuất món ở quán quá xa. Điểm phù hợp của món = trọng số giữa (a) độ khớp ngữ cảnh/tâm trạng từ bước 2 và (b) mức độ phổ biến của món trong review (tần suất được nhắc đến tích cực). Ở giai đoạn đầu có thể dùng công thức trọng số đơn giản; khi có đủ dữ liệu tương tác (người dùng bấm chọn món nào), có thể nâng cấp thành một mô hình học nhẹ tương tự Lớp 3.

Kết quả của Lớp 5 được hiển thị như một gợi ý bổ sung đi kèm mỗi quán trong danh sách kết quả (ví dụ: "Quán A — gợi ý: lẩu gà lá giang, phù hợp cho hôm nay trời mưa se lạnh"), chứ không thay thế việc đề xuất quán của Lớp 3.

Các lớp trên phối hợp theo trình tự: câu tìm kiếm/khảo sát của người dùng → tính độ tương đồng ngữ nghĩa và xác định cụm gần nhất (Lớp 1, 2) → lọc theo các ràng buộc cứng (ngân sách, dị ứng, giờ mở cửa) → đưa toàn bộ tín hiệu vào mô hình xếp hạng để tính điểm dự đoán mức độ phù hợp cho từng quán (Lớp 3) → trong phạm vi các quán được chọn, chạy đề xuất món ăn theo tâm trạng (Lớp 5) → hiển thị kết quả (quán + món gợi ý) kèm theo nhận xét tổng hợp từ Lớp 4.

---

## 4. Tín hiệu ngữ cảnh thời gian thực

Điểm khác biệt cốt lõi của MoodBite so với các công cụ tìm kiếm nhà hàng tĩnh là việc đưa các yếu tố thời điểm vào mô hình dự đoán, thay vì chỉ dựa vào đặc trưng cố định của nhà hàng:

- **Thời tiết:** lấy từ một API thời tiết theo vị trí hiện tại của người dùng. Trời mưa sẽ tăng trọng số ưu tiên cho các quán có không gian trong nhà/mái che kín; trời nắng nóng sẽ ưu tiên các quán có điều hoà.
- **Nhiệt độ:** ảnh hưởng đến việc ưu tiên không gian trong nhà có điều hoà hay không gian ngoài trời thoáng mát.
- **Giao thông thực tế:** thay vì dùng khoảng cách đường chim bay như một con số tĩnh, hệ thống lấy thời gian di chuyển thực tế theo tình trạng giao thông hiện tại (qua API bản đồ/giao thông) để tính lại trọng số "gần/xa" — một quán 2km vào giờ cao điểm có thể "xa hơn" một quán 3km vào giờ vắng.
- **Thời điểm trong ngày/ngày trong tuần:** giờ ăn sáng, trưa, tối, hay cuối tuần ảnh hưởng đến loại hình phù hợp và khả năng còn chỗ trống, được đưa vào làm một đặc trưng thời gian cho mô hình xếp hạng.

Các tín hiệu này không được thu thập một lần rồi lưu tĩnh, mà được gọi tại thời điểm người dùng tìm kiếm, vì bản chất của chúng thay đổi liên tục — khác với dữ liệu tĩnh của nhà hàng (tên, loại món, mức giá) chỉ cần thu thập theo lô như mô tả ở mục 6.

---

## 5. Định vị và bản đồ

Toàn bộ trải nghiệm tìm kiếm được thiết kế dựa trên bản đồ thay vì một biểu mẫu khảo sát tách rời:

- Vị trí hiện tại của người dùng được lấy trực tiếp qua định vị của trình duyệt/thiết bị, dùng làm tâm điểm mặc định cho việc tìm kiếm xung quanh — người dùng không cần tự chọn "bán kính 1km/3km" như một câu hỏi khảo sát trừu tượng.
- Kết quả gợi ý được hiển thị trực tiếp trên bản đồ tương tác, kèm theo tuyến đường và thời gian di chuyển ước tính đến từng quán, thay vì chỉ hiển thị dưới dạng danh sách.
- Người dùng có thể kéo/thu phóng bản đồ để chủ động đổi khu vực tìm kiếm (ví dụ tìm quanh nơi mình sắp đến thay vì vị trí hiện tại), hệ thống sẽ tính lại toàn bộ tín hiệu ngữ cảnh (khoảng cách, giao thông, mật độ cụm trải nghiệm) theo tâm bản đồ mới.

---

## 6. Nền tảng triển khai: ứng dụng web

Hệ thống được xây dựng dưới dạng một ứng dụng web hoàn chỉnh thay vì một công cụ dạng notebook hay giao diện khảo sát đơn giản, để đáp ứng được yêu cầu về bản đồ tương tác, tìm kiếm ngữ nghĩa theo thời gian thực, và tín hiệu ngữ cảnh động:

- **Phía giao diện (frontend):** hiển thị bản đồ tương tác, ô tìm kiếm bằng ngôn ngữ tự nhiên, kết quả gợi ý kèm nhận xét tổng hợp, và trang phân tích dữ liệu.
- **Phía xử lý (backend):** tiếp nhận câu tìm kiếm và vị trí người dùng, gọi các API thời tiết/giao thông, chạy pipeline bốn lớp mô hình ở mục 3, trả về danh sách đã xếp hạng.
- **Cơ sở dữ liệu:** lưu dữ liệu tĩnh của nhà hàng (thông tin, đặc trưng đã xử lý, vector embedding phục vụ tìm kiếm ngữ nghĩa) và tách riêng với các tín hiệu động (thời tiết, giao thông) chỉ được gọi tại thời điểm tìm kiếm chứ không lưu trữ lâu dài.

Kiến trúc này cho phép mở rộng độc lập từng phần: đổi mô hình xếp hạng, đổi nguồn dữ liệu, hay đổi nhà cung cấp bản đồ/thời tiết mà không ảnh hưởng đến các phần còn lại.

---

## 7. Thu thập và xử lý dữ liệu

Dữ liệu nhà hàng được thu thập theo hình thức **crawl một lần, lưu trữ lâu dài**, không phải cào lại mỗi khi có người dùng tìm kiếm:

- **Nguồn dữ liệu:** kết hợp Google Maps/Places (thông tin cơ bản, toạ độ, giờ mở cửa, rating) và các kênh review trên TikTok cùng các nền tảng đánh giá khác (nội dung review dạng văn bản, dùng cho tìm kiếm ngữ nghĩa và tổng hợp nhận xét ở Lớp 4). Đối với các quán có thực đơn công khai (trên Google Maps, fanpage, hoặc website), thu thập thêm danh sách món ăn kèm giá, dùng làm dữ liệu đầu vào cho Lớp 5; với các quán không có thực đơn cấu trúc sẵn, món ăn được trích xuất từ nội dung review (tên món được nhắc đến) như một phương án dự phòng, chấp nhận độ phủ thấp hơn.
- **Tần suất:** việc crawl chỉ diễn ra theo đợt (một lần khi khởi tạo, sau đó định kỳ làm mới ở tần suất thấp, ví dụ hàng tháng) và lưu toàn bộ vào cơ sở dữ liệu. Mọi lượt tìm kiếm của người dùng chỉ truy vấn dữ liệu đã lưu sẵn, không kích hoạt việc cào dữ liệu mới — tách bạch rõ giữa pha thu thập dữ liệu (offline, theo đợt) và pha phục vụ tìm kiếm (online, thời gian thực).
- **Xử lý sau khi thu thập:** làm sạch dữ liệu, tính các đặc trưng phân cụm (Lớp 1), sinh vector embedding cho mô tả/review của từng nhà hàng để phục vụ tìm kiếm ngữ nghĩa (Lớp 2), và chạy trước mô hình tổng hợp nhận xét (Lớp 4) để lưu sẵn kết quả — tránh phải xử lý ngôn ngữ tự nhiên nặng tại thời điểm người dùng tìm kiếm.
- **Kiểm soát chất lượng:** kiểm tra dữ liệu thiếu, trùng lặp giữa các nguồn (cùng một nhà hàng xuất hiện trên cả Google Maps và TikTok), và mất cân bằng giữa các khu vực/loại hình trước khi đưa vào huấn luyện mô hình.

---

## 8. Đánh giá hiệu quả

Vì hệ thống hiện có ba thành phần học máy riêng biệt, việc đánh giá cần thực hiện theo từng lớp:

- **Lớp phân cụm:** dùng Silhouette Score, Davies–Bouldin Index và Calinski–Harabasz Index để xác nhận các cụm tách biệt có ý nghĩa thống kê.
- **Lớp tìm kiếm ngữ nghĩa:** đánh giá bằng cách kiểm tra thủ công trên một tập câu tìm kiếm mẫu, xem các nhà hàng được trả về có thực sự khớp về mặt ý nghĩa hay không (đánh giá độ liên quan — relevance).
- **Lớp xếp hạng:** vì đây là mô hình dự đoán có giám sát, cần đánh giá bằng các chỉ số xếp hạng tiêu chuẩn như NDCG hoặc Precision@K trên tập dữ liệu tương tác (nhà hàng nào thực sự được người dùng chọn trong số các gợi ý).
- **Lớp đề xuất món ăn:** đánh giá bằng kiểm tra thủ công trên các cặp (ngữ cảnh, món được đề xuất) xem có hợp lý hay không (đánh giá độ liên quan tương tự Lớp 2), kết hợp theo dõi tỷ lệ người dùng bấm xem/lưu món được gợi ý sau khi triển khai thực tế.
- **Trải nghiệm tổng thể:** đo lường qua tỷ lệ người dùng chọn một trong các gợi ý đầu tiên, và thời gian trung bình để ra quyết định so với việc duyệt thủ công.

---

## 9. Kết quả kỳ vọng

MoodBite không còn là một công cụ phân cụm đơn thuần, mà là một nền tảng dự đoán mức độ phù hợp giữa người dùng và nhà hàng (và xa hơn là món ăn cụ thể) tại một thời điểm cụ thể, kết hợp bốn năng lực: hiểu ngữ nghĩa nhu cầu diễn đạt tự do, cập nhật theo tín hiệu thời điểm thực (thời tiết, giao thông), định vị theo bản đồ thay vì khảo sát trừu tượng, và gợi ý món ăn theo tâm trạng chứ không chỉ dừng ở cấp độ quán. Cách tiếp cận này mang lại giá trị ở ba khía cạnh:

- **Về sản phẩm:** người dùng tìm kiếm tự nhiên như đang hỏi một người bạn địa phương, thay vì điền một biểu mẫu, và nhận được gợi ý đủ cụ thể để hành động ngay ("đến quán A, gọi món B") thay vì chỉ một danh sách quán để tự chọn tiếp.
- **Về khoa học dữ liệu:** bài toán được nhìn nhận đúng bản chất là dự đoán/xếp hạng theo ngữ cảnh động, sử dụng kết hợp học không giám sát, tìm kiếm ngữ nghĩa và học có giám sát — không gói gọn trong một thuật toán phân cụm duy nhất.
- **Về kỹ thuật:** tách bạch rõ giữa dữ liệu tĩnh (thu thập một lần, xử lý theo đợt) và tín hiệu động (gọi thời gian thực), giúp hệ thống vừa nhanh khi phục vụ người dùng, vừa không tốn kém khi vận hành lâu dài.

# MoodBite_So_Do_Kien_Truc

SƠ ĐỒ KIẾN TRÚC

(Bổ sung trực quan cho Tài liệu Kiến trúc Kỹ thuật v1.1)

MoodBite

Phiên bản 1.0

Ngày ban hành: 24/07/2026

Tài liệu nguồn: MoodBite – Kiến trúc Kỹ thuật v1.1, SRS v1.2, WBS v1.6, Data Dictionary & ERD v1.3

Lịch sử thay đổi tài liệu

Phiên bản

Ngày

Mô tả thay đổi

1.0

24/07/2026

Khởi tạo — 4 sơ đồ trực quan (4 lớp, trình tự, triển khai, lộ trình Phase) bổ sung cho Kiến trúc Kỹ thuật v1.1; phát hiện module Ghi nhận hành vi người dùng bị thiếu trong bảng Phân rã Module gốc.

Mục lục

1. Giới thiệu

Tài liệu “Kiến trúc Kỹ thuật v1.1” đã mô tả đầy đủ nguyên tắc Clean Architecture, Phân rã Module và chi tiết theo từng Phase — nhưng toàn bộ dưới dạng bảng và văn bản, không có một hình vẽ nào. Tài liệu này bổ sung phần còn thiếu đó: năm sơ đồ trực quan bám sát đúng nội dung đã chốt (không phát minh kiến trúc mới), giúp một người đọc nắm được bức tranh tổng thể trong vài giây thay vì phải đọc hết bảng chữ.

Trong lúc đối chiếu để vẽ sơ đồ, tài liệu này phát hiện một khoảng trống: mục 5 “Phân rã Module” của Kiến trúc Kỹ thuật liệt kê 8 module nhưng không có module nào cho việc ghi nhận hành vi người dùng (InteractionEvent) — dù đây là yêu cầu Bắt buộc trong SRS (FR-9.1–9.3) và đã có đầy đủ trong Data Dictionary (search_result_items, interaction_events). Sơ đồ ở tài liệu này bổ sung module thứ 9 tương ứng, đánh dấu “⚠ mới”, và khuyến nghị đồng bộ ngược lại vào Kiến trúc Kỹ thuật ở mục 6.

2. Sơ đồ Kiến trúc 4 lớp (Clean Architecture)

Bốn lớp đồng tâm theo đúng Quy tắc phụ thuộc (Dependency Rule) đã mô tả ở Kiến trúc Kỹ thuật mục 2.1: Presentation gọi vào Application, Application phụ thuộc Domain, Infrastructure cài đặt các Port do Application định nghĩa (Dependency Inversion — mũi tên đi ngược so với luồng gọi thông thường). config/di_container là nơi duy nhất quyết định Adapter nào được dùng cho mỗi Port tại mỗi thời điểm.

Hình 1 — Kiến trúc 4 lớp: Presentation, Application, Domain, Infrastructure. Nhãn ⚠ mới đánh dấu thành phần bổ sung để khớp module Ghi nhận hành vi (mục 6).

Domain là lớp duy nhất không import bất kỳ thứ gì từ ba lớp còn lại — có thể copy nguyên lớp này sang một dự án hoàn toàn khác mà vẫn biên dịch được, vì không phụ thuộc framework hay công nghệ cụ thể nào (Kiến trúc Kỹ thuật mục 4.1).

3. Ma trận Module × Lớp

Bám theo đúng bảng Phân rã Module ở Kiến trúc Kỹ thuật mục 5, trình bày lại dưới dạng ma trận trực quan (dễ quét mắt hơn bảng liệt kê thuần văn bản), bổ sung module thứ 9 phát hiện ở mục 1.

Module

Domain

Application

Infrastructure

Presentation

Xuất hiện từ

1. Restaurant & Dish Catalog

●

●

Giai đoạn 0 → 1 → 3

2. User Context

●

Giai đoạn 0

3. Search & Ranking

●

●

Giai đoạn 0 → 1 → 2 → 3

4. External Context Signals

●

●

Giai đoạn 1 (bản đồ) → 3

5. Review Synthesis

●

●

Giai đoạn 2

6. Dish Recommendation

●

Giai đoạn 3

7. Data Ingestion

●

Giai đoạn 1 trở đi

8. Presentation/Web

●

Giai đoạn 0, mở rộng dần

9. Interaction Logging ⚠ mới

●

●

Giai đoạn 1 (MVP) — xem mục 6

Đọc bảng: một chấm (●) nghĩa là module có thành phần thuộc lớp đó. Không có module nào chạm cả 4 lớp — đúng theo tinh thần Clean Architecture, mỗi module nên mỏng và chỉ hiện diện ở đúng những lớp cần thiết.

4. Sơ đồ trình tự — luồng Tìm kiếm & Xếp hạng

Minh hoạ luồng gọi thực tế của use case chính (Search & Ranking), qua đúng các Port/Adapter đã định nghĩa ở Kiến trúc Kỹ thuật mục 4, 6.1–6.4. Bước 7 (ghi nhận hành vi) là bổ sung mới, chạy song song, không chặn phản hồi cho người dùng — đúng tinh thần “InteractionEvent ghi liên tục từ MVP dù mô hình học có giám sát chưa xây” đã thống nhất ở SRS/WBS.

Hình 2 — Luồng gọi từ Presentation → Application → Infrastructure cho một lượt tìm kiếm, kèm bước ghi log kết quả hiển thị (search_result_items).

Điểm đáng chú ý ở bước 5: khi experience_cluster_id là NULL (nhà hàng mới, Cold Start), RankingAdapter không được để NULL lan truyền hay mặc định về 0 — quy tắc này đã thống nhất ở Data Dictionary mục 7.12 và khớp với thiết kế “tín hiệu cụm là tham số tuỳ chọn” của Kiến trúc Kỹ thuật mục 6.3.

5. Sơ đồ triển khai

Thể hiện đúng nguyên tắc đã chốt ở Kiến trúc Kỹ thuật mục 6.3: huấn luyện/crawl là job offline độc lập, “chạy tách biệt hoàn toàn khỏi luồng phục vụ người dùng” — không phải một Port mà RankingUseCase gọi lúc truy vấn. Cả runtime phục vụ người dùng và các job offline đều đọc/ghi chung một CSDL PostgreSQL, không có tầng trung gian nào khác.

Hình 3 — Web/API Server phục vụ người dùng (trên) tách biệt hoàn toàn khỏi các job batch/offline (dưới), gặp nhau duy nhất tại CSDL.

Adapter tầng Infrastructure (SemanticSearchAdapter, GoogleMapsAdapter...) là nơi duy nhất được phép gọi ra external API — đúng vai trò anti-corruption layer đã mô tả ở Kiến trúc Kỹ thuật mục 2.3: Application không biết và không cần biết các API này tồn tại.

6. Lộ trình 5 giai đoạn (trực quan hoá mục 3 và mục 6 của Kiến trúc Kỹ thuật)

Visual hoá lại đúng nội dung bảng “Phase Tổng quan” — không đổi phạm vi, chỉ đổi cách trình bày để dễ đối chiếu “Port nào xuất hiện ở Phase nào” trong một cái nhìn. Mũi tên nối các giai đoạn thể hiện nguyên tắc xuyên suốt: giai đoạn sau chỉ được thêm Port/Adapter mới, không sửa lại chữ ký Port hay Adapter của giai đoạn trước.

Hình 4 — 5 giai đoạn triển khai; IInteractionRepository (⚠ mới) được thêm vào Giai đoạn 2 trong sơ đồ gốc của Kiến trúc Kỹ thuật, nhưng khuyến nghị dời lên Giai đoạn 1 — xem lý do ở mục 6 bên dưới.

7. Phát hiện: Module Ghi nhận hành vi người dùng chưa có trong Kiến trúc Kỹ thuật

Kiến trúc Kỹ thuật mục 5 (Phân rã Module) liệt kê 8 module, không có module nào cho InteractionEvent/ghi nhận hành vi — dù:

SRS mục 3.9 (FR-9.1–9.3) xếp việc ghi nhận này ở mức Bắt buộc, khuyến nghị triển khai ngay từ MVP để rút ngắn thời gian tích luỹ dữ liệu cho mô hình xếp hạng học có giám sát sau này (Giai đoạn 3).

WBS v1.6 đã có work package cho việc này (nhóm 4 — API ghi nhận sự kiện tương tác).

Data Dictionary v1.3 đã thiết kế đầy đủ hai bảng search_result_items và interaction_events, kể cả FK, index, quy tắc phân loại tín hiệu dương.

Vì use case RecommendDish và tín hiệu cụm (IClusterAssignmentPort) đều xuất hiện từ Giai đoạn 2/3 mà InteractionEvent lại cần ghi càng sớm càng tốt (không phụ thuộc các module đó), tài liệu này khuyến nghị đưa module 9 vào Giai đoạn 1 (MVP), không phải Giai đoạn 2 như suy luận ban đầu khi vẽ Hình 4 — cụ thể:

Thành phần

Vị trí trong kiến trúc 4 lớp

Xuất hiện từ

LogInteractionUseCase

Application (use case mới)

Giai đoạn 1 (MVP)

IInteractionRepository

Application (port mới)

Giai đoạn 1 (MVP)

PostgresInteractionRepository

Infrastructure (adapter mới, cài đặt IInteractionRepository)

Giai đoạn 1 (MVP)

Khuyến nghị cập nhật vào Kiến trúc Kỹ thuật: thêm một dòng module thứ 9 vào bảng mục 5, và thêm ba thành phần trên vào mục 6.2 (Giai đoạn 1 — MVP) thay vì để trống hoàn toàn như bản v1.1 hiện tại. Đây là bổ sung thuần tuý theo nguyên tắc Ports & Adapters đã có — không phá vỡ cam kết “phase sau không sửa phase trước”, vì Giai đoạn 0 chưa từng khai báo bất kỳ Port nào liên quan đến logging để phải giữ tương thích ngược.


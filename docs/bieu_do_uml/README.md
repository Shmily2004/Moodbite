# Biểu đồ UML — MoodBite

**Cách xem:** mở `index.html` bằng trình duyệt. Trang có biểu đồ use case và 24 cặp (hoạt động, trình tự), mỗi use case một cặp.

| Thư mục / file | Nội dung |
|---|---|
| `index.html` | Trang xem tất cả biểu đồ |
| `svg/00_use_case_tong_quat.svg` | Biểu đồ use case tổng quát: tác nhân → các use case lớn |
| `svg/UC_nhom*.svg` | Biểu đồ use case chi tiết cho 5 nhóm lớn, có `<<include>>` và `<<extend>>` |
| `svg/hoat_dong/UCxx_*.svg` | 24 biểu đồ hoạt động, làn bơi Khách hàng / Hệ thống / Quản trị viên |
| `svg/trinh_tu/UCxx_*.svg` | 24 biểu đồ trình tự, **sinh tự động từ biểu đồ hoạt động** (cùng bước, cùng rẽ nhánh/fork) |
| `sinh_bieu_do.py` | Đặc tả 24 use case (biến `DAC_TA`): API và các bước biểu đồ hoạt động |
| `ve_bieu_do.py` | Bộ vẽ đọc đặc tả và sinh SVG + `index.html` |
| `puml_du_phong/hoat_dong/` | Bản PlantUML của biểu đồ hoạt động, dự phòng khi có PlantUML để render |
| `_cu/` | Bản cũ (một luồng chọn món, Mermaid), không dùng nữa |

## Ký hiệu

- **Trình tự** (theo hình 2.16a của giáo trình): actor là hình người; boundary là vòng tròn có vạch đứng bên trái; control là vòng tròn có mũi tên; entity là vòng tròn có gạch ngang phía dưới. Lời gọi là mũi tên đặc, trả về là nét đứt mũi hở. Thanh kích hoạt là hình chữ nhật hẹp trên đường đời. Khung `alt` có nhãn điều kiện và ngăn `[không]`; khung `par` cho hai nhánh song song.
- **Hoạt động** (theo hình 2.15): làn bơi có tiêu đề; chấm đen là bắt đầu; vòng tròn có chấm là kết thúc; hành động là hình chữ nhật bo góc; rẽ nhánh là hình thoi có nhãn "có" / "không"; fork/join là thanh đen.
- **Use case**: actor là hình người; use case là elip; `<<include>>` nét đứt mũi tên về use case con; `<<extend>>` nét đứt mũi tên từ use case mở rộng về use case gốc.

## Cách sửa và sinh lại

1. Sửa **nội dung** (bước, nhãn, thứ tự): sửa đặc tả trong `sinh_bieu_do.py`, rồi chạy:
   ```
   python docs/bieu_do_uml/ve_bieu_do.py
   ```
   Lệnh này ghi đè `svg/` và `index.html`.
2. Sửa **vị trí** use case: bảng `VI_TRI` trong `ve_bieu_do.py`.
3. Lệnh trên chạy được nguyên dạng trên PowerShell 5.1 (không dùng `&&`).

## Trạng thái kiểm chứng

- Đã vẽ đủ 49 file SVG (24 hoạt động, 24 trình tự, 1 use case). Đã chụp màn hình bằng Microsoft Edge và kiểm bằng mắt các mẫu: UC01 (alt), UC02 (rẽ nhánh), UC03 (fork/join), UC06 và UC19 (trình tự có kích hoạt).
- **Chưa kiểm** tất cả 49 file từng cái một, và chưa đối chiếu từng ký hiệu với hình mẫu theo kiểu so pixel. Nếu thấy chỗ nào lệch chuẩn, gửi tên file để sửa.
- **Đối chiếu lại với code ngày 2026-11-11: UC02, UC08, UC09, UC10, UC11** (cụm gợi ý món và tài khoản/thư). Đã sửa: UC10 từng vẽ "gửi mã / nhập mã" trong khi code gửi ĐƯỜNG DẪN trong thư; UC08/UC09 từng ghi đăng ký bằng email và đăng nhập phải "đã xác minh" (thật ra dùng tên đăng nhập, và không chặn đăng nhập khi chưa xác minh); UC02 thêm bộ lọc cách chế biến và cảnh báo món bị ẩn. **19 use case còn lại CHƯA đối chiếu từng bước** (2026-11-12 đã đối chiếu các điều kiện rẽ nhánh và chạy thử trên trình duyệt; xem mục Trạng thái trong `PROJECT_CHECKLIST.md`). Đã làm theo biểu đồ (2026-11-12): UC06/UC21 (báo đóng cửa vào hàng chờ, không tự ẩn; quản trị ẩn hoặc gỡ) và UC01 (không có quán khớp thì thông báo gợi ý nới bộ lọc). UC15 đã sửa biểu đồ cho khớp code (2026-11-12): sau đăng xuất vào trang đăng nhập, vì trang chủ bắt đăng nhập. UC12 khớp (biểu đồ chỉ lưu địa chỉ lên máy chủ, sở thích lưu trên máy); đã đo bằng số liệu rằng không khung hành động nào bị tràn chữ (24/24 biểu đồ hoạt động).
- Nội dung đối chiếu với `frontend/openapi.json` và các route trong `src/presentation/api/routers/`. Một số bước (cơ chế phiên đăng nhập, gửi email xác minh) được ghi ở mức tổng quát, chưa kiểm chứng chi tiết.
- Bản PlantUML trong `puml_du_phong/` chưa được render. Nếu sau này có PlantUML, có thể dùng để so sánh.

## Quy tắc sinh trình tự từ hoạt động

- Bước của **Khách** có hành động nhập liệu (Chọn, Nhập, Bấm, Mở…) → thông điệp Khách → Giao diện. Bước chỉ xem thì không có thông điệp.
- Bước của **Hệ thống** → Giao diện → Xử lý. Nếu bước đọc/ghi dữ liệu thì Xử lý gọi tới Dữ liệu (Ent_CoSoDuLieu, hoặc Ent_TaiKhoan / Ent_NhatKy tuỳ nội dung).
- Bước chỉ **hiển thị** (Hiển thị, Thông báo, Báo…) → Giao diện trả về Khách.
- Rẽ nhánh (hình thoi) → khung **alt**; hai nhánh song song (fork) → khung **par**.

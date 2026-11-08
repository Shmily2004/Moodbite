"""Sinh file PlantUML cho TỪNG use case: biểu đồ hoạt động + biểu đồ trình tự.

    python docs/bieu_do_uml/sinh_bieu_do.py

Đặc tả nằm ngay trong file này (biến DAC_TA). Chạy lại sẽ GHI ĐÈ các file .puml sinh ra.
Muốn sửa một biểu đồ: sửa đặc tả ở đây rồi chạy lại, HOẶC sửa thẳng file .puml sinh ra
(khi đó đừng chạy lại script, nếu không sửa tay sẽ mất).

Ký hiệu theo UML chuẩn (PlantUML):
  Trình tự : actor = tác nhân, boundary = giao diện, control = xử lý, entity = dữ liệu.
             Mũi tên đặc = lời gọi đồng bộ; mũi tên đứt = trả về.
             alt / opt / loop = khung rẽ nhánh / tùy chọn / lặp.
  Hoạt động: swimlane |Tác nhân|, start/stop, hình thoi (if), thanh fork/join.

Mỗi đặc tả là một danh sách bước. Các ký hiệu bước:
  ("msg", từ, đến, nhãn)          lời gọi đồng bộ
  ("ret", từ, đến, nhãn)          trả về (nét đứt)
  ("alt", điều_kiện, [nhánh_có], [nhánh_không])     khung alt, có else
  ("opt", điều_kiện, [các bước])                    khung opt
  ("note", chữ)                                     ghi chú trên lifeline Ctrl
  Hoạt động:
  ("lane", tên)                   chuyển cột
  ("act", chữ)                    hành động
  ("if", điều_kiện, [có], [không])  rẽ nhánh
  ("fork", [[nhánh1], [nhánh2]])  hai nhánh song song
  ("stop",)                       kết thúc
"""
from __future__ import annotations

from pathlib import Path

GOC = Path(__file__).resolve().parent
THU_MUC_HD = GOC / "puml_du_phong" / "hoat_dong"
THU_MUC_TT = GOC / "puml_du_phong" / "trinh_tu"

KH_TEN = "Khách"
QT_TEN = "Quản trị viên"

# Tên thành phần: đặt theo vai trò, không theo tên file code.
UI_KH = "UI_GiaoDienWeb"
UI_QT = "UI_TrangQuanTri"
CTRL_KH = "Ctrl_HeThongXuLy"
CTRL_QT = "Ctrl_QuanTriHeThong"
DB = "Ent_CoSoDuLieu"
TK = "TK"   # alias trong PlantUML; tên hiển thị là Ent_TaiKhoan
NK = "NK"   # alias trong PlantUML; tên hiển thị là Ent_NhatKy


def _ten_an_toan(s: str) -> str:
    bo = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
    thay = "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"
    s = s.lower()
    out = []
    for ch in s:
        if ch in bo:
            out.append(thay[bo.index(ch)])
        elif ch.isalnum():
            out.append(ch)
        else:
            out.append("_")
    return "".join(out).strip("_")


# ---------------------------------------------------------------------------
# ĐẶC TẢ 24 USE CASE — đối chiếu với endpoint trong frontend/openapi.json
# ---------------------------------------------------------------------------
DAC_TA = [
    # ---------------- PHÍA NGƯỜI DÙNG ----------------
    {
        "ma": "UC01", "ten": "Tìm quán bằng câu tự do", "nhom": "Khách",
        "api": "POST /api/v1/search",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Nhập câu tìm kiếm"),
            ("msg", "UI", "CTRL", "2. POST /search {truy vấn, vị trí, bán kính}"),
            ("msg", "CTRL", "DB", "3. Lấy quán đang bật"),
            ("ret", "DB", "CTRL", "4. Danh sách quán"),
            ("note", "5. Bỏ dấu, khớp từ nguyên vẹn, xếp hạng"),
            ("alt", "có quán khớp",
                [("ret", "CTRL", "UI", "6a. Danh sách quán + gợi ý món"), ("ret", "UI", "KH", "7a. Hiển thị kết quả")],
                [("ret", "CTRL", "UI", "6b. Danh sách rỗng + warnings"), ("ret", "UI", "KH", "7b. Thông báo không có quán khớp")]),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Nhập câu tìm kiếm tự do"),
            ("lane", "Hệ thống"), ("act", "POST /search"),
            ("if", "Có quán khớp?", [("act", "Hiển thị danh sách quán, gợi ý món trong từng kết quả")],
             [("act", "Thông báo không có quán khớp, gợi ý nới bộ lọc")]),
            ("lane", KH_TEN), ("act", "Xem kết quả"), ("stop",),
        ],
    },
    {
        "ma": "UC02", "ten": "Gợi ý món theo bộ lọc", "nhom": "Khách",
        "api": "POST /api/v1/dishes/suggest",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Chọn tâm trạng, bữa ăn, bán kính"),
            ("msg", "UI", "CTRL", "2. POST /dishes/suggest"),
            ("msg", "CTRL", "DB", "3. Lấy danh mục món đang bật và chỉ mục món-quán"),
            ("ret", "DB", "CTRL", "4. Danh sách món + số quán"),
            ("note", "5. Suy ngữ cảnh (giờ, thời tiết) rồi xếp hạng món"),
            ("alt", "có món phù hợp",
                [("ret", "CTRL", "UI", "6a. Danh sách món + warnings"), ("ret", "UI", "KH", "7a. Hiển thị lưới món")],
                [("ret", "CTRL", "UI", "6b. Danh sách rỗng"), ("ret", "UI", "KH", "7b. Thông báo không khớp, gợi ý bỏ bớt bộ lọc")]),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Chọn bộ lọc: tâm trạng, bữa ăn, khoảng cách"),
            ("lane", "Hệ thống"), ("act", "POST /dishes/suggest"),
            ("if", "Có món phù hợp?", [("act", "Hiển thị lưới món kèm cảnh báo nếu có")],
             [("act", "Thông báo không khớp, gợi ý bỏ bớt bộ lọc")]),
            ("lane", KH_TEN), ("act", "Chọn một món hoặc bỏ bớt bộ lọc"), ("stop",),
        ],
    },
    {
        "ma": "UC03", "ten": "Xem chi tiết món", "nhom": "Khách",
        "api": "GET /api/v1/dishes/{id} (song song với xem quán bán món)",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Chọn một món"),
            ("msg", "UI", "CTRL", "2. GET /dishes/{id}"),
            ("msg", "CTRL", "DB", "3. Tra món theo id"),
            ("ret", "DB", "CTRL", "4. Thông tin món + độ tin cậy gợi ý"),
            ("ret", "CTRL", "UI", "5. Chi tiết món"),
            ("ret", "UI", "KH", "6. Hiển thị giới thiệu món"),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Chọn một món"),
            ("lane", "Hệ thống"),
            ("fork", [[("act", "GET /dishes/{id}: tải thông tin món")],
                      [("act", "GET /dishes/{id}/restaurants (xem quán bán món)")]]),
            ("act", "Hiển thị trang món"), ("stop",),
        ],
    },
    {
        "ma": "UC04", "ten": "Xem danh sách quán của món", "nhom": "Khách",
        "api": "GET /api/v1/dishes/{id}/restaurants",
        "trinh_tu": [
            ("msg", "UI", "CTRL", "1. GET /dishes/{id}/restaurants"),
            ("msg", "CTRL", "DB", "2. Quán khớp món theo chỉ mục"),
            ("ret", "DB", "CTRL", "3. Danh sách quán"),
            ("note", "4. Lọc bán kính; nới và cảnh báo nếu không có quán gần"),
            ("ret", "CTRL", "UI", "5. Quán + warnings"),
            ("ret", "UI", "KH", "6. Hiển thị danh sách quán và bản đồ"),
        ],
        "hoat_dong": [
            ("lane", "Hệ thống"), ("act", "Tra các quán khớp món theo chỉ mục"),
            ("if", "Có quán trong bán kính?", [("act", "Xếp quán theo mức phù hợp")],
             [("act", "Nới bán kính, lấy quán gần nhất, CẢNH BÁO khoảng cách")]),
            ("lane", KH_TEN), ("act", "Xem danh sách quán"), ("stop",),
        ],
    },
    {
        "ma": "UC05", "ten": "Xem chi tiết quán", "nhom": "Khách",
        "api": "GET /api/v1/restaurants/{id}, POST /api/v1/interactions (view)",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Chọn một quán"),
            ("msg", "UI", "CTRL", "2. GET /restaurants/{id}"),
            ("msg", "CTRL", "DB", "3. Đọc quán và chi tiết (nếu có)"),
            ("ret", "DB", "CTRL", "4. Dữ liệu quán"),
            ("ret", "CTRL", "UI", "5. Chi tiết quán, has_details"),
            ("ret", "UI", "KH", "6. Hiển thị địa chỉ, giờ, nguồn, mức tin cậy"),
            ("msg", "UI", "CTRL", "7. POST /interactions {view}"),
            ("msg", "CTRL", "DB", "8. Ghi lượt xem"),
            ("ret", "CTRL", "UI", "9. 201 Created"),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Chọn một quán"),
            ("lane", "Hệ thống"), ("act", "GET /restaurants/{id}"),
            ("act", "Hiển thị chi tiết quán và nguồn dữ liệu"),
            ("act", "POST /interactions (ghi lượt xem)"),
            ("lane", KH_TEN), ("act", "Xem thông tin quán"), ("stop",),
        ],
    },
    {
        "ma": "UC06", "ten": "Báo quán đã đóng cửa", "nhom": "Khách",
        "api": "POST /api/v1/interactions {action_type: report_closed}",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Bấm Báo đã đóng cửa"),
            ("msg", "UI", "CTRL", "2. POST /interactions {report_closed}"),
            ("note", "3. Server tính khoá người báo = IP đã băm HMAC (không lấy từ body)"),
            ("msg", "CTRL", "DB", "4. Ghi lượt báo"),
            ("ret", "DB", "CTRL", "5. Đã ghi"),
            ("ret", "CTRL", "UI", "6. 201 Created"),
            ("ret", "UI", "KH", "7. Cảm ơn, quán chờ quản trị xác nhận"),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Bấm Báo đã đóng cửa"),
            ("lane", "Hệ thống"), ("act", "POST /interactions (report_closed)"),
            ("act", "Ghi lượt báo, đưa quán vào hàng chờ quản trị"),
            ("lane", KH_TEN), ("act", "Nhận thông báo đã ghi nhận"), ("stop",),
        ],
    },
    {
        "ma": "UC07", "ten": "Lưu món / quán yêu thích", "nhom": "Khách",
        "api": "Khách: lưu trên máy. Đã đăng nhập: POST /api/v1/me/favorites",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Bấm biểu tượng yêu thích"),
            ("alt", "đã đăng nhập",
                [("msg", "UI", "CTRL", "2a. POST /me/favorites"), ("msg", "CTRL", "DB", "3a. Ghi bảng saved_items"),
                 ("ret", "CTRL", "UI", "4a. 201 Created")],
                [("msg", "UI", "UI", "2b. Ghi vào bộ nhớ trình duyệt (trên máy)")]),
            ("ret", "UI", "KH", "5. Đổi trạng thái nút"),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Bấm biểu tượng yêu thích"),
            ("lane", "Hệ thống"),
            ("if", "Đã đăng nhập?", [("act", "POST /me/favorites, lưu trên server")],
             [("act", "Lưu vào bộ nhớ trình duyệt của khách")]),
            ("lane", KH_TEN), ("act", "Thấy nút đổi trạng thái"), ("stop",),
        ],
    },
    {
        "ma": "UC08", "ten": "Đăng ký (xác minh email)", "nhom": "Tài khoản",
        "api": "POST /api/v1/auth/register; POST /auth/verify-email/request; POST /auth/verify-email/confirm",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Nhập email, mật khẩu"),
            ("msg", "UI", "CTRL", "2. POST /auth/register"),
            ("msg", "CTRL", "TK", "3. Kiểm tra email chưa tồn tại, lưu tài khoản chưa xác minh"),
            ("ret", "TK", "CTRL", "4. Đã lưu"),
            ("msg", "CTRL", "TK", "5. Tạo mã xác minh"),
            ("ret", "CTRL", "UI", "6. 201 Created, yêu cầu xác minh"),
            ("ret", "UI", "KH", "7. Yêu cầu nhập mã xác minh email"),
            ("msg", "KH", "UI", "8. Nhập mã từ email"),
            ("msg", "UI", "CTRL", "9. POST /auth/verify-email/confirm"),
            ("msg", "CTRL", "TK", "10. Đánh dấu email đã xác minh"),
            ("ret", "CTRL", "UI", "11. 200 OK"),
            ("ret", "UI", "KH", "12. Tài khoản đã kích hoạt"),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Nhập email và mật khẩu"),
            ("lane", "Hệ thống"), ("act", "POST /auth/register"),
            ("if", "Email đã tồn tại?", [("act", "Báo lỗi, yêu cầu email khác")],
             [("act", "Lưu tài khoản chưa xác minh, gửi mã xác minh")]),
            ("lane", KH_TEN), ("act", "Nhập mã xác minh từ email"),
            ("lane", "Hệ thống"), ("act", "POST /auth/verify-email/confirm"),
            ("if", "Mã đúng và còn hạn?", [("act", "Kích hoạt tài khoản")],
             [("act", "Báo mã sai hoặc hết hạn, cho gửi lại")]),
            ("stop",),
        ],
    },
    {
        "ma": "UC09", "ten": "Đăng nhập", "nhom": "Tài khoản",
        "api": "POST /api/v1/auth/login",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Nhập email, mật khẩu"),
            ("msg", "UI", "CTRL", "2. POST /auth/login"),
            ("msg", "CTRL", "TK", "3. Tìm tài khoản, kiểm tra mật khẩu"),
            ("ret", "TK", "CTRL", "4. Kết quả"),
            ("alt", "đúng mật khẩu và đã xác minh",
                [("ret", "CTRL", "UI", "5a. 200 OK + phiên đăng nhập"), ("ret", "UI", "KH", "6a. Vào trang cá nhân")],
                [("ret", "CTRL", "UI", "5b. 401 Sai thông tin"), ("ret", "UI", "KH", "6b. Báo lỗi")]),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Nhập email và mật khẩu"),
            ("lane", "Hệ thống"), ("act", "POST /auth/login"),
            ("if", "Đúng mật khẩu và đã xác minh?", [("act", "Tạo phiên đăng nhập")],
             [("act", "Báo lỗi đăng nhập")]),
            ("lane", KH_TEN), ("act", "Vào trang cá nhân hoặc sửa lại thông tin"), ("stop",),
        ],
    },
    {
        "ma": "UC10", "ten": "Quên / đặt lại mật khẩu", "nhom": "Tài khoản",
        "api": "POST /api/v1/auth/forgot-password; POST /auth/reset-password",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Nhập email quên mật khẩu"),
            ("msg", "UI", "CTRL", "2. POST /auth/forgot-password"),
            ("msg", "CTRL", "TK", "3. Tạo mã đặt lại"),
            ("ret", "CTRL", "UI", "4. 200 OK (không lộ email có tồn tại hay không)"),
            ("msg", "KH", "UI", "5. Nhập mã và mật khẩu mới"),
            ("msg", "UI", "CTRL", "6. POST /auth/reset-password"),
            ("msg", "CTRL", "TK", "7. Kiểm tra mã, cập nhật mật khẩu"),
            ("ret", "CTRL", "UI", "8. 200 OK"),
            ("ret", "UI", "KH", "9. Mời đăng nhập lại"),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Nhập email quên mật khẩu"),
            ("lane", "Hệ thống"), ("act", "POST /auth/forgot-password (gửi mã)"),
            ("lane", KH_TEN), ("act", "Nhập mã và mật khẩu mới"),
            ("lane", "Hệ thống"),
            ("if", "Mã đúng và còn hạn?", [("act", "POST /auth/reset-password, cập nhật mật khẩu")],
             [("act", "Báo mã sai hoặc hết hạn")]),
            ("stop",),
        ],
    },
    {
        "ma": "UC11", "ten": "Đổi mật khẩu", "nhom": "Tài khoản",
        "api": "POST /api/v1/auth/change-password",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Nhập mật khẩu cũ và mới"),
            ("msg", "UI", "CTRL", "2. POST /auth/change-password"),
            ("msg", "CTRL", "TK", "3. Kiểm tra phiên và mật khẩu cũ"),
            ("alt", "phiên hợp lệ và mật khẩu cũ đúng",
                [("msg", "CTRL", "TK", "4a. Cập nhật mật khẩu mới"), ("ret", "CTRL", "UI", "5a. 200 OK"),
                 ("ret", "UI", "KH", "6a. Đã đổi mật khẩu")],
                [("ret", "CTRL", "UI", "4b. 401 hoặc 400"), ("ret", "UI", "KH", "5b. Báo lỗi")]),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Nhập mật khẩu cũ và mật khẩu mới"),
            ("lane", "Hệ thống"), ("act", "POST /auth/change-password"),
            ("if", "Phiên hợp lệ và mật khẩu cũ đúng?", [("act", "Cập nhật mật khẩu mới")],
             [("act", "Báo lỗi")]),
            ("stop",),
        ],
    },
    {
        "ma": "UC12", "ten": "Quản lý hồ sơ, địa chỉ, sở thích", "nhom": "Tài khoản",
        "api": "GET /auth/me; /me/addresses (GET, POST, PATCH, DELETE); /me/stats",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Mở trang hồ sơ"),
            ("msg", "UI", "CTRL", "2. GET /auth/me, /me/addresses"),
            ("msg", "CTRL", "TK", "3. Đọc hồ sơ và địa chỉ"),
            ("ret", "TK", "CTRL", "4. Dữ liệu"),
            ("ret", "CTRL", "UI", "5. Hồ sơ + danh sách địa chỉ"),
            ("ret", "UI", "KH", "6. Hiển thị"),
            ("msg", "KH", "UI", "7. Thêm / sửa / xoá địa chỉ"),
            ("msg", "UI", "CTRL", "8. POST | PATCH | DELETE /me/addresses"),
            ("msg", "CTRL", "TK", "9. Ghi thay đổi"),
            ("ret", "CTRL", "UI", "10. Kết quả"),
            ("ret", "UI", "KH", "11. Cập nhật danh sách"),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Mở trang hồ sơ"),
            ("lane", "Hệ thống"), ("act", "GET /auth/me, GET /me/addresses"),
            ("lane", KH_TEN), ("act", "Thêm, sửa hoặc xoá địa chỉ, chỉnh sở thích"),
            ("lane", "Hệ thống"), ("act", "POST | PATCH | DELETE /me/addresses"),
            ("lane", KH_TEN), ("act", "Thấy hồ sơ đã cập nhật"), ("stop",),
        ],
    },
    {
        "ma": "UC13", "ten": "Quản lý bộ sưu tập", "nhom": "Tài khoản",
        "api": "/api/v1/me/collections (GET, POST, PATCH, DELETE) và /items",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Tạo hoặc đổi tên bộ sưu tập"),
            ("msg", "UI", "CTRL", "2. POST | PATCH /me/collections"),
            ("msg", "CTRL", "TK", "3. Ghi bộ sưu tập"),
            ("ret", "CTRL", "UI", "4. Kết quả"),
            ("ret", "UI", "KH", "5. Hiển thị bộ sưu tập mới"),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Tạo, đổi tên hoặc xoá bộ sưu tập"),
            ("lane", "Hệ thống"), ("act", "POST | PATCH | DELETE /me/collections"),
            ("lane", KH_TEN), ("act", "Thêm hoặc bỏ món, quán trong bộ sưu tập"), ("stop",),
        ],
    },
    {
        "ma": "UC14", "ten": "Xem tin tức", "nhom": "Khách",
        "api": "GET /api/v1/posts, GET /api/v1/posts/{slug}",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Mở trang tin tức"),
            ("msg", "UI", "CTRL", "2. GET /posts"),
            ("msg", "CTRL", "DB", "3. Bài đã công khai"),
            ("ret", "DB", "CTRL", "4. Danh sách bài"),
            ("ret", "CTRL", "UI", "5. Danh sách bài"),
            ("ret", "UI", "KH", "6. Hiển thị danh sách"),
            ("msg", "KH", "UI", "7. Mở một bài"),
            ("msg", "UI", "CTRL", "8. GET /posts/{slug}"),
            ("ret", "CTRL", "UI", "9. Nội dung bài"),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Mở trang tin tức"),
            ("lane", "Hệ thống"), ("act", "GET /posts (chỉ bài đã công khai)"),
            ("lane", KH_TEN), ("act", "Chọn một bài"),
            ("lane", "Hệ thống"), ("act", "GET /posts/{slug}"),
            ("lane", KH_TEN), ("act", "Đọc bài"), ("stop",),
        ],
    },
    {
        "ma": "UC15", "ten": "Đăng xuất", "nhom": "Tài khoản",
        "api": "POST /api/v1/auth/logout",
        "trinh_tu": [
            ("msg", "KH", "UI", "1. Bấm đăng xuất và xác nhận"),
            ("msg", "UI", "CTRL", "2. POST /auth/logout"),
            ("msg", "CTRL", "TK", "3. Thu hồi phiên"),
            ("ret", "CTRL", "UI", "4. 200 OK"),
            ("ret", "UI", "KH", "5. Về trang khách"),
        ],
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Bấm đăng xuất, xác nhận"),
            ("lane", "Hệ thống"), ("act", "POST /auth/logout, thu hồi phiên"),
            ("lane", KH_TEN), ("act", "Về trang khách"), ("stop",),
        ],
    },
    # ---------------- PHÍA QUẢN TRỊ ----------------
    {
        "ma": "UC16", "ten": "Đăng nhập quản trị", "nhom": "Quản trị",
        "api": "POST /api/v1/admin/login; POST /admin/logout",
        "trinh_tu": [
            ("msg", "QT", "UI", "1. Nhập tài khoản quản trị"),
            ("msg", "UI", "CTRL", "2. POST /admin/login"),
            ("msg", "CTRL", "TK", "3. Kiểm tra quyền quản trị"),
            ("ret", "TK", "CTRL", "4. Đúng quyền"),
            ("alt", "đúng quyền",
                [("ret", "CTRL", "UI", "5a. 200 OK + phiên quản trị"), ("ret", "UI", "QT", "6a. Vào trang quản trị")],
                [("ret", "CTRL", "UI", "5b. 401/403"), ("ret", "UI", "QT", "6b. Báo lỗi")]),
        ],
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Nhập tài khoản quản trị"),
            ("lane", "Hệ thống"), ("act", "POST /admin/login"),
            ("if", "Đúng quyền quản trị?", [("act", "Tạo phiên quản trị")],
             [("act", "Báo lỗi, từ chối truy cập")]),
            ("lane", QT_TEN), ("act", "Vào trang quản trị"), ("stop",),
        ],
    },
    {
        "ma": "UC17", "ten": "Xem tổng quan", "nhom": "Quản trị",
        "api": "GET /api/v1/admin/overview; /admin/interactions/stats; /admin/system",
        "trinh_tu": [
            ("msg", "QT", "UI", "1. Mở trang tổng quan"),
            ("msg", "UI", "CTRL", "2. GET /admin/overview"),
            ("msg", "CTRL", "DB", "3. Đọc số liệu quán, món, tương tác"),
            ("ret", "DB", "CTRL", "4. Số liệu"),
            ("ret", "CTRL", "UI", "5. Tổng quan"),
            ("ret", "UI", "QT", "6. Hiển thị số liệu"),
        ],
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở trang tổng quan"),
            ("lane", "Hệ thống"), ("act", "GET /admin/overview"),
            ("lane", QT_TEN), ("act", "Xem số liệu"), ("stop",),
        ],
    },
    {
        "ma": "UC18", "ten": "Xem và sửa mô tả món", "nhom": "Quản trị",
        "api": "GET /admin/dishes, GET/PATCH /admin/dishes/{id}",
        "trinh_tu": [
            ("msg", "QT", "UI", "1. Mở một món"),
            ("msg", "UI", "CTRL", "2. GET /admin/dishes/{id}"),
            ("msg", "CTRL", "DB", "3. Đọc món kèm bản sửa (nếu có)"),
            ("ret", "CTRL", "UI", "4. Chi tiết món"),
            ("msg", "QT", "UI", "5. Sửa mô tả, bấm Lưu"),
            ("msg", "UI", "CTRL", "6. PATCH /admin/dishes/{id} {description}"),
            ("alt", "mô tả hợp lệ (<= 1000 ký tự)",
                [("msg", "CTRL", NK, "7a. Ghi nhật ký update_dish"), ("msg", "CTRL", "DB", "8a. Lưu bản sửa (không đụng dữ liệu gốc)"),
                 ("ret", "CTRL", "UI", "9a. 200 OK")],
                [("ret", "CTRL", "UI", "7b. 400 INVALID_REQUEST"), ("ret", "UI", "QT", "8b. Báo lỗi tại ô sửa")]),
        ],
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở món, bấm Sửa mô tả"),
            ("act", "Nhập mô tả, bấm Lưu (hoặc Gỡ bản sửa)"),
            ("lane", "Hệ thống"), ("act", "PATCH /admin/dishes/{id}"),
            ("if", "Mô tả hợp lệ?", [("act", "Lưu bản sửa, ghi nhật ký")],
             [("act", "Trả lỗi 400, không ghi gì")]),
            ("lane", QT_TEN), ("act", "Xem mô tả mới"), ("stop",),
        ],
    },
    {
        "ma": "UC19", "ten": "Quản lý quán", "nhom": "Quản trị",
        "api": "/admin/restaurants (GET, POST, PATCH), /hide, /restore, /bulk-visibility",
        "trinh_tu": [
            ("msg", "QT", "UI", "1. Tìm quán, sửa hoặc ẩn"),
            ("msg", "UI", "CTRL", "2. GET /admin/restaurants?q=..."),
            ("msg", "CTRL", "DB", "3. Tìm không phân biệt dấu và hoa thường"),
            ("ret", "DB", "CTRL", "4. Kết quả"),
            ("ret", "CTRL", "UI", "5. Danh sách quán"),
            ("msg", "QT", "UI", "6. Bấm Ẩn / Khôi phục / Sửa"),
            ("msg", "UI", "CTRL", "7. POST /hide | /restore hoặc PATCH"),
            ("msg", "CTRL", "DB", "8. Ghi trạng thái"),
            ("msg", "CTRL", NK, "9. Ghi nhật ký"),
            ("ret", "CTRL", "UI", "10. 200 OK"),
            ("ret", "UI", "QT", "11. Cập nhật danh sách"),
        ],
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Tìm quán (không cần gõ dấu)"),
            ("lane", "Hệ thống"), ("act", "GET /admin/restaurants?q=..."),
            ("lane", QT_TEN), ("act", "Chọn quán: sửa, ẩn, khôi phục hoặc thêm"),
            ("lane", "Hệ thống"), ("act", "POST /hide | /restore, PATCH, POST"),
            ("act", "Ghi trạng thái và nhật ký"),
            ("lane", QT_TEN), ("act", "Xem danh sách đã cập nhật"), ("stop",),
        ],
    },
    {
        "ma": "UC20", "ten": "Xử lý vấn đề dữ liệu", "nhom": "Quản trị",
        "api": "GET /admin/issues; POST | DELETE /admin/issues/resolve",
        "trinh_tu": [
            ("msg", "QT", "UI", "1. Mở danh sách vấn đề"),
            ("msg", "UI", "CTRL", "2. GET /admin/issues"),
            ("msg", "CTRL", "DB", "3. Đọc vấn đề chưa xử lý"),
            ("ret", "CTRL", "UI", "4. Danh sách vấn đề"),
            ("msg", "QT", "UI", "5. Đánh dấu đã xử lý"),
            ("msg", "UI", "CTRL", "6. POST /admin/issues/resolve"),
            ("msg", "CTRL", NK, "7. Ghi nhật ký"),
            ("ret", "CTRL", "UI", "8. 200 OK"),
        ],
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở danh sách vấn đề"),
            ("lane", "Hệ thống"), ("act", "GET /admin/issues"),
            ("lane", QT_TEN), ("act", "Xem chi tiết, đánh dấu đã xử lý"),
            ("lane", "Hệ thống"), ("act", "POST /admin/issues/resolve"),
            ("lane", QT_TEN), ("act", "Xem danh sách đã cập nhật"), ("stop",),
        ],
    },
    {
        "ma": "UC21", "ten": "Xem xét báo đóng cửa", "nhom": "Quản trị",
        "api": "GET /admin/closure-reports; POST /admin/restaurants/{id}/closure-reports/clear",
        "trinh_tu": [
            ("msg", "QT", "UI", "1. Mở danh sách quán bị báo"),
            ("msg", "UI", "CTRL", "2. GET /admin/closure-reports"),
            ("msg", "CTRL", "DB", "3. Đọc lượt báo chưa xử lý"),
            ("ret", "CTRL", "UI", "4. Danh sách quán bị báo"),
            ("msg", "QT", "UI", "5. Xác nhận đã đóng cửa, hoặc gỡ các lượt báo"),
            ("msg", "UI", "CTRL", "6. POST .../closure-reports/clear"),
            ("msg", "CTRL", "DB", "7. Gỡ lượt báo của quán"),
            ("msg", "CTRL", NK, "8. Ghi nhật ký"),
            ("ret", "CTRL", "UI", "9. 200 OK"),
        ],
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở danh sách quán bị báo"),
            ("lane", "Hệ thống"), ("act", "GET /admin/closure-reports"),
            ("lane", QT_TEN), ("act", "Kiểm tra và quyết định"),
            ("if", "Quán thực sự đã đóng cửa?", [("act", "Ẩn quán (POST /hide), ghi nhật ký")],
             [("act", "POST .../closure-reports/clear, gỡ lượt báo")]),
            ("stop",),
        ],
    },
    {
        "ma": "UC22", "ten": "Xem chất lượng dữ liệu", "nhom": "Quản trị",
        "api": "GET /api/v1/admin/quality; /admin/restaurants/stats",
        "trinh_tu": [
            ("msg", "QT", "UI", "1. Mở trang chất lượng dữ liệu"),
            ("msg", "UI", "CTRL", "2. GET /admin/quality"),
            ("msg", "CTRL", "DB", "3. Đo tỷ lệ phủ: tọa độ, giá, đánh giá, ảnh"),
            ("ret", "DB", "CTRL", "4. Số đo"),
            ("ret", "CTRL", "UI", "5. Chỉ số chất lượng"),
            ("ret", "UI", "QT", "6. Hiển thị, kèm tỷ lệ phủ"),
        ],
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở trang chất lượng dữ liệu"),
            ("lane", "Hệ thống"), ("act", "GET /admin/quality"),
            ("lane", QT_TEN), ("act", "Xem chỉ số và tỷ lệ phủ"), ("stop",),
        ],
    },
    {
        "ma": "UC23", "ten": "Quản lý bài viết", "nhom": "Quản trị",
        "api": "/api/v1/admin/posts (GET, POST, PUT, DELETE)",
        "trinh_tu": [
            ("msg", "QT", "UI", "1. Soạn hoặc sửa bài"),
            ("msg", "UI", "CTRL", "2. POST | PUT /admin/posts"),
            ("msg", "CTRL", "DB", "3. Ghi bài (nháp hoặc công khai)"),
            ("ret", "CTRL", "UI", "4. 200 OK"),
            ("msg", "CTRL", NK, "5. Ghi nhật ký"),
            ("ret", "UI", "QT", "6. Hiển thị bài đã lưu"),
        ],
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Soạn, sửa hoặc xoá bài"),
            ("lane", "Hệ thống"), ("act", "POST | PUT | DELETE /admin/posts"),
            ("if", "Bài đang công khai?", [("act", "Hiển thị trên trang tin tức của khách")],
             [("act", "Giữ ở trạng thái nháp, chỉ quản trị thấy")]),
            ("stop",),
        ],
    },
    {
        "ma": "UC24", "ten": "Xem nhật ký hoạt động", "nhom": "Quản trị",
        "api": "GET /api/v1/admin/activity",
        "trinh_tu": [
            ("msg", "QT", "UI", "1. Mở nhật ký"),
            ("msg", "UI", "CTRL", "2. GET /admin/activity"),
            ("msg", "CTRL", NK, "3. Đọc nhật ký"),
            ("ret", NK, "CTRL", "4. Các dòng nhật ký"),
            ("ret", "CTRL", "UI", "5. Danh sách"),
            ("ret", "UI", "QT", "6. Hiển thị theo thời gian"),
        ],
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở nhật ký"),
            ("lane", "Hệ thống"), ("act", "GET /admin/activity"),
            ("lane", QT_TEN), ("act", "Lọc và xem các thao tác"), ("stop",),
        ],
    },
]


# ---------------------------------------------------------------------------
# SINH PLANTUML
# ---------------------------------------------------------------------------
def _quet_nguoi_tham_gia(buoc: list, dung: set[str]) -> None:
    for b in buoc:
        if b[0] in ("msg", "ret"):
            dung.add(b[1])
            dung.add(b[2])
        elif b[0] == "alt":
            _quet_nguoi_tham_gia(b[2], dung)
            _quet_nguoi_tham_gia(b[3], dung)
        elif b[0] == "opt":
            _quet_nguoi_tham_gia(b[2], dung)


def _dong_trinh_tu(buoc: list, ind: str = "") -> list[str]:
    out: list[str] = []
    for b in buoc:
        loai = b[0]
        if loai == "msg":
            out.append(f"{ind}{b[1]} -> {b[2]} : {b[3]}")
        elif loai == "ret":
            out.append(f"{ind}{b[1]} --> {b[2]} : {b[3]}")
        elif loai == "note":
            out.append(f"{ind}note over CTRL : {b[1]}")
        elif loai == "alt":
            out.append(f"{ind}alt {b[1]}")
            out += _dong_trinh_tu(b[2], ind + "  ")
            out.append(f"{ind}else khác")
            out += _dong_trinh_tu(b[3], ind + "  ")
            out.append(f"{ind}end")
        elif loai == "opt":
            out.append(f"{ind}opt {b[1]}")
            out += _dong_trinh_tu(b[2], ind + "  ")
            out.append(f"{ind}end")
    return out


def sinh_trinh_tu(uc: dict) -> str:
    la_qt = uc["nhom"] == "Quản trị"
    tac_nhan = QT_TEN if la_qt else KH_TEN
    ma_nguoi = "QT" if la_qt else "KH"
    ui = UI_QT if la_qt else UI_KH
    ctrl = CTRL_QT if la_qt else CTRL_KH

    dung: set[str] = set()
    _quet_nguoi_tham_gia(uc["trinh_tu"], dung)
    khai = [
        f'actor "{tac_nhan}" as {ma_nguoi}',
        f'boundary "{ui}" as UI',
        f'control "{ctrl}" as CTRL',
        f'entity "{DB}" as DB',
    ]
    if "TK" in dung:
        khai.append('entity "Ent_TaiKhoan" as TK')
    if "NK" in dung:
        khai.append('entity "Ent_NhatKy" as NK')

    dong = [
        f"@startuml {uc['ma']}_trinh_tu",
        f"' {uc['ma']} — {uc['ten']}",
        f"' API: {uc['api']}",
        "skinparam shadowing false",
        "skinparam sequenceMessageAlign center",
        "",
        *khai,
        "",
        *_dong_trinh_tu(uc["trinh_tu"]),
        "@enduml",
    ]
    # Tác nhân trong đặc tả là KH/QT; đổi thành mã đúng của use case.
    text = "\n".join(dong) + "\n"
    if la_qt:
        text = text.replace("KH ", "QT ").replace("KH->", "QT->").replace("->KH", "->QT")
    return text


def _dong_hoat_dong(buoc: list, ind: str = "") -> list[str]:
    out: list[str] = []
    for b in buoc:
        loai = b[0]
        if loai == "lane":
            out.append(f"{ind}|{b[1]}|")
        elif loai == "act":
            # `|` mở đầu dòng là dấu làn bơi trong PlantUML; `;` kết thúc hành động.
            # Thay `|` bằng `/` để nội dung hành động không bị hiểu nhầm.
            chu = b[1].replace("|", "/").replace(";", ",")
            out.append(f"{ind}:{chu};")
        elif loai == "stop":
            out.append(f"{ind}stop")
        elif loai == "if":
            out.append(f"{ind}if ({b[1]}) then (có)")
            out += _dong_hoat_dong(b[2], ind + "  ")
            out.append(f"{ind}else (không)")
            out += _dong_hoat_dong(b[3], ind + "  ")
            out.append(f"{ind}endif")
        elif loai == "fork":
            out.append(f"{ind}fork")
            for i, nhanh in enumerate(b[1]):
                if i:
                    out.append(f"{ind}fork again")
                out += _dong_hoat_dong(nhanh, ind + "  ")
            out.append(f"{ind}end fork")
    return out


def sinh_hoat_dong(uc: dict) -> str:
    dong = [
        f"@startuml {uc['ma']}_hoat_dong",
        f"' {uc['ma']} — {uc['ten']}",
        f"' API: {uc['api']}",
        "skinparam shadowing false",
        "start",
        *_dong_hoat_dong(uc["hoat_dong"]),
        "@enduml",
    ]
    return "\n".join(dong) + "\n"


def main() -> None:
    THU_MUC_HD.mkdir(parents=True, exist_ok=True)
    THU_MUC_TT.mkdir(parents=True, exist_ok=True)
    for uc in DAC_TA:
        ten = f"{uc['ma']}_{_ten_an_toan(uc['ten'])}"
        (THU_MUC_HD / f"{ten}.puml").write_text(sinh_hoat_dong(uc), encoding="utf-8")
        (THU_MUC_TT / f"{ten}.puml").write_text(sinh_trinh_tu(uc), encoding="utf-8")
    print(f"Đã sinh {len(DAC_TA)} use case x 2 biểu đồ vào {THU_MUC_HD} và {THU_MUC_TT}")


if __name__ == "__main__":
    main()

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

KH_TEN = "Khách hàng"
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
        "ma": "UC01", "ten": "Tìm quán bằng câu tự do", "nhom": "Khách hàng",
        "api": "POST /api/v1/search",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Nhập câu tìm kiếm tự do"),
            ("lane", "Hệ thống"), ("act", "Tìm quán khớp câu tìm kiếm"),
            ("if", "Có quán khớp?", [("act", "Hiển thị danh sách quán, gợi ý món trong từng kết quả")],
             [("act", "Thông báo không có quán khớp, gợi ý nới bộ lọc")]),
            ("lane", KH_TEN), ("act", "Xem kết quả"), ("stop",),
        ],
    },
    {
        "ma": "UC02", "ten": "Gợi ý món theo bộ lọc", "nhom": "Khách hàng",
        "api": "POST /api/v1/dishes/suggest",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Chọn bộ lọc: tâm trạng, bữa ăn, cách chế biến, khoảng cách"),
            ("lane", "Hệ thống"), ("act", "Tính gợi ý món theo bộ lọc"),
            ("if", "Có món phù hợp?",
             [("act", "Hiển thị lưới món kèm cảnh báo món bị ẩn")],
             [("act", "Thông báo không khớp, gợi ý bỏ bớt bộ lọc")]),
            ("lane", KH_TEN), ("act", "Chọn một món hoặc bỏ bớt bộ lọc"), ("stop",),
        ],
    },
    {
        "ma": "UC03", "ten": "Xem chi tiết món", "nhom": "Khách hàng",
        "api": "GET /api/v1/dishes/{id} (song song với xem quán bán món)",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Chọn một món"),
            ("lane", "Hệ thống"),
            ("fork", [[("act", "Tải thông tin món")],
                      [("act", "Tải danh sách quán bán món")]]),
            ("act", "Hiển thị trang món"), ("stop",),
        ],
    },
    {
        "ma": "UC04", "ten": "Xem danh sách quán của món", "nhom": "Khách hàng",
        "api": "GET /api/v1/dishes/{id}/restaurants",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Bấm xem quán bán món này"),
            ("lane", "Hệ thống"), ("act", "Tra các quán khớp món theo chỉ mục"),
            ("if", "Có quán trong bán kính?", [("act", "Xếp quán theo mức phù hợp")],
             [("act", "Nới bán kính, lấy quán gần nhất, CẢNH BÁO khoảng cách")]),
            ("lane", KH_TEN), ("act", "Xem danh sách quán"), ("stop",),
        ],
    },
    {
        "ma": "UC05", "ten": "Xem chi tiết quán", "nhom": "Khách hàng",
        "api": "GET /api/v1/restaurants/{id}, POST /api/v1/interactions (view)",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Chọn một quán"),
            ("lane", "Hệ thống"), ("act", "Tải chi tiết quán"),
            ("act", "Hiển thị chi tiết quán và nguồn dữ liệu"),
            ("act", "Ghi nhận lượt xem"),
            ("lane", KH_TEN), ("act", "Xem thông tin quán"), ("stop",),
        ],
    },
    {
        "ma": "UC06", "ten": "Báo quán đã đóng cửa", "nhom": "Khách hàng",
        "api": "POST /api/v1/interactions {action_type: report_closed}",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Bấm Báo đã đóng cửa"),
            ("lane", "Hệ thống"), ("act", "Ghi nhận lượt báo đóng cửa"),
            ("act", "Ghi lượt báo, đưa quán vào hàng chờ quản trị"),
            ("lane", KH_TEN), ("act", "Nhận thông báo đã ghi nhận"), ("stop",),
        ],
    },
    {
        "ma": "UC07", "ten": "Lưu món / quán yêu thích", "nhom": "Khách hàng",
        "api": "POST /api/v1/me/favorites (chỉ người đã đăng nhập; khách bị chuyển sang đăng nhập)",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Bấm biểu tượng yêu thích"),
            ("lane", "Hệ thống"), ("act", "Lưu yêu thích trên máy chủ"),
            ("lane", KH_TEN), ("act", "Thấy nút đổi trạng thái"), ("stop",),
        ],
    },
    {
        "ma": "UC08", "ten": "Đăng ký (xác minh email)", "nhom": "Tài khoản",
        "api": "POST /api/v1/auth/register; POST /auth/verify-email/request; POST /auth/verify-email/confirm",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Nhập tên đăng nhập, email và mật khẩu"),
            ("lane", "Hệ thống"), ("act", "Kiểm tra định dạng và tên đăng nhập"),
            ("if", "Tên đăng nhập đã có người dùng?", [("act", "Báo lỗi, yêu cầu chọn tên khác"), ("stop",)],
             [("act", "Lưu tài khoản, cấp phiên, gửi thư xác minh kèm đường dẫn")]),
            ("lane", KH_TEN), ("act", "Mở đường dẫn xác minh trong thư"),
            ("lane", "Hệ thống"), ("act", "Kiểm tra đường dẫn xác minh"),
            ("if", "Đường dẫn còn hạn và chưa dùng?", [("act", "Đánh dấu email đã xác minh")],
             [("act", "Báo đường dẫn không hợp lệ, cho gửi lại thư")]),
            ("stop",),
        ],
    },
    {
        "ma": "UC09", "ten": "Đăng nhập", "nhom": "Tài khoản",
        "api": "POST /api/v1/auth/login",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Nhập tên đăng nhập và mật khẩu"),
            ("lane", "Hệ thống"), ("act", "Kiểm tra tài khoản và mật khẩu"),
            ("if", "Đúng tên đăng nhập và mật khẩu?", [("act", "Tạo phiên đăng nhập")],
             [("act", "Báo lỗi chung, không nói sai tên hay sai mật khẩu")]),
            ("lane", KH_TEN), ("act", "Vào trang cá nhân hoặc sửa lại thông tin"), ("stop",),
        ],
    },
    {
        "ma": "UC10", "ten": "Quên / đặt lại mật khẩu", "nhom": "Tài khoản",
        "api": "POST /api/v1/auth/forgot-password; POST /auth/reset-password",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Nhập email hoặc tên đăng nhập"),
            ("lane", "Hệ thống"), ("act", "Kiểm tra cấu hình gửi thư và giới hạn số lần gọi"),
            ("if", "Gửi thư được và chưa vượt giới hạn?",
             [("act", "Gửi thư kèm đường dẫn nếu có email, luôn trả cùng một câu")],
             [("act", "Báo lỗi (chưa cấu hình thư hoặc gọi quá nhiều lần), không gửi thư"), ("stop",)]),
            ("lane", KH_TEN), ("act", "Mở đường dẫn trong thư và nhập mật khẩu mới"),
            ("lane", "Hệ thống"),
            ("if", "Đường dẫn còn hạn và chưa dùng?",
             [("act", "Cập nhật mật khẩu mới, thu hồi các phiên đăng nhập cũ")],
             [("act", "Báo đường dẫn không hợp lệ hoặc hết hạn")]),
            ("stop",),
        ],
    },
    {
        "ma": "UC11", "ten": "Đổi mật khẩu", "nhom": "Tài khoản",
        "api": "POST /api/v1/auth/change-password",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Nhập mật khẩu cũ và mật khẩu mới"),
            ("lane", "Hệ thống"), ("act", "Kiểm tra mật khẩu cũ và cập nhật mật khẩu mới"),
            ("if", "Phiên hợp lệ và mật khẩu cũ đúng?",
             [("act", "Cập nhật mật khẩu mới, thu hồi phiên ở các máy khác")],
             [("act", "Báo lỗi")]),
            ("stop",),
        ],
    },
    {
        "ma": "UC12", "ten": "Quản lý hồ sơ, địa chỉ, sở thích", "nhom": "Tài khoản",
        "api": "GET /auth/me; /me/addresses (GET, POST, PATCH, DELETE); /me/stats",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Mở trang hồ sơ"),
            ("lane", "Hệ thống"), ("act", "Tải hồ sơ và danh sách địa chỉ"),
            ("lane", KH_TEN), ("act", "Thêm, sửa hoặc xoá địa chỉ, chỉnh sở thích"),
            ("lane", "Hệ thống"), ("act", "Lưu thay đổi địa chỉ"),
            ("lane", KH_TEN), ("act", "Thấy hồ sơ đã cập nhật"), ("stop",),
        ],
    },
    {
        "ma": "UC13", "ten": "Quản lý bộ sưu tập", "nhom": "Tài khoản",
        "api": "/api/v1/me/collections (GET, POST, PATCH, DELETE) và /items",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Tạo, đổi tên hoặc xoá bộ sưu tập"),
            ("lane", "Hệ thống"), ("act", "Lưu thay đổi bộ sưu tập"),
            ("lane", KH_TEN), ("act", "Thêm hoặc bỏ món, quán trong bộ sưu tập"), ("stop",),
        ],
    },
    {
        "ma": "UC14", "ten": "Xem tin tức", "nhom": "Khách hàng",
        "api": "GET /api/v1/posts, GET /api/v1/posts/{slug}",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Mở trang tin tức"),
            ("lane", "Hệ thống"), ("act", "Tải bài đã công khai"),
            ("lane", KH_TEN), ("act", "Chọn một bài"),
            ("lane", "Hệ thống"), ("act", "Tải nội dung bài"),
            ("lane", KH_TEN), ("act", "Đọc bài"), ("stop",),
        ],
    },
    {
        "ma": "UC15", "ten": "Đăng xuất", "nhom": "Tài khoản",
        "api": "POST /api/v1/auth/logout",
        "hoat_dong": [
            ("lane", KH_TEN), ("act", "Bấm đăng xuất, xác nhận"),
            ("lane", "Hệ thống"), ("act", "Thu hồi phiên đăng nhập"),
            ("lane", KH_TEN), ("act", "Tự động chuyển về trang chủ"), ("stop",),
        ],
    },
    # ---------------- PHÍA QUẢN TRỊ ----------------
    {
        "ma": "UC16", "ten": "Đăng nhập quản trị", "nhom": "Quản trị",
        "api": "POST /api/v1/admin/login; POST /admin/logout",
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Nhập tài khoản quản trị"),
            ("lane", "Hệ thống"), ("act", "Kiểm tra quyền quản trị"),
            ("if", "Đúng quyền quản trị?", [("act", "Tạo phiên quản trị")],
             [("act", "Báo lỗi, từ chối truy cập")]),
            ("lane", QT_TEN), ("act", "Vào trang quản trị"), ("stop",),
        ],
    },
    {
        "ma": "UC17", "ten": "Xem tổng quan", "nhom": "Quản trị",
        "api": "GET /api/v1/admin/overview; /admin/interactions/stats; /admin/system",
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở trang tổng quan"),
            ("lane", "Hệ thống"), ("act", "Tổng hợp số liệu"),
            ("lane", QT_TEN), ("act", "Xem số liệu"), ("stop",),
        ],
    },
    {
        "ma": "UC18", "ten": "Xem và sửa mô tả món", "nhom": "Quản trị",
        "api": "GET /admin/dishes, GET/PATCH /admin/dishes/{id}",
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở món, bấm Sửa mô tả"),
            ("act", "Nhập mô tả, bấm Lưu (hoặc Gỡ bản sửa)"),
            ("lane", "Hệ thống"), ("act", "Lưu bản sửa mô tả, ghi nhật ký"),
            ("if", "Mô tả hợp lệ?", [("act", "Lưu bản sửa, ghi nhật ký")],
             [("act", "Trả lỗi 400, không ghi gì")]),
            ("lane", QT_TEN), ("act", "Xem mô tả mới"), ("stop",),
        ],
    },
    {
        "ma": "UC19", "ten": "Quản lý quán", "nhom": "Quản trị",
        "api": "/admin/restaurants (GET, POST, PATCH), /hide, /restore, /bulk-visibility",
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Tìm quán (không cần gõ dấu)"),
            ("lane", "Hệ thống"), ("act", "Tìm quán theo từ khoá"),
            ("lane", QT_TEN), ("act", "Chọn quán: sửa, ẩn, khôi phục hoặc thêm"),
            ("lane", "Hệ thống"), ("act", "Ẩn, khôi phục hoặc sửa quán"),
            ("act", "Ghi trạng thái và nhật ký"),
            ("lane", QT_TEN), ("act", "Xem danh sách đã cập nhật"), ("stop",),
        ],
    },
    {
        "ma": "UC20", "ten": "Xử lý vấn đề dữ liệu", "nhom": "Quản trị",
        "api": "GET /admin/issues; POST | DELETE /admin/issues/resolve",
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở danh sách vấn đề"),
            ("lane", "Hệ thống"), ("act", "Tải danh sách vấn đề"),
            ("lane", QT_TEN), ("act", "Xem chi tiết, đánh dấu đã xử lý"),
            ("lane", "Hệ thống"), ("act", "Đánh dấu đã xử lý"),
            ("lane", QT_TEN), ("act", "Xem danh sách đã cập nhật"), ("stop",),
        ],
    },
    {
        "ma": "UC21", "ten": "Xem xét báo đóng cửa", "nhom": "Quản trị",
        "api": "GET /admin/closure-reports; POST /admin/restaurants/{id}/closure-reports/clear",
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở danh sách quán bị báo"),
            ("lane", "Hệ thống"), ("act", "Tải danh sách quán bị báo"),
            ("lane", QT_TEN), ("act", "Kiểm tra và quyết định"),
            ("if", "Quán thực sự đã đóng cửa?", [("act", "Ẩn quán, ghi nhật ký")],
             [("act", "Gỡ các lượt báo của quán")]),
            ("stop",),
        ],
    },
    {
        "ma": "UC22", "ten": "Xem chất lượng dữ liệu", "nhom": "Quản trị",
        "api": "GET /api/v1/admin/quality; /admin/restaurants/stats",
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở trang chất lượng dữ liệu"),
            ("lane", "Hệ thống"), ("act", "Tổng hợp chỉ số chất lượng"),
            ("lane", QT_TEN), ("act", "Xem chỉ số và tỷ lệ phủ"), ("stop",),
        ],
    },
    {
        "ma": "UC23", "ten": "Quản lý bài viết", "nhom": "Quản trị",
        "api": "/api/v1/admin/posts (GET, POST, PUT, DELETE)",
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Soạn, sửa hoặc xoá bài"),
            ("lane", "Hệ thống"), ("act", "Ghi bài viết, ghi nhật ký"),
            ("if", "Bài đang công khai?", [("act", "Hiển thị trên trang tin tức của khách")],
             [("act", "Giữ ở trạng thái nháp, chỉ quản trị thấy")]),
            ("stop",),
        ],
    },
    {
        "ma": "UC24", "ten": "Xem nhật ký hoạt động", "nhom": "Quản trị",
        "api": "GET /api/v1/admin/activity",
        "hoat_dong": [
            ("lane", QT_TEN), ("act", "Mở nhật ký"),
            ("lane", "Hệ thống"), ("act", "Tải nhật ký hoạt động"),
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
    # Bản PlantUML chỉ sinh biểu đồ hoạt động. Biểu đồ trình tự được sinh từ hoạt động
    # bởi ve_bieu_do.py (xem dan_trinh_tu), nên không còn file trình tự viết tay.
    THU_MUC_HD.mkdir(parents=True, exist_ok=True)
    for uc in DAC_TA:
        ten = f"{uc['ma']}_{_ten_an_toan(uc['ten'])}"
        (THU_MUC_HD / f"{ten}.puml").write_text(sinh_hoat_dong(uc), encoding="utf-8")
    print(f"Đã sinh {len(DAC_TA)} biểu đồ hoạt động vào {THU_MUC_HD}")




# ---------------------------------------------------------------------------
# RÀNG BUỘC NGHIỆP VỤ — áp lên đặc tả hoạt động (trình tự được sinh từ đây)
# ---------------------------------------------------------------------------
def _boc_dieu_kien(buoc: list, dieu_kien: str, khong: list) -> list:
    """Bọc luồng bằng một chốt kiểm tra truy cập (ràng buộc).

    Các bước MỞ ĐẦU của người dùng (làn Khách/Quản trị ở đầu luồng, ví dụ "Mở trang hồ sơ")
    đứng TRƯỚC chốt: người dùng bấm trước, hệ thống mới kiểm tra. Nếu chốt đứng đầu thì
    điểm bắt đầu nằm ở làn Hệ thống, đọc ngược với thực tế.
    """
    mo_dau: list = []
    i = 0
    while i + 1 < len(buoc) and buoc[i][0] == "lane" and buoc[i][1] != "Hệ thống":
        if buoc[i + 1][0] != "act":
            break
        mo_dau += [buoc[i], buoc[i + 1]]
        i += 2
    con = buoc[i:]  # luồng chính: phần còn lại sau bước mở đầu
    return mo_dau + [("lane", "Hệ thống"), ("if", dieu_kien, con, khong)]


def _chen_sau(buoc: list, tien_to: str, moi: list) -> list:
    """Chèn các bước mới ngay sau bước (hành động hoặc hình thoi) có nhãn bắt đầu bằng
    `tien_to`. Tìm ĐỆ QUY vào các nhánh: sau khi bọc chốt đăng nhập, mốc nằm trong nhánh
    "có" chứ không còn ở mức trên cùng."""
    ket_qua, da_chen = _chen_de_quy(buoc, tien_to, moi)
    if not da_chen:
        raise SystemExit(f"Không tìm thấy mốc để chèn ràng buộc: {tien_to!r}")
    return ket_qua


def _chen_de_quy(buoc: list, tien_to: str, moi: list) -> tuple[list, bool]:
    out: list = []
    da_chen = False
    for b in buoc:
        if not da_chen and b[0] in ("act", "if") and b[1].startswith(tien_to):
            out.append(b)
            out.extend(moi)
            da_chen = True
            continue
        if not da_chen and b[0] == "if":
            co, ok = _chen_de_quy(b[2], tien_to, moi)
            if ok:
                out.append(("if", b[1], co, b[3]))
                da_chen = True
                continue
            khong, ok = _chen_de_quy(b[3], tien_to, moi)
            if ok:
                out.append(("if", b[1], b[2], khong))
                da_chen = True
                continue
        out.append(b)
    return out, da_chen


_KHOANG_CACH = ("if", "Đã đăng nhập và có vị trí của bạn?",
                [("act", "Hiển thị khoảng cách từ vị trí của bạn đến quán")],
                [("act", "Ẩn khoảng cách, chỉ hiển thị tên và địa chỉ quán")])

# Chốt 2026-11-10 (`docs/UI_REQUIREMENTS.md`): khách chưa đăng nhập KHÔNG dùng được app,
# chỉ đăng nhập / đăng ký / quên mật khẩu (UC08–UC10) là mở. Các luồng dưới đây phải có
# chốt này, đúng như `RequireLogin` ở frontend.
_CAN_DANG_NHAP = {"UC01", "UC02", "UC03", "UC04", "UC05", "UC06", "UC07",
                  "UC11", "UC12", "UC13", "UC14", "UC15"}

for _uc in DAC_TA:
    _ma = _uc["ma"]
    # Đọc `_uc["hoat_dong"]` HIỆN TẠI ở mỗi bước: đọc một biến lưu từ trước sẽ làm chốt
    # áp trước đó bị ghi đè (lỗi thật, phát hiện 2026-11-10).
    # Khu quản trị: chỉ vào được khi đã đăng nhập quản trị (trừ chính màn đăng nhập).
    if _uc["nhom"] == "Quản trị" and _ma != "UC16":
        _uc["hoat_dong"] = _boc_dieu_kien(
            _uc["hoat_dong"], "Đã đăng nhập quản trị?",
            [("act", "Chuyển về trang đăng nhập quản trị"), ("stop",)])
    elif _ma in _CAN_DANG_NHAP:
        _uc["hoat_dong"] = _boc_dieu_kien(
            _uc["hoat_dong"], "Đã đăng nhập?",
            [("act", "Chuyển tới trang đăng nhập"), ("stop",)])
    # Khoảng cách chỉ hiện khi đã đăng nhập và có vị trí (khách không thấy khoảng cách).
    if _ma == "UC01":
        _uc["hoat_dong"] = _chen_sau(_uc["hoat_dong"], "Có quán khớp", [_KHOANG_CACH])
    elif _ma == "UC04":
        _uc["hoat_dong"] = _chen_sau(_uc["hoat_dong"], "Có quán trong bán kính", [_KHOANG_CACH])
    elif _ma == "UC05":
        _uc["hoat_dong"] = _chen_sau(_uc["hoat_dong"], "Hiển thị chi tiết quán", [_KHOANG_CACH])


if __name__ == "__main__":
    main()

"""Người dùng BÁO quán đã đóng cửa — đếm lượt báo để đưa vào hàng chờ quản trị.

THEO BIỂU ĐỒ `UC06`/`UC21` (đổi 2026-11-12): lượt báo KHÔNG tự ẩn quán. Nó đưa quán vào
hàng chờ "Quán bị khách báo đóng cửa", và quản trị quyết định: quán thật sự đã đóng thì
ẩn quán (ghi nhật ký `hide_restaurant`), không thì gỡ lượt báo. Trước đó quán tự ẩn khi đủ
3 người báo (quyết định 2026-10-06); bản đó đã bỏ theo biểu đồ.

VÌ SAO CẦN CÁI NÀY
------------------
Dữ liệu quán lấy từ OSM, Overture và một đợt Apify cũ. Đo ngày 2026-08-19: 65% bản ghi
OSM chưa ai sửa trong hơn một năm, có bản ghi lần cuối được sửa năm 2010. Quán đóng cửa
tháng trước thì không nguồn nào trong số đó biết.

Các nguồn cho biết trạng thái theo thời gian thực (Google Places, ShopeeFood, Foody) đều
hoặc CẦN THẺ THANH TOÁN, hoặc CẤM truy cập tự động theo ToS — cả hai đều bị loại bởi ràng
buộc của dự án (CLAUDE.md mục 1b và 4b). Vậy nên tín hiệu tươi DUY NHẤT còn lại là chính
người đang đứng trước cửa quán.

THUẦN PYTHON. Đây là quy tắc nghiệp vụ ("bao nhiêu lượt báo thì tin", "ai được tính là
một người báo"), không phải chuyện lưu trữ, nên nó nằm ở domain. `hashlib`/`hmac` là thư
viện chuẩn, không phải framework.

CHỐNG PHÁ HOẠI (viết lại 2026-10-06 sau rà soát)
-----------------------------------------------
Bản cũ đếm theo `session_id`. Đó là chuỗi CLIENT TỰ ĐẶT: gửi 3 lượt `report_closed` với 3
session_id bịa là ẩn được bất kỳ quán nào khỏi MỌI luồng, cho MỌI người — tái hiện được.

Nay đếm theo KHOÁ NGƯỜI BÁO do SERVER xác định (`reporter_key_from_ip`), không bao giờ lấy
từ body request. Kèm theo ở tầng HTTP: giới hạn tần suất riêng cho `report_closed`.

VÌ SAO KHOÁ LÀ IP CHỨ KHÔNG PHẢI TÀI KHOẢN (kể cả khi đã đăng nhập): tạo tài khoản gần như
miễn phí (3 tài khoản/giờ/IP, không bắt xác minh email) — đếm theo `user_id` thì một máy
tạo 3 tài khoản là lại ẩn được quán, đúng lỗ hổng vừa vá. Đổi IP thì khó hơn hẳn.

GIỚI HẠN CÒN LẠI — phải nói rõ, không giả vờ đã chống được hết:
  - Kẻ có trong tay ≥3 IP khác nhau (VPN, 4G đổi IP) VẪN ẩn được một quán. Vì thế admin
    PHẢI gỡ được lượt báo: `ClosureReportTally.clear` + endpoint
    `POST /admin/restaurants/{id}/closure-reports/clear`.
  - Nhiều người thật dùng chung một IP (cùng wifi quán, NAT của nhà mạng) chỉ tính là 1.
    Sai theo hướng AN TOÀN: quán chậm bị ẩn hơn, không bao giờ bị ẩn oan nhanh hơn.
  - Chạy sau reverse proxy mà chưa bật `--proxy-headers` thì mọi người chung IP của proxy
    -> cả hệ thống chỉ đếm được 1 người báo/quán, tức tính năng ẩn thôi chạy. Xem ghi chú
    ở `presentation/api/dependencies.client_key`.
"""
from __future__ import annotations

import hashlib
import hmac
import threading
from collections import defaultdict
from typing import Dict, Iterable, Optional, Set, Tuple

# KHÔNG CÒN NGƯỠNG ẨN. Biểu đồ UC06 đưa quán bị báo vào hàng chờ quản trị; quản trị là
# người quyết định ẩn (UC21). Bộ đếm chỉ đếm số NGƯỜI BÁO khác nhau để hàng chờ ưu tiên
# quán bị nhiều người báo nhất. Chống phá hoại (một người không đếm hai lần, khoá là IP
# băm do server tính) vẫn giữ nguyên, vì hàng chờ mà bị bơm giả thì admin mất thời gian.

# Tiền tố khoá người báo. Có tiền tố để sau này thêm loại khoá khác (VD đã xác minh số
# điện thoại) mà không đụng độ với khoá cũ trong nhật ký.
REPORTER_KEY_PREFIX_IP = "ip:"
# 16 ký tự hex = 64 bit: đủ để hai IP khác nhau gần như không bao giờ trùng khoá trong
# phạm vi vài nghìn người báo, mà dòng nhật ký không phình thêm 64 ký tự vô ích.
REPORTER_KEY_HEX_LENGTH = 16

# Loại sự kiện phát lại từ nhật ký. Tách hằng số để adapter đọc nhật ký và domain dùng
# CHUNG một bộ từ, không ai gõ lại chuỗi bằng tay.
EVENT_REPORT = "report"
EVENT_CLEAR = "clear"

ClosureEvent = Tuple[str, str, Optional[str]]  # (loại, place_id, khoá người báo | None)


def reporter_key_from_ip(client_ip: str, salt: str) -> str:
    """Khoá NGƯỜI BÁO từ IP — BĂM, không lưu IP gốc.

    VÌ SAO BĂM: khoá này được ghi vào `interactions.jsonl`, tức là dữ liệu huấn luyện sẽ
    được chép đi chép lại. IP là dữ liệu cá nhân; ta chỉ cần biết "hai lượt báo có cùng
    một nguồn không", không cần biết nguồn đó là ai.

    VÌ SAO CÓ `salt`: IPv4 chỉ có ~4 tỷ giá trị, băm trần thì vét cạn ngược lại được trong
    vài phút. HMAC với một secret của máy chủ thì không. Đổi secret -> cùng một IP sẽ ra
    khoá mới, tức là MỘT người có thể được đếm hai lần quanh mốc đổi secret. Chấp nhận
    được; admin gỡ được lượt báo.
    """
    digest = hmac.new(
        (salt or "").encode("utf-8"), (client_ip or "").encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return REPORTER_KEY_PREFIX_IP + digest[:REPORTER_KEY_HEX_LENGTH]


class ClosureReportTally:
    """Đếm lượt báo đóng cửa và trả lời "quán này có nên ẩn không".

    GIỮ TRONG BỘ NHỚ, dựng lại từ nhật ký tương tác lúc khởi động (`tally_from_events`).
    Không thêm kho lưu trữ mới: nhật ký `interactions.jsonl` vốn đã chỉ-ghi-thêm và đã ghi
    mọi tương tác khác, nên báo đóng cửa và lệnh "admin gỡ lượt báo" đi chung đường là hợp
    lý nhất. Đổi lại, tra cứu là O(1) - việc này nằm trên đường đi của MỌI lượt tìm kiếm
    nên không được phép đọc file.

    Có khoá vì nhiều request chạy song song: `reported_counts()` duyệt dict trong khi một
    request khác thêm quán mới vào sẽ ném "dictionary changed size during iteration".
    """

    __slots__ = ("_reporters_by_place", "_lock")

    def __init__(self) -> None:
        self._reporters_by_place: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.Lock()

    def record(self, place_id: str, reporter_key: str) -> int:
        """Ghi nhận một lượt báo. Trả về số NGƯỜI BÁO khác nhau đã báo quán này.

        Cùng một người báo lại thì số không tăng - xem phần chống phá hoại ở đầu file.
        """
        if not place_id or not reporter_key:
            return 0
        with self._lock:
            reporters = self._reporters_by_place[str(place_id)]
            reporters.add(str(reporter_key))
            return len(reporters)

    def clear(self, place_id: str) -> int:
        """Admin gỡ MỌI lượt báo của một quán. Trả về số người báo đã bị gỡ.

        Gỡ là "bắt đầu lại từ 0", KHÔNG phải "miễn nhiễm": quán đóng cửa thật thì người
        dùng sẽ báo lại và quán lại bị ẩn. Muốn chặn hẳn một quán thì đó là việc của nút
        "Ẩn quán", không phải của bộ đếm này.
        """
        with self._lock:
            return len(self._reporters_by_place.pop(str(place_id), set()))

    def report_count(self, place_id: str) -> int:
        # KHÔNG khoá ở đây, cố ý: hàm này nằm trên đường nóng — `rank_restaurants` gọi nó
        # cho TỪNG quán (52.871 lần mỗi lượt tìm). Một lần `dict.get` + `len(set)` là
        # nguyên tử dưới GIL của CPython, nên không cần khoá để đọc đúng. Khoá chỉ cần
        # cho thao tác DUYỆT cả dict (`reported_counts`) và cho ghi.
        reporters = self._reporters_by_place.get(str(place_id))
        return len(reporters) if reporters else 0

    def reported_counts(self) -> Dict[str, int]:
        """{place_id: số người báo} cho MỌI quán có ít nhất 1 lượt báo. Cho trang quản trị."""
        with self._lock:
            return {p: len(r) for p, r in self._reporters_by_place.items() if r}

    def status(self) -> dict:
        """Tự mô tả cho /health, giống các adapter khác."""
        return {"ready": True, "quan_bi_bao": len(self.reported_counts())}


def tally_from_events(events: Iterable[ClosureEvent]) -> ClosureReportTally:
    """Dựng lại bộ đếm từ nhật ký, ĐÚNG THỨ TỰ đã ghi.

    Thứ tự là điều cốt lõi: "báo, báo, báo, ADMIN GỠ, báo" phải ra 1 người báo chứ không
    phải 4. Lượt báo không có khoá người báo (bản ghi trước 2026-10-06 chỉ có session_id)
    bị BỎ QUA ở đây — xem `JsonlInteractionRepository.replay_closure_events`.
    """
    tally = ClosureReportTally()
    for kind, place_id, reporter_key in events:
        if kind == EVENT_CLEAR:
            tally.clear(place_id)
        elif kind == EVENT_REPORT and reporter_key:
            tally.record(place_id, reporter_key)
    return tally


__all__ = [
    "EVENT_REPORT",
    "EVENT_CLEAR",
    "ClosureEvent",
    "ClosureReportTally",
    "reporter_key_from_ip",
    "tally_from_events",
]

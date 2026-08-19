"""Người dùng BÁO quán đã đóng cửa — đếm và quyết định khi nào thì ẩn.

VÌ SAO CẦN CÁI NÀY
------------------
Dữ liệu quán lấy từ OSM, Overture và một đợt Apify cũ. Đo ngày 2026-08-19: 65% bản ghi
OSM chưa ai sửa trong hơn một năm, có bản ghi lần cuối được sửa năm 2010. Quán đóng cửa
tháng trước thì không nguồn nào trong số đó biết.

Các nguồn cho biết trạng thái theo thời gian thực (Google Places, ShopeeFood, Foody) đều
hoặc CẦN THẺ THANH TOÁN, hoặc CẤM truy cập tự động theo ToS — cả hai đều bị loại bởi ràng
buộc của dự án (CLAUDE.md mục 1b và 4b). Vậy nên tín hiệu tươi DUY NHẤT còn lại là chính
người đang đứng trước cửa quán.

THUẦN PYTHON. Đây là quy tắc nghiệp vụ ("bao nhiêu lượt báo thì tin"), không phải chuyện
lưu trữ, nên nó nằm ở domain.

CHỐNG PHÁ HOẠI
--------------
Một người bực mình có thể bấm báo hàng chục lần để dìm quán đối thủ. Vì vậy đếm theo
SỐ PHIÊN KHÁC NHAU, không đếm số lượt bấm: bấm 50 lần trong một phiên vẫn chỉ tính là 1.
Chưa phải là chống được người quyết tâm (họ vẫn đổi phiên được), nhưng chặn đứng trường
hợp phổ biến nhất, và làm được mà không cần bắt ai đăng nhập.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Set

# Số PHIÊN khác nhau phải cùng báo thì mới ẩn quán.
#
# CHỌN 3, và đây là đánh đổi giữa hai kiểu sai:
#   - Ngưỡng quá thấp (1): một lượt báo nhầm là xoá sổ một quán đang buôn bán bình thường.
#     Người dùng cũng hay bấm nhầm, hoặc báo vì quán đóng cửa lúc 2 giờ chiều.
#   - Ngưỡng quá cao (10): với quán ít người ghé, sẽ không bao giờ đủ - tức là tính năng
#     này chỉ chạy cho quán đông khách, đúng nhóm ít cần nó nhất.
# 3 người lạ mặt độc lập cùng nói một chuyện là đủ tin ở mức "thôi đừng gợi ý nữa", nhất
# là khi hậu quả có thể sửa được (admin bỏ ẩn lại).
MIN_REPORTS_TO_HIDE = 3


class ClosureReportTally:
    """Đếm lượt báo đóng cửa và trả lời "quán này có nên ẩn không".

    GIỮ TRONG BỘ NHỚ, dựng lại từ nhật ký tương tác lúc khởi động. Không thêm kho lưu trữ
    mới: nhật ký `interactions.jsonl` vốn đã chỉ-ghi-thêm và đã ghi mọi tương tác khác,
    nên báo đóng cửa đi chung đường là hợp lý nhất. Đổi lại, tra cứu là O(1) - việc này
    nằm trên đường đi của MỌI lượt tìm kiếm nên không được phép đọc file.
    """

    __slots__ = ("_sessions_by_place", "_threshold")

    def __init__(self, threshold: int = MIN_REPORTS_TO_HIDE) -> None:
        self._sessions_by_place: Dict[str, Set[str]] = defaultdict(set)
        self._threshold = max(1, threshold)

    def record(self, place_id: str, session_id: str) -> int:
        """Ghi nhận một lượt báo. Trả về số phiên KHÁC NHAU đã báo quán này.

        Cùng một phiên báo lại thì số không tăng - xem phần chống phá hoại ở đầu file.
        """
        if not place_id or not session_id:
            return 0
        self._sessions_by_place[str(place_id)].add(str(session_id))
        return len(self._sessions_by_place[str(place_id)])

    def report_count(self, place_id: str) -> int:
        return len(self._sessions_by_place.get(str(place_id), ()))

    def is_reported_closed(self, place_id: str) -> bool:
        """Đã đủ số phiên báo để ẩn quán chưa."""
        return self.report_count(place_id) >= self._threshold

    @property
    def threshold(self) -> int:
        return self._threshold

    def hidden_place_ids(self) -> Set[str]:
        """Toàn bộ quán đang bị ẩn vì bị báo. Dùng cho trang quản trị và /health."""
        return {
            place_id
            for place_id, sessions in self._sessions_by_place.items()
            if len(sessions) >= self._threshold
        }

    def status(self) -> dict:
        """Tự mô tả cho /health, giống các adapter khác."""
        return {
            "ready": True,
            "nguong_an": self._threshold,
            "quan_bi_bao": len(self._sessions_by_place),
            "quan_da_an": len(self.hidden_place_ids()),
        }

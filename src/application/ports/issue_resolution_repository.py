"""PORT: hợp đồng đánh dấu một VẤN ĐỀ ĐÃ ĐƯỢC XỬ LÝ.

Bản thiết kế `needs to be handled admin.png` có thẻ "Đã xử lý hôm nay: 5" và tab
"Đã xử lý (156)". Hai con số đó KHÔNG suy ra được từ dữ liệu quán/món: một quán đã có
số điện thoại thì nó biến mất khỏi danh sách thiếu liên hệ, nhưng ta không còn biết ai
đã sửa và sửa lúc nào. Muốn trả lời thì phải GHI LẠI thao tác — đó là việc của kho này.

QUAN HỆ VỚI NHẬT KÝ HOẠT ĐỘNG (`audit_log`)
--------------------------------------------
Khác nhau, đừng gộp. `audit_log` ghi *người quản trị đã LÀM GÌ* (sửa, ẩn, thêm quán) và
CHỈ GHI THÊM. Kho này ghi *vấn đề nào đã được đánh dấu XONG* — một trạng thái bật/tắt
được, vì người quản trị có thể đánh dấu nhầm và phải gỡ ra được.

⚠️ ĐÁNH DẤU XONG KHÔNG SỬA DỮ LIỆU. Nó chỉ nói "tôi đã xem và không cần làm gì nữa"
(ví dụ: quán đúng là đã đóng cửa thật, đã ẩn xong). Việc sửa dữ liệu đi qua
`/admin/restaurants` như thường và được `audit_log` ghi lại riêng.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Protocol, runtime_checkable

from src.domain.entities.issue_resolution import DanhDauXong


@runtime_checkable
class IssueResolutionRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        """False -> mọi thao tác đánh dấu bị TỪ CHỐI rõ ràng, không im lặng nuốt."""
        ...

    def danh_dau(self, ban_ghi: DanhDauXong) -> DanhDauXong:
        """Đánh dấu một bản ghi đã xử lý. Đánh dấu lại thì cập nhật thời điểm."""
        ...

    def bo_danh_dau(self, khoa: str, target_id: str) -> bool:
        """Gỡ đánh dấu. Trả `True` nếu có dòng bị gỡ."""
        ...

    def da_xong(self, khoa: str, target_ids: List[str]) -> Dict[str, DanhDauXong]:
        """Tra nhanh trạng thái của một loạt bản ghi. Trả {target_id: bản ghi}.

        Nhận cả danh sách thay vì hỏi từng cái: màn "Cần xử lý" hiện 20 dòng một trang,
        và hỏi 20 lần là 20 lượt mở CSDL cho một câu hỏi duy nhất.
        """
        ...

    def dem(self, khoa: Optional[str] = None) -> int:
        """Tổng số bản ghi đã đánh dấu xong, lọc theo `khoa` nếu có."""
        ...

    def dem_trong_ngay(self, ngay: str) -> int:
        """Số bản ghi được đánh dấu trong đúng một ngày (`YYYY-MM-DD`, giờ UTC).

        Đây chính là thẻ "Đã xử lý hôm nay" của bản thiết kế.
        """
        ...

    def liet_ke(self, limit: int = 50) -> List[DanhDauXong]:
        """Các bản ghi đã xử lý, MỚI NHẤT ĐỨNG ĐẦU — cho tab "Đã xử lý"."""
        ...


__all__ = ["IssueResolutionRepository"]

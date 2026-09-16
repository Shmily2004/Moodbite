"""ĐÁNH DẤU MỘT VẤN ĐỀ ĐÃ XỬ LÝ — thực thể của màn "Cần xử lý". Thuần Python.

VÌ SAO CẦN
----------
`domain/services/data_issues.py` đếm được vấn đề CÒN TỒN TẠI trong dữ liệu, nhưng không
đếm được vấn đề ĐÃ ĐƯỢC NGƯỜI TA XEM XONG. Hai chuyện đó khác nhau, và bản thiết kế
`needs to be handled admin.png` hỏi cả hai:

  - "Nghiêm trọng 12"      → suy ra từ dữ liệu (data_issues.py)
  - "Đã xử lý hôm nay 5"   → KHÔNG suy ra được, phải ghi lại (file này)

Ví dụ rõ nhất: một quán bị nguồn đánh dấu "đóng tạm thời". Người quản trị gọi điện, xác
nhận quán vẫn mở bình thường, nguồn ghi sai. Không có gì trong dữ liệu để sửa cả — nhưng
lần sau mở trang, dòng đó lại hiện lên như chưa ai đụng tới. Đánh dấu xong là cách nói
"tôi đã xem rồi, không phải làm gì nữa".

GỠ ĐƯỢC — KHÁC VỚI NHẬT KÝ HOẠT ĐỘNG
-------------------------------------
`audit_log` chỉ ghi thêm, không bao giờ sửa, vì nó là bằng chứng. Còn đây là TRẠNG THÁI
hiện tại của một việc, và người ta bấm nhầm được, nên phải gỡ ra được. Đừng gộp hai thứ
này vào một bảng chỉ vì chúng trông giống nhau.

KHÔNG SỬA DỮ LIỆU GỐC. Đánh dấu xong không ẩn quán, không thêm ảnh cho món. Nó chỉ đổi
cách một dòng hiện lên ở màn "Cần xử lý".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class DanhDauXong:
    """Một bản ghi đã được người quản trị đánh dấu là xử lý xong."""

    # Loại vấn đề — khoá của `data_issues.viec_can_xu_ly` ("dong_tam", "mon_thieu_anh"…).
    khoa: str
    # Bản ghi cụ thể: `place_id` với quán, `dish_id` với món.
    #
    # Cặp (khoa, target_id) là KHOÁ CHÍNH. Cùng một quán có thể vừa thiếu liên hệ vừa
    # nghi đã đóng cửa — đó là HAI việc khác nhau, xử lý xong việc này không có nghĩa
    # đã xử lý việc kia.
    target_id: str
    actor: str
    # Ghi chú tuỳ chọn: "đã gọi điện, quán vẫn mở". Để trống được — bắt buộc nhập ghi chú
    # chỉ khiến người ta gõ bừa một dấu chấm cho xong.
    ghi_chu: Optional[str] = None
    # Kho đóng dấu nếu để trống. Domain KHÔNG tự gọi `datetime.now()` ở giá trị mặc định:
    # làm vậy thì test không cố định được thời gian.
    resolved_at: Optional[datetime] = None

    @property
    def ngay(self) -> Optional[str]:
        """Ngày `YYYY-MM-DD` của lần đánh dấu — dùng cho thẻ "Đã xử lý hôm nay"."""
        if self.resolved_at is None:
            return None
        return self.resolved_at.date().isoformat()


__all__ = ["DanhDauXong"]

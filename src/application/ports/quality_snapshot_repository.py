"""PORT: hợp đồng lưu/đọc ẢNH CHỤP CHẤT LƯỢNG DỮ LIỆU theo ngày.

Vì sao cần: bản thiết kế `quality data admin.png` có biểu đồ xu hướng 7 ngày và dòng
"so với tháng trước". Một ảnh chụp tại một thời điểm không trả lời được hai thứ đó —
phải giữ lại số của những ngày trước. Xem `domain/services/data_quality_history.py`.

⚠️ ĐÂY LÀ DỮ LIỆU GỐC (mất là mất hẳn, không dựng lại được từ dataset hiện tại) nên nằm
chung file CSDL với tài khoản và nhật ký, KHÔNG nằm ở `moodbite.db` — file đó là dữ liệu
dẫn xuất và tài liệu còn khuyến khích xoá đi dựng lại.

⚠️ MỖI NGÀY MỘT DÒNG. `ghi` cùng một ngày hai lần thì lần sau GHI ĐÈ lần trước, không
thêm dòng mới — nếu không, người quản trị mở trang 10 lần trong ngày sẽ tạo ra 10 điểm
chồng lên nhau ở hôm nay và vẽ ra một xu hướng không có thật.
"""
from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from src.domain.services.data_quality_history import AnhChupChatLuong


@runtime_checkable
class QualitySnapshotRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        """False -> bỏ qua việc ghi/đọc lịch sử, KHÔNG làm hỏng màn hình chất lượng.

        Lịch sử là phần LÀM GIÀU của màn hình đó; mất nó thì biểu đồ trống và giao diện
        nói rõ là chưa có, còn ném lỗi ra ngoài sẽ làm trắng cả trang vì một khối phụ.
        """
        ...

    def ghi(self, anh_chup: AnhChupChatLuong) -> None:
        """Lưu ảnh chụp của một ngày. Cùng ngày gọi lại thì ghi đè."""
        ...

    def doc_gan_day(self, so_ngay: int = 60) -> List[AnhChupChatLuong]:
        """Ảnh chụp trong `so_ngay` ngày gần nhất, CŨ TRƯỚC.

        Mặc định 60 ngày vì mốc so sánh xa nhất mà giao diện dùng là 30 ngày — lấy gấp
        đôi để vẫn còn mốc khi có vài ngày trống.
        """
        ...


__all__ = ["QualitySnapshotRepository"]

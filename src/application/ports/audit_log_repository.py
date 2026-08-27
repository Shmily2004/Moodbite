"""PORT: hợp đồng ghi/đọc NHẬT KÝ HOẠT ĐỘNG QUẢN TRỊ.

Cùng lý do tách port như mọi kho khác: application chỉ biết interface này, không biết
nhật ký nằm ở SQLite, ở file, hay ở dịch vụ log bên ngoài.

⚠️ ĐÂY LÀ DỮ LIỆU GỐC (mất là mất hẳn) nên nằm chung file CSDL với tài khoản, KHÔNG nằm
ở `moodbite.db` — file đó là dữ liệu dẫn xuất và tài liệu còn khuyến khích xoá đi dựng
lại. Xem `sqlite_user_repository.py` để biết đầy đủ lý do.

⚠️ CHỈ GHI THÊM. Cố ý KHÔNG có `update` hay `delete_one` — nhật ký sửa được thì không
còn là nhật ký. Dọn dẹp chỉ theo TUỔI (`xoa_cu_hon`), không theo nội dung.
"""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from src.domain.entities.audit_log import AuditEntry


@runtime_checkable
class AuditLogRepository(Protocol):
    @property
    def is_ready(self) -> bool:
        """False -> ghi nhật ký bị BỎ QUA, KHÔNG làm hỏng thao tác đang ghi. Xem use case."""
        ...

    def add(self, entry: AuditEntry) -> AuditEntry:
        """Ghi một dòng. Trả bản đã có `created_at` do kho đóng dấu."""
        ...

    def list_recent(
        self, limit: int = 50, action: Optional[str] = None
    ) -> List[AuditEntry]:
        """Nhật ký gần nhất, MỚI NHẤT ĐỨNG ĐẦU."""
        ...

    def count(self) -> int:
        """Tổng số dòng — cho `/health` và cho biết nhật ký đã phình tới đâu."""
        ...

    def xoa_cu_hon(self, so_ngay: int) -> int:
        """Xoá dòng cũ hơn `so_ngay`. Trả số dòng đã xoá.

        Cách dọn DUY NHẤT được phép: theo tuổi, không theo nội dung. Nếu cho xoá theo nội
        dung thì người vừa làm sai có thể xoá đúng dòng ghi lại việc mình vừa làm.
        """
        ...


__all__ = ["AuditLogRepository"]

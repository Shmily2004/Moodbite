"""USE CASE: ghi và đọc NHẬT KÝ HOẠT ĐỘNG QUẢN TRỊ.

Chỉ ĐIỀU PHỐI: kiểm dữ liệu bằng hàm ở domain rồi gọi kho. Luật "một dòng nhật ký trông
thế nào" nằm ở `domain/entities/audit_log.py`.

⚠️ GHI NHẬT KÝ KHÔNG BAO GIỜ ĐƯỢC LÀM HỎNG THAO TÁC ĐANG GHI.
Đây là quyết định quan trọng nhất của file này. Nếu ghi nhật ký ném lỗi ra ngoài thì:

    admin bấm "ẩn quán" -> quán ĐÃ bị ẩn trong CSDL -> ghi nhật ký hỏng -> trả 500
    -> admin thấy "thất bại" nên bấm lại -> lần này báo "quán đã ẩn rồi" -> bối rối hoàn toàn

Thao tác chính đã xong và không rút lại được; ném lỗi lúc này chỉ tạo ra một trạng thái
mà người dùng không hiểu nổi. Nên `ghi()` NUỐT mọi lỗi và ghi `logger.error` — mất một
dòng nhật ký là chấp nhận được, làm hỏng thao tác thì không.

Đây cũng chính là lý do `RequestEmailVerificationUseCase.try_send` tồn tại: cùng một
kiểu "việc phụ không được giết việc chính".
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from src.application.ports.audit_log_repository import AuditLogRepository
from src.domain.entities.audit_log import (
    AuditEntry,
    validate_audit_entry,
)

logger = logging.getLogger("moodbite.audit")

MAX_TRANG = 200


@dataclass
class GhiNhatKyUseCase:
    """Ghi một dòng nhật ký. KHÔNG BAO GIỜ ném lỗi ra ngoài — xem docstring đầu file."""

    audit_log: Optional[AuditLogRepository] = None

    def ghi(
        self,
        *,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        summary: str,
    ) -> bool:
        """Trả True nếu đã ghi được. Giá trị trả về CHỈ để test và gỡ lỗi."""
        if self.audit_log is None or not self.audit_log.is_ready:
            return False
        try:
            ai, hanh_dong, loai, ma, tom_tat = validate_audit_entry(
                actor, action, target_type, target_id, summary
            )
            self.audit_log.add(
                AuditEntry(
                    actor=ai,
                    action=hanh_dong,
                    target_type=loai,
                    target_id=ma,
                    summary=tom_tat,
                )
            )
            return True
        except Exception as exc:  # noqa: BLE001 - xem docstring đầu file
            logger.error("Không ghi được nhật ký (%s trên %s): %s", action, target_id, exc)
            return False


@dataclass
class DocNhatKyUseCase:
    """Đọc nhật ký gần nhất cho trang quản trị."""

    audit_log: Optional[AuditLogRepository] = None

    def execute(self, limit: int = 50, action: Optional[str] = None) -> List[AuditEntry]:
        """Kho chưa mở được -> trả DANH SÁCH RỖNG, không ném lỗi.

        Nhật ký rỗng và nhật ký hỏng nhìn giống nhau với người dùng, nhưng khác nhau ở
        chỗ: hỏng thì `/health` đã báo rồi. Làm trắng cả trang quản trị vì nhật ký hỏng
        là phản ứng quá tay.
        """
        if self.audit_log is None or not self.audit_log.is_ready:
            return []
        so = max(1, min(int(limit), MAX_TRANG))
        return self.audit_log.list_recent(limit=so, action=action)


__all__ = ["GhiNhatKyUseCase", "DocNhatKyUseCase", "MAX_TRANG"]

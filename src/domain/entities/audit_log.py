"""NHẬT KÝ HOẠT ĐỘNG QUẢN TRỊ — ai đã làm gì, lúc nào. Thuần Python.

VÌ SAO CẦN (chủ dự án yêu cầu 2026-08-26, có trong `design/Dashboard admin.png`)
--------------------------------------------------------------------------------
Trước file này, việc admin **ẩn / sửa / thêm quán KHÔNG được ghi lại ở đâu cả**. Hệ quả
thật, không phải giả định:

  - Một quán biến mất khỏi kết quả tìm kiếm và không ai truy được ai đã ẩn, lúc nào,
    vì lý do gì. Cách duy nhất là so dữ liệu với bản sao lưu — nếu có bản sao lưu.
  - Sửa nhầm tên một quán rồi thì không có gì để lần lại giá trị cũ.

Đây là dữ liệu vận hành có thật, khác hẳn mấy con số xu hướng trong bản thiết kế mà dự
án không có nguồn để tính.

CHỈ GHI THÊM, KHÔNG BAO GIỜ SỬA
--------------------------------
Nhật ký mà sửa được thì không còn là nhật ký. Không có use case nào cập nhật hay xoá một
dòng; muốn dọn thì phải xoá theo TUỔI (`xoa_cu_hon`), không xoá theo nội dung.

GHI GÌ VÀ KHÔNG GHI GÌ
----------------------
CÓ:    ai (`actor`), làm gì (`action`), trên bản ghi nào (`target_type`/`target_id`),
       lúc nào, và một câu tóm tắt đọc được (`summary`).
KHÔNG: mật khẩu, token, header, và TOÀN BỘ nội dung bản ghi trước/sau.

Không chép cả bản ghi vì hai lý do: nhật ký sẽ phình nhanh hơn cả dữ liệu gốc, và nó
biến thành một bản sao thứ hai của dữ liệu người dùng nằm ngoài mọi quy tắc xoá. Tóm tắt
dạng "Đổi tên: 'Phở Thìn' -> 'Phở Thìn 13 Lò Đúc'" đủ để lần lại mà không nhân đôi dữ liệu.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class AuditAction(str, Enum):
    """Những việc ĐÁNG ghi lại.

    Cố ý KHÔNG có `VIEW`/`LIST`: người quản trị mở danh sách hàng chục lần mỗi phiên, ghi
    lại sẽ nhấn chìm những việc thật sự đổi dữ liệu. Nhật ký này để trả lời "ai đã ĐỔI
    cái gì", không phải "ai đã nhìn cái gì".
    """

    CREATE_RESTAURANT = "create_restaurant"
    UPDATE_RESTAURANT = "update_restaurant"
    HIDE_RESTAURANT = "hide_restaurant"
    RESTORE_RESTAURANT = "restore_restaurant"


# Nhãn tiếng Việt để giao diện khỏi tự dịch. Để ở domain vì đây là NGÔN NGỮ NGHIỆP VỤ —
# gọi "ẩn quán" hay "vô hiệu hoá quán" là một quyết định về sản phẩm, không phải về UI.
NHAN_HANH_DONG = {
    AuditAction.CREATE_RESTAURANT: "Thêm quán mới",
    AuditAction.UPDATE_RESTAURANT: "Cập nhật thông tin quán",
    AuditAction.HIDE_RESTAURANT: "Ẩn quán",
    AuditAction.RESTORE_RESTAURANT: "Khôi phục quán",
}

# Chặn trên độ dài câu tóm tắt. Không phải để "bảo mật" mà để một lần sửa 30 trường không
# đẻ ra một dòng nhật ký dài vài KB.
MAX_SUMMARY_LENGTH = 500


class InvalidAuditEntry(ValueError):
    """Bản ghi nhật ký không hợp lệ -> lỗi lập trình, không phải lỗi người dùng."""


@dataclass(frozen=True)
class AuditEntry:
    """Một dòng nhật ký. `frozen` vì nhật ký chỉ ghi thêm, không sửa."""

    actor: str
    action: AuditAction
    target_type: str
    target_id: str
    summary: str
    created_at: Optional[datetime] = None

    @property
    def nhan(self) -> str:
        """Nhãn tiếng Việt của hành động."""
        return NHAN_HANH_DONG.get(self.action, self.action.value)

    def to_public(self) -> dict:
        return {
            "actor": self.actor,
            "action": self.action.value,
            "action_label": self.nhan,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def validate_audit_entry(
    actor: str, action: str, target_type: str, target_id: str, summary: str
) -> tuple:
    """Kiểm và chuẩn hoá. Trả `(actor, AuditAction, target_type, target_id, summary)`.

    Đặt ở domain vì đây là quy tắc "một dòng nhật ký trông thế nào" — mai kia có lệnh CLI
    nhập lại nhật ký từ bản sao lưu thì vẫn phải theo đúng luật này.
    """
    ai = (actor or "").strip()
    if not ai:
        raise InvalidAuditEntry("Thiếu actor — không biết ai làm thì ghi lại vô nghĩa.")

    try:
        hanh_dong = AuditAction(action)
    except ValueError:
        hop_le = [a.value for a in AuditAction]
        raise InvalidAuditEntry(f"action '{action}' không hợp lệ. Hợp lệ: {hop_le}")

    loai = (target_type or "").strip()
    ma = (target_id or "").strip()
    if not loai or not ma:
        raise InvalidAuditEntry("Thiếu target_type hoặc target_id.")

    tom_tat = (summary or "").strip()
    if len(tom_tat) > MAX_SUMMARY_LENGTH:
        # Cắt bớt thay vì báo lỗi: mất một phần câu tóm tắt vẫn tốt hơn là làm hỏng chính
        # thao tác mà nó đang ghi lại.
        tom_tat = tom_tat[: MAX_SUMMARY_LENGTH - 1] + "…"

    return ai, hanh_dong, loai, ma, tom_tat


def tom_tat_thay_doi(truoc: dict, sau: dict) -> str:
    """Dựng câu tóm tắt cho một lần SỬA: chỉ nêu trường THỰC SỰ đổi.

    Ví dụ: `Đổi name: "Phở Thìn" -> "Phở Thìn 13 Lò Đúc"; đổi phone: (trống) -> "0243..."`

    Chỉ nêu trường đổi chứ không liệt kê hết: một lần sửa thường chạm 1-2 trường, còn bản
    ghi quán có hơn 30 trường. Liệt kê hết thì dòng nhật ký nào cũng giống dòng nào và
    không ai đọc nữa.
    """
    phan: list = []
    for khoa in sorted(sau.keys()):
        cu = truoc.get(khoa)
        moi = sau.get(khoa)
        if cu == moi:
            continue
        phan.append(f"{khoa}: {_hien(cu)} -> {_hien(moi)}")

    if not phan:
        # Gửi lên đúng y giá trị đang có cũng là một thao tác có thật — ghi lại để khỏi
        # có dòng nhật ký trống nghĩa.
        return "Không có trường nào thay đổi"
    return "Đổi " + "; ".join(phan)


def _hien(x) -> str:
    """`None` và chuỗi rỗng hiện thành `(trống)`, KHÔNG hiện thành `None` hay `""`.

    Người đọc nhật ký là người, không phải lập trình viên đọc repr Python.
    """
    if x is None or (isinstance(x, str) and not x.strip()):
        return "(trống)"
    return f'"{x}"'


__all__ = [
    "AuditEntry",
    "AuditAction",
    "InvalidAuditEntry",
    "validate_audit_entry",
    "tom_tat_thay_doi",
    "NHAN_HANH_DONG",
    "MAX_SUMMARY_LENGTH",
]

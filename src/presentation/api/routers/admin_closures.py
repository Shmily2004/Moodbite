"""Router QUẢN TRỊ: quán bị người dùng BÁO ĐÓNG CỬA (thêm 2026-10-06).

    GET  /api/v1/admin/closure-reports                          quán đang bị báo
    POST /api/v1/admin/restaurants/{id}/closure-reports/clear   gỡ mọi lượt báo của 1 quán

VÌ SAO CÓ (rà soát 2026-10-06): quán đủ 3 người báo thì bị ẩn khỏi MỌI luồng, và trước
router này admin KHÔNG có cách nào bỏ ẩn — lượt báo được phát lại từ nhật ký mỗi lần khởi
động, còn nút "Khôi phục" chỉ đặt `is_active=1`.

⚠️ HAI CƠ CHẾ ẨN ĐỘC LẬP, HAI NÚT RIÊNG:
  - Admin tắt quán (`/admin/restaurants/{id}/hide` | `/restore`) -> cột `is_active`.
  - Người dùng báo đóng cửa (router này) -> bộ đếm lượt báo, quán vẫn `is_active=1`.
  "Khôi phục" KHÔNG gỡ lượt báo, và "gỡ lượt báo" KHÔNG bật lại quán admin đã tắt.

File RIÊNG thay vì thêm vào `routers/admin.py` (~900 dòng, CLAUDE.md mục 6). Xác thực gắn
ở CẤP ROUTER như `admin.router`, để endpoint thêm sau không thể quên.

Router MỎNG: kiểm/ghi nằm ở `application/use_cases/manage_closure_reports.py`.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.application.errors import DataNotReadyError
from src.presentation.api.dependencies import Container, get_container, require_admin
from src.presentation.api.envelope import success
from src.presentation.api.schemas_closure_reports import (
    CLOSURE_ADMIN_ERROR_RESPONSES,
    ClearedClosureReportsData,
    ClearedClosureReportsResponse,
    ClosureReportItem,
    ClosureReportListData,
    ClosureReportListResponse,
)

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


def _require(use_case):
    """Chưa lắp use case (container dựng tay) -> 503 kèm cách khắc phục, không 500."""
    if use_case is None:
        raise DataNotReadyError(
            "chức năng gỡ lượt báo đóng cửa chưa được lắp",
            "khởi động lại backend bằng build_container() mặc định",
        )
    return use_case


@router.get("/closure-reports", response_model=ClosureReportListResponse,
            responses=CLOSURE_ADMIN_ERROR_RESPONSES,
            summary="Quán đang bị người dùng báo đóng cửa")
def list_closure_reports(container: Container = Depends(get_container)):
    """Mọi quán có ít nhất 1 lượt báo. Quán ĐANG BỊ ẨN đứng đầu."""
    use_case = _require(container.list_closure_reports)
    rows = use_case.execute()
    return success(
        ClosureReportListData(
            threshold=use_case.threshold,
            items=[
                ClosureReportItem(
                    restaurant_id=r.restaurant_id,
                    name=r.name,
                    report_count=r.report_count,
                    is_hidden=r.is_hidden,
                )
                for r in rows
            ],
        ).model_dump()
    )


@router.post("/restaurants/{restaurant_id}/closure-reports/clear",
             response_model=ClearedClosureReportsResponse,
             responses=CLOSURE_ADMIN_ERROR_RESPONSES,
             summary="Gỡ mọi lượt báo đóng cửa của một quán")
def clear_closure_reports(
    restaurant_id: str,
    container: Container = Depends(get_container),
    admin: str = Depends(require_admin),
):
    """Gỡ mọi lượt báo -> quán hiện lại NGAY, và vẫn hiện sau khi khởi động lại (sự kiện
    gỡ được ghi vào chính nhật ký tương tác mà bộ đếm phát lại). Có ghi nhật ký quản trị
    (`clear_closure_reports`).

    Gỡ là "đếm lại từ 0", không phải "miễn nhiễm": quán đóng cửa thật sẽ bị báo lại.
    404 RESTAURANT_NOT_FOUND khi quán không tồn tại VÀ không có lượt báo nào.
    """
    kq = _require(container.clear_closure_reports).execute(restaurant_id, actor=admin)
    return success(
        ClearedClosureReportsData(
            restaurant_id=kq.restaurant_id,
            cleared_reports=kq.cleared_reports,
            is_hidden=kq.is_hidden,
        ).model_dump()
    )

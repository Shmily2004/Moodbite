"""Router quản trị — `/api/v1/admin/*`.

MỎNG theo đúng CLAUDE.md mục 3: chỉ nhận HTTP, gọi use case, trả envelope. Không có
quy tắc nghiệp vụ ở đây (quy tắc "sửa được trường nào" nằm ở
`domain/value_objects/restaurant_edit.py`).

BẢO MẬT — hai chốt chặn độc lập:
  1. `Depends(require_admin)` gắn ở CẤP ROUTER cho mọi endpoint dưới đây, trừ `/login`.
     Đặt ở router thay vì từng hàm để thêm endpoint mới KHÔNG THỂ quên xác thực.
  2. Chưa cấu hình đủ biến môi trường -> `AdminAuthService` ném AdminNotConfiguredError
     -> 503. Fail-closed, không bao giờ mặc định cho qua.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query, Request

from src.application.errors import DataNotReadyError
from src.domain.entities.audit_log import tom_tat_thay_doi
from src.presentation.api.dependencies import (
    Container,
    client_key,
    get_container,
    require_admin,
)
from src.presentation.api.envelope import success
from src.presentation.api.schemas import (
    AdminCreateRestaurantRequest,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminOverviewResponse,
    AdminDishListResponse,
    AdminRecommendationResponse,
    AdminSystemResponse,
    AuditLogResponse,
    AdminRestaurantListResponse,
    AdminRestaurantResponse,
    AdminRestaurantSummary,
    AdminUpdateRestaurantRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])

# Router riêng cho /login: đây là endpoint DUY NHẤT không yêu cầu token, vì nó chính là
# nơi phát token ra.
public_router = APIRouter(prefix="/admin", tags=["admin"])


def _require_writable(container: Container):
    """Kho hiện tại có ghi được không. CSV thì không."""
    if container.admin_restaurants is None:
        raise DataNotReadyError(
            "kho lưu trữ hiện tại không ghi được",
            "Dựng CSDL bằng `python scripts/build_sqlite.py` rồi chạy lại backend với "
            "MOODBITE_STORAGE=sqlite",
        )


def _to_summary(restaurant) -> AdminRestaurantSummary:
    return AdminRestaurantSummary(
        restaurant_id=restaurant.place_id,
        name=restaurant.name,
        category=restaurant.category,
        cuisine=restaurant.cuisine,
        address=restaurant.address,
        district=restaurant.district,
        # `price` là CHUỖI khoảng giá, không phải số - xem CLAUDE.md mục 4 quy tắc 2.
        price=restaurant.price,
        phone=restaurant.phone,
        website=restaurant.website,
        # `None` giữ nguyên None: "chưa có đánh giá" khác hẳn "0 sao".
        rating=restaurant.rating,
        reviews_count=restaurant.reviews_count,
        is_active=restaurant.is_active,
        source=restaurant.source,
    )


@public_router.post("/login", response_model=AdminLoginResponse)
def login(
    payload: AdminLoginRequest,
    request: Request,
    container: Container = Depends(get_container),
):
    """Đổi tài khoản/mật khẩu lấy token ngắn hạn.

    Sai thông tin -> 401 UNAUTHORIZED. Chưa cấu hình admin -> 503 kèm hướng dẫn.
    Quá số lần thử -> 429 RATE_LIMITED.

    ⚠️ ĐẾM TRƯỚC KHI KIỂM MẬT KHẨU. Kiểm mật khẩu chạy PBKDF2 600.000 vòng (~0,4 giây
    CPU); để sau thì kẻ tấn công vẫn ép được máy chủ làm việc nặng dù request rốt cuộc
    bị từ chối. Cùng lý lẽ đã ghi ở `/auth/register`.
    """
    container.admin_login_rate_limiter.check(client_key(request))

    token = container.admin_auth.login(payload.username, payload.password)
    # Đăng nhập ĐÚNG thì xoá lịch sử đếm — người quản trị gõ nhầm vài lần rồi vào được
    # không đáng bị chặn oan ở lần sau. Giống hệt `/auth/login`.
    container.admin_login_rate_limiter.reset(client_key(request))
    return success(
        {
            "token": token,
            "token_type": "bearer",
            "expires_in": container.admin_auth.token_ttl_seconds,
        }
    )


@router.get("/dishes", response_model=AdminDishListResponse)
def list_dishes(
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
    q: Optional[str] = Query(None, description="Tìm theo tên hoặc mã món"),
    filter: str = Query(
        "all",
        description="all | with_restaurants | without_restaurants | missing_image | "
        "missing_description",
    ),
    limit: int = Query(50, ge=1, le=200),
):
    """Danh mục món cho trang quản trị.

    ⚠️ KHÁC `/dishes/suggest`: ở đây thấy CẢ món chưa có quán (557 món) và CẢ danh mục
    ("Bún"). Người dùng cuối không được thấy hai nhóm đó, còn admin thì phải — việc của
    họ chính là tìm những món đang thiếu.
    """
    results, total = container.list_dishes_for_admin.execute(
        query=q, loc=filter, limit=limit
    )
    return success(
        {
            "results": [asdict(r) for r in results],
            "returned": len(results),
            "total": total,
        }
    )


@router.get("/recommendation", response_model=AdminRecommendationResponse)
def admin_recommendation(
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
):
    """Trạng thái NĂM LỚP MÔ HÌNH của đề án (CLAUDE.md mục 4c).

    Đây là màn để KIỂM TRA và HIỂU hệ gợi ý, KHÔNG phải để chỉnh nó. Admin không được
    sửa trọng số hay điểm bằng tay — công thức là quy tắc nghiệp vụ và chỉ được nằm ở
    `domain/services/`. Sửa qua HTTP thì mỗi lần deploy lại một kết quả khác nhau và
    không ai tái hiện được.

    ⚠️ Nói ĐÚNG độ phủ, kể cả khi xấu. Đo 2026-08-26: chỉ 1.193/52.854 quán (2,3%) có
    cụm trải nghiệm, vì phân cụm cần tín hiệu rating/giá/review mà chỉ ~2% quán có.
    Phần còn lại đi đường Cold Start với điểm trung tính 0,5 (rules.md mục 3.3) — hệ vẫn
    chạy đúng, nhưng con số này phải hiện ra chứ không được giấu sau chữ "✅ Xong".
    """
    quan = container.restaurant_repository.list_all()
    tong = len(quan)
    co_cum = sum(1 for r in quan if r.experience_cluster_id is not None)

    dem_nhan: dict = {}
    for r in quan:
        if r.experience_cluster_label:
            dem_nhan[r.experience_cluster_label] = dem_nhan.get(r.experience_cluster_label, 0) + 1

    tk_ngu_nghia = _status_an_toan(container.semantic_search)
    tk_rule = _status_an_toan(container.dish_knowledge_repository)
    tk_ml = _status_an_toan(container.rule_predictor)
    tk_ctx = _status_an_toan(container.context_provider)
    so_tuong_tac = int(_status_an_toan(container.interaction_repository).get("count", 0) or 0)

    layers = [
        {
            "layer": 1,
            "name": "Phân cụm trải nghiệm",
            "status": "mot_phan" if 0 < co_cum < tong else ("chay" if co_cum else "chua_lam"),
            "method": "KMeans k=7 (chạy offline ở data_pipeline/clustering.py)",
            "coverage": _ty_le(co_cum, tong, "quán"),
            "note": (
                "Quán chưa phân cụm KHÔNG bị coi là quán dở — dùng điểm trung tính 0,5 "
                "(Cold Start). Phân cụm cần tín hiệu rating/giá/review mà rất ít quán có."
            ),
        },
        {
            "layer": 2,
            "name": "Tìm kiếm ngữ nghĩa",
            "status": "chay" if tk_ngu_nghia.get("ready") else "chua_lam",
            "method": tk_ngu_nghia.get("method"),
            "coverage": _ty_le(int(tk_ngu_nghia.get("indexed") or 0), tong, "quán"),
            "note": None,
        },
        {
            "layer": 3,
            "name": "Xếp hạng theo ngữ cảnh",
            "status": "chay",
            "method": "Công thức trọng số (domain/services/search_ranking.py)",
            "coverage": None,
            "note": (
                "Thời tiết đang "
                + ("BẬT" if tk_ctx.get("weather_enabled") else "TẮT")
                + f" (nguồn ngữ cảnh: {tk_ctx.get('source')}). "
                "Đây là công thức trọng số, CHƯA phải mô hình học từ dữ liệu."
            ),
        },
        {
            "layer": 4,
            "name": "Tóm tắt review",
            "status": "chay",
            "method": "Trích nguyên văn câu tiêu biểu, không sinh chữ mới",
            "coverage": None,
            "note": "Trích nguyên văn để không bịa nội dung review.",
        },
        {
            "layer": 5,
            "name": "Gợi ý món",
            "status": "chay" if tk_rule.get("ready") else "chua_lam",
            "method": f"Khớp từ khoá theo {tk_rule.get('rules', 0)} rule"
            + ("" if tk_ml.get("available") else " (chưa có model ML — đây là mặc định bình thường)"),
            "coverage": None,
            "note": tk_ml.get("reason") if not tk_ml.get("available") else None,
        },
    ]

    return success(
        {
            "layers": layers,
            "interactions_total": so_tuong_tac,
            "clustered_restaurants": co_cum,
            "restaurants_total": tong,
            "cluster_labels": [
                {"label": nhan, "count": so}
                for nhan, so in sorted(dem_nhan.items(), key=lambda x: -x[1])
            ],
        }
    )


def _status_an_toan(doi_tuong) -> dict:
    """`status()` của một kho, hoặc dict rỗng. Một kho hỏng không được làm trắng cả trang."""
    lay = getattr(doi_tuong, "status", None)
    if not callable(lay):
        return {}
    try:
        return lay() or {}
    except Exception:  # noqa: BLE001 - xem docstring
        return {}


def _ty_le(phan: int, tong: int, don_vi: str) -> str:
    if tong <= 0:
        return f"0 {don_vi}"
    return f"{phan:,}/{tong:,} {don_vi} ({phan / tong * 100:.1f}%)".replace(",", ".")


@router.get("/system", response_model=AdminSystemResponse)
def admin_system(
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
):
    """Cấu hình đang chạy + trạng thái từng kho dữ liệu. CHỈ ĐỌC.

    ⚠️ KHÔNG trả secret nào (mật khẩu SMTP, khoá ký token, hash mật khẩu admin). Chỉ trả
    cờ "đã cấu hình hay chưa". Trang quản trị chạy trong trình duyệt — mọi thứ gửi ra đây
    coi như đã lộ với bất kỳ ai xem được máy đó.

    ⚠️ CŨNG KHÔNG SỬA ĐƯỢC. Cấu hình nằm ở biến môi trường / `.env.local`; cho sửa qua
    HTTP nghĩa là một lỗ hổng ở trang quản trị đổi được cả khoá ký token. Muốn đổi thì
    sửa `.env.local` rồi khởi động lại — xem `scripts/chuan_bi_may_moi.py`.
    """
    settings = container.settings
    kho = [
        ("restaurants", "Kho quán ăn", container.restaurant_repository),
        ("dish_catalog", "Danh mục món", container.dish_catalog_repository),
        ("restaurant_details", "Chi tiết quán (review/ảnh)", container.details_repository),
        ("semantic_search", "Tìm kiếm ngữ nghĩa", container.semantic_search),
        ("users", "Kho tài khoản", container.users),
        ("saved_items", "Món & quán đã lưu", container.saved_items),
        ("audit_log", "Nhật ký hoạt động", container.audit_log),
    ]
    return success(
        {
            "storage_backend": getattr(settings, "storage_backend", "?"),
            "weather_enabled": bool(getattr(settings, "enable_weather", False)),
            "admin_token_ttl_seconds": getattr(settings, "admin_token_ttl_seconds", 0),
            "user_token_ttl_seconds": getattr(settings, "user_token_ttl_seconds", 0),
            # CỜ, không phải địa chỉ hay mật khẩu.
            "email_configured": bool(
                getattr(container.emails, "is_configured", False)
            ),
            "app_base_url": getattr(settings, "app_base_url", ""),
            "services": [
                {
                    "key": khoa,
                    "label": nhan,
                    "ready": bool(getattr(doi_tuong, "is_ready", False)),
                    "detail": _chi_tiet_kho(doi_tuong),
                }
                for khoa, nhan, doi_tuong in kho
            ],
        }
    )


def _chi_tiet_kho(doi_tuong) -> Optional[str]:
    """Một dòng mô tả kho: số bản ghi, hoặc lý do hỏng.

    Đọc qua `status()` vì mỗi kho tự biết cách mô tả mình; ép một hình dạng chung sẽ mất
    thông tin riêng (VD kho tìm kiếm ngữ nghĩa báo số đặc trưng, kho quán báo số quán).
    """
    lay = getattr(doi_tuong, "status", None)
    if not callable(lay):
        return None
    try:
        tt = lay()
    except Exception:  # noqa: BLE001 - một kho hỏng không được làm trắng cả trang
        return "không đọc được trạng thái"
    if tt.get("error"):
        return str(tt["error"])
    for khoa in ("count", "dishes", "indexed", "rules"):
        if khoa in tt and tt[khoa] is not None:
            return f"{tt[khoa]:,} bản ghi".replace(",", ".")
    return None


@router.get("/activity", response_model=AuditLogResponse)
def admin_activity(
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(
        None,
        description="Lọc theo hành động: create_restaurant | update_restaurant | "
        "hide_restaurant | restore_restaurant",
    ),
):
    """Nhật ký hoạt động quản trị, MỚI NHẤT ĐỨNG ĐẦU.

    Kho nhật ký hỏng -> trả danh sách RỖNG kèm `available: false`, KHÔNG phải 503. Nhật
    ký hỏng không ngăn được người quản trị làm việc, nên không có lý do gì chặn cả trang.
    Giao diện dùng `available` để nói đúng "chưa ghi gì" hay "không mở được kho".
    """
    entries = container.doc_nhat_ky.execute(limit=limit, action=action)
    kho = getattr(container, "audit_log", None)
    return success(
        {
            "entries": [e.to_public() for e in entries],
            "total": len(entries),
            "available": bool(kho is not None and getattr(kho, "is_ready", False)),
        }
    )


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
    refresh: bool = Query(False, description="Bỏ qua bộ đệm, tính lại ngay"),
):
    """Số liệu màn "Tổng quan" — đếm quán/món, độ phủ dữ liệu, việc cần xử lý.

    Có bộ đệm 5 phút ở use case; `?refresh=true` để tính lại ngay sau khi vừa sửa dữ liệu.

    ⚠️ Router MỎNG, không tính toán gì: mọi quy tắc ("thế nào là đủ thông tin cơ bản")
    nằm ở `domain/services/data_quality.py`.
    """
    tong_quan = container.admin_overview.execute(bo_qua_dem=refresh)
    return success(
        {
            "restaurants_total": tong_quan.quan.tong,
            "restaurants_visible": tong_quan.quan.dang_hien,
            "restaurants_hidden": tong_quan.quan.da_an,
            "dishes_total": tong_quan.mon.tong,
            "dishes_with_restaurants": tong_quan.mon.co_quan,
            "dishes_without_restaurants": tong_quan.mon.chua_co_quan,
            "interactions_total": tong_quan.so_tuong_tac,
            "data_quality": [
                {
                    "key": x.khoa,
                    "label": x.nhan,
                    "description": x.mo_ta,
                    "covered": x.so_co,
                    "total": x.tong,
                    "percent": x.phan_tram,
                    "level": x.muc,
                }
                for x in tong_quan.do_phu
            ],
            "by_source": [
                {"source": x.nguon, "count": x.so_luong, "percent": x.phan_tram}
                for x in tong_quan.nguon
            ],
            "needs_attention": [
                {
                    "key": x.khoa,
                    "label": x.nhan,
                    "description": x.mo_ta,
                    "count": x.so_luong,
                    "severity": x.muc_do,
                }
                for x in tong_quan.can_xu_ly
            ],
            "needs_attention_total": tong_quan.tong_can_xu_ly,
            # Đổi sang chuỗi ISO Ở ĐÂY, không phải ở use case: định dạng ngày giờ là việc
            # của tầng trình bày.
            "generated_at": datetime.fromtimestamp(
                tong_quan.tinh_luc, tz=timezone.utc
            ).isoformat(),
        }
    )


@router.get("/restaurants", response_model=AdminRestaurantListResponse)
def list_restaurants(
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
    q: Optional[str] = Query(None, description="Lọc theo tên, địa chỉ hoặc placeId"),
    limit: int = Query(50, ge=1, le=200),
    include_hidden: bool = Query(True, description="Có kèm quán đã ẩn hay không"),
):
    """Danh sách quán cho trang quản trị.

    MẶC ĐỊNH có cả quán đã ẩn — khác với `/search` của người dùng cuối. Không có nó thì
    ẩn xong sẽ không còn cách nào tìm lại để bỏ ẩn.
    """
    _require_writable(container)
    results = container.list_restaurants_for_admin.execute(
        query=q, limit=limit, include_hidden=include_hidden
    )
    return success(
        {
            "total": len(results),
            "results": [_to_summary(r).model_dump() for r in results],
        }
    )


@router.post("/restaurants", response_model=AdminRestaurantResponse, status_code=201)
def create_restaurant(
    payload: AdminCreateRestaurantRequest = Body(...),
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
):
    """Thêm một quán hoàn toàn mới.

    201 CREATED chứ không phải 200: có tài nguyên mới được tạo ra.
    `place_id` do SERVER sinh với tiền tố `manual:` — nhìn mã là biết quán này do người
    gõ vào chứ không phải từ Google/OSM/Overture. Client KHÔNG được tự đặt mã.

    Toạ độ ngoài Hà Nội -> 400 (phạm vi dự án chốt 2026-08-19).
    """
    _require_writable(container)
    created = container.create_restaurant.execute(payload.model_dump(exclude_unset=True))
    # Ghi nhật ký SAU KHI thao tác đã thành công. Ghi trước sẽ để lại dòng "đã thêm quán"
    # cho một quán không bao giờ được tạo, nếu bước tạo ném lỗi.
    container.ghi_nhat_ky.ghi(
        actor=_admin,
        action="create_restaurant",
        target_type="restaurant",
        target_id=created.place_id or "",
        summary=f'Thêm quán "{created.name}"',
    )
    return success(_to_summary(created).model_dump(), status_code=201)


@router.patch("/restaurants/{restaurant_id}", response_model=AdminRestaurantResponse)
def update_restaurant(
    restaurant_id: str,
    payload: AdminUpdateRestaurantRequest = Body(...),
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
):
    """Sửa các trường mô tả của một quán.

    `exclude_unset=True`: chỉ gửi trường nào thì sửa trường đó. Nhờ vậy client phân biệt
    được "không đụng tới trường này" với "xoá giá trị của trường này" (gửi `null`).
    """
    _require_writable(container)
    changes = payload.model_dump(exclude_unset=True)
    # Chụp giá trị TRƯỚC KHI sửa để tóm tắt được "cũ -> mới". Chỉ đọc đúng những trường
    # sắp bị đụng tới, không chép cả bản ghi — xem `domain/entities/audit_log.py`.
    truoc = container.list_restaurants_for_admin.execute(query=restaurant_id, limit=1)
    cu = (
        {k: getattr(truoc[0], k, None) for k in changes}
        if truoc and truoc[0].place_id == restaurant_id
        else {}
    )
    updated = container.update_restaurant.execute(restaurant_id, changes)
    container.ghi_nhat_ky.ghi(
        actor=_admin,
        action="update_restaurant",
        target_type="restaurant",
        target_id=restaurant_id,
        summary=f'{updated.name} — {tom_tat_thay_doi(cu, changes)}',
    )
    return success(_to_summary(updated).model_dump())


@router.post("/restaurants/{restaurant_id}/hide", response_model=AdminRestaurantResponse)
def hide_restaurant(
    restaurant_id: str,
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
):
    """Ẩn quán (soft-delete). Dữ liệu KHÔNG bị xoá, chỉ biến mất khỏi luồng người dùng."""
    _require_writable(container)
    updated = container.set_restaurant_visibility.execute(restaurant_id, is_active=False)
    container.ghi_nhat_ky.ghi(
        actor=_admin,
        action="hide_restaurant",
        target_type="restaurant",
        target_id=restaurant_id,
        summary=f'Ẩn quán "{updated.name}"',
    )
    return success(_to_summary(updated).model_dump())


@router.post("/restaurants/{restaurant_id}/restore", response_model=AdminRestaurantResponse)
def restore_restaurant(
    restaurant_id: str,
    container: Container = Depends(get_container),
    _admin: str = Depends(require_admin),
):
    """Bỏ ẩn quán đã ẩn."""
    _require_writable(container)
    updated = container.set_restaurant_visibility.execute(restaurant_id, is_active=True)
    container.ghi_nhat_ky.ghi(
        actor=_admin,
        action="restore_restaurant",
        target_type="restaurant",
        target_id=restaurant_id,
        summary=f'Khôi phục quán "{updated.name}"',
    )
    return success(_to_summary(updated).model_dump())

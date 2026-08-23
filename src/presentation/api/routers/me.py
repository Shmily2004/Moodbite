"""Router "của tôi" — `/api/v1/me/*`. Quán & món đã lưu · số liệu · cấp độ · huy hiệu.

Chốt của chủ dự án 2026-08-22: làm **quán yêu thích, lượt khám phá, cấp độ, huy hiệu**;
KHÔNG làm review người dùng.

VÌ SAO TÁCH KHỎI `auth.py`: `auth.py` lo việc *trở thành* một người dùng (đăng ký, đăng
nhập, quên mật khẩu). File này lo *dữ liệu của* người dùng đó. Gộp lại thì một file phải
biết cả hai chuyện và sẽ dài ra mãi (CLAUDE.md mục 6: một file một trách nhiệm).

MỌI endpoint ở đây đều BẮT BUỘC đăng nhập qua `get_current_user`. Không có endpoint nào
nhận `user_id` từ client — id luôn lấy từ token, nếu không thì ai cũng đọc và sửa được
danh sách yêu thích của người khác chỉ bằng cách đổi một con số trong URL.

Router MỎNG: không có công thức tính điểm nào ở đây; nó nằm ở `domain/services/gamification.py`.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.application.use_cases.get_user_stats import UserStats
from src.application.use_cases.manage_favorites import SaveFavoriteCommand
from src.domain.entities.user import User
from src.presentation.api.dependencies import Container, get_container, get_current_user
from src.presentation.api.envelope import success
from src.presentation.api.schemas import (
    ERROR_RESPONSES,
    FavoritesResponse,
    MessageResponse,
    SaveFavoriteRequest,
    SavedItemResponse,
    UserStatsResponse,
)

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/favorites", response_model=FavoritesResponse, responses=ERROR_RESPONSES)
def list_favorites(
    item_type: Optional[str] = Query(
        default=None, description="Lọc theo loại: restaurant | dish. Bỏ trống = cả hai."
    ),
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """Danh sách quán & món đã lưu của chính chủ, MỚI NHẤT ĐỨNG ĐẦU."""
    items = container.list_favorites.execute(user.user_id, item_type)
    return success({"items": [i.to_public() for i in items], "total": len(items)})


@router.post(
    "/favorites", response_model=SavedItemResponse, status_code=201,
    responses=ERROR_RESPONSES,
)
def save_favorite(
    body: SaveFavoriteRequest,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """Lưu một quán hoặc một món.

    Lưu lại thứ đã lưu KHÔNG phải lỗi — chỉ cập nhật tên và giữ nguyên thứ tự. Người dùng
    bấm tim hai lần vì mạng chậm không đáng nhận một thông báo lỗi.
    """
    item = container.save_favorite.execute(
        SaveFavoriteCommand(
            user_id=user.user_id,
            item_type=body.item_type,
            item_id=body.item_id,
            name=body.name,
        )
    )
    return success(item.to_public(), status_code=201)


@router.delete(
    "/favorites/{item_type}/{item_id}", response_model=MessageResponse,
    responses=ERROR_RESPONSES,
)
def remove_favorite(
    item_type: str,
    item_id: str,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """Bỏ lưu.

    Bỏ thứ vốn không có trong danh sách vẫn trả 200. Đây là thao tác ĐƯA VỀ TRẠNG THÁI
    MONG MUỐN ("tôi không muốn lưu cái này nữa") — kết quả cuối cùng giống hệt nhau, nên
    404 chỉ làm client phải viết thêm nhánh xử lý cho một tình huống vô hại.
    """
    da_xoa = container.remove_favorite.execute(user.user_id, item_type, item_id)
    return success(
        {"message": "Đã bỏ lưu." if da_xoa else "Mục này vốn không có trong danh sách."}
    )


def _stats_payload(stats: UserStats) -> dict:
    """Đổi kết quả use case sang hình dạng JSON. Thuần trình bày, không có luật nghiệp vụ."""
    tien_do = stats.level
    return {
        "saved_restaurants": stats.saved_restaurants,
        "saved_dishes": stats.saved_dishes,
        "viewed_restaurants": stats.activity.viewed_restaurants,
        "explorations": stats.activity.explorations,
        "directions": stats.activity.directions,
        "ratings": stats.activity.ratings,
        "closure_reports": stats.activity.closure_reports,
        "active_days": stats.activity.active_days,
        "points": stats.activity.points,
        "level": {
            "current": {
                "number": tien_do.level.number,
                "name": tien_do.level.name,
                "min_points": tien_do.level.min_points,
            },
            "next": (
                {
                    "number": tien_do.next_level.number,
                    "name": tien_do.next_level.name,
                    "min_points": tien_do.next_level.min_points,
                }
                if tien_do.next_level
                else None
            ),
            "points": tien_do.points,
            "points_to_next": tien_do.points_to_next,
            "ratio": round(tien_do.ratio, 4),
        },
        "badges": [
            {
                "badge_id": b.rule.badge_id,
                "name": b.rule.name,
                "description": b.rule.description,
                "emoji": b.rule.emoji,
                "target": b.rule.target,
                "current": b.current,
                "earned": b.earned,
            }
            for b in stats.badges
        ],
    }


@router.get("/stats", response_model=UserStatsResponse, responses=ERROR_RESPONSES)
def user_stats(
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """Số liệu hoạt động + cấp độ + huy hiệu của chính chủ.

    Tài khoản mới thì MỌI SỐ ĐỀU LÀ 0 và cấp là 1 — đó là sự thật, và giao diện phải hiện
    đúng như vậy. Bản thiết kế vẽ "320/500 điểm" chỉ là minh hoạ.
    """
    return success(_stats_payload(container.get_user_stats.execute(user.user_id)))

"""Đổi kết quả của use case sang dict JSON — NƠI DUY NHẤT làm việc này.

VÌ SAO CÓ FILE NÀY (bug 2026-08-20): `search.py` và `dishes.py` mỗi bên tự tay liệt kê
lại 20 trường của một kết quả tìm kiếm. Khi backend thêm `temporarily_closed`,
`source_updated_at`, `source_datasets`, `surveyed_at` thì CẢ HAI bên đều quên — schema
có giá trị mặc định nên response vẫn hợp lệ và không ai thấy gì sai, chỉ có điều API trả
`null` cho 97,3% quán vốn CÓ dữ liệu.

Đây đúng là sai lầm "hai nơi cùng mô tả một hợp đồng" mà dự án đã trả giá ở phía backend
(hai server song song) và đã tránh được ở phía frontend (`packages/api-client`). Gộp về
một hàm để lần sau thêm trường chỉ phải sửa MỘT chỗ.

Hai lối vào (`POST /search` và `GET /dishes/{id}/restaurants`) được phép khác nhau về
THỨ TỰ quán, không bao giờ được khác nhau về TRƯỜNG — `tests/test_search_result_contract.py`
khoá điều đó lại.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from src.application.use_cases.search_restaurants import SearchResultItem, SuggestedDish


def suggested_dish_to_dict(dish: Optional[SuggestedDish]) -> Optional[Dict[str, Any]]:
    """Món gợi ý (Lớp 5). `None` = không suy luận được, KHÔNG phải "quán không bán gì"."""
    if dish is None:
        return None
    return {
        "dish_id": dish.dish_id,
        "name": dish.name,
        "cuisine": dish.cuisine,
        "spice_level": dish.spice_level,
        "temperature": dish.temperature,
        # Món là SUY LUẬN từ tên/loại hình quán, chưa bao giờ đọc thực đơn thật, nên
        # `confidence` là trường BẮT BUỘC đi kèm - giao diện phải hiện nó ra chữ.
        "confidence": dish.confidence,
        "reason": dish.reason,
    }


def search_result_to_dict(item: SearchResultItem) -> Dict[str, Any]:
    """Một quán trong danh sách kết quả, đúng `SearchResultItemSchema`."""
    return {
        "restaurant_id": item.restaurant_id,
        "name": item.name,
        "category": item.category,
        "address": item.address,
        "latitude": item.latitude,
        "longitude": item.longitude,
        "distance_m": item.distance_m,
        # Giá là CHUỖI khoảng giá ("100-200 N ₫"), ép về số là làm hỏng response.
        "price_range": item.price_range,
        # `None` = CHƯA CÓ DỮ LIỆU, không phải 0. Giao diện nói "chưa có đánh giá".
        "rating": item.rating,
        "user_ratings_total": item.user_ratings_total,
        "rank_position": item.rank_position,
        "predicted_score": item.predicted_score,
        "match_source": item.match_source,
        "thumbnail_url": item.thumbnail_url,
        "district": item.district,
        "dietary": list(item.dietary),
        "amenities": list(item.amenities),
        "source": item.source,
        "experience_cluster_id": item.experience_cluster_id,
        "experience_cluster_label": item.experience_cluster_label,
        # --- TRẠNG THÁI & TUỔI THẬT: bốn trường từng bị bỏ quên, xem docstring đầu file ---
        # True/False/None là BA trạng thái khác nhau. `None` = nguồn không cho biết.
        "temporarily_closed": item.temporarily_closed,
        # Ngày NGUỒN cập nhật, KHÁC ngày ta cào. Giao diện hiện "cập nhật 3 năm trước".
        "source_updated_at": item.source_updated_at,
        # Nền tảng độc lập cùng ghi nhận quán này - nhiều nền tảng = đáng tin hơn.
        "source_datasets": list(item.source_datasets),
        # Ngày có NGƯỜI đi xác minh tận nơi. Hiếm (0,3%) nhưng là bằng chứng mạnh nhất.
        "surveyed_at": item.surveyed_at,
        "suggested_dish": suggested_dish_to_dict(item.suggested_dish),
    }

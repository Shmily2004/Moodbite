"""Quy tắc nghiệp vụ: một quán NHẬP TAY phải có gì thì mới được vào dataset.

Thuần Python — không import framework, không đụng CSDL.

VÌ SAO TÁCH KHỎI `restaurant_edit.py`: SỬA và THÊM MỚI có luật khác hẳn nhau.
Khi sửa, quán đã tồn tại nên mọi trường đều tuỳ chọn. Khi thêm mới, phải có TÊN và
TOẠ ĐỘ — thiếu một trong hai thì bản ghi vô dụng (CLAUDE.md mục 4: `title`/`lat`/`lng`
là trường thiết yếu). Nhét cả hai luật vào một file sẽ sinh ra một mớ `if dang_tao`.

⚠️ BA ĐIỀU BẮT BUỘC, đều là luật đã chốt của dự án:

  1. CHỈ HÀ NỘI. Phạm vi địa lý chốt 2026-08-19 (CLAUDE.md mục 4b). Toạ độ ngoài hộp bao
     Hà Nội bị từ chối ngay ở đây — không phải ở router, vì mai kia có lệnh nhập hàng loạt
     thì vẫn phải theo đúng luật này.

  2. PHẢI CÓ NGUỒN. "Mọi bản ghi BẮT BUỘC có `source`, `source_url`, `last_updated`,
     `data_confidence`" (CLAUDE.md mục 4b). Quán nhập tay có nguồn là `manual`, và
     `source_url` là chỗ người nhập ghi lại mình lấy thông tin ở đâu (trang chủ quán,
     bài báo, hay "đi qua thấy tận mắt").

  3. KHÔNG BỊA. Rating, số review, điểm mood đều KHÔNG nhận từ form. Chúng do nguồn thu
     thập hoặc do pipeline tính; gõ tay vào là làm sai lệch chính những con số dùng để
     xếp hạng.
"""
from __future__ import annotations

import unicodedata
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

# Hộp bao Hà Nội — CÙNG giá trị với `CITY_BBOXES['ha_noi']` và `HANOI_BBOX` bên
# data_pipeline. Ba chỗ phải khớp nhau; đổi thì đổi cả ba.
HANOI_BOUNDS = {"south": 20.85, "west": 105.70, "north": 21.40, "east": 106.05}

MAX_NAME_LENGTH = 200
MAX_FIELD_LENGTH = 500

# Loại hình mặc định khi người nhập để trống. KHÔNG để `None`: `categoryName` là trường
# thiết yếu và cả bộ chấm điểm mood lẫn phần suy luận món đều đọc nó.
DEFAULT_CATEGORY = "Nhà hàng"

# Trường tuỳ chọn nhận từ form. Đúng bằng tập trường admin được SỬA — nếu không thì sẽ có
# trường thêm được mà không sửa lại được, hoặc ngược lại.
OPTIONAL_TEXT_FIELDS = (
    "category", "cuisine", "address", "price", "phone", "website", "district",
)


class InvalidNewRestaurant(ValueError):
    """Dữ liệu quán mới không hợp lệ -> HTTP 400 INVALID_REQUEST."""


def _chuoi(raw: Any, ten: str) -> Optional[str]:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise InvalidNewRestaurant(
            f"Trường '{ten}' phải là chuỗi, nhận được {type(raw).__name__}. "
            'Riêng "price" là chuỗi khoảng giá kiểu "1-100.000 ₫", không phải số.'
        )
    text = raw.strip()
    if not text:
        return None
    if len(text) > MAX_FIELD_LENGTH:
        raise InvalidNewRestaurant(
            f"Trường '{ten}' dài quá {MAX_FIELD_LENGTH} ký tự."
        )
    return text


def _toa_do(raw: Any, ten: str, thap: float, cao: float) -> float:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise InvalidNewRestaurant(f"Thiếu '{ten}'. Quán không có toạ độ thì vô dụng.")
    try:
        gia_tri = float(raw)
    except (TypeError, ValueError):
        raise InvalidNewRestaurant(f"'{ten}' phải là số thập phân, ví dụ 21.0285.")
    if not (thap <= gia_tri <= cao):
        raise InvalidNewRestaurant(
            f"'{ten}' = {gia_tri} nằm ngoài Hà Nội (hợp lệ: {thap}..{cao}). "
            "Phạm vi dự án chỉ có Hà Nội — muốn mở rộng phải bàn lại trước."
        )
    return gia_tri


def _ma_quan(ten: str) -> str:
    """Sinh `place_id` cho quán nhập tay.

    Tiền tố `manual:` để chỉ NHÌN mã là biết quán này do người gõ vào, không phải từ
    Google/OSM/Overture — quan trọng khi truy nguyên dữ liệu sai. Kèm phần tên đã bỏ dấu
    cho dễ đọc, và một mã ngẫu nhiên ngắn để hai quán trùng tên không đụng nhau.
    """
    khong_dau = "".join(
        c for c in unicodedata.normalize("NFD", ten.lower())
        if unicodedata.category(c) != "Mn"
    )
    goc = "".join(c if c.isalnum() else "-" for c in khong_dau).strip("-")
    goc = "-".join(p for p in goc.split("-") if p)[:40] or "quan"
    return f"manual:{goc}-{uuid.uuid4().hex[:8]}"


@dataclass(frozen=True)
class NewRestaurant:
    """Quán mới ĐÃ được kiểm tra, sẵn sàng ghi xuống kho."""

    place_id: str
    name: str
    lat: float
    lng: float
    fields: Mapping[str, Any]

    @staticmethod
    def from_dict(raw: Mapping[str, Any]) -> "NewRestaurant":
        ten = _chuoi(raw.get("name"), "name")
        if not ten:
            raise InvalidNewRestaurant("Thiếu 'name'. Quán phải có tên.")
        if len(ten) > MAX_NAME_LENGTH:
            raise InvalidNewRestaurant(f"Tên dài quá {MAX_NAME_LENGTH} ký tự.")

        lat = _toa_do(raw.get("lat"), "lat", HANOI_BOUNDS["south"], HANOI_BOUNDS["north"])
        lng = _toa_do(raw.get("lng"), "lng", HANOI_BOUNDS["west"], HANOI_BOUNDS["east"])

        fields: Dict[str, Any] = {}
        for ten_truong in OPTIONAL_TEXT_FIELDS:
            gia_tri = _chuoi(raw.get(ten_truong), ten_truong)
            if gia_tri is not None:
                fields[ten_truong] = gia_tri
        fields.setdefault("category", DEFAULT_CATEGORY)

        return NewRestaurant(
            place_id=_ma_quan(ten), name=ten, lat=lat, lng=lng, fields=fields
        )


__all__ = [
    "NewRestaurant",
    "InvalidNewRestaurant",
    "HANOI_BOUNDS",
    "DEFAULT_CATEGORY",
    "OPTIONAL_TEXT_FIELDS",
    "MAX_NAME_LENGTH",
]

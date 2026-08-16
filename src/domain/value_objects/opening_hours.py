"""Giờ mở cửa - phân tích và kiểm tra "quán này giờ có mở không".

Thuần Python - KHÔNG import pandas/fastapi.

PHẢI XỬ LÝ HAI ĐỊNH DẠNG vì dataset trộn hai nguồn:

  1. Google/Apify - danh sách theo thứ, tiếng Việt:
         [{'day': 'Thứ Hai', 'hours': '07:00 to 23:00'},
          {'day': 'Chủ Nhật', 'hours': 'Mở cửa cả ngày'}]
  2. OpenStreetMap - chuỗi chuẩn OSM:
         "Mo-Su 06:00-22:00"  |  "24/7"  |  "Mo-Fr 09:00-17:00; Sa 09:00-12:00"

NGUYÊN TẮC QUAN TRỌNG: không phân tích được -> trả None, và tầng gọi phải coi đó là
"KHÔNG BIẾT", KHÔNG phải "đóng cửa". Chỉ ~25% quán có dữ liệu giờ; loại bỏ quán chỉ vì
thiếu dữ liệu sẽ xoá sổ 3/4 dataset vì lý do thu thập, không phải vì quán không phù hợp.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

MINUTES_PER_DAY = 24 * 60

# Thứ trong tuần: 0 = Thứ Hai ... 6 = Chủ Nhật (khớp datetime.weekday()).
VIETNAMESE_DAYS = {
    "thứ hai": 0, "thứ 2": 0,
    "thứ ba": 1, "thứ 3": 1,
    "thứ tư": 2, "thứ 4": 2,
    "thứ năm": 3, "thứ 5": 3,
    "thứ sáu": 4, "thứ 6": 4,
    "thứ bảy": 5, "thứ 7": 5,
    "chủ nhật": 6, "cn": 6,
}

OSM_DAYS = {"mo": 0, "tu": 1, "we": 2, "th": 3, "fr": 4, "sa": 5, "su": 6}

# Các cách viết "mở cả ngày" gặp trong dữ liệu thật.
ALL_DAY_MARKERS = ("mở cửa cả ngày", "open 24 hours", "24/7", "24 giờ", "cả ngày")
CLOSED_MARKERS = ("đóng cửa", "closed", "nghỉ")

_TIME_RANGE = re.compile(
    r"(\d{1,2})[:h](\d{2})\s*(?:to|-|–|—|đến)\s*(\d{1,2})[:h](\d{2})", re.IGNORECASE
)

Interval = Tuple[int, int]  # (phút bắt đầu, phút kết thúc) trong ngày


@dataclass(frozen=True)
class WeeklySchedule:
    """Lịch mở cửa theo tuần. `intervals[weekday]` = các khoảng mở trong ngày đó."""

    intervals: Dict[int, List[Interval]] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not any(self.intervals.values())

    def is_open_at(self, weekday: int, minute_of_day: int) -> bool:
        """Ngày `weekday` (0=Thứ Hai), phút thứ `minute_of_day` trong ngày, quán có mở không."""
        for start, end in self.intervals.get(weekday, []):
            if start <= minute_of_day < end:
                return True

        # Khung giờ qua đêm (VD 18:00-02:00) được lưu ở NGÀY HÔM TRƯỚC dưới dạng
        # khoảng vượt quá 24h. Phải kiểm tra thêm ngày liền trước.
        previous_day = (weekday - 1) % 7
        for start, end in self.intervals.get(previous_day, []):
            if end > MINUTES_PER_DAY and minute_of_day < (end - MINUTES_PER_DAY):
                return True
        return False


def _to_minutes(hour: int, minute: int) -> int:
    return hour * 60 + minute


def _parse_hours_text(text: str) -> Optional[List[Interval]]:
    """Chuỗi giờ của MỘT ngày -> danh sách khoảng. None = không hiểu được."""
    lowered = text.strip().lower()
    if not lowered:
        return None
    if any(marker in lowered for marker in CLOSED_MARKERS):
        return []
    if any(marker in lowered for marker in ALL_DAY_MARKERS):
        return [(0, MINUTES_PER_DAY)]

    intervals: List[Interval] = []
    for match in _TIME_RANGE.finditer(lowered):
        start_hour, start_min, end_hour, end_min = (int(g) for g in match.groups())
        start = _to_minutes(start_hour, start_min)
        end = _to_minutes(end_hour, end_min)
        if end <= start:
            # Qua đêm: 18:00-02:00 -> lưu thành 1080 - 1560 (vượt mốc 24h) để
            # `is_open_at` biết khoảng này lấn sang ngày hôm sau.
            end += MINUTES_PER_DAY
        intervals.append((start, end))

    return intervals or None


def _parse_google(raw: List[dict]) -> Optional[WeeklySchedule]:
    intervals: Dict[int, List[Interval]] = {}
    understood = False
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        day_name = str(entry.get("day", "")).strip().lower()
        weekday = VIETNAMESE_DAYS.get(day_name)
        if weekday is None:
            continue
        parsed = _parse_hours_text(str(entry.get("hours", "")))
        if parsed is None:
            continue
        understood = True
        intervals.setdefault(weekday, []).extend(parsed)
    return WeeklySchedule(intervals) if understood else None


def _expand_osm_days(token: str) -> List[int]:
    """"Mo-Fr" -> [0,1,2,3,4];  "Sa,Su" -> [5,6];  "Mo" -> [0]."""
    days: List[int] = []
    for part in token.split(","):
        part = part.strip().lower()
        if "-" in part:
            start_name, _, end_name = part.partition("-")
            start = OSM_DAYS.get(start_name.strip())
            end = OSM_DAYS.get(end_name.strip())
            if start is None or end is None:
                continue
            current = start
            while True:
                days.append(current)
                if current == end:
                    break
                current = (current + 1) % 7
        elif part in OSM_DAYS:
            days.append(OSM_DAYS[part])
    return days


def _parse_osm(raw: str) -> Optional[WeeklySchedule]:
    lowered = raw.strip().lower()
    if not lowered:
        return None
    if "24/7" in lowered:
        return WeeklySchedule({d: [(0, MINUTES_PER_DAY)] for d in range(7)})

    intervals: Dict[int, List[Interval]] = {}
    understood = False
    for rule in lowered.split(";"):
        rule = rule.strip()
        if not rule:
            continue
        # Tách phần ngày (đầu) khỏi phần giờ (có chứa chữ số và dấu hai chấm).
        match = re.match(r"^([a-z,\-\s]+)\s+(.*)$", rule)
        if not match:
            continue
        day_token, hours_token = match.group(1), match.group(2)
        days = _expand_osm_days(day_token)
        parsed = _parse_hours_text(hours_token)
        if not days or parsed is None:
            continue
        understood = True
        for day in days:
            intervals.setdefault(day, []).extend(parsed)

    return WeeklySchedule(intervals) if understood else None


def parse_opening_hours(value: Any) -> Optional[WeeklySchedule]:
    """Phân tích giờ mở cửa từ BẤT KỲ định dạng nào đang có trong dataset.

    Trả None nghĩa là KHÔNG BIẾT (thiếu dữ liệu hoặc không hiểu định dạng) - tuyệt đối
    không được hiểu thành "quán đóng cửa".
    """
    if value is None:
        return None

    if isinstance(value, list):
        return _parse_google(value)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        # Cột CSV lưu list Python dưới dạng chuỗi -> thử khôi phục trước.
        if text.startswith("["):
            try:
                parsed = ast.literal_eval(text)
            except (ValueError, SyntaxError):
                return None
            return _parse_google(parsed) if isinstance(parsed, list) else None
        return _parse_osm(text)

    return None

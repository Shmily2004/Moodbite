"""Tín hiệu ngữ cảnh THỜI ĐIỂM (Lớp 4 của đề án: thời tiết, giờ trong ngày).

Thuần Python - KHÔNG import requests/fastapi. Việc GỌI API thời tiết là việc của
infrastructure; ở đây chỉ định nghĩa tín hiệu đó có ý nghĩa gì với việc xếp hạng.

Đề án nói: "cùng một quán có thể phù hợp vào lúc trời nắng nhưng không phù hợp vào lúc
trời mưa". Đây là nơi mã hoá điều đó.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class MealTime(str, Enum):
    """Bữa ăn suy ra từ giờ địa phương."""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    AFTERNOON = "afternoon"
    DINNER = "dinner"
    LATE_NIGHT = "late_night"

    @staticmethod
    def from_hour(hour: int) -> "MealTime":
        if 5 <= hour < 10:
            return MealTime.BREAKFAST
        if 10 <= hour < 14:
            return MealTime.LUNCH
        if 14 <= hour < 17:
            return MealTime.AFTERNOON
        if 17 <= hour < 22:
            return MealTime.DINNER
        return MealTime.LATE_NIGHT


class WeatherCondition(str, Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ContextSignal:
    """Ngữ cảnh tại thời điểm tìm kiếm. Mọi trường đều có thể thiếu -> khi đó tín hiệu
    tương ứng bị BỎ QUA chứ không bị coi là điểm xấu."""

    meal_time: Optional[MealTime] = None
    is_weekend: bool = False
    weather: WeatherCondition = WeatherCondition.UNKNOWN
    temperature_c: Optional[float] = None
    # Thời điểm hiện tại theo giờ Việt Nam, dùng để lọc "quán đang mở".
    # Đặt ở đây thay vì gọi datetime.now() trong domain: domain phải THUẦN và tất định,
    # nếu tự đọc đồng hồ thì test không thể cố định thời gian được.
    weekday: Optional[int] = None          # 0 = Thứ Hai ... 6 = Chủ Nhật
    minute_of_day: Optional[int] = None    # 0..1439

    @property
    def is_available(self) -> bool:
        return self.meal_time is not None or self.weather != WeatherCondition.UNKNOWN

    def mood_bias(self) -> Dict[str, float]:
        """Ngữ cảnh đẩy nhẹ trọng số của các cột mood-score.

        CỐ Ý để giá trị nhỏ (<= 0.4): ngữ cảnh chỉ là tín hiệu PHỤ, không được lấn át
        điều người dùng thực sự gõ vào ô tìm kiếm.
        """
        bias: Dict[str, float] = {}

        # Trời mưa / lạnh -> ưu tiên món nóng, ấm bụng, ngồi trong nhà.
        if self.weather == WeatherCondition.RAIN:
            bias["comfort_cozy_score"] = bias.get("comfort_cozy_score", 0.0) + 0.4
            bias["spicy_hot_score"] = bias.get("spicy_hot_score", 0.0) + 0.2
        if self.temperature_c is not None:
            if self.temperature_c <= 20:
                bias["comfort_cozy_score"] = bias.get("comfort_cozy_score", 0.0) + 0.3
                bias["spicy_hot_score"] = bias.get("spicy_hot_score", 0.0) + 0.2
            elif self.temperature_c >= 32:
                # Nắng nóng -> đồ mát, nhẹ.
                bias["fresh_healthy_score"] = bias.get("fresh_healthy_score", 0.0) + 0.4
                bias["spicy_hot_score"] = bias.get("spicy_hot_score", 0.0) - 0.2

        # Sáng và trưa đi làm -> ưu tiên nhanh, rẻ. Tối/cuối tuần -> ngồi lâu, ấm cúng.
        if self.meal_time == MealTime.BREAKFAST:
            bias["quick_fast_score"] = bias.get("quick_fast_score", 0.0) + 0.3
            bias["cheap_budget_score"] = bias.get("cheap_budget_score", 0.0) + 0.2
        elif self.meal_time == MealTime.LUNCH and not self.is_weekend:
            bias["quick_fast_score"] = bias.get("quick_fast_score", 0.0) + 0.3
        elif self.meal_time in (MealTime.DINNER, MealTime.LATE_NIGHT):
            bias["comfort_cozy_score"] = bias.get("comfort_cozy_score", 0.0) + 0.2

        return bias

    def describe(self) -> list[str]:
        """Mô tả ngắn để trả về cho client - người dùng thấy được VÌ SAO kết quả đổi."""
        parts: list[str] = []
        if self.meal_time:
            labels = {
                MealTime.BREAKFAST: "buổi sáng",
                MealTime.LUNCH: "buổi trưa",
                MealTime.AFTERNOON: "buổi chiều",
                MealTime.DINNER: "buổi tối",
                MealTime.LATE_NIGHT: "đêm khuya",
            }
            parts.append(labels[self.meal_time])
        if self.weather == WeatherCondition.RAIN:
            parts.append("trời mưa")
        elif self.weather == WeatherCondition.CLEAR:
            parts.append("trời quang")
        if self.temperature_c is not None:
            parts.append(f"{round(self.temperature_c)}°C")
        return parts


NEUTRAL_CONTEXT = ContextSignal()

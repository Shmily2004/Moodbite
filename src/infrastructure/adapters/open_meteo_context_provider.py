"""ADAPTER: tín hiệu ngữ cảnh thời điểm (giờ địa phương + thời tiết).

Thời tiết lấy từ Open-Meteo: MIỄN PHÍ, KHÔNG cần API key, không cần đăng ký.
Chọn nguồn này thay vì OpenWeatherMap/Google vì đề án cần tín hiệu thời tiết nhưng dự án
không nên phát sinh chi phí hay phải quản lý thêm một API key nữa.

NGUYÊN TẮC: mạng hỏng, API chậm, trả dữ liệu lạ -> trả ngữ cảnh TRUNG LẬP, tuyệt đối
không ném lỗi ra ngoài. Người dùng vẫn phải tìm được quán kể cả khi không biết trời mưa hay nắng.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.domain.value_objects.context_signal import (
    NEUTRAL_CONTEXT,
    ContextSignal,
    MealTime,
    WeatherCondition,
)
from src.domain.value_objects.location import Location

logger = logging.getLogger("moodbite.context")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Giờ Việt Nam. Server có thể chạy ở múi giờ khác (Railway/Heroku thường là UTC), nên
# KHÔNG được dùng giờ hệ thống để suy ra bữa ăn.
VIETNAM_TZ = timezone(timedelta(hours=7))

# Mã thời tiết WMO của Open-Meteo. Chỉ cần phân biệt 3 nhóm cho việc xếp hạng.
_CLEAR_CODES = {0, 1}
_CLOUDY_CODES = {2, 3, 45, 48}


class OpenMeteoContextProvider:
    """Triển khai ContextProvider. `enable_weather=False` -> chỉ dùng giờ, không gọi mạng."""

    def __init__(self, enable_weather: bool = True, timeout_seconds: float = 2.0) -> None:
        self.enable_weather = enable_weather
        self.timeout_seconds = timeout_seconds
        self._last_error: Optional[str] = None

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def get_context(self, location: Location) -> ContextSignal:
        now = datetime.now(VIETNAM_TZ)
        meal_time = MealTime.from_hour(now.hour)
        is_weekend = now.weekday() >= 5

        weather, temperature = WeatherCondition.UNKNOWN, None
        if self.enable_weather:
            weather, temperature = self._fetch_weather(location)

        return ContextSignal(
            meal_time=meal_time,
            is_weekend=is_weekend,
            weather=weather,
            temperature_c=temperature,
            weekday=now.weekday(),
            minute_of_day=now.hour * 60 + now.minute,
        )

    def _fetch_weather(
        self, location: Location
    ) -> tuple[WeatherCondition, Optional[float]]:
        try:
            import requests

            response = requests.get(
                OPEN_METEO_URL,
                params={
                    "latitude": round(location.lat, 3),
                    "longitude": round(location.lng, 3),
                    "current": "temperature_2m,weather_code",
                    "timezone": "Asia/Bangkok",
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            current = response.json().get("current", {})
            code = current.get("weather_code")
            temperature = current.get("temperature_2m")
            self._last_error = None
            return self._to_condition(code), (
                float(temperature) if temperature is not None else None
            )
        except Exception as exc:
            # Ghi log ở mức debug: thời tiết hỏng là chuyện thường và không đáng báo động,
            # vì hệ thống vẫn chạy đúng khi thiếu tín hiệu này.
            self._last_error = str(exc)
            logger.debug("Không lấy được thời tiết, dùng ngữ cảnh trung lập: %s", exc)
            return WeatherCondition.UNKNOWN, None

    @staticmethod
    def _to_condition(code: Optional[int]) -> WeatherCondition:
        if code is None:
            return WeatherCondition.UNKNOWN
        if code in _CLEAR_CODES:
            return WeatherCondition.CLEAR
        if code in _CLOUDY_CODES:
            return WeatherCondition.CLOUDY
        return WeatherCondition.RAIN

    def status(self) -> dict:
        return {
            "weather_enabled": self.enable_weather,
            "source": "open-meteo (miễn phí, không cần key)" if self.enable_weather else None,
            "error": self._last_error,
        }


class ClockOnlyContextProvider:
    """Chỉ dùng giờ, không gọi mạng. Dùng trong test và khi tắt thời tiết."""

    def get_context(self, location: Location) -> ContextSignal:
        now = datetime.now(VIETNAM_TZ)
        return ContextSignal(
            meal_time=MealTime.from_hour(now.hour),
            is_weekend=now.weekday() >= 5,
            weekday=now.weekday(),
            minute_of_day=now.hour * 60 + now.minute,
        )

    def status(self) -> dict:
        return {"weather_enabled": False, "source": "clock only", "error": None}


__all__ = ["OpenMeteoContextProvider", "ClockOnlyContextProvider", "NEUTRAL_CONTEXT"]

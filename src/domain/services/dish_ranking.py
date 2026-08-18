"""Chấm điểm và xếp hạng MÓN ĂN theo bộ lọc + ngữ cảnh.

Đây là quy tắc nghiệp vụ của luồng mới "chọn món trước, tìm quán sau", nên nó nằm ở
`domain/` - THUẦN PYTHON, không import fastapi/pandas/sklearn. Muốn đổi cách xếp hạng
món thì sửa DUY NHẤT ở file này.

Song song với `search_ranking.py` (xếp hạng QUÁN) chứ không thay thế nó: hai thứ xếp hạng
hai loại thực thể khác nhau, trộn chung sẽ thành một hàm 400 dòng không ai đọc nổi.

HAI TẦNG, ĐỪNG LẪN:
  1. `filter_dishes`  - ràng buộc CỨNG. Người dùng bấm "đồ nướng" thì phở phải biến mất.
  2. `rank_dishes`    - xếp hạng MỀM trong số món còn lại.

Quy tắc xuyên suốt dự án, áp dụng lại ở đây: THIẾU DỮ LIỆU KHÔNG BỊ LOẠI. Món chưa
điền `cooking_method` vẫn qua được bộ lọc "đồ nướng" - vì chưa biết KHÁC HẲN với biết là
không phải. Loại chúng đi là trừng phạt món chỉ vì ta chưa nhập đủ dữ liệu.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional

from src.domain.entities.dish import (
    METHOD_GRILLED,
    METHOD_RAW,
    METHOD_SOUP,
    Dish,
)
from src.domain.value_objects.context_signal import (
    ContextSignal,
    MealTime,
    WeatherCondition,
)
from src.domain.value_objects.mood import MOOD_TO_DISH_KEYWORDS

# Điểm khi CHƯA BIẾT - dùng lại đúng quy ước Cold Start của rules.md mục 3.3:
# chưa có dữ liệu thì cho điểm trung tính, TUYỆT ĐỐI không cho 0.
# Món chưa nhập cách chế biến không phải là món dở.
NEUTRAL_SCORE = 0.5

# Trọng số xếp hạng. TỔNG PHẢI = 1.0 để `score` luôn nằm trong [0,1] - có test khoá
# (`test_dish_ranking.py::test_weights_sum_to_one`). Đổi số ở đây phải đổi cả test.
#
# Vì sao bộ lọc nặng nhất: người dùng BẤM "đồ nướng" là phát biểu ý định rõ ràng nhất
# mà ta có. Ngữ cảnh (trời mưa) chỉ là suy đoán của hệ thống, phải nhẹ hơn.
W_FILTER = 0.40        # khớp bộ lọc người dùng chủ động chọn
W_CONTEXT = 0.25       # hợp thời tiết + bữa trong ngày
W_MOOD = 0.20          # hợp tâm trạng
W_AVAILABILITY = 0.15  # có bao nhiêu quán bán món này gần đây

# Số quán để coi một món là "dễ tìm". Dùng đường cong bão hoà count/(count+K) thay vì
# chia tuyến tính: chênh lệch 1 quán và 6 quán mới đáng kể, còn 60 quán và 120 quán thì
# với người dùng là như nhau (đằng nào cũng chỉ xem ~10 quán gần nhất).
AVAILABILITY_SATURATION = 5


@dataclass(frozen=True)
class DishFilter:
    """Bộ lọc người dùng chọn ở trang chủ.

    Mọi field đều rỗng/None = KHÔNG lọc chiều đó. Trang chủ lúc chưa bấm gì sẽ truyền
    một `DishFilter()` trống và vẫn phải ra được danh sách món hợp lệ.
    """

    cooking_methods: List[str] = field(default_factory=list)
    temperatures: List[str] = field(default_factory=list)
    cuisines: List[str] = field(default_factory=list)
    meal_times: List[str] = field(default_factory=list)
    # Cay TỐI ĐA chấp nhận được. 0 = không ăn được cay.
    max_spice_level: Optional[int] = None
    mood: Optional[str] = None
    # Người dùng TỰ khai thời tiết, ghi đè giá trị đo tự động từ Open-Meteo.
    # Có mặt vì đề bài của chủ dự án là người dùng CHỌN "nay trời mưa", chứ không chỉ
    # để hệ thống tự đoán. Tự khai thắng đo tự động - người dùng đang đứng ngoài đường,
    # họ biết rõ hơn API thời tiết.
    weather: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        return not any(
            [
                self.cooking_methods, self.temperatures, self.cuisines,
                self.meal_times, self.mood, self.weather,
                self.max_spice_level is not None,
            ]
        )


@dataclass(frozen=True)
class RankedDish:
    dish: Dish
    rank_position: int
    score: float
    restaurant_count: int
    # Vì sao món này được đề xuất - hiện thẳng lên thẻ món, không giấu trong tooltip.
    reasons: List[str] = field(default_factory=list)


def effective_weather(f: DishFilter, context: ContextSignal) -> WeatherCondition:
    """Thời tiết dùng để xếp hạng: người dùng tự khai THẮNG đo tự động.

    Giá trị lạ (client gửi sai chính tả) -> lui về giá trị đo được, KHÔNG ném lỗi:
    tín hiệu ngữ cảnh hỏng không được làm hỏng lượt tìm kiếm (CLAUDE.md mục 4 quy tắc 7).
    """
    if f.weather:
        try:
            return WeatherCondition(f.weather.strip().lower())
        except ValueError:
            return context.weather
    return context.weather


def filter_dishes(dishes: List[Dish], f: DishFilter) -> List[Dish]:
    """Ràng buộc CỨNG. Món thiếu dữ liệu ở chiều đang lọc thì VẪN GIỮ.

    Lọc xong rỗng thì trả nguyên danh sách vào - thà đề xuất món chưa chắc khớp còn hơn
    đưa người dùng vào màn hình trắng. Cùng nguyên tắc với `_filter_opening_hours` ở
    use case tìm quán.
    """
    kept = [d for d in dishes if _passes_hard_filter(d, f)]
    return kept or dishes


def _passes_hard_filter(dish: Dish, f: DishFilter) -> bool:
    if f.cooking_methods and dish.cooking_method is not None:
        if dish.cooking_method not in f.cooking_methods:
            return False

    if f.temperatures and dish.temperature is not None:
        if dish.temperature not in f.temperatures:
            return False

    if f.cuisines and dish.cuisine is not None:
        # Ẩm thực so khớp KHÔNG PHÂN BIỆT hoa thường: dữ liệu thật có cả "Việt Nam" lẫn
        # "việt nam" do gộp từ nhiều nguồn.
        wanted = {c.strip().lower() for c in f.cuisines}
        if dish.cuisine.strip().lower() not in wanted:
            return False

    if f.meal_times and dish.meal_times:
        if not set(dish.meal_times) & set(f.meal_times):
            return False

    if f.max_spice_level is not None and dish.spice_level is not None:
        if dish.spice_level > f.max_spice_level:
            return False

    return True


def rank_dishes(
    dishes: List[Dish],
    f: DishFilter,
    context: ContextSignal,
    restaurant_counts: Mapping[str, int],
    limit: int = 20,
) -> List[RankedDish]:
    """Xếp hạng món đã qua bộ lọc cứng.

    `restaurant_counts`: dish_id -> số quán bán món đó TRONG BÁN KÍNH người dùng chọn.
    Truyền từ ngoài vào thay vì tự đếm, vì đếm cần kho quán - domain không được biết
    kho quán tồn tại.
    """
    weather = effective_weather(f, context)

    scored: List[RankedDish] = []
    for dish in dishes:
        count = restaurant_counts.get(dish.identifier, 0)
        filter_score, filter_reasons = _score_filter(dish, f)
        context_score, context_reasons = _score_context(dish, weather, context)
        mood_score, mood_reasons = _score_mood(dish, f.mood)

        total = (
            W_FILTER * filter_score
            + W_CONTEXT * context_score
            + W_MOOD * mood_score
            + W_AVAILABILITY * _score_availability(count)
        )

        scored.append(
            RankedDish(
                dish=dish,
                rank_position=0,      # điền sau khi sắp xếp
                score=round(total, 4),
                restaurant_count=count,
                reasons=filter_reasons + context_reasons + mood_reasons,
            )
        )

    # Sắp xếp phụ theo TÊN món để kết quả TẤT ĐỊNH: nhiều món điểm bằng nhau là chuyện
    # thường (cùng thiếu dữ liệu -> cùng điểm trung tính), không chốt thứ tự thì mỗi lần
    # gọi lại ra một thứ tự khác và test sẽ chập chờn.
    scored.sort(key=lambda r: (-r.score, r.dish.name))

    return [
        RankedDish(
            dish=r.dish,
            rank_position=i + 1,
            score=r.score,
            restaurant_count=r.restaurant_count,
            reasons=r.reasons,
        )
        for i, r in enumerate(scored[:limit])
    ]


# --- các thành phần điểm -----------------------------------------------------


def _score_filter(dish: Dish, f: DishFilter) -> tuple[float, List[str]]:
    """Tỷ lệ chiều lọc mà món khớp RÕ RÀNG.

    Ba trạng thái mỗi chiều, đừng gộp: khớp (1.0) · không khớp (0.0) · chưa có dữ liệu
    (NEUTRAL). Gộp "chưa có dữ liệu" vào "không khớp" sẽ đẩy mọi món chưa nhập đủ xuống
    đáy và người dùng không bao giờ thấy chúng để mà sửa.
    """
    if f.is_empty:
        return NEUTRAL_SCORE, []

    parts: List[float] = []
    reasons: List[str] = []

    if f.cooking_methods:
        if dish.cooking_method is None:
            parts.append(NEUTRAL_SCORE)
        elif dish.cooking_method in f.cooking_methods:
            parts.append(1.0)
            reasons.append("đúng cách chế biến bạn chọn")
        else:
            parts.append(0.0)

    if f.temperatures:
        if dish.temperature is None:
            parts.append(NEUTRAL_SCORE)
        elif dish.temperature in f.temperatures:
            parts.append(1.0)
            reasons.append("đúng món nóng/mát bạn chọn")
        else:
            parts.append(0.0)

    if f.cuisines:
        if dish.cuisine is None:
            parts.append(NEUTRAL_SCORE)
        elif dish.cuisine.strip().lower() in {c.strip().lower() for c in f.cuisines}:
            parts.append(1.0)
            reasons.append(f"ẩm thực {dish.cuisine}")
        else:
            parts.append(0.0)

    if f.meal_times:
        if not dish.meal_times:
            parts.append(NEUTRAL_SCORE)
        elif set(dish.meal_times) & set(f.meal_times):
            parts.append(1.0)
            reasons.append("hợp bữa bạn chọn")
        else:
            parts.append(0.0)

    if f.max_spice_level is not None:
        if dish.spice_level is None:
            parts.append(NEUTRAL_SCORE)
        elif dish.spice_level <= f.max_spice_level:
            parts.append(1.0)
        else:
            parts.append(0.0)

    if not parts:
        return NEUTRAL_SCORE, []
    return sum(parts) / len(parts), reasons


def _score_context(
    dish: Dish, weather: WeatherCondition, context: ContextSignal
) -> tuple[float, List[str]]:
    """Hợp thời tiết và bữa trong ngày tới đâu.

    Bắt đầu từ NEUTRAL rồi cộng/trừ, nên món KHÔNG có dữ liệu nhiệt độ/cách chế biến
    giữ nguyên điểm trung tính thay vì bị đẩy về 0.
    """
    score = NEUTRAL_SCORE
    reasons: List[str] = []

    # Trời mưa -> món nóng, món nước. Đây chính là quy tắc đề án nêu ("cùng một quán phù
    # hợp lúc nắng nhưng không phù hợp lúc mưa"), áp cho MÓN thay vì quán.
    if weather == WeatherCondition.RAIN:
        if dish.temperature == "hot":
            score += 0.3
            reasons.append("trời mưa, món nóng ấm bụng")
        elif dish.temperature == "cold":
            score -= 0.25
        if dish.cooking_method == METHOD_SOUP:
            score += 0.2
            reasons.append("món nước hợp trời mưa")
        elif dish.cooking_method == METHOD_RAW:
            score -= 0.2

    # Nắng nóng -> đồ mát, đồ tươi. Ngưỡng 32°C lấy đúng ngưỡng đã dùng ở
    # `ContextSignal.mood_bias()` để hai chỗ không nói hai kiểu.
    if context.temperature_c is not None and context.temperature_c >= 32:
        if dish.temperature == "cold":
            score += 0.3
            reasons.append("trời nắng nóng, món mát")
        elif dish.temperature == "hot":
            score -= 0.15
        if dish.cooking_method == METHOD_GRILLED:
            # Ngồi cạnh bếp than giữa trưa 35°C là cực hình, dù món có ngon.
            score -= 0.1

    meal = _meal_time_key(context.meal_time)
    if meal and dish.meal_times:
        if meal in dish.meal_times:
            score += 0.2
            reasons.append("hợp giờ ăn hiện tại")
        else:
            score -= 0.1

    return _clamp(score), reasons


def _score_mood(dish: Dish, mood: Optional[str]) -> tuple[float, List[str]]:
    """Món có mang tag mood người dùng chọn không.

    Không chọn mood -> trung tính. Chọn mood nhưng món chưa gắn tag nào -> cũng trung
    tính, KHÔNG phải 0: món chưa gắn tag là thiếu dữ liệu, không phải không hợp.
    """
    if not mood:
        return NEUTRAL_SCORE, []

    wanted = MOOD_TO_DISH_KEYWORDS.get(mood.strip().lower())
    if not wanted:
        return NEUTRAL_SCORE, []
    if not dish.mood_keywords:
        return NEUTRAL_SCORE, []

    overlap = set(dish.mood_keywords) & set(wanted)
    if not overlap:
        return 0.2, []
    return 1.0, ["hợp tâm trạng bạn chọn"]


def _score_availability(count: int) -> float:
    """Món có nhiều quán gần đây thì hữu ích hơn.

    CỐ TÌNH cho 0 khi không có quán nào: món không tìm được quán là ngõ cụt với người
    dùng. Đây là NGOẠI LỆ duy nhất của quy tắc "chưa có dữ liệu thì trung tính" - vì
    `count = 0` không phải thiếu dữ liệu, nó là kết quả ĐO ĐƯỢC trên kho quán thật.
    """
    if count <= 0:
        return 0.0
    return count / (count + AVAILABILITY_SATURATION)


def _meal_time_key(meal: Optional[MealTime]) -> Optional[str]:
    """MealTime (ngữ cảnh, tiếng Anh) -> khoá meal_times của món (tiếng Việt không dấu).

    Hai bộ từ vựng khác nhau vì `MealTime` mô tả GIỜ HIỆN TẠI còn `meal_times` của món mô
    tả món đó hợp bữa nào. Ánh xạ ở một chỗ để không rải `if` khắp nơi.
    """
    mapping: Dict[MealTime, str] = {
        MealTime.BREAKFAST: "sang",
        MealTime.LUNCH: "trua",
        MealTime.DINNER: "toi",
        MealTime.LATE_NIGHT: "khuya",
        # AFTERNOON cố tình KHÔNG ánh xạ: buổi chiều không phải một bữa chính, gán ép
        # vào "trưa" hay "tối" đều làm lệch điểm.
    }
    return mapping.get(meal) if meal else None


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

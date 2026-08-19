"""Pydantic schemas = HỢP ĐỒNG API. Đây là nguồn sự thật cho frontend.

QUY ƯỚC TÊN TRƯỜNG: snake_case, theo đặc tả API mục 1.3 - khớp trực tiếp tên cột trong
Data Dictionary để bớt một tầng ánh xạ DTO. Đây là quyết định CÓ CHỦ ĐÍCH, đánh đổi việc
không theo convention camelCase phổ biến của JSON.

Đổi field ở đây là BREAKING CHANGE với frontend - phải sửa frontend/src/services/ cùng lúc.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.domain.entities.dish import COOKING_METHODS, MEAL_TIMES
from src.domain.entities.interaction import ActionType
from src.domain.entities.user import (
    MAX_PASSWORD_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
)
from src.domain.services.search_ranking import DEFAULT_MAX_DISTANCE_KM
from src.domain.value_objects.location import HANOI_CENTER_LAT, HANOI_CENTER_LNG
from src.domain.value_objects.mood import SUPPORTED_MOODS


# --- POST /api/v1/search -----------------------------------------------------

class SearchRequest(BaseModel):
    session_id: str = Field(
        ...,
        description="UUID v4 do client tự sinh và lưu ở localStorage. VẪN BẮT BUỘC dù đã "
                    "có tài khoản (2026-08-17): nó định danh một LƯỢT DÙNG, còn tài khoản "
                    "định danh một NGƯỜI. Việc gắn `user_id` vào tương tác là bước riêng, "
                    "chưa làm.",
    )
    latitude: float = Field(default=HANOI_CENTER_LAT, ge=-90, le=90)
    longitude: float = Field(default=HANOI_CENTER_LNG, ge=-180, le=180)
    query_text: Optional[str] = Field(
        default=None,
        max_length=500,
        description='Nhu cầu bằng câu tự nhiên, VD "quán lẩu ấm cúng gần đây".',
    )
    mood: Optional[str] = Field(
        default=None,
        description=f"Lối tắt tuỳ chọn thay cho query_text. Hợp lệ: {list(SUPPORTED_MOODS)}",
    )
    max_distance_km: Optional[float] = Field(
        default=DEFAULT_MAX_DISTANCE_KM, gt=0, le=100,
        description="null = tắt lọc theo khoảng cách.",
    )
    dietary_restrictions: List[str] = Field(
        default_factory=list,
        description="vegetarian | vegan | halal | kosher | gluten_free. "
                    "Dữ liệu rất thưa - quán chưa khai báo vẫn được giữ lại.",
    )
    opening_hours_constraint: Optional[str] = Field(
        default=None, description='"now" hoặc "HH:mm". Quán chưa có dữ liệu giờ vẫn giữ lại.'
    )
    district: Optional[str] = Field(
        default=None,
        description='Đơn vị hành chính, VD "Phường Cầu Giấy". Không khớp quán nào -> bỏ lọc.',
    )
    limit: int = Field(default=10, ge=1, le=50)


class SuggestedDishSchema(BaseModel):
    dish_id: str
    name: str
    cuisine: Optional[str] = None
    spice_level: Optional[int] = None
    temperature: Optional[str] = None
    # "specific" | "generic_fallback" | "unknown" | "ml" - UI PHẢI hiển thị mức tin cậy
    # này, vì món ăn là SUY LUẬN từ loại hình quán chứ không phải thực đơn thật.
    confidence: str
    reason: Optional[str] = None


class SearchResultItemSchema(BaseModel):
    restaurant_id: Optional[str]
    name: str
    category: Optional[str]
    address: Optional[str]
    latitude: float
    longitude: float
    distance_m: int
    # null = CHƯA CÓ DỮ LIỆU, không phải "miễn phí"/"0 sao".
    # price_range là CHUỖI khoảng giá của Google Maps ("100-200 N ₫"), không phải số.
    price_range: Optional[str]
    rating: Optional[float]
    user_ratings_total: Optional[int]
    rank_position: int
    predicted_score: float
    # Vì sao quán này khớp: review / atmosphere / category / name / mood.
    match_source: str
    thumbnail_url: Optional[str] = Field(
        None, description="Ảnh đại diện. null = chưa có ảnh (78.5% quán)"
    )
    # Đơn vị hành chính. Từ 2025 Việt Nam bỏ cấp quận nên giá trị là "Phường ...".
    district: Optional[str] = None
    dietary: List[str] = []
    amenities: List[str] = []
    # Nguồn gốc dữ liệu - client có thể hiển thị "theo OpenStreetMap" cho minh bạch.
    source: Optional[str] = None
    # Cụm trải nghiệm (Lớp 1 đề án). null = CHƯA phân cụm, KHÔNG phải "cụm kém" -
    # client nên hiện "Đang cập nhật" thay vì để trống hoặc báo lỗi.
    experience_cluster_id: Optional[int] = None
    experience_cluster_label: Optional[str] = None
    suggested_dish: Optional[SuggestedDishSchema] = None


class SearchResponseData(BaseModel):
    search_query_id: str
    results: List[SearchResultItemSchema]
    # Ngữ cảnh đã dùng để xếp hạng (VD ["buổi tối", "trời mưa", "24°C"]).
    context: List[str] = []
    # Điều server KHÔNG làm được với request này - hiện lên UI thay vì im lặng bỏ qua.
    warnings: List[str] = []


# --- POST /api/v1/dishes/suggest ---------------------------------------------
#
# Bước 1 của luồng "chọn món trước, tìm quán sau". Trả về DANH SÁCH MÓN, không phải quán.


class DishSuggestRequest(BaseModel):
    session_id: str = Field(..., description="Giống SearchRequest - định danh một LƯỢT DÙNG.")
    latitude: float = Field(default=HANOI_CENTER_LAT, ge=-90, le=90)
    longitude: float = Field(default=HANOI_CENTER_LNG, ge=-180, le=180)
    cooking_methods: List[str] = Field(
        default_factory=list,
        description=f"Cách chế biến. Hợp lệ: {list(COOKING_METHODS)}. "
                    "Món CHƯA khai cách chế biến vẫn được giữ (chưa biết ≠ không phải).",
    )
    temperatures: List[str] = Field(
        default_factory=list, description='"hot" | "cold" | "room".'
    )
    cuisines: List[str] = Field(
        default_factory=list, description='VD ["Việt Nam", "Nhật Bản"].'
    )
    meal_times: List[str] = Field(
        default_factory=list, description=f"Hợp lệ: {list(MEAL_TIMES)}."
    )
    max_spice_level: Optional[int] = Field(
        default=None, ge=0, le=5, description="Mức cay TỐI ĐA chấp nhận được."
    )
    mood: Optional[str] = Field(
        default=None, description=f"Hợp lệ: {list(SUPPORTED_MOODS)}"
    )
    weather: Optional[str] = Field(
        default=None,
        description='Người dùng TỰ khai ("rain"|"clear"|"cloudy"), ghi đè số đo tự động. '
                    "Người đang đứng ngoài đường biết rõ hơn API thời tiết.",
    )
    max_distance_km: Optional[float] = Field(
        default=DEFAULT_MAX_DISTANCE_KM, gt=0, le=100,
        description="null = tắt lọc khoảng cách. Ảnh hưởng tới `restaurant_count`.",
    )
    limit: int = Field(default=20, ge=1, le=100)


class DishItemSchema(BaseModel):
    dish_id: str
    name: str
    cuisine: Optional[str] = None
    spice_level: Optional[int] = None
    temperature: Optional[str] = None
    cooking_method: Optional[str] = None
    meal_times: List[str] = []
    # GIỚI THIỆU NGẮN - nội dung chính của TRANG CHI TIẾT MÓN.
    # Tách cờ riêng để UI KHÔNG phải đoán từ chuỗi rỗng: rỗng nghĩa là chưa tra được nguồn
    # nào, không phải "món này không có gì để nói".
    has_description: bool = False
    description: Optional[str] = None
    image_url: Optional[str] = None
    # ĐO ĐƯỢC trong bán kính đã chọn, không phải ước lượng.
    restaurant_count: int
    rank_position: int
    score: float
    reasons: List[str] = []
    # Xuất xứ dữ liệu giới thiệu: "manual" | "wikipedia_vi" | "seed_kb" | "admin".
    # Hiện ra để người đọc biết đoạn giới thiệu này ở đâu ra (CLAUDE.md mục 4b).
    source: Optional[str] = None
    source_url: Optional[str] = None
    data_confidence: Optional[str] = None


class DishSuggestResponseData(BaseModel):
    search_query_id: str
    results: List[DishItemSchema]
    context: List[str] = []
    warnings: List[str] = []


class DishSuggestResponse(BaseModel):
    data: DishSuggestResponseData


class DishDetailResponse(BaseModel):
    data: DishItemSchema


# --- GET /api/v1/restaurants/{id} --------------------------------------------

class RestaurantDetailData(BaseModel):
    restaurant_id: str
    has_details: bool
    reason: Optional[str] = None
    name: Optional[str] = None
    price_range: Optional[str] = None
    atmosphere: Optional[object] = None
    opening_hours: Optional[object] = None
    images: List[str] = []
    reviews: List[dict] = []
    menu_url: Optional[str] = None
    website: Optional[str] = None
    google_maps_url: Optional[str] = None
    # LỚP 4 đề án — nhận xét tổng hợp từ review, TÍNH SẴN offline.
    #   {summary: [...], positive: [...], negative: [...], review_count, average_stars,
    #    method: "extractive_tfidf"}
    # `null` = quán chưa đủ review (dưới 3) để tóm tắt, KHÔNG phải "quán không có gì".
    # Mọi câu là TRÍCH NGUYÊN VĂN từ review thật - UI phải nói rõ điều đó.
    review_summary: Optional[dict] = None


# --- POST /api/v1/interactions -----------------------------------------------

class InteractionRequest(BaseModel):
    session_id: str
    restaurant_id: str
    action_type: ActionType
    search_query_id: Optional[str] = None
    dwell_time_ms: Optional[int] = Field(
        default=None, ge=0,
        description="Bắt buộc khi action_type = view_detail.",
    )
    rank_position: Optional[int] = Field(default=None, ge=1)


class InteractionResponseData(BaseModel):
    interaction_event_id: str
    # Chỉ trả để debug. Client KHÔNG được dùng trường này để đổi giao diện -
    # quy tắc phân loại tín hiệu chỉ có một nguồn sự thật là server (đặc tả API mục 3.4).
    is_positive_signal: bool


# --- GET /api/v1/health & /api/v1/moods --------------------------------------

class HealthData(BaseModel):
    status: str
    api_version: str
    services: dict


class MoodsData(BaseModel):
    supported_moods: List[str]
    description: str


# --- Envelope (đặc tả API mục 1.5) -------------------------------------------
#
# VÌ SAO PHẢI KHAI BÁO TƯỜNG MINH: nếu route dùng `response_model=None` và trả
# JSONResponse thô, OpenAPI ghi schema rỗng `{}`. Khi đó `openapi-typescript` không sinh
# được kiểu cho frontend - mất toàn bộ lợi ích của việc dùng TypeScript.
#
# Khai báo các lớp bọc dưới đây để hợp đồng API xuất hiện đầy đủ trong OpenAPI, và
# frontend sinh type tự động từ đó.


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = {}


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class SearchResponse(BaseModel):
    data: SearchResponseData


class RestaurantDetailResponse(BaseModel):
    data: RestaurantDetailData


class InteractionResponse(BaseModel):
    data: InteractionResponseData


class HealthResponse(BaseModel):
    data: HealthData


class MoodsResponse(BaseModel):
    data: MoodsData


# --- Tài khoản người dùng: /api/v1/auth/* -------------------------------------
#
# ⚠️ QUY TẮC ĐẶT TÊN/MẬT KHẨU KHÔNG ĐƯỢC VIẾT LẠI Ở ĐÂY.
# Chúng là quy tắc NGHIỆP VỤ, nằm ở `domain/entities/user.py`, và use case gọi chúng.
# Ở tầng schema chỉ đặt chặn TRÊN về độ dài — mục đích khác hẳn: chặn body khổng lồ
# trước khi nó kịp chạm vào hàm băm PBKDF2 tốn CPU. Hằng số vẫn lấy từ domain để không
# có hai con số cần đồng bộ bằng tay.


class RegisterRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=1,
        max_length=MAX_USERNAME_LENGTH,
        description=(
            f"{MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} ký tự, chỉ chữ thường không dấu "
            "(a-z), số, gạch dưới, gạch ngang. Tự chuẩn hoá về chữ thường."
        ),
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=MAX_PASSWORD_LENGTH,
        description=f"Tối thiểu {MIN_PASSWORD_LENGTH} ký tự. Không bắt buộc hoa/số/ký tự "
                    "đặc biệt — độ dài quan trọng hơn (NIST SP 800-63B).",
    )
    display_name: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Tên hiển thị, ĐƯỢC dùng tiếng Việt có dấu. Không dùng để đăng nhập.",
    )


class LoginRequest(BaseModel):
    # KHÔNG áp `min_length` theo quy tắc domain ở đây: sai mật khẩu lúc ĐĂNG NHẬP phải
    # luôn trả 401 với một câu chung chung. Nếu schema chặn trước ở 400 kèm "mật khẩu
    # phải >= 8 ký tự" thì kẻ tấn công biết được độ dài tối thiểu và phân biệt được
    # hai tình huống khác nhau.
    username: str = Field(..., min_length=1, max_length=MAX_USERNAME_LENGTH)
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_LENGTH)


class UserPublic(BaseModel):
    """Bản công khai của một tài khoản. KHÔNG BAO GIỜ chứa `password_hash`."""

    user_id: str
    username: str
    role: str = Field(..., description="user | admin")
    display_name: Optional[str] = None


class AuthData(BaseModel):
    user: UserPublic
    token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Số giây token còn hiệu lực")


class AuthResponse(BaseModel):
    data: AuthData


class MeResponse(BaseModel):
    data: UserPublic


# --- Quản trị ---------------------------------------------------------------
#
# Tách hẳn khỏi schema của người dùng cuối: đây là hợp đồng của MỘT ỨNG DỤNG KHÁC
# (`apps/admin`), có nhu cầu khác — nó cần thấy cả quán đã ẩn và cả trường `is_active`,
# những thứ luồng người dùng cuối không bao giờ được thấy.


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


class AdminLoginData(BaseModel):
    token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Số giây token còn hiệu lực")


class AdminLoginResponse(BaseModel):
    data: AdminLoginData


class AdminRestaurantSummary(BaseModel):
    """Một quán nhìn từ phía quản trị.

    `rating`/`reviews_count`/`price` để None khi CHƯA CÓ DỮ LIỆU — không đổi thành 0
    hay chuỗi rỗng, vì admin cần phân biệt "thiếu dữ liệu" với "giá trị bằng 0".
    """

    restaurant_id: Optional[str]
    name: str
    category: Optional[str] = None
    cuisine: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    price: Optional[str] = Field(None, description='Chuỗi khoảng giá, VD "1-100.000 ₫"')
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    is_active: bool
    source: Optional[str] = None


class AdminRestaurantListData(BaseModel):
    total: int
    results: List[AdminRestaurantSummary]


class AdminRestaurantListResponse(BaseModel):
    data: AdminRestaurantListData


class AdminRestaurantResponse(BaseModel):
    data: AdminRestaurantSummary


class AdminUpdateRestaurantRequest(BaseModel):
    """Chỉ những trường được gửi lên mới bị sửa (`exclude_unset=True` ở router).

    Gửi `null` = XOÁ giá trị. Không gửi trường = giữ nguyên. Đây là hai ý định khác
    nhau nên không được gộp làm một.
    """

    name: Optional[str] = None
    category: Optional[str] = None
    cuisine: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    price: Optional[str] = Field(None, description="CHUỖI, không phải số")
    phone: Optional[str] = None
    website: Optional[str] = None


# Mô tả lỗi dùng chung cho mọi endpoint, để OpenAPI ghi rõ hình dạng lỗi.
ERROR_RESPONSES = {
    400: {"model": ErrorEnvelope, "description": "INVALID_REQUEST"},
    404: {"model": ErrorEnvelope, "description": "RESTAURANT_NOT_FOUND"},
    503: {"model": ErrorEnvelope, "description": "DATA_NOT_READY"},
    500: {"model": ErrorEnvelope, "description": "INTERNAL_ERROR"},
}

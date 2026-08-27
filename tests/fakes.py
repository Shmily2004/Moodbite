"""Repository/adapter GIẢ dùng chung cho test.

Nhờ có port (Protocol) ở application/ports, test không cần file dữ liệu thật -
chạy nhanh và không phụ thuộc máy đang chạy có chạy data_pipeline hay chưa.
"""
import pathlib

from src.domain.entities.dish import Dish, DishRule
from src.domain.entities.restaurant import Restaurant
from src.domain.value_objects.context_signal import NEUTRAL_CONTEXT, ContextSignal
from src.domain.value_objects.location import Location
from src.domain.value_objects.mood import MOOD_SCORE_COLUMNS


class FakeRestaurantRepo:
    def __init__(self, restaurants, ready=True):
        self._restaurants = restaurants
        self._ready = ready

    @property
    def is_ready(self):
        return self._ready

    def list_all(self):
        return list(self._restaurants)

    def get_by_place_id(self, place_id):
        return next((r for r in self._restaurants if r.place_id == place_id), None)


class FakeDishKnowledge:
    def __init__(self, rules):
        self._rules = rules

    def list_rules(self):
        return list(self._rules)

    def match_rule_for_category(self, category_name):
        return next((r for r in self._rules if r.matches_category(category_name)), None)


class FakeDetailsRepo:
    def __init__(self, data, ready=True):
        self._data = data
        self._ready = ready

    @property
    def is_ready(self):
        return self._ready

    def get(self, place_id):
        return self._data.get(place_id)

    def review_texts(self):
        return {}


class FakeInteractionRepo:
    """Ghi vào bộ nhớ thay vì file, để test không đụng đĩa."""

    def __init__(self, ready=True):
        self.events = []
        self._ready = ready

    @property
    def is_ready(self):
        return self._ready

    def append(self, event):
        self.events.append(event)
        return f"evt-{len(self.events)}"


class StubPredictor:
    """Giả lập có model ML: trả rule_id theo bảng tra cứu."""

    def __init__(self, mapping):
        self._mapping = mapping

    @property
    def is_available(self):
        return True

    def predict_rule_id(self, category, cuisine=None):
        return self._mapping.get(category)


class UnavailablePredictor:
    """Giả lập trạng thái MẶC ĐỊNH: không có model -> luôn fallback về khớp từ khoá."""

    is_available = False

    def predict_rule_id(self, category, cuisine=None):
        return None


class FixedContextProvider:
    """Ngữ cảnh cố định, để test không phụ thuộc giờ chạy hay thời tiết thật."""

    def __init__(self, context: ContextSignal = NEUTRAL_CONTEXT):
        self._context = context

    def get_context(self, location):
        return self._context


class BrokenContextProvider:
    """Giả lập API thời tiết hỏng - lượt tìm kiếm vẫn phải chạy bình thường."""

    def get_context(self, location):
        raise ConnectionError("API thời tiết không phản hồi")


def make_restaurant(name, lat=21.03, lng=105.85, category="Nhà hàng", **kwargs):
    scores = {k: v for k, v in kwargs.items() if k in MOOD_SCORE_COLUMNS}
    other = {k: v for k, v in kwargs.items() if k not in MOOD_SCORE_COLUMNS}
    defaults = {"rating": 4.0, "address": f"{name} address", "place_id": f"id-{name}"}
    defaults.update(other)
    return Restaurant(
        name=name,
        category=category,
        location=Location(lat=lat, lng=lng),
        mood_scores={c: 0.0 for c in MOOD_SCORE_COLUMNS} | scores,
        **defaults,
    )


class UnavailableUserRepo:
    """Kho tài khoản KHÔNG mở được. Dùng cho các bộ test có tính năng tài khoản tắt hẳn."""

    is_ready = False

    def get_by_username(self, username):
        return None

    def get_by_id(self, user_id):
        return None

    def get_by_email(self, email):
        return None

    def update_password(self, user_id, password_hash):
        raise AssertionError("Bộ test này không được đổi mật khẩu")

    def create(self, user):
        raise AssertionError("Bộ test này không được tạo tài khoản")

    def count(self):
        return 0

    def status(self):
        return {"ready": False, "error": "tat trong test"}


class FakeEmailSender:
    """Máy gửi thư GIẢ — giữ lại thư trong bộ nhớ thay vì gửi thật.

    Bắt buộc phải có: không ai được để bộ test bắn thư thật vào hộp thư của ai đó, và
    kiểm nội dung thư (có đúng đường dẫn không, có lộ mật khẩu không) là một phần của
    tính năng quên mật khẩu.
    """

    def __init__(self, *, configured=True, loi=None):
        self.da_gui = []          # danh sách dict(to, subject, body)
        self._configured = configured
        self._loi = loi           # đặt một Exception vào đây để giả lập máy chủ thư hỏng

    @property
    def is_configured(self):
        return self._configured

    def send(self, *, to, subject, body, html=None):
        if self._loi is not None:
            raise self._loi
        self.da_gui.append({"to": to, "subject": subject, "body": body, "html": html})

    def status(self):
        return {"ready": self._configured, "source": "gia-lap", "error": None}


def attach_disabled_auth(container):
    """Gắn phần tài khoản ở trạng thái TẮT vào một container test.

    Cần thiết vì các test dựng container bằng `Container.__new__` (bỏ qua `__init__` để
    khỏi nạp dataset thật), nên trường mới thêm vào Container sẽ không tự có. Thà gắn
    tường minh ở đây còn hơn để `health()` dùng `getattr(..., None)` — cách đó biến lỗi
    quên lắp dây thành im lặng.
    """
    from src.application.use_cases.manage_account import (
        ConfirmEmailVerificationUseCase,
        LoginUseCase,
        RegisterUserUseCase,
        RequestEmailVerificationUseCase,
        RequestPasswordResetUseCase,
        ResetPasswordUseCase,
    )
    from src.infrastructure.auth.email_verification import EmailVerificationTokenService
    from src.infrastructure.auth.password_reset import PasswordResetTokenService
    from src.infrastructure.auth.rate_limit import SlidingWindowRateLimiter
    from src.infrastructure.auth.user_auth import UserTokenService

    users = UnavailableUserRepo()
    tokens = UserTokenService(token_secret="")   # rỗng = chưa cấu hình
    reset_tokens = PasswordResetTokenService(token_secret="")
    verify_tokens = EmailVerificationTokenService(token_secret="")
    emails = FakeEmailSender(configured=False)
    container.users = users
    container.user_tokens = tokens
    container.reset_tokens = reset_tokens
    container.email_verify_tokens = verify_tokens
    container.emails = emails
    container.register_user = RegisterUserUseCase(users, lambda p: "x", tokens.issue)
    container.login_user = LoginUseCase(users, lambda p, h: False, tokens.issue)
    container.request_password_reset = RequestPasswordResetUseCase(
        users=users,
        emails=emails,
        issue_reset_token=reset_tokens.issue,
        app_base_url="http://localhost:5173",
        token_ttl_seconds=reset_tokens.token_ttl_seconds,
    )
    container.reset_password = ResetPasswordUseCase(users, lambda p: "x", reset_tokens)
    container.request_email_verification = RequestEmailVerificationUseCase(
        emails=emails,
        verify_tokens=verify_tokens,
        app_base_url="http://localhost:5173",
        token_ttl_seconds=verify_tokens.token_ttl_seconds,
    )
    container.confirm_email_verification = ConfirmEmailVerificationUseCase(
        users, verify_tokens
    )
    container.login_rate_limiter = SlidingWindowRateLimiter(5, 300)
    # Đăng nhập quản trị có bộ đếm RIÊNG — xem `rate_limit.ADMIN_LOGIN_MAX_ATTEMPTS`.
    # Để rộng (50) vì phần lớn test không nói về giới hạn tần suất; test về giới hạn
    # tự dựng bộ đếm nhỏ.
    container.admin_login_rate_limiter = SlidingWindowRateLimiter(50, 900)
    container.register_rate_limiter = SlidingWindowRateLimiter(3, 3600)
    container.forgot_password_rate_limiter = SlidingWindowRateLimiter(3, 3600)
    return container


class FakeDishCatalog:
    """Danh mục món GIẢ. Mặc định rỗng nhưng SẴN SÀNG.

    Rỗng-mà-sẵn-sàng khác hẳn chưa-sẵn-sàng: bộ test luồng tìm quán không quan tâm tới
    món, nhưng `/health` vẫn phải báo được trạng thái, và endpoint món phải trả danh sách
    rỗng chứ không phải 503.
    """

    def __init__(self, dishes=None, ready=True):
        self._dishes = list(dishes or [])
        self._ready = ready

    @property
    def is_ready(self):
        return self._ready

    def list_dishes(self):
        return list(self._dishes)

    def get_dish(self, dish_id):
        return next((d for d in self._dishes if d.identifier == dish_id), None)

    def list_all_dishes(self):
        """Bản giả KHÔNG phân biệt bật/tắt: mọi món truyền vào đều coi là đang bật.

        Muốn test món tắt thì truyền `Dish(is_active=False)` — `viec_can_xu_ly` đọc
        thẳng trường đó, không phụ thuộc kho.
        """
        return list(self._dishes)

    def status(self):
        return {"ready": self._ready, "dishes": len(self._dishes)}


def attach_dish_catalog(container, dishes=None, index=None, context_provider=None):
    """Gắn phần MÓN ĂN vào một container test.

    Cùng lý do tồn tại với `attach_disabled_auth`: container test dựng bằng
    `Container.__new__` nên không tự có trường mới. Gắn tường minh để việc quên lắp dây
    biến thành lỗi ồn ào, thay vì `getattr(..., None)` im lặng nuốt mất.
    """
    from src.application.use_cases.find_restaurants_for_dish import (
        FindRestaurantsForDishUseCase,
    )
    from src.application.use_cases.suggest_dishes import SuggestDishesUseCase

    from src.domain.services.dish_matching import MATCHED_BY_NAME, DishMatch

    catalog = dishes if hasattr(dishes, "list_dishes") else FakeDishCatalog(dishes)
    # Test viết chỉ mục cho gọn dạng {dish_id: [quán]}. Bọc thành `DishMatch` ở đây để
    # từng test khỏi phải nhắc lại "khớp bằng tên" - mặc định là tín hiệu mạnh.
    dish_index = {
        dish_id: [
            item if isinstance(item, DishMatch) else DishMatch(item, MATCHED_BY_NAME)
            for item in items
        ]
        for dish_id, items in (index or {}).items()
    }

    container.dish_catalog_repository = catalog
    container.suggest_dishes = SuggestDishesUseCase(
        catalog=catalog,
        dish_restaurant_index=dish_index,
        context_provider=context_provider,
    )
    container.find_restaurants_for_dish = FindRestaurantsForDishUseCase(
        catalog=catalog,
        dish_restaurant_index=dish_index,
        context_provider=context_provider,
    )
    return container


PHO_RULE = DishRule(
    id="pho",
    confidence="specific",
    match_category=["phở"],
    dishes=[Dish(name="Phở bò", cuisine="Việt Nam", mood_keywords=["comfort", "cozy"])],
)

GENERIC_RULE = DishRule(
    id="generic",
    confidence="generic_fallback",
    match_category=["nhà hàng"],
    dishes=[Dish(name="Cơm rang", mood_keywords=["comfort", "cozy"])],
)


def attach_closure_tally(container, tally=None):
    """Gắn bộ đếm BÁO ĐÓNG CỬA vào một container test.

    Cùng lý do tồn tại với `attach_disabled_auth` và `attach_dish_catalog`: container test
    dựng bằng `Container.__new__` nên không tự có trường mới thêm vào Container. Gắn tường
    minh để việc quên lắp dây thành lỗi ồn ào, thay vì `getattr(..., None)` im lặng nuốt.

    Mặc định là bộ đếm RỖNG - tức "chưa ai báo quán nào", đúng trạng thái của một hệ thống
    vừa dựng lên, và các bộ test không quan tâm tới tính năng này sẽ chạy y như trước.
    """
    from src.domain.services.closure_reports import ClosureReportTally

    container.closure_tally = tally or ClosureReportTally()
    return container


def attach_user_activity(container, tmp_path=None):
    """Gắn kho "đã lưu" + bộ đếm hoạt động + use case cấp độ vào container test.

    Cùng lý do tồn tại với `attach_closure_tally`: container test dựng bằng
    `Container.__new__` nên không tự có trường mới. Gắn tường minh để quên lắp dây thành
    lỗi ồn ào thay vì `getattr(..., None)` im lặng nuốt.

    `tmp_path=None` -> tự tạo một thư mục tạm. KHÔNG dùng ":memory:" của SQLite: adapter
    mở kết nối MỚI ở mỗi truy vấn (đúng như lúc chạy thật), mà CSDL trong RAM biến mất
    ngay khi kết nối đóng — bảng vừa tạo xong sẽ không còn ở câu lệnh kế tiếp.
    """
    import tempfile
    from src.application.use_cases.get_user_stats import GetUserStatsUseCase
    from src.application.use_cases.manage_favorites import (
        ListFavoritesUseCase,
        RemoveFavoriteUseCase,
        SaveFavoriteUseCase,
    )
    from src.domain.services.activity_tally import ActivityTally
    from src.infrastructure.repositories.sqlite_saved_item_repository import (
        SqliteSavedItemRepository,
    )

    thu_muc = pathlib.Path(tmp_path) if tmp_path is not None else pathlib.Path(
        tempfile.mkdtemp(prefix="moodbite-test-")
    )
    duong_dan = thu_muc / "users.db"
    saved = SqliteSavedItemRepository(duong_dan)
    tally = ActivityTally()

    container.saved_items = saved
    container.activity_tally = tally
    container.save_favorite = SaveFavoriteUseCase(saved)
    container.remove_favorite = RemoveFavoriteUseCase(saved)
    container.list_favorites = ListFavoritesUseCase(saved)
    container.get_user_stats = GetUserStatsUseCase(tally, saved)
    return container

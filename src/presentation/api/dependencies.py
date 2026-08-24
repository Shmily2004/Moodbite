"""DI container: nơi DUY NHẤT lắp adapter thật vào use case.

Đây là chỗ trả lời câu hỏi "cái gì nối với cái gì". Muốn đổi CSV sang PostgreSQL thì
sửa đúng file này, không đụng vào use case hay router.

Container được tạo MỘT LẦN lúc khởi động và gắn vào app.state. Router lấy ra qua
Depends(...) chứ không tự khởi tạo gì.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Request

from src.application.ports.admin_restaurant_repository import AdminRestaurantRepository
from src.application.use_cases.get_restaurant_details import GetRestaurantDetailsUseCase
from src.application.use_cases.log_interaction import LogInteractionUseCase
from src.domain.services.activity_tally import ActivityTally
from src.domain.services.closure_reports import ClosureReportTally
from src.application.use_cases.manage_restaurants import (
    CreateRestaurantUseCase,
    ListRestaurantsForAdminUseCase,
    SetRestaurantVisibilityUseCase,
    UpdateRestaurantUseCase,
)
from src.application.use_cases.manage_account import (
    ChangePasswordUseCase,
    LoginUseCase,
    RegisterUserUseCase,
    ConfirmEmailVerificationUseCase,
    RequestEmailVerificationUseCase,
    RequestPasswordResetUseCase,
    ResetPasswordUseCase,
)
from src.application.use_cases.manage_favorites import (
    ListFavoritesUseCase,
    RemoveFavoriteUseCase,
    SaveFavoriteUseCase,
)
from src.application.use_cases.get_user_stats import GetUserStatsUseCase
from src.application.use_cases.find_restaurants_for_dish import (
    FindRestaurantsForDishUseCase,
)
from src.application.use_cases.search_restaurants import SearchRestaurantsUseCase
from src.application.use_cases.suggest_dishes import SuggestDishesUseCase
from src.domain.services.dish_matching import build_dish_restaurant_index
from src.application.errors import (
    DataNotReadyError,
    InvalidCredentialsError,
    PermissionDeniedError,
)
from src.domain.entities.interaction import ActionType
from src.domain.entities.user import User, UserRole
from src.infrastructure.auth.admin_auth import AdminAuthService
from src.infrastructure.auth.crypto import hash_password, verify_password
from src.infrastructure.auth.rate_limit import (
    ADMIN_LOGIN_MAX_ATTEMPTS,
    ADMIN_LOGIN_WINDOW_SECONDS,
    FORGOT_PASSWORD_MAX_ATTEMPTS,
    FORGOT_PASSWORD_WINDOW_SECONDS,
    LOGIN_MAX_ATTEMPTS,
    LOGIN_WINDOW_SECONDS,
    REGISTER_MAX_ATTEMPTS,
    REGISTER_WINDOW_SECONDS,
    SlidingWindowRateLimiter,
)
from src.infrastructure.auth.user_auth import UserTokenService
from src.infrastructure.notifications.smtp_email_sender import SmtpEmailSender
from src.infrastructure.auth.password_reset import PasswordResetTokenService
from src.infrastructure.auth.email_verification import EmailVerificationTokenService
from src.infrastructure.repositories.sqlite_saved_item_repository import (
    SqliteSavedItemRepository,
)
from src.infrastructure.repositories.sqlite_user_repository import SqliteUserRepository
from src.infrastructure.adapters.ml_rule_predictor import MlRulePredictor
from src.infrastructure.adapters.open_meteo_context_provider import (
    ClockOnlyContextProvider,
    OpenMeteoContextProvider,
)
from src.infrastructure.config.settings import Settings
from src.infrastructure.repositories.csv_restaurant_repository import (
    CsvRestaurantRepository,
)
from src.infrastructure.repositories.json_dish_catalog_repository import (
    JsonDishCatalogRepository,
)
from src.infrastructure.repositories.json_dish_knowledge_repository import (
    JsonDishKnowledgeRepository,
)
from src.infrastructure.repositories.json_restaurant_details_repository import (
    JsonRestaurantDetailsRepository,
)
from src.infrastructure.adapters.tfidf_semantic_search import TfidfSemanticSearch
from src.infrastructure.repositories.jsonl_interaction_repository import (
    JsonlInteractionRepository,
)
from src.infrastructure.repositories.sqlite_restaurant_repository import (
    SqliteRestaurantRepository,
)


logger = logging.getLogger("moodbite.dependencies")


def _status_of(adapter: object) -> dict:
    """Trạng thái 1 adapter. Adapter nào chưa có `status()` (VD bản giả trong test) thì
    suy ra tối thiểu từ `is_ready`, để /health không bao giờ làm sập app."""
    status = getattr(adapter, "status", None)
    if callable(status):
        return status()
    return {"ready": bool(getattr(adapter, "is_ready", False))}


@dataclass
class Container:
    settings: Optional[Settings]
    restaurant_repository: object
    details_repository: object
    dish_knowledge_repository: object
    dish_catalog_repository: object
    interaction_repository: object
    rule_predictor: object
    context_provider: object
    semantic_search: object
    search_restaurants: SearchRestaurantsUseCase
    get_restaurant_details: GetRestaurantDetailsUseCase
    log_interaction: LogInteractionUseCase
    # Bộ đếm báo đóng cửa. Giữ trên Container để /health nói được trạng thái,
    # và để trang quản trị sau này liệt kê được quán nào đang bị ẩn vì bị báo.
    closure_tally: ClosureReportTally
    # --- Luồng "chọn món trước, tìm quán sau" ---------------------------------
    suggest_dishes: SuggestDishesUseCase
    find_restaurants_for_dish: FindRestaurantsForDishUseCase
    # --- Quản trị ------------------------------------------------------------
    # `None` khi kho lưu trữ không ghi được (CSV). Router admin phải kiểm và trả 503,
    # KHÔNG được để nổ AttributeError.
    admin_auth: AdminAuthService
    admin_restaurants: Optional[object]
    list_restaurants_for_admin: Optional[ListRestaurantsForAdminUseCase]
    create_restaurant: Optional[CreateRestaurantUseCase]
    update_restaurant: Optional[UpdateRestaurantUseCase]
    set_restaurant_visibility: Optional[SetRestaurantVisibilityUseCase]
    # --- Tài khoản người dùng cuối --------------------------------------------
    users: object
    # Kho "quán & món đã lưu" + bộ đếm hoạt động: hai thứ đứng sau cấp độ và huy hiệu.
    saved_items: object
    activity_tally: ActivityTally
    save_favorite: SaveFavoriteUseCase
    remove_favorite: RemoveFavoriteUseCase
    list_favorites: ListFavoritesUseCase
    get_user_stats: GetUserStatsUseCase
    user_tokens: UserTokenService
    reset_tokens: PasswordResetTokenService
    email_verify_tokens: EmailVerificationTokenService
    emails: SmtpEmailSender
    register_user: RegisterUserUseCase
    login_user: LoginUseCase
    change_password: ChangePasswordUseCase
    request_password_reset: RequestPasswordResetUseCase
    request_email_verification: RequestEmailVerificationUseCase
    confirm_email_verification: ConfirmEmailVerificationUseCase
    reset_password: ResetPasswordUseCase
    # Hai bộ đếm RIÊNG BIỆT. Dùng chung một bộ thì người đăng ký hụt vài lần sẽ ăn hết
    # hạn mức đăng nhập của chính mình — hai hành vi khác nhau, ngưỡng khác nhau.
    login_rate_limiter: SlidingWindowRateLimiter
    admin_login_rate_limiter: SlidingWindowRateLimiter
    register_rate_limiter: SlidingWindowRateLimiter
    forgot_password_rate_limiter: SlidingWindowRateLimiter

    def health(self) -> dict:
        """Trạng thái từng nguồn dữ liệu, kèm LÝ DO khi chưa sẵn sàng.

        Mỗi adapter TỰ mô tả mình qua `status()`. Container không đọc thuộc tính riêng của
        adapter cụ thể, nhờ vậy thay adapter (CSV -> PostgreSQL) không phải sửa hàm này.
        """
        return {
            "restaurants": _status_of(self.restaurant_repository),
            "restaurant_details": _status_of(self.details_repository),
            "dish_knowledge": _status_of(self.dish_knowledge_repository),
            "dish_catalog": _status_of(self.dish_catalog_repository),
            "interactions": _status_of(self.interaction_repository),
            "closure_reports": _status_of(self.closure_tally),
            "ml_rule_predictor": _status_of(self.rule_predictor),
            "context_provider": _status_of(self.context_provider),
            "semantic_search": _status_of(self.semantic_search),
            "admin_auth": _status_of(self.admin_auth),
            "admin_storage": {
                "ready": self.admin_restaurants is not None,
                "error": None
                if self.admin_restaurants is not None
                else "kho hiện tại không ghi được - cần MOODBITE_STORAGE=sqlite",
            },
            "users": _status_of(self.users),
            "saved_items": _status_of(self.saved_items),
            "user_activity": _status_of(self.activity_tally),
            "user_auth": _status_of(self.user_tokens),
            "email": self.emails.status(),
        }


def build_container(settings: Optional[Settings] = None) -> Container:
    """Lắp toàn bộ app. Thiếu file dữ liệu KHÔNG làm sập - repository ghi nhận lỗi và
    endpoint liên quan trả 503 kèm hướng dẫn, các endpoint khác vẫn chạy."""
    settings = settings or Settings.from_env()

    details_repository = JsonRestaurantDetailsRepository(
        settings.restaurant_details_json
    )
    # Ghép review từ file chi tiết vào dataset chính để tìm kiếm bằng câu tự do khớp được
    # nội dung review. Việc ghép 2 nguồn là trách nhiệm của composition root, không phải
    # của repository - mỗi repository chỉ đọc đúng một nguồn.
    review_texts = details_repository.review_texts() if details_repository.is_ready else {}
    # Ảnh đại diện cho card kết quả - ghép cùng chỗ với review, theo đúng một lối.
    thumbnail_urls = (
        details_repository.thumbnail_urls() if details_repository.is_ready else {}
    )

    # ĐÂY là toàn bộ chi phí của việc đổi kho lưu trữ: một câu if ở composition root.
    # Use case, domain và router không biết dữ liệu đến từ CSV hay SQLite - cả hai
    # adapter đều triển khai cùng port `RestaurantRepository`.
    #
    # SQLite đã lưu sẵn `review_text` (do `scripts/build_sqlite.py` ghép lúc dựng CSDL),
    # nên không cần truyền `review_texts` vào nữa.
    if settings.storage_backend == "sqlite":
        restaurant_repository = SqliteRestaurantRepository(settings.restaurants_db)
    else:
        restaurant_repository = CsvRestaurantRepository(
            settings.restaurants_csv,
            review_texts=review_texts,
            thumbnail_urls=thumbnail_urls,
        )
    dish_knowledge_repository = JsonDishKnowledgeRepository(
        settings.dish_knowledge_json
    )
    dish_catalog_repository = JsonDishCatalogRepository(settings.dish_catalog_json)

    # LỚP 4 - nhận xét tổng hợp từ review, ĐÃ TÍNH SẴN offline bởi
    # `python -m data_pipeline.review_summary`. Đọc ở composition root rồi truyền vào use
    # case, đúng lối đã dùng cho `review_texts`/`thumbnail_urls`: use case không được biết
    # đường dẫn file nào.
    #
    # CHƯA CHẠY SCRIPT thì file không tồn tại -> dict rỗng, phần nhận xét vắng mặt còn mọi
    # thứ khác vẫn chạy. Thiếu file KHÔNG được làm sập app (CLAUDE.md mục 4 quy tắc 3).
    review_summaries: dict = {}
    if settings.review_summaries_json.exists():
        try:
            review_summaries = json.loads(
                settings.review_summaries_json.read_text(encoding="utf-8")
            ).get("summaries", {})
        except (OSError, ValueError) as exc:
            logger.warning("Khong doc duoc tom tat review: %s", exc)

    # Chỉ mục món -> quán dựng MỘT LẦN lúc khởi động (đo được: 0.05 giây cho 79 món x
    # 4938 quán). Dựng lại ở mỗi yêu cầu mất ~11 giây - xem `domain/services/dish_matching.py`.
    #
    # Danh mục món hoặc kho quán chưa sẵn sàng -> chỉ mục RỖNG chứ không nổ. Endpoint món
    # sẽ tự trả 503 kèm hướng dẫn, các endpoint khác vẫn chạy bình thường.
    dish_restaurant_index = (
        build_dish_restaurant_index(
            dish_catalog_repository.list_dishes(), restaurant_repository.list_all()
        )
        if dish_catalog_repository.is_ready and restaurant_repository.is_ready
        else {}
    )
    interaction_repository = JsonlInteractionRepository(settings.interactions_path)

    # Bộ đếm "người dùng báo quán đã đóng cửa", DỰNG LẠI TỪ NHẬT KÝ lúc khởi động.
    # Giữ trong RAM vì nó nằm trên đường đi của mọi lượt tìm kiếm, nhưng nguồn sự thật vẫn
    # là file nhật ký - khởi động lại không làm quán đã bị ẩn hiện lại.
    closure_tally = ClosureReportTally()
    for place_id, session_id in interaction_repository.replay_closure_reports():
        closure_tally.record(place_id, session_id)
    if closure_tally.hidden_place_ids():
        logger.info(
            "Có %d quán bị người dùng báo đã đóng cửa (ngưỡng %d phiên).",
            len(closure_tally.hidden_place_ids()), closure_tally.threshold,
        )
    rule_predictor = MlRulePredictor(
        settings.dish_model_path, mode=settings.dish_adapter_mode
    )
    context_provider = (
        OpenMeteoContextProvider(enable_weather=True)
        if settings.enable_weather
        else ClockOnlyContextProvider()
    )
    # Chỉ mục ngữ nghĩa dựng MỘT LẦN lúc khởi động từ dữ liệu đã nạp - không dựng lại
    # ở mỗi request (dựng mất ~1 giây cho 5000 quán).
    semantic_search = TfidfSemanticSearch(
        restaurant_repository.list_all() if restaurant_repository.is_ready else []
    )

    admin_auth = AdminAuthService(
        username=settings.admin_username,
        password_hash=settings.admin_password_hash,
        token_secret=settings.admin_token_secret,
        token_ttl_seconds=settings.admin_token_ttl_seconds,
    )
    # Chỉ SQLite mới ghi được. Bản CSV cố tình KHÔNG triển khai port ghi, nên phép kiểm
    # dưới đây tự động đúng khi thêm adapter mới - không phải nhớ sửa thêm chỗ nào.
    admin_restaurants = (
        restaurant_repository
        if isinstance(restaurant_repository, AdminRestaurantRepository)
        else None
    )

    # Kho tài khoản luôn được dựng, kể cả khi chưa đặt MOODBITE_AUTH_SECRET: mở file
    # SQLite rỗng gần như không tốn gì, và nhờ vậy /health nói được "kho sẵn sàng nhưng
    # chưa có secret" thay vì gộp hai vấn đề khác nhau vào một thông báo.
    users = SqliteUserRepository(settings.users_db)
    # CÙNG FILE CSDL với tài khoản, cố ý — cả hai đều là dữ liệu gốc. Xem ghi chú đầu
    # `sqlite_saved_item_repository.py`.
    saved_items = SqliteSavedItemRepository(settings.users_db)

    # Bộ đếm "lượt khám phá" cho cấp độ/huy hiệu. Dựng lại từ nhật ký tương tác đúng như
    # bộ đếm báo đóng cửa ở trên, để khởi động lại không xoá sạch cấp độ của người dùng.
    activity_tally = ActivityTally()
    replay_activity = getattr(interaction_repository, "replay_user_activity", None)
    if callable(replay_activity):
        so_ban_ghi = 0
        for rec in replay_activity():
            try:
                hanh_dong = ActionType(rec.get("action_type"))
            except ValueError:
                continue  # action_type lạ trong bản ghi cũ -> bỏ qua, không làm sập app
            ngay = str(rec.get("created_at") or "")[:10] or None
            activity_tally.record(
                user_id=rec.get("user_id"),
                action_type=hanh_dong,
                restaurant_id=str(rec.get("restaurant_id") or ""),
                day=ngay,
                dwell_time_ms=rec.get("dwell_time_ms"),
            )
            so_ban_ghi += 1
        if so_ban_ghi:
            logger.info(
                "Dựng lại hoạt động người dùng từ %d bản ghi (%d tài khoản).",
                so_ban_ghi, activity_tally.tracked_users,
            )
    user_tokens = UserTokenService(
        settings.user_token_secret, settings.user_token_ttl_seconds
    )
    # Chưa khai secret riêng thì lui về secret đăng nhập: thà tính năng chạy được với một
    # secret còn hơn tắt hẳn ở một đồ án. Khai riêng vẫn tốt hơn — xem `password_reset.py`.
    reset_tokens = PasswordResetTokenService(
        settings.reset_token_secret or settings.user_token_secret,
        settings.reset_token_ttl_seconds,
    )
    # Thứ tự lui: secret riêng -> secret đặt lại mật khẩu -> secret đăng nhập.
    # Cùng lý lẽ với `reset_tokens` ngay trên: thà chạy được bằng một secret còn hơn tắt
    # hẳn tính năng ở một đồ án, nhưng khai riêng vẫn tốt hơn.
    email_verify_tokens = EmailVerificationTokenService(
        settings.email_verify_token_secret
        or settings.reset_token_secret
        or settings.user_token_secret,
        settings.email_verify_token_ttl_seconds,
    )
    emails = SmtpEmailSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        sender=settings.smtp_sender,
    )

    return Container(
        settings=settings,
        admin_auth=admin_auth,
        admin_restaurants=admin_restaurants,
        list_restaurants_for_admin=(
            ListRestaurantsForAdminUseCase(admin_restaurants) if admin_restaurants else None
        ),
        create_restaurant=(
            CreateRestaurantUseCase(admin_restaurants) if admin_restaurants else None
        ),
        update_restaurant=(
            UpdateRestaurantUseCase(admin_restaurants) if admin_restaurants else None
        ),
        set_restaurant_visibility=(
            SetRestaurantVisibilityUseCase(admin_restaurants) if admin_restaurants else None
        ),
        restaurant_repository=restaurant_repository,
        details_repository=details_repository,
        dish_knowledge_repository=dish_knowledge_repository,
        dish_catalog_repository=dish_catalog_repository,
        interaction_repository=interaction_repository,
        rule_predictor=rule_predictor,
        context_provider=context_provider,
        semantic_search=semantic_search,
        search_restaurants=SearchRestaurantsUseCase(
            restaurants=restaurant_repository,
            dish_knowledge=dish_knowledge_repository,
            context_provider=context_provider,
            rule_predictor=rule_predictor,
            semantic_search=semantic_search,
            closure_tally=closure_tally,
        ),
        get_restaurant_details=GetRestaurantDetailsUseCase(
            details_repository, restaurant_repository, review_summaries
        ),
        closure_tally=closure_tally,
        log_interaction=LogInteractionUseCase(
            interactions=interaction_repository,
            restaurants=restaurant_repository,
            closure_tally=closure_tally,
            activity_tally=activity_tally,
        ),
        suggest_dishes=SuggestDishesUseCase(
            catalog=dish_catalog_repository,
            dish_restaurant_index=dish_restaurant_index,
            context_provider=context_provider,
            closure_tally=closure_tally,
        ),
        find_restaurants_for_dish=FindRestaurantsForDishUseCase(
            catalog=dish_catalog_repository,
            dish_restaurant_index=dish_restaurant_index,
            context_provider=context_provider,
            closure_tally=closure_tally,
        ),
        users=users,
        saved_items=saved_items,
        activity_tally=activity_tally,
        save_favorite=SaveFavoriteUseCase(saved_items),
        remove_favorite=RemoveFavoriteUseCase(saved_items),
        list_favorites=ListFavoritesUseCase(saved_items),
        get_user_stats=GetUserStatsUseCase(activity_tally, saved_items),
        user_tokens=user_tokens,
        reset_tokens=reset_tokens,
        email_verify_tokens=email_verify_tokens,
        emails=emails,
        register_user=RegisterUserUseCase(users, hash_password, user_tokens.issue),
        login_user=LoginUseCase(users, verify_password, user_tokens.issue),
        change_password=ChangePasswordUseCase(users, verify_password, hash_password),
        request_password_reset=RequestPasswordResetUseCase(
            users=users,
            emails=emails,
            issue_reset_token=reset_tokens.issue,
            app_base_url=settings.app_base_url,
            token_ttl_seconds=reset_tokens.token_ttl_seconds,
        ),
        reset_password=ResetPasswordUseCase(users, hash_password, reset_tokens),
        request_email_verification=RequestEmailVerificationUseCase(
            emails=emails,
            verify_tokens=email_verify_tokens,
            app_base_url=settings.app_base_url,
            token_ttl_seconds=email_verify_tokens.token_ttl_seconds,
        ),
        confirm_email_verification=ConfirmEmailVerificationUseCase(
            users, email_verify_tokens
        ),
        login_rate_limiter=SlidingWindowRateLimiter(
            LOGIN_MAX_ATTEMPTS, LOGIN_WINDOW_SECONDS
        ),
        admin_login_rate_limiter=SlidingWindowRateLimiter(
            ADMIN_LOGIN_MAX_ATTEMPTS, ADMIN_LOGIN_WINDOW_SECONDS
        ),
        register_rate_limiter=SlidingWindowRateLimiter(
            REGISTER_MAX_ATTEMPTS, REGISTER_WINDOW_SECONDS
        ),
        forgot_password_rate_limiter=SlidingWindowRateLimiter(
            FORGOT_PASSWORD_MAX_ATTEMPTS, FORGOT_PASSWORD_WINDOW_SECONDS
        ),
    )


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_search_restaurants(
    container: Container = Depends(get_container),
) -> SearchRestaurantsUseCase:
    return container.search_restaurants


def get_suggest_dishes(
    container: Container = Depends(get_container),
) -> SuggestDishesUseCase:
    return container.suggest_dishes


def get_find_restaurants_for_dish(
    container: Container = Depends(get_container),
) -> FindRestaurantsForDishUseCase:
    return container.find_restaurants_for_dish


def get_restaurant_details_use_case(
    container: Container = Depends(get_container),
) -> GetRestaurantDetailsUseCase:
    return container.get_restaurant_details


def get_log_interaction(
    container: Container = Depends(get_container),
) -> LogInteractionUseCase:
    return container.log_interaction


def _bearer_token(request: Request) -> str:
    """Lấy token từ header `Authorization: Bearer <token>`.

    Dùng chung cho cả admin lẫn người dùng để hai bên không lệch nhau về cách đọc header.
    `partition` chịu được cả chuỗi rỗng lẫn thiếu dấu cách, không cần try/except.
    """
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise InvalidCredentialsError(
            "Thiếu header 'Authorization: Bearer <token>'. Hãy đăng nhập trước."
        )
    return token.strip()


def client_key(request: Request) -> str:
    """Khoá đếm cho giới hạn tần suất: địa chỉ IP của client.

    VÌ SAO KHÔNG ĐẾM THEO TÊN ĐĂNG NHẬP: làm vậy thì bất kỳ ai cũng khoá được tài khoản
    người khác chỉ bằng cách nhập sai mật khẩu vài lần — biến chính cơ chế bảo vệ thành
    công cụ tấn công từ chối dịch vụ.

    ⚠️ Chạy sau reverse proxy thì `request.client.host` là IP của PROXY, tức mọi người
    dùng chung một bộ đếm và sẽ khoá lẫn nhau. Cách khắc phục ĐÚNG là bật
    `uvicorn --proxy-headers --forwarded-allow-ips=<ip proxy>`, KHÔNG PHẢI tự đọc header
    `X-Forwarded-For` ở đây: header đó client tự đặt được, tin nó là mở cửa cho việc lách
    giới hạn bằng cách bịa IP.
    """
    return request.client.host if request.client else "unknown"


def get_current_user(
    request: Request,
    container: Container = Depends(get_container),
) -> User:
    """Chốt chặn ĐĂNG NHẬP cho mọi endpoint cần biết người dùng là ai.

    Ném `InvalidCredentialsError` -> 401. Chưa bật tính năng tài khoản -> 503 kèm hướng dẫn.
    """
    # Kiểm CẤU HÌNH trước khi kiểm token, cùng lý do như `require_admin`: chưa đặt secret
    # thì không token nào chạy được, trả 401 sẽ khiến người ta đi mò sai chỗ.
    container.user_tokens.ensure_configured()
    if not container.users.is_ready:
        raise DataNotReadyError(
            "kho tài khoản không mở được",
            "Kiểm tra quyền ghi ở đường dẫn MOODBITE_USERS_DB.",
        )

    user_id = container.user_tokens.subject_of(_bearer_token(request))

    # Đọc LẠI tài khoản từ kho ở mỗi request thay vì tin nội dung token. Nhờ vậy đổi vai
    # hay xoá tài khoản có hiệu lực NGAY, không phải đợi token hết hạn.
    user = container.users.get_by_id(user_id)
    if user is None:
        raise InvalidCredentialsError(
            "Tài khoản không còn tồn tại. Hãy đăng nhập lại."
        )
    return user


def get_optional_user(
    request: Request,
    container: Container = Depends(get_container),
) -> Optional[User]:
    """Người đang đăng nhập, hoặc `None` nếu là KHÁCH. KHÔNG BAO GIỜ ném lỗi.

    Dùng cho endpoint mà cả khách lẫn người đã đăng nhập đều gọi được — hiện chỉ có
    `POST /interactions`. Khách vẫn phải ghi được tương tác (đó là nguồn nhãn huấn luyện
    và cũng là nguồn của tính năng báo đóng cửa); người đã đăng nhập thì ghi kèm `user_id`
    để đếm được lượt khám phá.

    ⚠️ Token hỏng/hết hạn ở đây được coi như KHÁCH, không phải 401. Lý do: người dùng đang
    xem một quán mà token vừa hết hạn thì không có lý gì để chặn việc ghi nhật ký — hành
    vi đó vẫn có thật. Trả 401 chỉ khiến client hiện lỗi ở một chỗ chẳng liên quan gì.
    """
    if not request.headers.get("Authorization"):
        return None
    try:
        container.user_tokens.ensure_configured()
        user_id = container.user_tokens.subject_of(_bearer_token(request))
        return container.users.get_by_id(user_id)
    except Exception:  # noqa: BLE001 - mọi lỗi xác thực đều quy về "coi như khách"
        return None


def require_role(role: UserRole):
    """Sinh ra một guard chỉ cho qua đúng một vai. Ném `PermissionDeniedError` -> 403.

    Trả về HÀM chứ không phải giá trị, để dùng được dưới dạng
    `Depends(require_role(UserRole.ADMIN))` ở từng router.
    """

    def guard(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise PermissionDeniedError(
                f"Chức năng này chỉ dành cho vai '{role.value}'."
            )
        return user

    return guard


def require_admin(
    request: Request,
    container: Container = Depends(get_container),
) -> str:
    """Chốt chặn xác thực cho MỌI endpoint /api/v1/admin/* trừ /login.

    Đặt ở đây (composition root) chứ không ở router, để router giữ đúng vai trò "mỏng".
    Ném `InvalidCredentialsError` -> `error_handlers.py` đổi thành 401 UNAUTHORIZED.
    """
    # Kiểm CẤU HÌNH trước khi kiểm token. Ngược lại thì lúc chưa bật admin, mọi request
    # đều nhận 401 "sai xác thực" — sai sự thật và gây lạc hướng khi chẩn đoán: không có
    # token nào chạy được cả, vấn đề nằm ở việc chưa đặt biến môi trường. Phải là 503
    # kèm hướng dẫn.
    container.admin_auth.ensure_configured()
    return container.admin_auth.verify(_bearer_token(request))

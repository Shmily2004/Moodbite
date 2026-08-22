"""Cấu hình chạy được đọc từ biến môi trường. MỘT nơi duy nhất định nghĩa đường dẫn file.

Trước đây đường dẫn CSV bị hardcode ở 3 chỗ khác nhau (service, startup, repository) nên
đổi 1 chỗ là hỏng 2 chỗ còn lại.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Cùng tầng infrastructure nên import được. Lấy hằng số từ nơi ĐỊNH NGHĨA nó thay vì chép
# lại số 86400 vào đây - chép là có ngày hai chỗ lệch nhau.
from src.infrastructure.auth.user_auth import DEFAULT_USER_TOKEN_TTL_SECONDS
from src.infrastructure.config.dotenv import nap_env_local
from src.infrastructure.auth.password_reset import DEFAULT_RESET_TTL_SECONDS

# Gốc repo = thư mục chứa src/ (file này ở src/infrastructure/config/settings.py).
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def describe_path(path) -> str:
    """Đường dẫn AN TOÀN để đưa ra ngoài (`/health`, thông báo lỗi).

    VÌ SAO KHÔNG DÙNG `str(path)`: `/health` là endpoint CÔNG KHAI, không cần đăng nhập.
    Trả đường dẫn tuyệt đối là để lộ tên người dùng hệ điều hành và cấu trúc thư mục máy
    chủ (kiểu "C:/Users/<tên>/..."). Đó là thông tin trinh sát miễn phí cho người muốn
    tấn công, mà chẳng giúp gì thêm cho người vận hành.

    Trả đường dẫn TƯƠNG ĐỐI so với gốc dự án: vẫn đủ để biết thiếu file nào và sửa ở đâu,
    nhưng không nói gì về máy đang chạy. File nằm ngoài gốc dự án thì chỉ trả tên file.
    """
    resolved = Path(path)
    try:
        return resolved.resolve().relative_to(PROJECT_ROOT).as_posix()
    except (ValueError, OSError):
        return resolved.name


def _path_from_env(env_key: str, default_relative: str) -> Path:
    raw = os.getenv(env_key)
    if raw:
        return Path(raw)
    return PROJECT_ROOT / default_relative


@dataclass(frozen=True)
class Settings:
    restaurants_csv: Path
    # CSDL SQLite dựng bằng `python scripts/build_sqlite.py`. Chỉ dùng khi
    # storage_backend='sqlite'.
    restaurants_db: Path
    # 'csv' (mặc định) | 'sqlite'. Để CSV làm mặc định vì đó là thứ pipeline sinh ra
    # trực tiếp; SQLite là bước chuẩn bị cho trang Admin (cần SỬA/ẨN quán, CSV không
    # làm được an toàn). Bật bằng MOODBITE_STORAGE=sqlite.
    storage_backend: str
    restaurant_details_json: Path
    dish_knowledge_json: Path
    # Danh mục MÓN ĂN cho luồng "chọn món trước, tìm quán sau".
    # Sinh bởi `python scripts/build_dish_catalog.py`. Khác `dish_knowledge_json`: file kia
    # là RULE để đoán quán bán gì, file này là DANH MỤC món tra cứu được theo id.
    dish_catalog_json: Path
    # Tóm tắt review (Lớp 4). Sinh bởi `python -m data_pipeline.review_summary`.
    review_summaries_json: Path
    dish_model_path: Path
    # Nơi ghi sự kiện tương tác (nguồn nhãn cho mô hình xếp hạng sau này).
    interactions_path: Path
    # 'auto' = dùng ML nếu có, không thì khớp từ khoá | 'kb' = ép chỉ dùng từ khoá
    # | 'ml' = chỉ dùng ML.
    dish_adapter_mode: str
    cors_allow_origins: tuple[str, ...]
    # Gọi API thời tiết (Open-Meteo, miễn phí, không cần key). Tắt trong test/CI để
    # không phụ thuộc mạng.
    enable_weather: bool
    # --- Trang quản trị -------------------------------------------------------
    # FAIL-CLOSED: thiếu bất kỳ giá trị nào trong 3 giá trị dưới -> admin TẮT hoàn toàn
    # và /api/v1/admin/* trả 503. Không bao giờ được mặc định thành "cho qua".
    admin_username: str
    admin_password_hash: str
    admin_token_secret: str
    admin_token_ttl_seconds: int
    # --- Tài khoản người dùng cuối --------------------------------------------
    # File CSDL RIÊNG, không chung với `restaurants_db`: kho quán dựng lại được từ CSV,
    # kho tài khoản thì mất là mất hẳn. Xem `sqlite_user_repository.py`.
    users_db: Path
    # FAIL-CLOSED giống admin: thiếu secret -> tính năng tài khoản TẮT, /auth/* trả 503.
    # Phải KHÁC `admin_token_secret` để chữ ký hai bên không dùng lẫn được.
    user_token_secret: str
    user_token_ttl_seconds: int

    # --- Quên mật khẩu: gửi thư qua SMTP -------------------------------------
    # Thiếu bất kỳ thứ nào trong 4 dòng dưới thì tính năng TẮT hẳn và endpoint trả 503 kèm
    # hướng dẫn — không giả vờ "đã gửi" rồi để người dùng ngồi đợi lá thư không tồn tại.
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_sender: str
    # Secret RIÊNG cho token đặt lại mật khẩu. Bỏ trống thì lui về `user_token_secret`
    # (xem `dependencies.py`) — chạy được vẫn hơn tắt hẳn, nhưng tách ra thì an toàn hơn.
    reset_token_secret: str
    reset_token_ttl_seconds: int
    # Địa chỉ gốc của FRONTEND, dùng để dựng đường dẫn trong thư. Chạy máy mình thì là
    # http://localhost:5173; deploy thật thì đổi bằng biến môi trường.
    app_base_url: str

    @staticmethod
    def from_env() -> "Settings":
        # Nạp `.env.local` TRƯỚC khi đọc biến môi trường. Không có file thì bỏ qua, và
        # biến đã đặt sẵn trong shell luôn THẮNG file — xem `config/dotenv.py`.
        nap_env_local()

        origins = os.getenv("MOODBITE_CORS_ORIGINS", "*")
        return Settings(
            restaurants_csv=_path_from_env(
                "MOODBITE_RESTAURANTS_CSV",
                "data_pipeline/data_cleaned/dataset_moodbite_features.csv",
            ),
            restaurants_db=_path_from_env(
                "MOODBITE_RESTAURANTS_DB",
                "data_pipeline/data_cleaned/moodbite.db",
            ),
            storage_backend=os.getenv("MOODBITE_STORAGE", "csv").strip().lower(),
            restaurant_details_json=_path_from_env(
                "MOODBITE_RESTAURANT_DETAILS_JSON",
                "data_pipeline/data_cleaned/restaurant_details.json",
            ),
            dish_knowledge_json=_path_from_env(
                "MOODBITE_DISH_KNOWLEDGE_JSON",
                "data_pipeline/dish_knowledge_base.json",
            ),
            dish_catalog_json=_path_from_env(
                "MOODBITE_DISH_CATALOG_JSON",
                "data_pipeline/data_cleaned/dish_catalog.json",
            ),
            review_summaries_json=_path_from_env(
                "MOODBITE_REVIEW_SUMMARIES_JSON",
                "data_pipeline/data_cleaned/review_summaries.json",
            ),
            dish_model_path=_path_from_env(
                "MOODBITE_DISH_MODEL", "models/dish_rule_classifier.joblib"
            ),
            interactions_path=_path_from_env(
                "MOODBITE_INTERACTIONS", "data_pipeline/data_cleaned/interactions.jsonl"
            ),
            dish_adapter_mode=os.getenv("DISH_ADAPTER", "auto").strip().lower(),
            cors_allow_origins=tuple(
                o.strip() for o in origins.split(",") if o.strip()
            ),
            # Mặc định TẮT: bật thời tiết làm mọi lượt tìm kiếm phụ thuộc mạng.
            # Bật bằng MOODBITE_ENABLE_WEATHER=1 khi chạy thật.
            enable_weather=os.getenv("MOODBITE_ENABLE_WEATHER", "") == "1",
            admin_username=os.getenv("MOODBITE_ADMIN_USER", "").strip(),
            admin_password_hash=os.getenv("MOODBITE_ADMIN_PASSWORD_HASH", "").strip(),
            admin_token_secret=os.getenv("MOODBITE_ADMIN_SECRET", "").strip(),
            admin_token_ttl_seconds=int(
                os.getenv("MOODBITE_ADMIN_TOKEN_TTL", "3600") or 3600
            ),
            users_db=_path_from_env(
                "MOODBITE_USERS_DB", "data_pipeline/data_cleaned/moodbite_users.db"
            ),
            user_token_secret=os.getenv("MOODBITE_AUTH_SECRET", "").strip(),
            user_token_ttl_seconds=int(
                os.getenv("MOODBITE_AUTH_TOKEN_TTL", str(DEFAULT_USER_TOKEN_TTL_SECONDS))
                or DEFAULT_USER_TOKEN_TTL_SECONDS
            ),
            smtp_host=os.getenv("MOODBITE_SMTP_HOST", "").strip(),
            # 587 = cổng SMTP có STARTTLS, cổng Gmail khuyên dùng.
            smtp_port=int(os.getenv("MOODBITE_SMTP_PORT", "587") or 587),
            smtp_username=os.getenv("MOODBITE_SMTP_USER", "").strip(),
            # KHÔNG `.strip()` mật khẩu: mật khẩu ứng dụng của Google hiển thị theo nhóm
            # 4 ký tự có khoảng trắng, nhưng khoảng trắng đó KHÔNG thuộc mật khẩu. Xử lý
            # đúng là bỏ MỌI khoảng trắng, không chỉ hai đầu.
            smtp_password="".join(os.getenv("MOODBITE_SMTP_PASSWORD", "").split()),
            smtp_sender=os.getenv("MOODBITE_SMTP_FROM", "").strip(),
            reset_token_secret=os.getenv("MOODBITE_RESET_SECRET", "").strip(),
            reset_token_ttl_seconds=int(
                os.getenv("MOODBITE_RESET_TOKEN_TTL", str(DEFAULT_RESET_TTL_SECONDS))
                or DEFAULT_RESET_TTL_SECONDS
            ),
            app_base_url=os.getenv("MOODBITE_APP_URL", "http://localhost:5173").strip(),
        )

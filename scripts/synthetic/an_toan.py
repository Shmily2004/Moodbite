"""Chốt chặn: dữ liệu GIẢ LẬP không bao giờ được lẫn vào dữ liệu THẬT.

VÌ SAO PHẢI CÓ FILE RIÊNG CHO CHUYỆN NÀY: `interactions.jsonl` và `moodbite_users.db` thật
là thứ KHÔNG dựng lại được. Một lần chạy giả lập ghi nhầm vào đó là trộn hàng nghìn sự kiện
bịa vào nguồn nhãn huấn luyện, và sau đó không còn cách nào tách ra cho sạch.

Nên có HAI lớp kiểm độc lập:
  1. `assert_safe_out_dir`  — kiểm thư mục đích TRƯỚC khi làm gì.
  2. `assert_settings_are_synthetic` — kiểm Settings app THỰC SỰ đọc được, SAU khi đặt
     biến môi trường. Lớp này bắt được trường hợp `.env.local` hay code đổi cách đọc biến.

Mọi bản ghi giả lập đều mang dấu nhận diện: session `synthetic-`, tên `demo_`, email
`@example.invalid` (tên miền RFC 2606 dành riêng, không bao giờ nhận thư thật).
"""
from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import MutableMapping, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REAL_DATA_DIR = PROJECT_ROOT / "data_pipeline" / "data_cleaned"
REAL_INTERACTIONS = REAL_DATA_DIR / "interactions.jsonl"
REAL_USERS_DB = REAL_DATA_DIR / "moodbite_users.db"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data_pipeline" / "data_synthetic"

SESSION_PREFIX = "synthetic-"
USERNAME_PREFIX = "demo_"
EMAIL_DOMAIN = "example.invalid"


class UnsafeSyntheticPathError(RuntimeError):
    """Đường dẫn giả lập trỏ vào (hoặc trùng) dữ liệu thật — từ chối chạy."""


@dataclass(frozen=True)
class SyntheticPaths:
    out_dir: Path
    interactions: Path
    users_db: Path
    sessions: Path
    personas: Path
    eval_results: Path


def synthetic_paths(out_dir: Path) -> SyntheticPaths:
    out_dir = Path(out_dir)
    return SyntheticPaths(
        out_dir=out_dir,
        interactions=out_dir / "interactions.jsonl",
        users_db=out_dir / "moodbite_users.db",
        sessions=out_dir / "sessions.jsonl",
        personas=out_dir / "personas.json",
        eval_results=out_dir / "eval_results.json",
    )


def _is_inside(path: Path, folder: Path) -> bool:
    try:
        path.resolve().relative_to(folder.resolve())
        return True
    except ValueError:
        return False


def assert_safe_out_dir(paths: SyntheticPaths) -> None:
    """Từ chối mọi thư mục đích nằm trong `data_cleaned/` hoặc trùng file thật."""
    if _is_inside(paths.out_dir, REAL_DATA_DIR):
        raise UnsafeSyntheticPathError(
            f"--out-dir nằm trong {REAL_DATA_DIR.name}/ (dữ liệu THẬT). "
            "Hãy dùng data_pipeline/data_synthetic."
        )
    for synthetic, real in (
        (paths.interactions, REAL_INTERACTIONS),
        (paths.users_db, REAL_USERS_DB),
    ):
        if synthetic.resolve() == real.resolve():
            raise UnsafeSyntheticPathError(f"Đường dẫn giả lập trùng file thật: {real.name}")


def apply_synthetic_env(
    paths: SyntheticPaths, environ: Optional[MutableMapping[str, str]] = None
) -> None:
    """Đặt biến môi trường để app (dựng TRONG tiến trình này) đọc/ghi file giả lập.

    Biến đặt trong tiến trình THẮNG `.env.local` (xem `config/dotenv.py`), nên dù máy có
    cấu hình thật thì app vẫn trỏ vào thư mục giả lập.
    """
    env = os.environ if environ is None else environ
    env["MOODBITE_INTERACTIONS"] = str(paths.interactions)
    env["MOODBITE_USERS_DB"] = str(paths.users_db)
    env["MOODBITE_SYNTHETIC_DATA"] = "1"
    # Không gọi mạng: thời tiết thật làm kết quả phụ thuộc giờ chạy, mất tính tái lập.
    env["MOODBITE_ENABLE_WEATHER"] = "0"
    # TẮT gửi thư. Đăng ký tự gửi thư xác minh; máy có cấu hình SMTP thật trong
    # `.env.local` sẽ bắn hàng chục lá thư tới @example.invalid và ăn hạn mức Gmail.
    env["MOODBITE_SMTP_HOST"] = ""
    # Khoá ký token RIÊNG cho lần chạy này: token giả lập không dùng được ở app thật.
    # Mật khẩu demo thì vẫn đăng nhập được sau này vì hash mật khẩu không phụ thuộc khoá.
    env["MOODBITE_AUTH_SECRET"] = secrets.token_hex(32)


def assert_settings_are_synthetic(settings, paths: SyntheticPaths) -> None:
    """Lớp kiểm thứ hai: đọc lại đúng Settings mà app dùng."""
    if Path(settings.interactions_path).resolve() != paths.interactions.resolve():
        raise UnsafeSyntheticPathError("App không trỏ interactions vào thư mục giả lập.")
    if Path(settings.users_db).resolve() != paths.users_db.resolve():
        raise UnsafeSyntheticPathError("App không trỏ kho tài khoản vào thư mục giả lập.")
    if not settings.synthetic_data:
        raise UnsafeSyntheticPathError("Cờ MOODBITE_SYNTHETIC_DATA chưa bật.")


def reset_out_dir(paths: SyntheticPaths) -> list[str]:
    """Xoá ĐÚNG các file giả lập đã biết tên — không `rmtree` cả thư mục.

    Xoá theo danh sách để lỡ truyền nhầm `--out-dir` cũng không quét sạch thứ khác.
    SQLite có thể để lại file `-wal`/`-shm` nên xoá cả họ tên đó.
    """
    assert_safe_out_dir(paths)
    removed = []
    for base in (paths.interactions, paths.sessions, paths.personas, paths.eval_results):
        if base.exists():
            base.unlink()
            removed.append(base.name)
    for f in paths.out_dir.glob(paths.users_db.name + "*"):
        f.unlink()
        removed.append(f.name)
    return removed


def file_fingerprint(path: Path) -> Optional[str]:
    """sha256 của file thật để CHỨNG MINH sau khi chạy là nó không đổi."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

"""Sinh NGƯỜI DÙNG + TƯƠNG TÁC GIẢ LẬP bằng cách gọi API thật của MoodBite.

    python scripts/gia_lap_nguoi_dung.py --users 60 --days 14 --reset

Chủ dự án yêu cầu 2026-09-16: "giả lập dữ liệu người dùng để xử lý, random".

DỮ LIỆU GIẢ LẬP KHÔNG BAO GIỜ CHẠM VÀO DỮ LIỆU THẬT:
  * mọi thứ ghi vào `data_pipeline/data_synthetic/` (đã .gitignore);
  * `data_cleaned/interactions.jsonl` và `moodbite_users.db` thật được băm sha256 trước
    và sau khi chạy — lệch là báo lỗi to;
  * mỗi bản ghi mang dấu: session `synthetic-`, tên `demo_`, email `@example.invalid`.

Vì sao gọi API qua TestClient mà không ghi thẳng file: dữ liệu phải đi qua đúng kiểm tra
hợp lệ, xác thực và luật tính nhãn của server. Ghi thẳng file là tự bịa ra định dạng.

GIỚI HẠN: "ngày" chỉ là mốc logic trong `sessions.jsonl`. Server tự đóng dấu giờ THẬT lúc
ghi, nên trong `interactions.jsonl` mọi sự kiện mang giờ của lần chạy script.

Mật khẩu mọi tài khoản demo: xem `DEMO_PASSWORD` (dùng để đăng nhập thử trên giao diện).
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.synthetic.an_toan import (  # noqa: E402
    DEFAULT_OUT_DIR, EMAIL_DOMAIN, REAL_INTERACTIONS, REAL_USERS_DB,
    apply_synthetic_env, assert_safe_out_dir, assert_settings_are_synthetic,
    file_fingerprint, reset_out_dir, synthetic_paths,
)
from scripts.synthetic.persona import sample_persona  # noqa: E402
from scripts.synthetic.session import run_session  # noqa: E402

logger = logging.getLogger("moodbite.synthetic")

DEMO_PASSWORD = "demo-moodbite-2026"
# Chỉ lấy phường có đủ quán làm "nơi ở": phường thưa quán thì người dùng giả lập ở đó
# gần như phiên nào cũng trống, không đại diện cho người dùng thật của app.
MIN_RESTAURANTS_PER_WARD = 300
TOP_WARDS = 15


def ward_centers_from_dataset(restaurants) -> list[dict]:
    """Tâm các phường ĐÔNG QUÁN, tính từ chính dataset (trung bình toạ độ quán).

    Không hardcode toạ độ: dataset đổi (thêm nguồn, sáp nhập phường) thì tâm tự đổi theo.
    """
    groups: dict[str, list] = defaultdict(list)
    for r in restaurants:
        if r.district:
            groups[r.district].append(r.location)
    centers = [
        {"ward": ward, "count": len(locs),
         "lat": sum(l.lat for l in locs) / len(locs),
         "lng": sum(l.lng for l in locs) / len(locs)}
        for ward, locs in groups.items() if len(locs) >= MIN_RESTAURANTS_PER_WARD
    ]
    return sorted(centers, key=lambda c: -c["count"])[:TOP_WARDS]


def poisson(rng: random.Random, lam: float) -> int:
    """Số phiên trong ngày (thuật toán Knuth; lam nhỏ nên vòng lặp ngắn)."""
    threshold, k, p = pow(2.718281828459045, -lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= threshold:
            return k
        k += 1


def client_for_ip(app, ip: str):
    """TestClient mà server thấy là đến từ `ip` riêng — mỗi người dùng một thiết bị.

    VÌ SAO: giới hạn tần suất đăng ký là 3 lần/giờ/IP. Mọi request TestClient mặc định
    cùng host "testclient", nên người demo thứ 4 bị chặn. Nới giới hạn là làm yếu bảo mật;
    gán mỗi người một IP thì đúng với thực tế hơn. Dải 198.18.0.0/15 (RFC 2544) dành cho
    đo kiểm, không bao giờ là IP thật.
    """
    from fastapi.testclient import TestClient

    async def asgi(scope, receive, send):
        if scope["type"] == "http":
            scope = dict(scope, client=(ip, 50000))
        await app(scope, receive, send)

    return TestClient(asgi, raise_server_exceptions=False)


def register_or_login(client, persona) -> str:
    body = {"username": persona.username, "password": DEMO_PASSWORD,
            "display_name": f"Người dùng demo {persona.username[-4:]}",
            "email": f"{persona.username}@{EMAIL_DOMAIN}"}
    resp = client.post("/api/v1/auth/register", json=body)
    if resp.status_code not in (201, 409):
        raise RuntimeError(f"Đăng ký {persona.username} lỗi: {resp.status_code} {resp.text[:200]}")
    # Đăng nhập lại cả khi vừa đăng ký: để luồng /auth/login cũng được chạy thật.
    resp = client.post("/api/v1/auth/login",
                       json={"username": persona.username, "password": DEMO_PASSWORD})
    if resp.status_code != 200:
        raise RuntimeError(f"Đăng nhập {persona.username} lỗi: {resp.status_code}")
    return resp.json()["data"]["token"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--users", type=int, default=200)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--reset", action="store_true",
                        help="Xoá dữ liệu giả lập cũ trong --out-dir trước khi sinh.")
    args = parser.parse_args()
    # Console Windows mặc định cp1252: không đổi thì log tiếng Việt thành ký tự rác.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    paths = synthetic_paths(args.out_dir)
    assert_safe_out_dir(paths)
    if args.reset:
        logger.info("Đã xoá file giả lập cũ: %s", reset_out_dir(paths) or "(không có)")
    elif paths.interactions.exists() or paths.users_db.exists():
        print(f"{paths.out_dir} đã có dữ liệu giả lập. Thêm --reset để sinh lại từ đầu.")
        return 2
    paths.out_dir.mkdir(parents=True, exist_ok=True)
    real_before = (file_fingerprint(REAL_INTERACTIONS), file_fingerprint(REAL_USERS_DB))

    apply_synthetic_env(paths)
    from src.domain.value_objects.mood import SUPPORTED_MOODS
    from src.infrastructure.config.settings import Settings
    from src.presentation.api.main import create_app

    settings = Settings.from_env()
    assert_settings_are_synthetic(settings, paths)
    # Log từng request (httpx + moodbite) quá ồn: hàng nghìn dòng che mất tiến độ.
    logging.getLogger("moodbite").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger.setLevel(logging.INFO)
    started = time.perf_counter()
    app = create_app(settings)
    repo = app.state.container.restaurant_repository
    if not repo.is_ready:
        print("Kho quán chưa sẵn sàng — chạy data_pipeline trước (xem /health).")
        return 1
    wards = ward_centers_from_dataset(repo.list_all())
    logger.info("Dựng app xong sau %.1fs. %d phường làm nơi ở.", time.perf_counter() - started, len(wards))

    rng = random.Random(args.seed)
    moods = tuple(SUPPORTED_MOODS)
    personas = [sample_persona(rng, i + 1, wards, moods) for i in range(args.users)]
    paths.personas.write_text(json.dumps(
        {"synthetic": True, "seed": args.seed, "wards": wards,
         "personas": [p.to_dict() for p in personas]}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    counters: Counter = Counter()
    users = []
    for i, persona in enumerate(personas):
        client = client_for_ip(app, f"198.18.{i // 250}.{i % 250 + 1}")
        users.append((persona, client, register_or_login(client, persona)))
    logger.info("Đã đăng ký + đăng nhập %d tài khoản demo.", len(users))

    with paths.sessions.open("w", encoding="utf-8") as out:
        for day in range(args.days):
            for persona, client, token in users:
                for _ in range(poisson(rng, persona.activity_per_day)):
                    record = run_session(client, token, persona, rng, day, moods, counters)
                    counters["sessions"] += 1
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.info("Ngày %d/%d: %d phiên, %d sự kiện.", day + 1, args.days,
                        counters["sessions"], counters["events_total"])

    real_after = (file_fingerprint(REAL_INTERACTIONS), file_fingerprint(REAL_USERS_DB))
    if real_after != real_before:
        print("!!! DỮ LIỆU THẬT BỊ THAY ĐỔI TRONG LÚC CHẠY — kiểm tra ngay. !!!")
        return 3
    print_summary(args, counters, time.perf_counter() - started, paths)
    return 0


def print_summary(args, counters: Counter, elapsed: float, paths) -> None:
    total = counters["events_total"]
    print("\n=== TÓM TẮT DỮ LIỆU GIẢ LẬP (không phải người dùng thật) ===")
    print(f"Người dùng demo      : {args.users}   (seed={args.seed}, {args.days} ngày)")
    print(f"Phiên                : {counters['sessions']}  (bỏ về không bấm: {counters['sessions_abandoned']})")
    print(f"Gọi API              : suggest={counters['api_dish_suggest']}  dish_detail={counters['api_dish_detail']}  "
          f"dish_restaurants={counters['api_dish_restaurants']}  search={counters['api_search']}")
    print(f"Sự kiện tương tác    : {total}  (lỗi: {counters['interaction_errors']})")
    for key in sorted(k for k in counters if k.startswith("event_") and k != "events_total"):
        print(f"  {key[6:]:<20}: {counters[key]}")
    rate = counters["events_positive"] / total if total else 0.0
    print(f"Tỷ lệ tín hiệu dương : {rate:.1%}  (server tự tính is_positive_signal)")
    for key in sorted(k for k in counters if k.startswith("saved_")):
        print(f"  {key:<27}: {counters[key]}")
    print(f"Thời gian            : {elapsed:.1f}s")
    print(f"Dữ liệu thật         : KHÔNG đổi (sha256 trước = sau)")
    print(f"Ghi vào              : {paths.out_dir}")


if __name__ == "__main__":
    raise SystemExit(main())

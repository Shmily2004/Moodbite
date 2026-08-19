"""Dựng CSDL SQLite từ dataset CSV.

    python scripts/build_sqlite.py

VÌ SAO: bản CSV chỉ đọc được, trong khi trang Admin cần sửa/ẩn quán. SQLite cho ta ghi
có transaction mà không cần cài server, không cần thẻ thanh toán.

Ý TƯỞNG QUAN TRỌNG: script này KHÔNG tự parse CSV. Nó dùng lại `CsvRestaurantRepository`
để đọc, rồi ghi chính các entity đó xuống SQLite. Nhờ vậy hai repository chắc chắn sinh ra
entity GIỐNG HỆT nhau - nếu tự viết lại phần parse thì hai bên sẽ trôi khác nhau theo thời
gian (giá bị ép thành số, NaN thành 0...) và đó đúng là loại bug dự án đã gặp.

Chạy lại nhiều lần được: mặc định ghi đè bảng cũ (--keep-hidden để giữ lại quán Admin đã ẩn).
"""
from __future__ import annotations

import argparse
import re
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.repositories.csv_restaurant_repository import (  # noqa: E402
    CsvRestaurantRepository,
)
from src.infrastructure.repositories.json_restaurant_details_repository import (  # noqa: E402
    JsonRestaurantDetailsRepository,
)
from src.infrastructure.repositories.sqlite_restaurant_repository import (  # noqa: E402
    SCHEMA,
)

INSERT = """
INSERT INTO restaurants (
    place_id, name, category, lat, lng, address, cuisine, price, rating,
    reviews_count, mood_scores, atmosphere_tags, review_text, thumbnail_url, opening_hours,
    is_active, permanently_closed, temporarily_closed,
    district, dietary, amenities, phone, website, source,
    data_confidence, experience_cluster_id, experience_cluster_label
) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""


def _row(restaurant, is_active: bool = True) -> tuple:
    """Entity -> tuple đúng thứ tự cột của INSERT.

    `ensure_ascii=False` để tiếng Việt lưu nguyên chữ, đọc CSDL bằng tay còn hiểu được.
    """
    return (
        restaurant.place_id,
        restaurant.name,
        restaurant.category,
        restaurant.location.lat,
        restaurant.location.lng,
        restaurant.address,
        restaurant.cuisine,
        restaurant.price,          # CHUỖI - tuyệt đối không ép float
        restaurant.rating,         # None giữ nguyên None -> NULL
        restaurant.reviews_count,
        json.dumps(restaurant.mood_scores, ensure_ascii=False),
        json.dumps(restaurant.atmosphere_tags, ensure_ascii=False),
        restaurant.review_text,
        restaurant.thumbnail_url,
        restaurant.opening_hours,
        1 if is_active else 0,
        # None giữ nguyên None -> NULL: 'không biết' phải khác 'biết chắc đang mở'.
        None if restaurant.permanently_closed is None else int(restaurant.permanently_closed),
        None if restaurant.temporarily_closed is None else int(restaurant.temporarily_closed),
        restaurant.district,
        json.dumps(restaurant.dietary, ensure_ascii=False),
        json.dumps(restaurant.amenities, ensure_ascii=False),
        restaurant.phone,
        restaurant.website,
        restaurant.source,
        restaurant.data_confidence,
        restaurant.experience_cluster_id,
        restaurant.experience_cluster_label,
    )


def _schema_khac(conn) -> bool:
    """Bảng hiện có thiếu cột nào so với `SCHEMA` không?

    So theo TÊN CỘT chứ không so chuỗi SQL: chuỗi có khoảng trắng/chú thích khác nhau vẫn
    là cùng một lược đồ.
    """
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(restaurants)").fetchall()
    }
    if not existing:
        return False        # bảng chưa tồn tại -> cứ tạo mới, không cần drop
    mong_doi = set(re.findall(r"^\s{4}(\w+)\s+(?:TEXT|INTEGER|REAL)", SCHEMA, re.M))
    return not mong_doi.issubset(existing)


def _hidden_place_ids(db_path: Path) -> set[str]:
    """placeId của các quán Admin đã ẩn, để dựng lại CSDL không làm chúng hiện lại."""
    if not db_path.exists():
        return set()
    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT place_id FROM restaurants WHERE is_active = 0"
            ).fetchall()
        return {r[0] for r in rows if r[0]}
    except sqlite3.Error:
        # Bảng chưa tồn tại / file hỏng -> coi như chưa ẩn quán nào.
        return set()


def _refuse_if_user_database(db_path: Path) -> str | None:
    """Chan viec ghi de len kho TAI KHOAN. Tra ly do neu phai dung, None neu an toan.

    VI SAO CAN CHOT NAY: hai file .db nam CUNG mot thu muc va chi khac ten. CSDL quan la
    DU LIEU DAN XUAT - tai lieu con khuyen khich xoa di dung lai. CSDL tai khoan la DU
    LIEU GOC - mat la mat han. Chi can go nham `--out` mot lan, hoac copy nham lenh, la
    script nay se DELETE sach bang trong file tai khoan.

    Kiem theo NOI DUNG (co bang `users` khong) chu khong chi theo ten file: doi ten file
    van phai duoc bao ve.
    """
    settings = Settings.from_env()
    if db_path.resolve() == settings.users_db.resolve():
        return f"{db_path} la kho TAI KHOAN (MOODBITE_USERS_DB), khong phai kho quan"
    if not db_path.exists():
        return None
    try:
        with sqlite3.connect(db_path) as conn:
            has_users = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'"
            ).fetchone()
    except sqlite3.Error:
        return None
    if has_users:
        return f"{db_path} dang chua bang `users` (tai khoan nguoi dung)"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Dung CSDL SQLite tu dataset CSV")
    parser.add_argument(
        "--out", default=None,
        help="Duong dan file .db (mac dinh: data_pipeline/data_cleaned/moodbite.db)",
    )
    parser.add_argument(
        "--keep-hidden", action="store_true",
        help="Giu nguyen cac quan da bi Admin an (is_active=0) trong CSDL cu",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    # Lay tu settings chu KHONG tu ghep duong dan: truoc day cho nay tu tinh
    # `restaurants_csv.parent / "moodbite.db"`, nen khi doi MOODBITE_RESTAURANTS_CSV thi
    # script ghi mot noi con backend doc mot noi khac - dung nhu loi hardcode duong dan
    # ma CLAUDE.md muc 6 cam.
    db_path = Path(args.out) if args.out else settings.restaurants_db

    ly_do = _refuse_if_user_database(db_path)
    if ly_do:
        print(f"[TU CHOI] {ly_do}.")
        print("          Script nay XOA SACH bang roi ghi lai tu CSV. Kho tai khoan")
        print("          khong dung lai duoc tu bat ky nguon nao - mat la mat han.")
        print(f"          Kho quan mac dinh: {settings.restaurants_db}")
        return 1

    if not settings.restaurants_csv.exists():
        print(f"[LOI] Khong tim thay CSV: {settings.restaurants_csv}")
        print("      Chay: python -m data_pipeline.feature_engineering")
        return 1

    hidden = _hidden_place_ids(db_path) if args.keep_hidden else set()
    if hidden:
        print(f"Giu lai {len(hidden)} quan da an tu CSDL cu")

    # Ghép review giống hệt composition root, để cột review_text không bị rỗng.
    details = JsonRestaurantDetailsRepository(settings.restaurant_details_json)
    review_texts = details.review_texts() if details.is_ready else {}
    print(f"Doc CSV : {settings.restaurants_csv}")
    repo = CsvRestaurantRepository(
        settings.restaurants_csv,
        review_texts=review_texts,
        thumbnail_urls=details.thumbnail_urls() if details.is_ready else {},
    )
    if not repo.is_ready:
        print(f"[LOI] {repo.load_error}")
        return 1

    restaurants = repo.list_all()
    print(f"Doc duoc: {len(restaurants)} quan")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        # CSDL cũ có thể thiếu cột mới thêm về sau (`CREATE TABLE IF NOT EXISTS` KHÔNG
        # thêm cột vào bảng đã tồn tại). Bug thật 2026-08-19: file .db dựng từ trước khi
        # có cột `thumbnail_url`, chạy lại script thì nổ
        # "table restaurants has no column named thumbnail_url".
        # Lược đồ lệch -> XOÁ BẢNG rồi dựng lại. An toàn vì mọi dữ liệu đều dựng lại được
        # từ CSV; riêng danh sách quán đã ẩn thì đã đọc ra trước đó (`--keep-hidden`).
        if _schema_khac(conn):
            print("Luoc do CSDL cu da lech -> dung lai bang restaurants")
            conn.execute("DROP TABLE IF EXISTS restaurants")
        conn.executescript(SCHEMA)
        # Dựng lại từ đầu: dataset là snapshot do pipeline sinh ra, không phải nguồn
        # ghi tay, nên hợp nhất từng dòng sẽ phức tạp mà không được lợi gì.
        conn.execute("DELETE FROM restaurants")
        conn.executemany(
            INSERT,
            [_row(r, is_active=(r.place_id not in hidden)) for r in restaurants],
        )
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM restaurants WHERE is_active = 1"
        ).fetchone()[0]

    size_mb = db_path.stat().st_size / 1024 / 1024
    print(f"Ghi xong: {db_path} ({size_mb:.1f} MB)")
    print(f"  tong    : {total}")
    print(f"  dang bat: {active}")
    print(f"  da an   : {total - active}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Chỉ ra KHU VỰC nào cần cào thêm dữ liệu Google Maps, kèm toạ độ để dán vào Apify.

    python scripts/scrape_targets.py
    python scripts/scrape_targets.py --points 12 --radius 1.5

VÌ SAO CẦN: dataset hiện có ~52.8k quán (OSM + Overture) nhưng chỉ ~1.4k quán có
rating/review/ảnh/giá (lấy từ Apify Google Maps). Phần thiếu KHÔNG rải đều - có phường
gần 4.000 quán mà chỉ 45 quán có chi tiết. Script này đo chỗ thiếu và xuất ra:

    1) Bảng phường/xã ưu tiên  - để người đọc hiểu đang nói tới khu nào.
    2) Danh sách ĐIỂM QUÉT     - tâm + ô vuông GeoJSON, dán thẳng vào `customGeolocation`
                                 của Apify Google Maps Scraper.

Điểm quét chọn theo THUẬT TOÁN THAM LAM: mỗi vòng lấy tâm bao phủ được nhiều quán
"chưa có chi tiết" nhất, rồi loại các quán đã nằm trong bán kính đó để vòng sau không
chọn lại chỗ cũ. Nhờ vậy N điểm quét không chồng lên nhau.

KHÔNG cào ShopeeFood/GrabFood/Foody/TripAdvisor/Facebook - ToS cấm (xem CLAUDE.md 4b).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATASET = Path("data_pipeline/data_cleaned/dataset_moodbite_features.csv")
OUT_JSON = Path("data_pipeline/data_raw/scrape_targets.json")

# 1 độ vĩ ~ 111km. Dùng để đổi bán kính km sang độ khi dựng ô vuông.
KM_PER_DEG_LAT = 111.0

# Từ khoá tìm kiếm cho Apify. Đây là các danh mục Google hay gắn cho quán ăn ở Hà Nội;
# tìm bằng LOẠI HÌNH phủ rộng hơn tìm bằng tên món, vì mục tiêu là làm giàu quán ĐÃ CÓ
# trong dataset chứ không phải khám phá món mới.
SEARCH_TERMS = [
    "nhà hàng",
    "quán ăn",
    "quán cà phê",
    "quán ăn vặt",
    "quán bia",
    "tiệm bánh",
]


def _haversine_km(lat1, lng1, lat2_series, lng2_series):
    """Khoảng cách trên mặt cầu từ MỘT điểm tới cả cột toạ độ."""
    r = 6371.0
    p1 = math.radians(lat1)
    lat2 = lat2_series.map(math.radians)
    dlat = lat2 - p1
    dlng = lng2_series.map(math.radians) - math.radians(lng1)
    a = (dlat / 2).map(math.sin) ** 2 + math.cos(p1) * lat2.map(math.cos) * (
        dlng / 2
    ).map(math.sin) ** 2
    return 2 * r * a.map(lambda x: math.asin(math.sqrt(x)))


def load() -> pd.DataFrame:
    if not DATASET.exists():
        raise SystemExit(
            f"Chưa có {DATASET}. Chạy pipeline trước:\n"
            "  python -m data_pipeline.merge_and_prepare_raw\n"
            "  python -m data_pipeline.data_cleaning\n"
            "  python -m data_pipeline.feature_engineering"
        )
    df = pd.read_csv(DATASET, low_memory=False)
    df = df.dropna(subset=["location/lat", "location/lng"])
    # "Có chi tiết" = đã đi qua Apify Google Maps: có điểm đánh giá thật.
    # KHÔNG coi ô trống là 0 sao - trống nghĩa là CHƯA CÓ DỮ LIỆU (CLAUDE.md mục 4).
    df["has_details"] = df["totalScore"].notna()
    return df


def by_ward(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("district").agg(
        total=("title", "size"),
        detailed=("has_details", "sum"),
        lat=("location/lat", "median"),
        lng=("location/lng", "median"),
    )
    g["missing"] = g["total"] - g["detailed"]
    g["pct"] = (g["detailed"] / g["total"] * 100).round(1)
    return g.sort_values("missing", ascending=False)


def greedy_points(df: pd.DataFrame, n_points: int, radius_km: float) -> list:
    """Chọn n tâm quét KHÔNG chồng nhau, mỗi tâm phủ nhiều quán thiếu chi tiết nhất."""
    pool = df[~df["has_details"]].copy()
    # Ứng viên tâm = ô lưới ~1.1km, lấy tâm khối lượng của ô. Duyệt từng quán làm tâm sẽ
    # chính xác hơn nhưng chậm gấp hàng trăm lần mà tâm chỉ lệch vài trăm mét.
    pool["gy"] = (pool["location/lat"] / 0.01).round() * 0.01
    pool["gx"] = (pool["location/lng"] / 0.01).round() * 0.01
    picks = []
    for _ in range(n_points):
        if pool.empty:
            break
        cand = (
            pool.groupby(["gy", "gx"])
            .agg(n=("title", "size"), lat=("location/lat", "mean"),
                 lng=("location/lng", "mean"))
            .sort_values("n", ascending=False)
        )
        if cand.empty:
            break
        top = cand.iloc[0]
        dist = _haversine_km(top["lat"], top["lng"],
                             pool["location/lat"], pool["location/lng"])
        inside = pool[dist <= radius_km]
        wards = inside["district"].value_counts()
        bbox = _bbox(float(top["lat"]), float(top["lng"]), radius_km)
        picks.append(
            {
                "center": {"lat": round(float(top["lat"]), 5),
                           "lng": round(float(top["lng"]), 5)},
                "radius_km": radius_km,
                "missing_in_radius": int(len(inside)),
                "wards": wards.head(3).index.tolist(),
                "bbox": bbox,
                "google_maps_url":
                    f"https://www.google.com/maps/@{float(top['lat']):.5f},"
                    f"{float(top['lng']):.5f},16z",
            }
        )
        pool = pool[dist > radius_km]
    return picks


def _bbox(lat: float, lng: float, radius_km: float) -> dict:
    dlat = radius_km / KM_PER_DEG_LAT
    dlng = radius_km / (KM_PER_DEG_LAT * math.cos(math.radians(lat)))
    return {
        "south": round(lat - dlat, 5),
        "west": round(lng - dlng, 5),
        "north": round(lat + dlat, 5),
        "east": round(lng + dlng, 5),
    }


def _geojson(bbox: dict) -> dict:
    """Ô vuông cho `customGeolocation` của Apify (GeoJSON Polygon, lng trước lat)."""
    w, s, e, n = bbox["west"], bbox["south"], bbox["east"], bbox["north"]
    return {"type": "Polygon", "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", type=int, default=12, help="số điểm quét cần xuất")
    ap.add_argument("--radius", type=float, default=1.5, help="bán kính mỗi điểm (km)")
    ap.add_argument("--wards", type=int, default=20, help="số phường/xã in ra bảng")
    args = ap.parse_args()

    df = load()
    total, detailed = len(df), int(df["has_details"].sum())
    print(f"Tổng quán: {total:,}  |  đã có chi tiết Google: {detailed:,} "
          f"({detailed / total * 100:.1f}%)  |  còn thiếu: {total - detailed:,}\n")

    g = by_ward(df)
    print(f"--- {args.wards} PHƯỜNG/XÃ THIẾU NHIỀU NHẤT ---")
    print(f"{'phường/xã':<32}{'tổng':>7}{'có ct':>7}{'%':>7}   toạ độ tâm")
    for name, r in g.head(args.wards).iterrows():
        print(f"{name:<32}{int(r['total']):>7}{int(r['detailed']):>7}{r['pct']:>7}   "
              f"{r['lat']:.5f},{r['lng']:.5f}")

    picks = greedy_points(df, args.points, args.radius)
    print(f"\n--- {len(picks)} ĐIỂM QUÉT ĐỀ XUẤT "
          f"(bán kính {args.radius}km, không chồng nhau) ---")
    for i, p in enumerate(picks, 1):
        print(f"{i:>2}. {p['center']['lat']:.5f},{p['center']['lng']:.5f}  "
              f"thiếu {p['missing_in_radius']:>4} quán  |  {', '.join(p['wards'])}")

    payload = {
        "generated_from": str(DATASET),
        "total_places": total,
        "detailed_places": detailed,
        "search_terms": SEARCH_TERMS,
        "wards": [
            {"name": name, "total": int(r["total"]), "detailed": int(r["detailed"]),
             "missing": int(r["missing"]),
             "center": {"lat": round(r["lat"], 5), "lng": round(r["lng"], 5)}}
            for name, r in g.head(args.wards).iterrows()
        ],
        "scan_points": [{**p, "custom_geolocation": _geojson(p["bbox"])} for p in picks],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã ghi: {OUT_JSON}")


if __name__ == "__main__":
    main()

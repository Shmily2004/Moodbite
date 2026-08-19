"""Bổ sung TUỔI THẬT và BẰNG CHỨNG XÁC NHẬN cho từng quán trong dataset.

    python scripts/enrich_freshness.py                # xem trước, KHÔNG ghi
    python scripts/enrich_freshness.py --apply        # ghi vào dataset_moodbite_features.csv
    python scripts/enrich_freshness.py --apply --bo-qua-osm    # chỉ làm phần Overture (không cần mạng)

VẤN ĐỀ ĐANG SỬA
---------------
Cột `last_updated` ghi 97,4% dữ liệu "cập nhật 16-19/08/2026". Nghe rất tươi. Nhưng đó là
NGÀY TA CÀO, không phải ngày quán được xác minh. Sự thật đo được ngày 2026-08-19:

    OSM      : chỉ 34,9% bản ghi được sửa trong năm 2026, cũ nhất là năm 2010
    Overture : 99,7% cập nhật trong năm 2026

Tức là dataset đang tự tin sai về phần OSM, và đang bán rẻ phần Overture.

NGUỒN LẤY TỪ ĐÂU
----------------
Cả hai đều MIỄN PHÍ, KHÔNG CẦN THẺ, KHÔNG VI PHẠM ToS:

  Overture  ->  file parquet ĐÃ TẢI SẴN trên đĩa. Cột `sources` chứa `dataset` và
                `update_time` của từng nền tảng đóng góp. Không tốn thêm byte mạng nào.
  OSM       ->  hỏi lại Overpass với `out meta` để lấy timestamp + tag `check_date`.

Nền tảng đóng góp vào Overture (đo trên dữ liệu Hà Nội): meta 287.839 · Microsoft 1.075 ·
Foursquare 514 · AllThePlaces 430 · PinMeTo 13.

⚠️ VỀ FACEBOOK/INSTAGRAM: cào trực tiếp là vi phạm ToS và bị CLAUDE.md mục 4b cấm. Nhưng
chính Meta ĐÓNG GÓP dữ liệu doanh nghiệp của họ vào Overture dưới giấy phép
CDLA-Permissive-2.0. Lấy qua đường đó là hợp pháp hoàn toàn - và 99,4% quán Overture có
sẵn link Facebook.

VÌ SAO LÀM GIÀU CHỨ KHÔNG DỰNG LẠI PIPELINE
-------------------------------------------
Chạy lại `merge_and_prepare_raw` sẽ chạy lại cả bước KHỬ TRÙNG LẶP, và kết quả khử trùng
lặp có thể khác lần trước (thứ tự file, ngưỡng khoảng cách...). Như vậy là đổi cả tập dữ
liệu chỉ để thêm mấy cột - rủi ro lớn hơn hẳn lợi ích. Script này chỉ GHÉP THÊM CỘT theo
`placeId`, không đụng tới bản thân danh sách quán.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.infrastructure.config.settings import Settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("enrich_freshness")

OVERTURE_CACHE = ROOT / "data_pipeline" / "data_raw" / ".overture_cache" / "ha_noi_places.parquet"

COT_MOI = [
    "source_updated_at",
    "source_datasets",
    "source_confidence",
    "surveyed_at",
    "socials",
]


def tu_overture() -> Dict[str, dict]:
    """{placeId: {...}} lấy từ parquet Overture đã tải sẵn. Không gọi mạng."""
    if not OVERTURE_CACHE.exists():
        logger.warning("Khong co %s - bo qua phan Overture.", OVERTURE_CACHE.name)
        return {}
    try:
        import duckdb
    except ImportError:
        logger.warning("Chua cai duckdb - bo qua phan Overture.")
        return {}

    con = duckdb.connect()
    rows = con.execute(
        f"""
        SELECT id,
               list_max(list_transform(sources, x -> CAST(x.update_time AS VARCHAR))) AS upd,
               list_transform(sources, x -> x.dataset) AS ds,
               confidence,
               socials
        FROM read_parquet('{OVERTURE_CACHE.as_posix()}')
        """
    ).fetchall()
    con.close()

    out: Dict[str, dict] = {}
    for oid, upd, ds, conf, socials in rows:
        # Bỏ "Overture" khỏi danh sách: bản ghi nào cũng có nên không phân biệt được gì.
        nen_tang = [str(d) for d in (ds or []) if d and str(d).lower() != "overture"]
        out[f"overture:{oid}"] = {
            "source_updated_at": upd,
            "source_datasets": json.dumps(nen_tang, ensure_ascii=False),
            "source_confidence": float(conf) if conf is not None else None,
            "surveyed_at": None,   # Overture không có khái niệm xác minh thực địa
            "socials": json.dumps([str(x) for x in (socials or []) if x], ensure_ascii=False),
        }
    return out


def tu_osm(bbox) -> Dict[str, dict]:
    """{placeId: {...}} hỏi lại Overpass với `out meta`.

    Dùng lại chính adapter đang có nên luật cắt ô, đổi mirror, thử lại và cache đều giống
    hệt lúc thu thập - không đẻ ra một đường lấy dữ liệu thứ hai.
    """
    from data_pipeline.sources.osm_overpass import OsmOverpassSource

    logger.info("Hoi lai OpenStreetMap de lay ngay sua that (out meta)...")
    # CACHE RIENG, khong dung chung voi `.osm_cache`: cache cu duoc tao boi cau truy van
    # `out center tags` (khong co meta). Dung chung thi adapter tra ve cache cu va khong
    # bao giờ thấy timestamp - lỗi câm, rất khó tìm ra.
    places = OsmOverpassSource(
        bbox=bbox, cache_dir="data_pipeline/data_raw/.osm_cache_meta"
    ).fetch()
    return {
        p.placeId: {
            "source_updated_at": p.source_updated_at,
            "source_datasets": json.dumps(p.source_datasets, ensure_ascii=False),
            "source_confidence": None,
            "surveyed_at": p.surveyed_at,
            "socials": json.dumps([], ensure_ascii=False),
        }
        for p in places
    }


# Hai bản ghi cùng tên cách nhau dưới ngưỡng này thì coi là CÙNG MỘT QUÁN.
# 150m: cùng ngưỡng đang dùng ở `refresh_check.py`, và cùng lý do - chuỗi như Highlands
# có chi nhánh thật cách nhau vài trăm mét, nới rộng hơn là gộp nhầm hai quán khác nhau.
MAX_KHOANG_CACH_KM = 0.15


def doi_chieu_cheo(df: pd.DataFrame, tra_cuu: Dict[str, dict]) -> int:
    """Tìm bản sao của quán OSM/Apify trong kho Overture -> XÁC NHẬN ĐỘC LẬP.

    VÌ SAO CÓ GIÁ TRỊ: Overture Places được dựng từ Meta, Microsoft, Foursquare,
    AllThePlaces, PinMeTo - KHÔNG có OpenStreetMap (đã kiểm bằng cột `sources`). Nên một
    quán xuất hiện ở CẢ OSM lẫn Overture nghĩa là hai hệ thống hoàn toàn độc lập cùng nói
    quán đó có thật. Đó là thứ gần nhất với "đối chiếu nhiều nền tảng" mà ta làm được mà
    không cần thẻ thanh toán và không vi phạm ToS của ai.

    Ghép theo TÊN (đã bỏ dấu) VÀ KHOẢNG CÁCH. Chỉ tên thì gộp nhầm chi nhánh - đã trả giá
    một lần ở `refresh_check.py`: 73 cặp trùng tên cách nhau tới 22 km.

    Trả về số quán được bổ sung xác nhận.
    """
    try:
        import duckdb
    except ImportError:
        return 0
    if not OVERTURE_CACHE.exists():
        return 0

    from src.domain.value_objects.text import normalize

    con = duckdb.connect()
    rows = con.execute(
        f"""
        SELECT name, lat, lng,
               list_transform(sources, x -> x.dataset) AS ds,
               list_max(list_transform(sources, x -> CAST(x.update_time AS VARCHAR))) AS upd
        FROM read_parquet('{OVERTURE_CACHE.as_posix()}')
        """
    ).fetchall()
    con.close()

    # Gom theo ô lưới ~110m để khỏi so từng cặp trong 289.871 x 4.544 bản ghi.
    B = 0.001
    luoi: Dict[tuple, list] = {}
    for ten, lat, lng, ds, upd in rows:
        chuan = normalize(ten)
        if not chuan or lat is None or lng is None:
            continue
        luoi.setdefault((round(lat / B), round(lng / B)), []).append(
            (chuan, float(lat), float(lng), ds or [], upd)
        )

    bo_sung = 0
    # `location/lat` có dấu '/' nên `itertuples` đổi tên thành `_3`/`_4` THEO VỊ TRÍ -
    # thêm một cột vào đầu CSV là hỏng âm thầm. Đổi tên tường minh trước khi duyệt.
    goi = df[["placeId", "title", "source", "location/lat", "location/lng"]].rename(
        columns={"location/lat": "lat", "location/lng": "lng"}
    )
    for row in goi.itertuples():
        if str(getattr(row, "source", "")).lower() == "overture":
            continue          # đã có sẵn, không cần đối chiếu
        ten = normalize(getattr(row, "title", None))
        lat, lng = row.lat, row.lng
        if not ten or lat is None or lng is None:
            continue
        ox, oy = round(float(lat) / B), round(float(lng) / B)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for chuan, la2, ln2, ds, upd in luoi.get((ox + dx, oy + dy), ()):
                    if chuan != ten:
                        continue
                    if _khoang_cach_km(float(lat), float(lng), la2, ln2) > MAX_KHOANG_CACH_KM:
                        continue
                    hien = tra_cuu.setdefault(row.placeId, {
                        "source_updated_at": None, "source_datasets": "[]",
                        "source_confidence": None, "surveyed_at": None, "socials": "[]",
                    })
                    cu = json.loads(hien.get("source_datasets") or "[]")
                    them = [str(d) for d in ds if d and str(d).lower() != "overture"]
                    hien["source_datasets"] = json.dumps(
                        sorted(set(cu) | set(them)), ensure_ascii=False
                    )
                    # Lấy ngày MỚI HƠN: nguồn nào xác nhận gần đây nhất mới là thứ đáng tin.
                    if upd and (not hien["source_updated_at"] or upd > hien["source_updated_at"]):
                        hien["source_updated_at"] = upd
                    bo_sung += 1
                    break
                else:
                    continue
                break
            else:
                continue
            break
    return bo_sung


def _khoang_cach_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Xấp xỉ phẳng - đủ chính xác ở quy mô vài trăm mét trong một thành phố."""
    return (((lat1 - lat2) * 111.0) ** 2 + ((lng1 - lng2) * 104.0) ** 2) ** 0.5


def _nam(gia_tri: Optional[str]) -> Optional[str]:
    return str(gia_tri)[:4] if gia_tri else None


def bao_cao(df: pd.DataFrame) -> None:
    n = len(df)
    co_ngay = df["source_updated_at"].notna()
    logger.info("")
    logger.info("=" * 64)
    logger.info("TUOI THAT CUA DU LIEU")
    logger.info("=" * 64)
    logger.info("  Co ngay cap nhat THAT : %d/%d = %.1f%%", co_ngay.sum(), n,
                100 * co_ngay.mean())

    nam = df.loc[co_ngay, "source_updated_at"].map(_nam).value_counts().sort_index()
    for k, v in nam.items():
        logger.info("     nam %s: %6d", k, v)

    for nguon in df["source"].dropna().unique():
        phan = df[df["source"] == nguon]
        co = phan["source_updated_at"].notna()
        if not co.any():
            logger.info("  %-18s chua co ngay that", nguon)
            continue
        moi = phan.loc[co, "source_updated_at"].map(_nam).astype(str).ge("2026").mean()
        logger.info("  %-18s %5.1f%% co ngay that, trong do %.1f%% la nam 2026",
                    nguon, 100 * co.mean(), 100 * moi)

    khao_sat = df["surveyed_at"].notna().sum()
    logger.info("  Co nguoi XAC MINH TAN NOI: %d (%.1f%%)", khao_sat, 100 * khao_sat / n)
    co_social = df["socials"].fillna("[]").ne("[]").sum()
    logger.info("  Co link mang xa hoi      : %d (%.1f%%)", co_social, 100 * co_social / n)

    so_nguon = df["source_datasets"].fillna("[]").map(lambda x: len(json.loads(x)))
    logger.info("")
    logger.info("  So NEN TANG doc lap cung xac nhan mot quan:")
    for k, v in so_nguon.value_counts().sort_index().items():
        logger.info("     %d nen tang: %6d quan (%.1f%%)", k, v, 100 * v / n)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bo sung tuoi that cho dataset")
    parser.add_argument("--apply", action="store_true", help="Ghi that vao CSV")
    parser.add_argument("--bo-qua-osm", action="store_true", dest="bo_qua_osm",
                        help="Chi lam phan Overture (khong can mang)")
    args = parser.parse_args()

    settings = Settings.from_env()
    df = pd.read_csv(settings.restaurants_csv, low_memory=False)
    logger.info("Dataset: %d quan", len(df))

    tra_cuu = tu_overture()
    logger.info("Overture: tra cuu duoc %d ban ghi (tu file da tai san)", len(tra_cuu))

    if not args.bo_qua_osm:
        from data_pipeline.sources.osm_overpass import HANOI_BBOX
        try:
            osm = tu_osm(HANOI_BBOX)
            logger.info("OSM: tra cuu duoc %d ban ghi", len(osm))
            tra_cuu.update(osm)
        except Exception as exc:
            # Mạng hỏng thì VẪN LÀM ĐƯỢC phần Overture. Bỏ cả lượt chỉ vì một nguồn lỗi là
            # lãng phí - phần Overture chiếm 89% dataset và không cần mạng.
            logger.warning("Bo qua phan OSM: %s", exc)

    # ĐỐI CHIẾU CHÉO: quán OSM/Apify nào cũng có mặt trong kho Overture thì được thêm
    # xác nhận từ nền tảng độc lập.
    bo_sung = doi_chieu_cheo(df, tra_cuu)
    logger.info("Doi chieu cheo: %d quan duoc nen tang doc lap xac nhan them", bo_sung)

    for cot in COT_MOI:
        df[cot] = df["placeId"].map(lambda pid: (tra_cuu.get(pid) or {}).get(cot))

    bao_cao(df)

    if not args.apply:
        logger.info("")
        logger.info("XEM TRUOC - chua ghi gi. Them --apply de ghi that.")
        return 0

    df.to_csv(settings.restaurants_csv, index=False, encoding="utf-8-sig")
    logger.info("")
    logger.info("Da ghi %s", settings.restaurants_csv.name)
    logger.info("Chay tiep: python scripts/build_sqlite.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

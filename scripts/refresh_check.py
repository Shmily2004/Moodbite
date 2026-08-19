"""Cào lại nguồn rồi SO SÁNH với dữ liệu đang dùng — quán nào mới, mất, đổi tên.

    python scripts/refresh_check.py                  # cào lại OSM rồi báo cáo
    python scripts/refresh_check.py --dung-cache     # dùng lại lần cào trước, không gọi mạng
    python scripts/refresh_check.py --xuat bao_cao.json

CHỈ BÁO CÁO, KHÔNG TỰ SỬA DỮ LIỆU. Đây là quyết định có chủ đích, không phải làm dở:

  - Nguồn cào về có thể THIẾU tạm thời. Overpass trả 504 cho một ô là chuyện thường
    (CLAUDE.md mục 4b), và một ô hỏng nghĩa là vài chục quán "biến mất" trong lần cào đó.
    Tự động xoá theo là mất dữ liệu vĩnh viễn vì một lỗi mạng.
  - Quán "mất" khỏi OSM thường KHÔNG phải quán đóng cửa, mà là người vẽ bản đồ gộp node
    vào toà nhà, đổi `amenity`, hoặc sửa nhầm.

Nên việc của script này là ĐƯA RA DANH SÁCH ĐỂ NGƯỜI ĐỌC, rồi người quyết định.

VÌ SAO CẦN
----------
Đo ngày 2026-08-19 trên 981 quán khu trung tâm: chỉ 34,9% bản ghi OSM được sửa trong năm
2026, còn lại là 2010-2025. Dữ liệu quán ăn hỏng dần theo thời gian mà không có tiếng
động nào. Chạy định kỳ (khoảng 1 tháng/lần) là cách rẻ nhất để biết nó hỏng tới đâu.

CHƯA LÀM: TUỔI THẬT CỦA TỪNG QUÁN
---------------------------------
Overpass có trả ngày sửa cuối nếu hỏi `out meta` (đã kiểm chứng: 981 quán khu trung tâm,
34,9% sửa trong năm 2026, cũ nhất là 2010). Adapter OSM hiện gọi `out center tags` nên
KHÔNG lấy về, và script này cũng chưa dùng. Muốn có thì phải sửa adapter + thêm cột vào
pipeline - chủ dự án chưa chọn làm phần đó. Ghi ra đây để người sau khỏi tưởng là không
làm được.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data_pipeline.sources.osm_overpass import OsmOverpassSource  # noqa: E402
from src.domain.value_objects.location import Location  # noqa: E402
from src.domain.value_objects.text import normalize  # noqa: E402
from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.repositories.csv_restaurant_repository import (  # noqa: E402
    CsvRestaurantRepository,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("refresh_check")

CACHE_PATH = ROOT / "data_pipeline" / "data_raw" / ".refresh_cache_osm.json"

# Nguồn mà script này đối chiếu được. Overture ra bản mới theo THÁNG và phải tải parquet
# vài GB, nên không hợp để chạy thường xuyên - đối chiếu Overture là việc riêng, làm khi
# có bản phát hành mới.
SOURCE_DOI_CHIEU = "openstreetmap"

# Hai bản ghi CÙNG TÊN cách nhau dưới ngưỡng này thì coi là MỘT quán bị vẽ lại với ID mới,
# chứ không phải một quán đóng cửa và một quán mới mở.
#
# 150m: người vẽ bản đồ hay xoá node rồi vẽ lại thành đường bao toà nhà, và tâm toà nhà
# có thể lệch vài chục mét so với node cũ. Không được nới rộng hơn nhiều - chuỗi như
# Highlands hay Circle K có nhiều chi nhánh thật cách nhau vài trăm mét, gộp nhầm chúng
# là giấu mất một quán có thật.
MAX_KHOANG_CACH_DOI_ID_KM = 0.15


def lay_moi(dung_cache: bool) -> List[dict]:
    """Cào lại OSM. Trả list dict thay vì RawPlace để ghi thẳng ra cache được."""
    if dung_cache and CACHE_PATH.exists():
        logger.info("Dung cache %s (them --khong-cache de cao lai).", CACHE_PATH.name)
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    logger.info("Cao lai OpenStreetMap (mien phi, khong can key)...")
    places = OsmOverpassSource().fetch()
    data = [
        {
            "placeId": p.placeId,
            "title": p.title,
            "lat": (p.location or {}).get("lat"),
            "lng": (p.location or {}).get("lng"),
            "categoryName": p.categoryName,
            "address": p.address,
        }
        for p in places
    ]
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    logger.info("Da cao %d quan, luu cache %s", len(data), CACHE_PATH.name)
    return data


def _gan_nhau(ban_ghi_cu, ban_ghi_moi: dict) -> bool:
    """Hai bản ghi có ở gần nhau đủ để coi là một quán không.

    Thiếu toạ độ ở một trong hai bên -> trả True (chấp nhận ghép). Lý do: thiếu toạ độ là
    chuyện của DỮ LIỆU ta có, không phải bằng chứng rằng đây là hai quán khác nhau. Coi
    chúng là hai quán sẽ đẩy một quán vào mục "biến mất" - tức là báo động giả, đúng thứ
    việc tách nhóm này sinh ra để dẹp.
    """
    vi_tri_cu = getattr(ban_ghi_cu, "location", None)
    lat, lng = ban_ghi_moi.get("lat"), ban_ghi_moi.get("lng")
    if vi_tri_cu is None or lat is None or lng is None:
        return True
    try:
        return vi_tri_cu.distance_km(Location(lat=float(lat), lng=float(lng))) <= (
            MAX_KHOANG_CACH_DOI_ID_KM
        )
    except (ValueError, TypeError):
        return True


def so_sanh(cu: Dict[str, object], moi: Dict[str, dict]) -> dict:
    """So bộ CŨ với bộ MỚI theo `placeId`.

    Đối chiếu theo ID chứ không theo tên: quán đổi tên vẫn là quán đó, và hai quán khác
    nhau hoàn toàn có thể trùng tên ("Phở Thìn" có nhiều hàng).
    """
    id_cu, id_moi = set(cu), set(moi)

    doi_ten = []
    for pid in id_cu & id_moi:
        ten_cu = getattr(cu[pid], "name", None)
        ten_moi = (moi[pid] or {}).get("title")
        # So sau khi BỎ DẤU + hạ chữ thường: người vẽ bản đồ sửa "Pho Thin" thành
        # "Phở Thìn" là chuẩn hoá chính tả, không phải quán đổi tên. Báo cả những thứ đó
        # thì báo cáo đầy nhiễu và không ai đọc nữa.
        if ten_cu and ten_moi and normalize(ten_cu) != normalize(ten_moi):
            doi_ten.append({"place_id": pid, "ten_cu": ten_cu, "ten_moi": ten_moi})

    quan_moi = [
        {"place_id": pid, "ten": moi[pid].get("title"),
         "loai": moi[pid].get("categoryName")}
        for pid in sorted(id_moi - id_cu)
    ]

    # TÁCH "ĐỔI ID" RA KHỎI "BIẾN MẤT".
    #
    # Người vẽ bản đồ hay xoá node cũ rồi vẽ lại thành đường bao toà nhà, và bản ghi nhận
    # một ID mới. Nhìn từ ngoài thì y hệt "một quán đóng cửa + một quán mới mở", trong khi
    # thực ra không có gì thay đổi.
    #
    # ⚠️ CHỈ SO TÊN LÀ KHÔNG ĐỦ - đo thật ngày 2026-08-19: 73 cặp trùng tên ở hai phía
    # (Highlands Coffee, KFC, Starbucks, Mixue, Dookki...) đều cách nhau từ 1,1 km tới
    # 22,3 km. Đó là các CHI NHÁNH KHÁC NHAU của cùng chuỗi, không phải node bị vẽ lại.
    # Ghép theo tên sẽ giấu mất 10 quán thật sự đã biến mất khỏi OSM. Vì vậy bắt buộc phải
    # có thêm điều kiện khoảng cách - xem `MAX_KHOANG_CACH_DOI_ID_KM`.
    # Cùng TÊN chưa đủ - "Phở Thìn" có nhiều hàng thật, và gộp chúng lại là giấu mất một
    # quán. Phải cùng tên VÀ ở gần nhau, xem `MAX_KHOANG_CACH_DOI_ID_KM`.
    ten_moi_theo_ten = {}
    for pid in {q["place_id"] for q in quan_moi}:
        ten_moi_theo_ten.setdefault(normalize(moi[pid].get("title")), []).append(pid)

    bien_mat, doi_id = [], []
    for pid in sorted(id_cu - id_moi):
        ban_ghi_cu = cu[pid]
        ten = getattr(ban_ghi_cu, "name", None)
        ghep = None
        for pid_moi in ten_moi_theo_ten.get(normalize(ten), []) if ten else []:
            if _gan_nhau(ban_ghi_cu, moi[pid_moi]):
                ghep = pid_moi
                break
        if ghep:
            doi_id.append({"place_id_cu": pid, "ten": ten, "place_id_moi": ghep})
        else:
            bien_mat.append({"place_id": pid, "ten": ten})

    # Quán đã ghép được với bản ghi cũ thì không còn là "mới" nữa.
    id_da_ghep = {d["place_id_moi"] for d in doi_id}
    quan_moi = [q for q in quan_moi if q["place_id"] not in id_da_ghep]

    return {
        "quan_moi": quan_moi,
        "quan_bien_mat": bien_mat,
        "quan_doi_id": doi_id,
        "quan_doi_ten": doi_ten,
        "van_giu_nguyen": len(id_cu & id_moi) - len(doi_ten),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cao lai nguon va bao cao khac biet")
    parser.add_argument("--dung-cache", action="store_true", dest="dung_cache",
                        help="Dung lai lan cao truoc, khong goi mang")
    parser.add_argument("--xuat", type=Path, help="Ghi bao cao day du ra file JSON")
    parser.add_argument("--so-dong", type=int, default=15, dest="so_dong",
                        help="So dong vi du in ra man hinh cho moi muc")
    args = parser.parse_args()

    settings = Settings.from_env()
    repo = CsvRestaurantRepository(settings.restaurants_csv)
    if not repo.is_ready:
        logger.error("Chua co dataset: %s", repo.load_error)
        return 1

    # Chỉ so phần quán ĐẾN TỪ OSM. So với cả 40.720 quán thì 36.176 quán Overture sẽ bị
    # báo là "biến mất" chỉ vì OSM không có chúng - đúng kiểu báo cáo vô dụng vì quá nhiều
    # nhiễu.
    cu = {
        r.place_id: r for r in repo.list_all()
        if (r.source or "").lower() == SOURCE_DOI_CHIEU and r.place_id
    }
    logger.info("Dang dung : %d quan tu %s", len(cu), SOURCE_DOI_CHIEU)

    moi_list = lay_moi(args.dung_cache)
    moi = {p["placeId"]: p for p in moi_list if p.get("placeId")}
    logger.info("Vua cao ve: %d quan", len(moi))

    if not moi:
        logger.error("Cao ve 0 quan - gan nhu chac chan la loi mang, KHONG phai")
        logger.error("Ha Noi khong con quan an nao. Dung lai de khoi bao cao sai.")
        return 1

    bao_cao = so_sanh(cu, moi)

    logger.info("")
    logger.info("=" * 68)
    logger.info("BAO CAO KHAC BIET (%s)", datetime.now(timezone.utc).date().isoformat())
    logger.info("=" * 68)
    logger.info("  Quan MOI xuat hien   : %d", len(bao_cao["quan_moi"]))
    logger.info("  Quan BIEN MAT        : %d  <- muc dang doc ky nhat", len(bao_cao["quan_bien_mat"]))
    logger.info("  Quan chi DOI ID      : %d  (van con, nguoi ve ban do ve lai node)",
                len(bao_cao["quan_doi_id"]))
    logger.info("  Quan DOI TEN         : %d", len(bao_cao["quan_doi_ten"]))
    logger.info("  Khong doi gi         : %d", bao_cao["van_giu_nguyen"])

    for tieu_de, khoa, dinh_dang in [
        ("QUAN MOI", "quan_moi", lambda x: f"{x['ten']} ({x.get('loai') or 'chua ro loai'})"),
        ("QUAN BIEN MAT", "quan_bien_mat", lambda x: f"{x['ten']}"),
        ("QUAN DOI TEN", "quan_doi_ten", lambda x: f"{x['ten_cu']}  ->  {x['ten_moi']}"),
    ]:
        muc = bao_cao[khoa]
        if not muc:
            continue
        logger.info("")
        logger.info("--- %s (%d) ---", tieu_de, len(muc))
        for item in muc[: args.so_dong]:
            logger.info("  %s", dinh_dang(item))
        if len(muc) > args.so_dong:
            logger.info("  ... con %d muc nua (dung --xuat de xem het)",
                        len(muc) - args.so_dong)

    logger.info("")
    logger.info("KHONG co gi bi sua tu dong. Quan 'bien mat' khoi OSM thuong la do nguoi")
    logger.info("ve ban do gop node hoac doi the loai, KHONG phai quan da dong cua.")
    logger.info("Doc xong roi tu quyet dinh: sua tay dish_seed/dataset, hoac bo qua.")

    if args.xuat:
        args.xuat.write_text(
            json.dumps(bao_cao, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info("Da ghi bao cao day du: %s", args.xuat)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

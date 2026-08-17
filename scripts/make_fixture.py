"""Tạo BỘ DỮ LIỆU MẪU cho frontend — 100 quán THẬT, giữ đúng độ thưa của dữ liệu thật.

    python scripts/make_fixture.py

VÌ SAO CÓ FILE NÀY:
Frontend không nên chờ cào xong dữ liệu mới làm. Nhưng nếu dùng mock tự bịa với mọi
trường đều đầy đủ thì giao diện sẽ đẹp lúc demo và VỠ khi cắm dữ liệu thật — vì thực tế
chỉ 21.5% quán có ảnh, 23.2% có đánh giá, 13% có giá.

Đây KHÔNG phải mock. Mọi bản ghi đều là **response THẬT của POST /api/v1/search**:
điểm xếp hạng thật, `match_source` thật, khoảng cách thật, món gợi ý thật. Script chỉ
CHỌN LỌC chứ không bịa giá trị nào.

CHỌN CÓ CHỦ ĐÍCH (stratified), không lấy ngẫu nhiên: bộ mẫu phải ép người thiết kế gặp
đủ mọi trạng thái khó — quán không ảnh, không đánh giá, tên rất dài, địa chỉ rất dài,
món suy luận rộng, chưa phân cụm. Lấy ngẫu nhiên rất dễ ra 100 quán "đẹp" rồi lại rơi
vào đúng cái bẫy trên.

Đầu ra: `frontend/fixtures/restaurants.json`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUTPUT = ROOT / "frontend" / "fixtures" / "restaurants.json"
TARGET_SIZE = 100

# Truy vấn đa dạng để gom được nhiều kiểu quán khác nhau. Toạ độ trải trên vài khu vực
# để có cả quán gần lẫn quán xa.
QUERIES = [
    ("phở bò", 21.0325, 105.8509),
    ("quán lẩu ấm cúng", 21.0325, 105.8509),
    ("chỗ yên tĩnh để làm việc", 21.0245, 105.8412),
    ("cà phê", 21.0395, 105.8381),
    ("bún chả", 21.0075, 105.8582),
    ("ăn nhẹ tốt cho sức khoẻ", 21.0325, 105.8509),
    ("hải sản", 21.0500, 105.8200),
    ("cơm bình dân", 21.0150, 105.8300),
    ("bánh mì", 21.0325, 105.8509),
    (None, 21.0325, 105.8509),          # không gõ gì - xếp theo mood/thời điểm
]

# Các trạng thái BẮT BUỘC phải có mặt trong bộ mẫu. Thiếu cái nào là fixture chưa đạt.
REQUIRED_CASES: Dict[str, Any] = {
    "co_anh":            lambda r: bool(r.get("thumbnail_url")),
    "khong_anh":         lambda r: not r.get("thumbnail_url"),
    "co_danh_gia":       lambda r: r.get("rating") is not None,
    "khong_danh_gia":    lambda r: r.get("rating") is None,
    "co_gia":            lambda r: bool(r.get("price_range")),
    "khong_gia":         lambda r: not r.get("price_range"),
    # Mọi quán đều có địa chỉ (đếm: 0/4938 thiếu) và đều nhận được gợi ý món nhờ luật
    # fallback, nên KHÔNG có trường hợp "không địa chỉ" / "không món" để đưa vào đây.
    "co_mon_cu_the":     lambda r: (r.get("suggested_dish") or {}).get("confidence") == "specific",
    "mon_suy_luan_rong": lambda r: (r.get("suggested_dish") or {}).get("confidence") == "generic_fallback",
    "da_phan_cum":       lambda r: r.get("experience_cluster_label"),
    "chua_phan_cum":     lambda r: not r.get("experience_cluster_label"),
    "ten_rat_dai":       lambda r: len(r.get("name") or "") >= 35,
    "dia_chi_rat_dai":   lambda r: len(r.get("address") or "") >= 45,
    "rat_gan":           lambda r: (r.get("distance_m") or 99999) <= 500,
    "kha_xa":            lambda r: (r.get("distance_m") or 0) >= 3000,
}


def gom_ket_qua_that() -> List[Dict[str, Any]]:
    """Gọi API THẬT nhiều lần, gom kết quả duy nhất theo restaurant_id."""
    from fastapi.testclient import TestClient

    from src.presentation.api.main import create_app

    pool: Dict[str, Dict[str, Any]] = {}
    with TestClient(create_app()) as client:
        for query, lat, lng in QUERIES:
            body = {
                "session_id": "fixture-generator",
                "latitude": lat,
                "longitude": lng,
                # Bán kính rộng để gom được cả quán xa - bộ mẫu cần đủ dải khoảng cách.
                "max_distance_km": 15,
                "limit": 50,
            }
            if query:
                body["query_text"] = query
            response = client.post("/api/v1/search", json=body)
            if response.status_code != 200:
                print(f"  [BO QUA] '{query}' -> HTTP {response.status_code}")
                continue
            for item in response.json()["data"]["results"]:
                key = item.get("restaurant_id") or f"{item['name']}|{item['latitude']}"
                pool.setdefault(key, item)
    return list(pool.values())


# Tỉ lệ MỤC TIÊU cho 100 bản ghi, lấy đúng theo độ phủ thật của dataset.
# ⚠️ ĐÂY LÀ PHẦN QUAN TRỌNG NHẤT CỦA SCRIPT. Bản đầu tiên không có hạn mức này và cho ra
# fixture giàu gấp 2-4 lần thực tế (ảnh 54% trong khi thật chỉ 21.5%), vì xếp hạng vốn ưu
# tiên quán CÓ dữ liệu nên pool lấy từ tìm kiếm đã lệch sẵn. Fixture giàu hơn thật chính là
# cái bẫy khiến giao diện đẹp lúc demo rồi vỡ khi cắm dữ liệu thật.
HAN_MUC = {
    "thumbnail_url": 22,   # thật 21.5%
    "rating": 23,          # thật 23.2%
    "price_range": 13,     # thật 13.0%
    "cluster": 24,         # thật 1197/4938 = 24.2%
}


def _thuoc_tinh(r: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "thumbnail_url": bool(r.get("thumbnail_url")),
        "rating": r.get("rating") is not None,
        "price_range": bool(r.get("price_range")),
        "cluster": bool(r.get("experience_cluster_label")),
    }


def chon_co_chu_dich(pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Chọn 100 quán: đủ mọi trạng thái khó VÀ giữ đúng tỉ lệ thưa của dữ liệu thật."""
    chosen: List[Dict[str, Any]] = []
    seen: set = set()
    dem = {k: 0 for k in HAN_MUC}

    def con_cho(r: Dict[str, Any]) -> bool:
        """Thêm bản ghi này có làm vượt hạn mức trường nào không?"""
        return all(
            not co or dem[k] < HAN_MUC[k] for k, co in _thuoc_tinh(r).items()
        )

    def them(r: Dict[str, Any], ep: bool = False) -> bool:
        key = r.get("restaurant_id") or r["name"]
        if key in seen or (not ep and not con_cho(r)):
            return False
        seen.add(key)
        chosen.append(r)
        for k, co in _thuoc_tinh(r).items():
            if co:
                dem[k] += 1
        return True

    # Bước 1: mỗi trạng thái bắt buộc lấy 2 mẫu. Dùng ep=True để chắc chắn có mặt, kể cả
    # khi làm nhỉnh hạn mức - thà lệch vài phần trăm còn hơn thiếu hẳn một trạng thái.
    for ten, dieu_kien in REQUIRED_CASES.items():
        khop = [r for r in pool if dieu_kien(r)]
        if not khop:
            print(f"  [CANH BAO] khong tim thay quan nao cho truong hop: {ten}")
            continue
        for item in khop[:2]:
            them(item, ep=True)

    # Chốt chặn: bước seed dùng ep=True nên VỀ NGUYÊN TẮC có thể vượt hạn mức. Hiện tại
    # nó chỉ đóng góp ~5/22 nên chưa xảy ra, nhưng dataset đổi thì có thể. Báo to thay vì
    # để tỉ lệ lệch âm thầm - mục 9 của verify.py cũng bắt được, nhưng ở đây báo sớm hơn.
    vuot = {k: (dem[k], HAN_MUC[k]) for k in HAN_MUC if dem[k] > HAN_MUC[k]}
    if vuot:
        print(f"  [CANH BAO] buoc seed da VUOT han muc: {vuot}")
        print("             -> ty le se lech. Xem lai REQUIRED_CASES hoac HAN_MUC.")

    # Bước 2: lấp cho đủ 100, nhưng CHỈ nhận bản ghi không làm vượt hạn mức.
    for item in pool:
        if len(chosen) >= TARGET_SIZE:
            break
        them(item)

    # Bước 3: nếu vẫn thiếu (pool quá nghèo quán "trống"), lấp nốt để đủ số lượng.
    if len(chosen) < TARGET_SIZE:
        for item in pool:
            if len(chosen) >= TARGET_SIZE:
                break
            them(item, ep=True)

    return chosen[:TARGET_SIZE]


def do_ty_le(records: List[Dict[str, Any]]) -> Dict[str, float]:
    n = len(records) or 1
    return {
        "thumbnail": sum(1 for r in records if r.get("thumbnail_url")) / n,
        "rating": sum(1 for r in records if r.get("rating") is not None) / n,
        "price": sum(1 for r in records if r.get("price_range")) / n,
        "clustered": sum(1 for r in records if r.get("experience_cluster_label")) / n,
    }


def main() -> int:
    print("Dang goi API that de gom ket qua...")
    pool = gom_ket_qua_that()
    if not pool:
        print("[LOI] Khong gom duoc ket qua nao. Da chay data_pipeline chua?")
        return 1
    print(f"  Gom duoc {len(pool)} quan duy nhat tu {len(QUERIES)} luot tim")

    records = chon_co_chu_dich(pool)

    print("\n-- Cac truong hop bat buoc --")
    thieu = []
    for ten, dieu_kien in REQUIRED_CASES.items():
        so = sum(1 for r in records if dieu_kien(r))
        print(f"  {'OK ' if so else 'THIEU'} {ten:20} {so}")
        if not so:
            thieu.append(ten)

    ty_le = do_ty_le(records)
    print("\n-- Ty le trong bo mau (so voi du lieu that) --")
    that = {"thumbnail": 0.215, "rating": 0.232, "price": 0.130}
    for truong, gia_tri in ty_le.items():
        goc = that.get(truong)
        them = f"  (that: {goc:.1%})" if goc else ""
        print(f"  {truong:12} {gia_tri:.1%}{them}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "_ghi_chu": (
                    "DU LIEU THAT tu POST /api/v1/search, khong phai mock. "
                    "Sinh boi scripts/make_fixture.py. Khong sua tay - chay lai script."
                ),
                "_so_ban_ghi": len(records),
                "_ty_le": {k: round(v, 4) for k, v in ty_le.items()},
                "results": records,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nDa ghi: {OUTPUT}  ({len(records)} quan, {OUTPUT.stat().st_size // 1024} KB)")
    if thieu:
        print(f"[CANH BAO] Thieu {len(thieu)} truong hop: {', '.join(thieu)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

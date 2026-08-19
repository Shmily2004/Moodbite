"""Gác BỘ DỮ LIỆU MẪU của frontend — chạy tự động trong `scripts/verify.py`.

    python scripts/verify_ui_data.py

VÌ SAO CÓ FILE NÀY: bộ mẫu ở `frontend/fixtures/restaurants.json` là thứ người thiết kế
và frontend dựa vào. Nếu nó **giàu hơn dữ liệu thật** thì giao diện sẽ đẹp lúc demo rồi
vỡ khi cắm API thật — đây là lỗi ĐÃ XẢY RA: bản fixture đầu tiên có 54% quán kèm ảnh
trong khi thực tế chỉ 21.5%, vì xếp hạng vốn ưu tiên quán có dữ liệu nên mẫu lấy từ tìm
kiếm lệch sẵn.

Script kiểm 4 việc:
  1. Bộ mẫu tồn tại và đọc được
  2. Mọi bản ghi có đủ trường theo đúng hợp đồng API
  3. Tỉ lệ có/thiếu dữ liệu BÁM SÁT dataset thật (sai số cho phép ±5 điểm phần trăm)
  4. Đủ mọi trạng thái khó mà giao diện phải xử lý

Thoát 0 = đạt.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent

# PowerShell tren Windows mac dinh dung bang ma cp1252, khong in duoc chu Viet co dau:
# chay `python scripts/verify_ui_data.py` truc tiep se vo giua chung voi UnicodeEncodeError.
# Chay qua `scripts/verify.py` thi khong sao vi ben do da dat PYTHONIOENCODING=utf-8 -
# nghia la loi chi lo ra khi nguoi dung tu chay tay, dung luc kho doan nhat.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "frontend" / "fixtures" / "restaurants.json"

# Sai số cho phép giữa bộ mẫu và dataset thật, tính theo ĐIỂM PHẦN TRĂM.
# ±5 đủ rộng để không đỏ vì làm tròn 100 bản ghi, đủ hẹp để chặn fixture lệch hẳn
# (bản hỏng trước đây lệch tới +32 điểm).
DUNG_SAI = 0.05

# Trường BẮT BUỘC theo hợp đồng `SearchResultItemSchema`. Thiếu = frontend sẽ nổ.
TRUONG_BAT_BUOC = [
    "restaurant_id", "name", "latitude", "longitude", "distance_m",
    "rank_position", "predicted_score", "match_source",
]

# Trạng thái giao diện PHẢI xử lý được. Bộ mẫu thiếu cái nào thì người thiết kế sẽ
# không bao giờ gặp, và sẽ quên xử lý.
TRANG_THAI_BAT_BUOC: Dict[str, Any] = {
    "có ảnh":              lambda r: bool(r.get("thumbnail_url")),
    "KHÔNG ảnh":           lambda r: not r.get("thumbnail_url"),
    "có đánh giá":         lambda r: r.get("rating") is not None,
    "KHÔNG đánh giá":      lambda r: r.get("rating") is None,
    "có giá":              lambda r: bool(r.get("price_range")),
    "KHÔNG giá":           lambda r: not r.get("price_range"),
    "món khớp cụ thể":     lambda r: (r.get("suggested_dish") or {}).get("confidence") == "specific",
    "món suy luận rộng":   lambda r: (r.get("suggested_dish") or {}).get("confidence") == "generic_fallback",
    "đã phân cụm":         lambda r: bool(r.get("experience_cluster_label")),
    "CHƯA phân cụm":       lambda r: not r.get("experience_cluster_label"),
    "tên rất dài":         lambda r: len(r.get("name") or "") >= 35,
    "địa chỉ rất dài":     lambda r: len(r.get("address") or "") >= 45,
}


def ty_le_that() -> Dict[str, float]:
    """Đo độ phủ trên ĐÚNG TẬP MÀ BỘ MẪU ĐƯỢC RÚT RA, không phải toàn bộ CSV.

    VÌ SAO KHÔNG DÙNG TOÀN BỘ CSV (sửa 2026-08-19): `make_fixture.py` lấy mẫu qua chính
    API `/search`, tức là đi qua BỘ XẾP HẠNG - mà xếp hạng cộng điểm cho quán có đánh giá,
    nên quán có ảnh/rating luôn nổi lên. Hai tập khác nhau một cách CÓ HỆ THỐNG, không
    phải do bộ mẫu sai.

    Đo được sau khi nhập 36.176 quán Overture (phần lớn chưa có ảnh/đánh giá):
        toàn bộ CSV            :  2.6% có ảnh
        tập kết quả tìm kiếm   : ~21% có ảnh
    Bản cũ so bộ mẫu với toàn bộ CSV nên báo lỗi, trong khi bộ mẫu phản ánh ĐÚNG thứ người
    dùng nhìn thấy. So sai tập thì con số nào cũng "lệch".

    Dùng THẲNG `gom_ket_qua_that()` của `make_fixture` để hai bên không thể lấy mẫu khác
    nhau - chép lại logic gom là cách chắc chắn để hai script trôi khỏi nhau.
    """
    try:
        from make_fixture import gom_ket_qua_that
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            from make_fixture import gom_ket_qua_that
        except ImportError:
            return {}

    pool = gom_ket_qua_that()
    return ty_le_mau(pool) if pool else {}


def ty_le_mau(records: List[dict]) -> Dict[str, float]:
    n = len(records) or 1
    return {
        "thumbnail": sum(1 for r in records if r.get("thumbnail_url")) / n,
        "rating": sum(1 for r in records if r.get("rating") is not None) / n,
        "price": sum(1 for r in records if r.get("price_range")) / n,
    }


def main() -> int:
    loi: List[str] = []

    print("=" * 68)
    print("KIEM BO DU LIEU MAU CUA FRONTEND")
    print("=" * 68)

    # --- 1. Tồn tại và đọc được -------------------------------------------
    if not FIXTURE.exists():
        print(f"[FAIL] Khong tim thay {FIXTURE.relative_to(ROOT)}")
        print("       Sinh lai: python scripts/make_fixture.py")
        return 1
    try:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        records = data["results"]
    except (ValueError, KeyError) as exc:
        print(f"[FAIL] Doc khong duoc: {exc}")
        return 1
    print(f"\n[ OK ] Doc duoc {len(records)} ban ghi")

    # --- 2. Đủ trường theo hợp đồng API -----------------------------------
    thieu_truong: Dict[str, int] = {}
    for r in records:
        for truong in TRUONG_BAT_BUOC:
            if truong not in r:
                thieu_truong[truong] = thieu_truong.get(truong, 0) + 1
    if thieu_truong:
        loi.append(f"thieu truong bat buoc: {thieu_truong}")
        print(f"[FAIL] Thieu truong: {thieu_truong}")
    else:
        print(f"[ OK ] Du {len(TRUONG_BAT_BUOC)} truong bat buoc theo hop dong API")

    # Kiểm kiểu dữ liệu dễ sai nhất: giá PHẢI là chuỗi, không phải số.
    gia_sai_kieu = [
        r["name"] for r in records
        if r.get("price_range") is not None and not isinstance(r["price_range"], str)
    ]
    if gia_sai_kieu:
        loi.append(f"price_range khong phai chuoi: {gia_sai_kieu[:3]}")
        print(f"[FAIL] price_range phai la CHUOI: {gia_sai_kieu[:3]}")
    else:
        print("[ OK ] price_range deu la chuoi (khong bi ep ve so)")

    # --- 3. Tỉ lệ bám sát dataset thật ------------------------------------
    that, mau = ty_le_that(), ty_le_mau(records)
    print(f"\n-- Ty le (dung sai cho phep +/-{DUNG_SAI:.0%} diem) --")
    if not that:
        print("  [BO QUA] chua co dataset that de doi chieu")
    else:
        for truong in ("thumbnail", "rating", "price"):
            m, t = mau[truong], that.get(truong, 0.0)
            lech = abs(m - t)
            dat = lech <= DUNG_SAI
            print(f"  {'OK  ' if dat else 'FAIL'} {truong:10} mau {m:5.1%} | that {t:5.1%} | lech {lech:.1%}")
            if not dat:
                loi.append(
                    f"{truong}: mau {m:.1%} lech {lech:.1%} so voi that {t:.1%}"
                )

    # --- 4. Đủ trạng thái khó ---------------------------------------------
    print("\n-- Trang thai giao dien phai xu ly --")
    thieu_trang_thai = []
    for ten, dieu_kien in TRANG_THAI_BAT_BUOC.items():
        so = sum(1 for r in records if dieu_kien(r))
        print(f"  {'OK  ' if so else 'FAIL'} {ten:20} {so:3} ban ghi")
        if not so:
            thieu_trang_thai.append(ten)
    if thieu_trang_thai:
        loi.append(f"thieu trang thai: {', '.join(thieu_trang_thai)}")

    print("\n" + "=" * 68)
    if loi:
        print(f"KET QUA: {len(loi)} van de")
        for v in loi:
            print(f"  - {v}")
        print("\nSua bang: python scripts/make_fixture.py")
        print("=" * 68)
        return 1
    print("KET QUA: DAT - bo mau phan anh dung do thua cua du lieu that.")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Ghi ẢNH CHỤP CHỈ SỐ CHẤT LƯỢNG DỮ LIỆU của hôm nay.

    python scripts/ghi_anh_chup_chat_luong.py

Mỗi ngày MỘT dòng. Chạy lại trong cùng ngày thì ghi đè, không đẻ dòng mới — nên chạy
nhiều lần vô hại.

KHI NÀO CẦN LỆNH NÀY
--------------------
Bình thường thì KHÔNG cần: trang quản trị `/chat-luong` tự ghi mỗi lần mở. Lệnh này dành
cho hai trường hợp:

  1. Muốn biểu đồ xu hướng đầy dù không ai mở trang quản trị ngày hôm đó — cắm vào
     Task Scheduler (Windows) hoặc cron, chạy một lần mỗi ngày.
  2. Vừa chạy lại `data_pipeline` và muốn mốc so sánh phản ánh ngay dữ liệu mới.

Chạy giống nhau ở PowerShell, CMD, bash, macOS, Linux — không phải nhớ cú pháp shell
(CLAUDE.md mục 1b).
"""
from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.presentation.api.dependencies import build_container  # noqa: E402


def main() -> int:
    # Nạp dataset mất vài giây và in một loạt dòng INFO. Tắt bớt để đầu ra của lệnh này
    # chỉ còn thứ người chạy quan tâm.
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    container = build_container()
    kho = container.quality_snapshots
    if not getattr(kho, "is_ready", False):
        print("HONG: khong mo duoc kho lich su chat luong.")
        print("      Kiem tra quyen ghi vao file CSDL tai khoan (MOODBITE_USERS_DB).")
        return 1

    # `bo_qua_dem=True`: lệnh này thường chạy ngay sau khi dữ liệu vừa đổi, nên phải tính
    # lại chứ không lấy số cũ trong bộ đệm 5 phút.
    ket_qua = container.data_quality.execute(bo_qua_dem=True)
    lich_su = kho.doc_gan_day()

    hom_nay = date.today().isoformat()
    print(f"Da ghi anh chup ngay {hom_nay}:")
    print(f"  quan            : {ket_qua.tong_quan.hien_tai:,}")
    print(f"  mon             : {ket_qua.tong_mon.hien_tai:,}")
    print(f"  hoan thien      : {ket_qua.hoan_thien_phan_tram}%")
    print(f"  nghiem trong    : {ket_qua.dem_uu_tien.get('nghiem_trong', 0):,}")
    print(f"  quan trong      : {ket_qua.dem_uu_tien.get('quan_trong', 0):,}")
    print(f"  can kiem tra    : {ket_qua.dem_uu_tien.get('can_kiem_tra', 0):,}")
    print()
    print(f"Tong so ngay da luu: {len(lich_su)}")

    if len(lich_su) < 2:
        print()
        print("Bieu do xu huong can it nhat 2 ngay. Chay lai lenh nay vao ngay mai,")
        print("hoac cam vao Task Scheduler de no tu chay moi ngay.")

    moc = ket_qua.tong_quan
    if moc.co_so_sanh:
        print(f"So voi {moc.ngay_moc}: {moc.chenh_lech:+,} quan")
    else:
        print("Chua co moc du cu (30 ngay) de so sanh — dung, khong phai loi.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

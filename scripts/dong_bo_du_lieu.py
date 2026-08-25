"""ĐỒNG BỘ DỮ LIỆU giữa các máy qua HuggingFace Hub — miễn phí, không cần thẻ.

    python scripts/dong_bo_du_lieu.py --tai        # máy mới: TẢI dữ liệu về
    python scripts/dong_bo_du_lieu.py --day        # máy có dữ liệu mới: ĐẨY lên
    python scripts/dong_bo_du_lieu.py --xem        # chỉ xem đang có gì, không đụng file

VẤN ĐỀ NÀY GIẢI QUYẾT
---------------------
`data_pipeline/data_cleaned/*` nằm trong `.gitignore` — cố ý, vì đó là DỮ LIỆU DẪN XUẤT
(dựng lại được từ pipeline) và nặng ~39MB. Hậu quả: `git pull` trên máy thứ hai cho ra
một dự án KHÔNG CHẠY ĐƯỢC, phải cào lại toàn bộ mất nhiều giờ, hoặc phải điều khiển từ xa
về máy có dữ liệu — chậm và vướng.

Nay: máy nào cũng chạy được `--tai` là có đủ dữ liệu để `python scripts/run_dev.py`.

VÌ SAO HUGGINGFACE CHỨ KHÔNG PHẢI THỨ KHÁC
------------------------------------------
| Cách | Vì sao KHÔNG |
|---|---|
| Git LFS | GitHub free chỉ cho 1GB lưu + 1GB băng thông/tháng. Vài lượt đẩy 39MB là hết |
| SQL Server / CSDL online | Bản miễn phí đều đòi thẻ tín dụng — `CLAUDE.md` cấm |
| Google Drive | Không có API tải về ổn định nếu không dựng OAuth |
| Bỏ `.gitignore`, commit thẳng | Repo phình mãi mãi; mỗi lần chạy lại pipeline là thêm 39MB vào lịch sử, không xoá được |

HuggingFace Hub: miễn phí, KHÔNG cần thẻ, cho file lớn, có sẵn `huggingface_hub` trong
môi trường, và dự án đã dùng nó ở `data_pipeline/upload_model_to_hf.py`.

⚠️ KHÔNG ĐẨY DỮ LIỆU NGƯỜI DÙNG. `moodbite_users.db` chứa tài khoản thật (email, chuỗi
băm mật khẩu) — xem danh sách `KHONG_BAO_GIO_DAY`. Đẩy nhầm lên kho công khai là rò rỉ
dữ liệu cá nhân, không thu hồi được.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("dong_bo")

# Kho mặc định. Đổi bằng --repo hoặc biến môi trường MOODBITE_HF_DATASET.
REPO_MAC_DINH = "moodbite/moodbite-data"

# ĐỦ ĐỂ CHẠY APP. Cố ý KHÔNG gồm `merged_places.csv` (76MB) và `dataset_moodbite_clean.csv`
# — hai file đó là bước TRUNG GIAN của pipeline, máy chỉ chạy app không cần tới.
FILE_CAN_DONG_BO: List[str] = [
    "data_pipeline/data_cleaned/moodbite.db",
    "data_pipeline/data_cleaned/dataset_moodbite_features.csv",
    "data_pipeline/data_cleaned/restaurant_details.json",
    "data_pipeline/data_cleaned/dish_catalog.json",
    "data_pipeline/data_cleaned/review_summaries.json",
]

# ⚠️ TUYỆT ĐỐI KHÔNG ĐẨY. Kiểm hai lần: một lần ở đây, một lần lúc lọc.
# `moodbite_users.db` là DỮ LIỆU GỐC chứa tài khoản thật — mất là mất hẳn, mà lộ thì
# không thu hồi được. `.env.local` chứa secret và mật khẩu SMTP.
KHONG_BAO_GIO_DAY = (
    "moodbite_users.db",
    "interactions.jsonl",   # nhật ký hành vi người dùng — dữ liệu cá nhân
    ".env",
)


def _an_toan_de_day(duong_dan: str) -> bool:
    return not any(cam in duong_dan for cam in KHONG_BAO_GIO_DAY)


def _kich_thuoc(p: Path) -> str:
    mb = p.stat().st_size / 1024 / 1024
    return f"{mb:.1f} MB"


def xem() -> int:
    """Liệt kê file cần đồng bộ và trạng thái ở máy này."""
    print(f"{'FILE':52s} {'MÁY NÀY':>12s}")
    print("-" * 66)
    thieu = 0
    for ten in FILE_CAN_DONG_BO:
        p = ROOT / ten
        if p.exists():
            print(f"{ten:52s} {_kich_thuoc(p):>12s}")
        else:
            print(f"{ten:52s} {'CHƯA CÓ':>12s}")
            thieu += 1
    print()
    if thieu:
        print(f"Thiếu {thieu} file. Chạy: python scripts/dong_bo_du_lieu.py --tai")
    else:
        print("Đủ file để chạy app.")
    return 0


def _lay_api():
    try:
        from huggingface_hub import HfApi
    except ImportError:
        logger.error(
            "Chưa có thư viện. Cài bằng:\n"
            "    pip install huggingface_hub"
        )
        return None
    return HfApi()


def _kiem_token() -> bool:
    """Có token ghi chưa. Chỉ cần cho `--day`; `--tai` từ kho công khai thì không cần."""
    if os.getenv("HF_TOKEN"):
        return True
    try:
        from huggingface_hub import HfFolder

        return bool(HfFolder.get_token())
    except Exception:
        return False


def day(repo: str) -> int:
    api = _lay_api()
    if api is None:
        return 1
    if not _kiem_token():
        logger.error(
            "Chưa đăng nhập HuggingFace. Làm một lần:\n"
            "    1. Tạo token 'Write' tại https://huggingface.co/settings/tokens\n"
            "    2. huggingface-cli login   (dán token)\n"
            "  hoặc đặt biến môi trường HF_TOKEN."
        )
        return 1

    from huggingface_hub import create_repo, upload_file

    create_repo(repo, repo_type="dataset", exist_ok=True, private=False)

    da_day = 0
    for ten in FILE_CAN_DONG_BO:
        if not _an_toan_de_day(ten):
            # Chốt chặn thứ hai. Không bao giờ tới đây nếu danh sách ở trên đúng — nhưng
            # cái giá của một lần lọt là rò rỉ dữ liệu cá nhân, nên vẫn kiểm.
            logger.warning("BỎ QUA (dữ liệu cá nhân): %s", ten)
            continue
        p = ROOT / ten
        if not p.exists():
            logger.warning("Không có ở máy này, bỏ qua: %s", ten)
            continue
        logger.info("Đẩy %s (%s)...", ten, _kich_thuoc(p))
        upload_file(
            path_or_fileobj=str(p),
            path_in_repo=ten,
            repo_id=repo,
            repo_type="dataset",
        )
        da_day += 1

    logger.info("Xong. Đã đẩy %d file lên https://huggingface.co/datasets/%s", da_day, repo)
    logger.info("Máy khác lấy về: python scripts/dong_bo_du_lieu.py --tai")
    return 0


def tai(repo: str) -> int:
    api = _lay_api()
    if api is None:
        return 1

    from huggingface_hub import hf_hub_download

    da_tai = 0
    for ten in FILE_CAN_DONG_BO:
        dich = ROOT / ten
        dich.parent.mkdir(parents=True, exist_ok=True)
        try:
            logger.info("Tải %s ...", ten)
            tam = hf_hub_download(
                repo_id=repo,
                filename=ten,
                repo_type="dataset",
                # Tải thẳng vào thư mục dự án thay vì cache rồi copy: bộ dữ liệu ~39MB,
                # giữ hai bản là tốn gấp đôi ổ cứng của một máy laptop.
                local_dir=str(ROOT),
            )
            if Path(tam).exists():
                da_tai += 1
        except Exception as exc:
            logger.error("Không tải được %s: %s", ten, exc)

    if da_tai == 0:
        logger.error(
            "Không tải được file nào. Kiểm tra kho '%s' đã tồn tại và công khai chưa "
            "(máy có dữ liệu chạy --day trước).", repo,
        )
        return 1

    logger.info("Xong %d file. Chạy tiếp: python scripts/run_dev.py", da_tai)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Dong bo du lieu MoodBite qua HuggingFace")
    nhom = parser.add_mutually_exclusive_group(required=True)
    nhom.add_argument("--tai", action="store_true", help="Tai du lieu ve may nay")
    nhom.add_argument("--day", action="store_true", help="Day du lieu may nay len kho")
    nhom.add_argument("--xem", action="store_true", help="Chi xem trang thai, khong doi gi")
    parser.add_argument(
        "--repo",
        default=os.getenv("MOODBITE_HF_DATASET", REPO_MAC_DINH),
        help=f"Kho tren HuggingFace (mac dinh {REPO_MAC_DINH})",
    )
    args = parser.parse_args()

    if args.xem:
        return xem()
    if args.day:
        return day(args.repo)
    return tai(args.repo)


if __name__ == "__main__":
    raise SystemExit(main())

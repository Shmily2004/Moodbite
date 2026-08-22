"""Đặt / xoá ảnh cho MỘT món — sửa tay, không phải mở file JSON 747 món.

    python scripts/set_dish_image.py --list-missing
    python scripts/set_dish_image.py --dish pho-bo --url "https://..." --credit "Ảnh: tôi tự chụp"
    python scripts/set_dish_image.py --dish pho-bo --clear

VÌ SAO CẦN: `find_dish_images.py` lấy ảnh tự động từ Wikipedia/Commons, nhưng nó chọn
BÀI KHỚP NHẤT chứ không hiểu nghĩa — "Phở gà" và "Phở bò" đều nhận ảnh của bài "Phở".
Script này để sửa lại từng món khi thấy ảnh chưa đúng, hoặc để dùng ảnh bạn tự chụp.

⚠️ ẢNH TỰ CHỤP THÌ GHI RÕ, ẢNH LẤY TRÊN MẠNG PHẢI CÓ GIẤY PHÉP RÕ RÀNG.
`--credit` là BẮT BUỘC khi đặt ảnh mới. Đồ án tốt nghiệp không nên dùng ảnh không rõ bản
quyền — đây là chỗ dễ bị hỏi nhất khi bảo vệ (CLAUDE.md mục 4b).

⚠️ CHỈ LƯU ĐƯỜNG DẪN, KHÔNG TẢI ẢNH VỀ. Muốn dùng ảnh trong máy thì chép vào
`frontend/apps/client/public/anh/` rồi đặt `--url /anh/ten-file.jpg`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data_pipeline" / "data_cleaned" / "dish_catalog.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def nap() -> dict:
    if not CATALOG.exists():
        raise SystemExit(f"Không thấy {CATALOG}. Chạy `python scripts/build_dish_catalog.py` trước.")
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def ghi(data: dict) -> None:
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dish", help="dish_id của món (VD pho-bo). Xem bằng --list-missing.")
    parser.add_argument("--url", help="Đường dẫn ảnh. Ảnh trong máy: /anh/ten-file.jpg")
    parser.add_argument("--credit", help="Nguồn + giấy phép. BẮT BUỘC khi đặt ảnh mới.")
    parser.add_argument("--clear", action="store_true", help="Xoá ảnh của món này.")
    parser.add_argument(
        "--list-missing",
        action="store_true",
        help="Liệt kê các món chưa có ảnh rồi thoát.",
    )
    args = parser.parse_args()

    data = nap()
    dishes = data["dishes"]

    if args.list_missing:
        thieu = [d for d in dishes if not d.get("image_url") and d.get("is_active", True)]
        print(f"{len(thieu)} món chưa có ảnh (trong tổng {len(dishes)}):")
        for d in thieu:
            print(f"  {d['dish_id']:<32} {d.get('name', '')}")
        return 0

    if not args.dish:
        parser.error("Thiếu --dish. Dùng --list-missing để xem danh sách.")

    mon = next((d for d in dishes if d.get("dish_id") == args.dish), None)
    if mon is None:
        print(f"Không có món nào mang dish_id = {args.dish!r}.")
        print("Dùng `python scripts/set_dish_image.py --list-missing` để xem danh sách.")
        return 1

    if args.clear:
        mon.pop("image_url", None)
        mon.pop("image_source", None)
        mon.pop("image_credit", None)
        ghi(data)
        print(f"Đã xoá ảnh của {mon.get('name')} ({args.dish}).")
    else:
        if not args.url:
            parser.error("Thiếu --url (hoặc dùng --clear để xoá ảnh).")
        if not args.credit:
            # Cố tình BẮT BUỘC: ảnh không rõ nguồn là rủi ro bản quyền, và sáu tháng sau
            # sẽ không ai nhớ tấm ảnh này lấy ở đâu.
            parser.error("Thiếu --credit. Mọi ảnh đều phải ghi nguồn + giấy phép.")

        mon["image_url"] = args.url
        mon["image_source"] = "thu_cong"
        mon["image_credit"] = args.credit
        ghi(data)
        print(f"Đã đặt ảnh cho {mon.get('name')} ({args.dish}).")
        print(f"  ảnh   : {args.url}")
        print(f"  nguồn : {args.credit}")

    print("⚠️ Backend đọc file này lúc KHỞI ĐỘNG -> khởi động lại server mới thấy thay đổi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

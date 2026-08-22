"""Nạp biến môi trường từ file `.env.local`.

VÌ SAO CẦN (thêm 2026-08-22): trước đây backend KHÔNG đọc file nào cả, người chạy phải tự
`$env:MOODBITE_...` cho 8-10 biến trong PowerShell mỗi lần mở terminal mới. Quên một biến
là tính năng tắt lặng lẽ, và chính chủ dự án đã điền nhầm giá trị thật vào `.env.example`
(file CÓ trong git) vì tưởng nó được đọc.

VÌ SAO KHÔNG DÙNG `python-dotenv`: cả việc này gói gọn trong ~30 dòng thư viện chuẩn, mà
thêm một phụ thuộc là thêm một thứ phải cài trên CI và trên máy chủ. Dự án đã cố ý cắt từ
15 gói xuống 7 (xem PROJECT_CHECKLIST).

⚠️ ĐỌC `.env.local` CHỨ KHÔNG PHẢI `.env.example`:
    `.env.example`  = MẪU, có trong git, chỉ chứa chỗ trống và ghi chú.
    `.env.local`    = giá trị THẬT, nằm trong .gitignore.
Đặt tên vậy để có lỡ mở nhầm file cũng không commit bí mật lên kho.

⚠️ BIẾN ĐÃ CÓ SẴN TRONG SHELL LUÔN THẮNG file. Trên máy chủ thật, biến được đặt bởi hệ
thống triển khai; một file `.env.local` sót lại tuyệt đối không được ghi đè lên nó.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("moodbite.config")

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = ROOT / ".env.local"


def nap_env_local(duong_dan: Path | None = None) -> int:
    """Đọc từng dòng `TÊN=giá trị` vào `os.environ`. Trả số biến đã nạp.

    Không có file thì trả 0 và im lặng — chạy bằng biến môi trường của shell là cách dùng
    hoàn toàn hợp lệ, không có gì để cảnh báo.
    """
    path = duong_dan or DEFAULT_ENV_FILE
    if not path.is_file():
        return 0

    da_nap = 0
    try:
        noi_dung = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Không đọc được %s: %s", path.name, exc)
        return 0

    for so_dong, dong in enumerate(noi_dung.splitlines(), start=1):
        dong = dong.strip()
        if not dong or dong.startswith("#"):
            continue
        if "=" not in dong:
            logger.warning("%s dòng %d: thiếu dấu '=' — bỏ qua.", path.name, so_dong)
            continue

        ten, gia_tri = dong.split("=", 1)
        ten = ten.strip()
        # Chỉ bỏ khoảng trắng hai đầu. KHÔNG bỏ khoảng trắng bên trong: mật khẩu ứng dụng
        # của Google hiển thị theo nhóm 4 ký tự cách nhau, người dùng dán y nguyên là
        # chuyện bình thường (chỗ dùng nó tự lọc — xem `Settings.from_env`).
        gia_tri = gia_tri.strip()

        # Bỏ cặp nháy bao ngoài nếu có: `TEN="giá trị"` cũng phải chạy đúng.
        if len(gia_tri) >= 2 and gia_tri[0] == gia_tri[-1] and gia_tri[0] in "\"'":
            gia_tri = gia_tri[1:-1]

        if not ten:
            continue
        # Shell thắng file — xem ghi chú đầu tệp.
        if ten in os.environ:
            continue

        os.environ[ten] = gia_tri
        da_nap += 1

    if da_nap:
        # ⚠️ CHỈ ghi SỐ LƯỢNG, tuyệt đối không ghi tên/giá trị biến: log hay bị dán lên
        # nhóm chat khi nhờ người khác xem giúp lỗi.
        logger.info("Đã nạp %d biến môi trường từ %s.", da_nap, path.name)
    return da_nap


__all__ = ["nap_env_local", "DEFAULT_ENV_FILE"]

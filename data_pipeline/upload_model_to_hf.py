"""
MoodBite - Upload model đã train (VD best.pt từ YOLO) lên HuggingFace Hub,
để lưu trữ lâu dài và dùng lại được trên máy khác mà không cần train lại.

CẦN TÀI KHOẢN HUGGINGFACE MIỄN PHÍ:
1. Đăng ký tại https://huggingface.co/join
2. Tạo access token tại https://huggingface.co/settings/tokens (chọn quyền "Write")
3. Chạy: huggingface-cli login   (dán token khi được hỏi)
   Hoặc set biến môi trường HF_TOKEN thay vì login tương tác.

CÁCH DÙNG:
    pip install huggingface_hub --break-system-packages
    huggingface-cli login
    python -m data_pipeline.upload_model_to_hf --file path/to/best.pt --repo-name moodbite-yolo-floorplan
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def upload_model(file_path: str, repo_name: str, private: bool = False) -> str | None:
    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        logger.error("Chưa cài huggingface_hub. Chạy: pip install huggingface_hub --break-system-packages")
        return None

    model_path = Path(file_path)
    if not model_path.exists():
        logger.error(f"Không tìm thấy file: {model_path}")
        return None

    api = HfApi()

    try:
        whoami = api.whoami()
        username = whoami["name"]
    except Exception as e:
        logger.error(
            f"Chưa đăng nhập HuggingFace. Chạy 'huggingface-cli login' trước. Lỗi: {e}"
        )
        return None

    full_repo_id = f"{username}/{repo_name}"
    logger.info(f"Tạo/kiểm tra repo: {full_repo_id}")

    try:
        create_repo(repo_id=full_repo_id, repo_type="model", private=private, exist_ok=True)
    except Exception as e:
        logger.error(f"Không tạo được repo: {e}")
        return None

    logger.info(f"Đang upload {model_path.name} ({model_path.stat().st_size / 1e6:.1f} MB)...")
    api.upload_file(
        path_or_fileobj=str(model_path),
        path_in_repo=model_path.name,
        repo_id=full_repo_id,
        repo_type="model",
    )

    url = f"https://huggingface.co/{full_repo_id}"
    logger.info(f"Upload thành công: {url}")
    logger.info(f"Link tải trực tiếp: https://huggingface.co/{full_repo_id}/resolve/main/{model_path.name}")

    return url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload model đã train lên HuggingFace Hub")
    parser.add_argument("--file", required=True, help="Đường dẫn file model (vd: best.pt)")
    parser.add_argument("--repo-name", required=True, help="Tên repo trên HuggingFace (vd: moodbite-yolo-floorplan)")
    parser.add_argument("--private", action="store_true", help="Tạo repo private thay vì public")
    args = parser.parse_args()

    upload_model(args.file, args.repo_name, args.private)

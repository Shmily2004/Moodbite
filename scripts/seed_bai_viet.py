"""Nạp vài bài viết MẪU vào kho bài viết (cẩm nang ẩm thực Hà Nội).

Chạy: python scripts/seed_bai_viet.py

VÌ SAO LÀ SCRIPT CHỨ KHÔNG PHẢI SQL TAY: đi qua đúng `CreatePostUseCase` nên mọi luật
kiểm tra (độ dài tiêu đề, slug không trùng, ghi thời điểm công khai) được áp dụng y như khi
admin tự viết trên web. Chạy lại nhiều lần cũng không tạo bài trùng: bài đã có slug thì bỏ qua.

Nội dung là VIẾT TAY, chung chung, KHÔNG chứa địa chỉ quán, giá, hay số liệu cụ thể — vì
đây là bài do admin viết (origin=admin), chủ bài chịu trách nhiệm nội dung. Muốn đổi thì
sửa thẳng trong SEED_BAI hoặc sửa trên trang quản trị sau khi nạp.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.application.use_cases.manage_posts import (  # noqa: E402
    CreatePostUseCase,
    PostInput,
    UpdatePostUseCase,
)
from src.domain.entities.post import PostOrigin, PostStatus, make_slug  # noqa: E402
from src.infrastructure.config.settings import Settings  # noqa: E402
from src.infrastructure.repositories.sqlite_post_repository import (  # noqa: E402
    SqlitePostRepository,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("seed_bai_viet")

SEED_BAI: list[dict] = [
    {
        # Ảnh là tranh minh hoạ do chính dự án có (`public/anh/`), không cần ghi nguồn.
        "image_url": "/anh/banner-trang-chu.png",
        "title": "Cẩm nang ăn sáng Hà Nội cho người mới đến",
        "summary": "Phở, bún chả, xôi và bánh cuốn: bốn món sáng nên thử và cách chọn quán.",
        "body": (
            "Hà Nội nổi tiếng với những bữa sáng giản dị nhưng rất có chiều sâu.\n\n"
            "Phở là lựa chọn quen thuộc nhất. Khi chọn quán, hãy để ý nước dùng trong, "
            "thơm mùi quế và hồi chứ không gắt mùi gia vị.\n\n"
            "Bún chả thường ăn kèm chả băm và chả miếng nướng trên than hoa. Nước chấm "
            "chua ngọt vừa phải là dấu hiệu của một quán làm kỹ.\n\n"
            "Xôi và bánh cuốn là món nhẹ bụng, hợp với người không quen ăn nặng vào buổi sáng.\n\n"
            "Mẹo nhỏ: nhiều quán nhỏ chỉ bán đến khi hết hàng, nên đi sớm sẽ có nhiều lựa chọn hơn."
        ),
    },
    {
        "title": "Ăn gì khi trời lạnh ở Hà Nội",
        "summary": "Các món nóng hợp mùa đông: chè, cháo, lẩu và bánh đa cua.",
        "body": (
            "Mùa đông Hà Nội có cái lạnh ẩm, dễ làm người ta thèm đồ nóng.\n\n"
            "Cháo nóng và cháo lòng là lựa chọn an toàn cho bữa trưa hoặc bữa tối nhẹ.\n\n"
            "Lẩu hợp đi theo nhóm bạn. Nên gọi thêm rau và đồ chua để cân bằng vị béo.\n\n"
            "Chè nóng và bánh gừng là món tráng miệng hợp với những buổi tối se lạnh.\n\n"
            "Bánh đa cua có nước dùng đậm vị, ăn vào buổi sáng sớm rất ấm bụng."
        ),
    },
    {
        "title": "Cách đọc thực đơn quán ăn Hà Nội",
        "summary": "Vài gợi ý để chọn món khi gặp thực đơn toàn chữ mà chưa biết bắt đầu từ đâu.",
        "body": (
            "Nhiều quán Hà Nội chỉ có một vài món chính nhưng làm rất chuyên. Thay vì gọi "
            "thật nhiều, hãy hỏi người bán món nào đang làm tốt nhất trong ngày.\n\n"
            "Các từ như \"đặc biệt\" hay \"thập cẩm\" thường có thêm nguyên liệu, nên giá cao "
            "hơn một chút.\n\n"
            "Nếu đi nhóm, nên chọn một món nước và một món khô để mọi người cùng ăn được.\n\n"
            "Lưu ý: giá và món thay đổi theo thời điểm, hãy xem lại khi đến quán."
        ),
    },
]


def main() -> int:
    settings = Settings.from_env()
    repo = SqlitePostRepository(settings.users_db)
    tao = CreatePostUseCase(repo)
    sua = UpdatePostUseCase(repo)
    hien_co = {bai.slug: bai for bai in repo.list(status=None)}

    tao_moi = cap_nhat = 0
    for bai in SEED_BAI:
        slug_du_kien = make_slug(bai["title"])
        anh = bai.get("image_url")
        if slug_du_kien in hien_co:
            cu = hien_co[slug_du_kien]
            # Bài đã có: chỉ bổ sung ẢNH nếu còn thiếu; không ghi đè chữ admin đã sửa.
            if anh and cu.image_url != anh:
                sua.execute(
                    cu.post_id,
                    PostInput(
                        title=cu.title,
                        summary=cu.summary,
                        body=cu.body,
                        status=cu.status,
                        source_name=cu.source_name,
                        source_url=cu.source_url,
                        last_updated=cu.last_updated,
                        origin=cu.origin,
                        image_url=anh,
                    ),
                )
                cap_nhat += 1
                log.info("Đã thêm ảnh cho: %s", slug_du_kien)
            else:
                log.info("Bỏ qua (đã có): %s", slug_du_kien)
            continue
        tao.execute(
            PostInput(
                title=bai["title"],
                summary=bai["summary"],
                body=bai["body"],
                status=PostStatus.PUBLISHED,
                origin=PostOrigin.ADMIN,
                image_url=anh,
            )
        )
        tao_moi += 1
        log.info("Đã nạp: %s", slug_du_kien)

    log.info("Xong. Bài mới: %d · thêm ảnh: %d · tổng mẫu: %d.", tao_moi, cap_nhat, len(SEED_BAI))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

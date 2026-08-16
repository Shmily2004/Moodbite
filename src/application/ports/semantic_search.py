"""PORT: hợp đồng TÌM KIẾM NGỮ NGHĨA (Lớp 2 của đề án).

Đề án mô tả: câu tìm kiếm và mô tả/review của quán được chuyển thành vector, rồi so
độ tương đồng cosine - nhờ vậy "chỗ yên tĩnh để làm việc" khớp được với quán được
review là "không gian tĩnh lặng, ngồi lâu thoải mái" dù KHÔNG chung từ nào.

VÌ SAO LÀ PORT: hiện dùng TF-IDF (nhẹ, chạy được ngay, không cần GPU). Khi có đủ review
có thể đổi sang sentence-transformers mà KHÔNG sửa use case - chỉ viết adapter mới.

Adapter KHÔNG sẵn sàng (chưa đủ dữ liệu, thiếu thư viện) -> trả điểm rỗng, hệ thống tự
lui về khớp từ khoá. Tìm kiếm ngữ nghĩa là tín hiệu BỔ SUNG, không phải điều kiện sống còn.
"""
from __future__ import annotations

from typing import Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class SemanticSearchPort(Protocol):
    @property
    def is_ready(self) -> bool:
        """False khi chưa dựng được chỉ mục - tầng gọi bỏ qua tín hiệu này."""
        ...

    def similarity(self, query_text: str) -> Dict[str, float]:
        """{place_id: độ tương đồng 0..1} cho các quán khớp NGỮ NGHĨA với câu hỏi.

        Chỉ trả về những quán có điểm > 0 để tầng gọi không phải duyệt cả 4900 quán.
        KHÔNG được ném exception: lỗi ở đây không được làm hỏng lượt tìm kiếm.
        """
        ...

    def status(self) -> dict:
        ...

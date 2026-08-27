"""QUY TẮC NGHIỆP VỤ: quán nào được gắn nhãn "Nổi tiếng".

Bản thiết kế `frontend/design/restaurance recommend.png` có nhãn "Nổi tiếng" cạnh tên
quán. Đây là một QUY TẮC NGHIỆP VỤ, không phải chuyện hiển thị — nó quyết định người
dùng tin quán nào hơn. Vì vậy nó nằm ở `domain/`, KHÔNG được tính ở frontend
(CLAUDE.md mục 1b: sửa công thức ở hai nơi thì chắc chắn có lúc quên một nơi).

CHỌN NGƯỠNG BẰNG SỐ ĐO, KHÔNG BẰNG CẢM TÍNH (CLAUDE.md mục 4c)
---------------------------------------------------------------
Đo trên dữ liệu thật ngày 2026-08-27 (52.854 quán):

    có `reviews_count`  : 1.252 quán = 2,4%
    phân vị số review   : p50=28 · p75=148 · p90=505 · p95=1.004 · p99=2.938

    >=  100 review : 382 quán (30,5% trong số có dữ liệu)
    >=  300 review : 190 quán (15,2%)   <-- chọn mức này
    >= 1000 review : 64 quán  (5,1%)

    >= 300 review VÀ rating >= 4,0 : **151 quán**

Vì sao 300 và 4,0:
  - Dưới 300 (VD 100) cho ra 382 quán — nhãn xuất hiện quá dày và mất nghĩa "nổi tiếng".
  - Trên 1.000 chỉ còn 64 quán, gần như chỉ là chuỗi lớn (KFC, McDonald's, The Coffee
    House) — thành nhãn "chuỗi", không phải "nổi tiếng".
  - Ngưỡng 300 nằm giữa p75 và p90, tức là quán này được nhắc tới nhiều hơn hẳn phần còn
    lại của chính nhóm có dữ liệu.
  - Thêm điều kiện rating >= 4,0 vì "nhiều người nhắc tới" chưa chắc là "đáng tới": một
    quán 500 review mà 2,8 sao thì gắn nhãn "Nổi tiếng" là đánh lừa người dùng.

⚠️ CHỈ 2,4% QUÁN CÓ DỮ LIỆU REVIEW. Vì vậy:

    KHÔNG có nhãn  ≠  quán không nổi tiếng
    KHÔNG có nhãn  =  ta KHÔNG BIẾT (97,6% trường hợp) hoặc không đủ ngưỡng

Giao diện TUYỆT ĐỐI không được suy ra "quán này không nổi tiếng" từ việc thiếu nhãn, và
không được sắp xếp hay lọc theo nhãn này — làm vậy là đẩy 97,6% quán xuống đáy vì một
thứ ta chưa đo được. Nhãn chỉ để KHẲNG ĐỊNH, không bao giờ để PHỦ ĐỊNH.
"""
from __future__ import annotations

from typing import Optional

# Xem phần "CHỌN NGƯỠNG BẰNG SỐ ĐO" ở đầu file để biết vì sao là 300 và 4.0.
SO_REVIEW_NOI_TIENG = 300
RATING_TOI_THIEU_NOI_TIENG = 4.0


def la_quan_noi_tieng(
    rating: Optional[float], reviews_count: Optional[int]
) -> bool:
    """`True` khi CHẮC CHẮN quán này nổi tiếng. `False` nghĩa là "không biết HOẶC không đủ".

    Cả hai điều kiện phải có mặt: thiếu một trong hai là không đủ bằng chứng, và ở đây
    thiếu bằng chứng phải cho ra `False` chứ không phải đoán bừa.

    `None` KHÔNG được coi là 0 (CLAUDE.md mục 4 quy tắc 1) — nhưng ở phép kiểm này thì
    cả hai đều dẫn tới `False`, nên viết thẳng cho gọn và an toàn.
    """
    if rating is None or reviews_count is None:
        return False
    try:
        return (
            int(reviews_count) >= SO_REVIEW_NOI_TIENG
            and float(rating) >= RATING_TOI_THIEU_NOI_TIENG
        )
    except (TypeError, ValueError):
        # Dữ liệu hỏng (chuỗi lạ trong cột số) -> KHÔNG gắn nhãn. Không làm sập lượt tìm.
        return False


__all__ = [
    "la_quan_noi_tieng",
    "SO_REVIEW_NOI_TIENG",
    "RATING_TOI_THIEU_NOI_TIENG",
]

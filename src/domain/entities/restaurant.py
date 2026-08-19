"""Entity Restaurant. Thuần Python - KHÔNG import pandas/FastAPI.

Quy ước QUAN TRỌNG về giá trị thiếu: `price`, `rating`, `reviews_count` để None nghĩa là
CHƯA CÓ DỮ LIỆU, không phải "miễn phí" hay "0 sao". 3623/4170 quán đến từ OpenStreetMap
vốn không hề có các trường này. Tuyệt đối không thay None bằng 0 khi trả cho client.

`price` là CHUỖI hiển thị theo khoảng giá của Google Maps ("1-100.000 ₫", "70 US$"),
KHÔNG phải số. Dataset có nhiều đơn vị tiền tệ và dạng khoảng, nên ép về float vừa sai
vừa làm hỏng response. Muốn lọc theo giá thì phải parse thành value object riêng trước.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.domain.value_objects.location import Location
from src.domain.value_objects.mood import MOOD_SCORE_COLUMNS


@dataclass(frozen=True)
class Restaurant:
    place_id: Optional[str]
    name: str
    category: Optional[str]
    location: Location
    address: Optional[str] = None
    cuisine: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    # {tên cột mood-score -> giá trị}. Thiếu cột nào coi như 0.0.
    mood_scores: Dict[str, float] = field(default_factory=dict)

    # --- Dữ liệu phục vụ tìm kiếm bằng câu tự do -------------------------------
    # Tất cả đều THƯA (xem PROJECT_CHECKLIST.md). Thiếu = None, và việc thiếu KHÔNG
    # được coi là điểm xấu khi xếp hạng.
    atmosphere_tags: List[str] = field(default_factory=list)   # 8.7% quán có
    review_text: Optional[str] = None                          # 8.4% quán có
    # Ảnh đại diện cho card kết quả. CHỈ 21.5% quán có -> giao diện phải coi "không có
    # ảnh" là trường hợp BÌNH THƯỜNG, không phải lỗi.
    thumbnail_url: Optional[str] = None
    opening_hours: Optional[str] = None                        # 25.6% quán có
    is_active: bool = True  # soft-delete: quán tắt không bao giờ được trả cho người dùng
    # TRẠNG THÁI KINH DOANH, lấy từ nguồn dữ liệu - KHÁC HẲN `is_active` (admin tự tắt).
    #
    # `None` = KHÔNG BIẾT. Chỉ quán từ Apify/Google mới có trường này; quán từ OSM và
    # Overture thì không, và "không biết" phải khác "biết chắc đang mở" - nếu không thì
    # 96,5% dataset sẽ mang tiếng là đã xác minh còn mở, trong khi chưa ai kiểm.
    permanently_closed: Optional[bool] = None
    temporarily_closed: Optional[bool] = None

    # --- TUỔI THẬT & BẰNG CHỨNG XÁC NHẬN ---------------------------------------
    #
    # ⚠️ ĐỪNG NHẦM VỚI `last_updated` của bản ghi (ngày TA CÀO). Đo 2026-08-19: cột kia
    # ghi 97,4% dữ liệu "cập nhật 3 ngày trước", trong khi 71,5% bản ghi OSM thật ra được
    # sửa lần cuối từ 2025 trở về trước, cũ nhất là năm 2010.
    #
    # Ngày NGUỒN cập nhật bản ghi lần cuối (ISO-8601). Sinh bởi `scripts/enrich_freshness.py`.
    source_updated_at: Optional[str] = None
    # Nền tảng ĐỘC LẬP cùng ghi nhận quán này (meta, Microsoft, Foursquare, openstreetmap).
    source_datasets: List[str] = field(default_factory=list)
    # Ngày có người đi XÁC MINH TẬN NƠI (tag `check_date` của OSM) - bằng chứng mạnh nhất.
    surveyed_at: Optional[str] = None
    # Link mạng xã hội do NGUỒN cung cấp (Meta đóng góp vào Overture, giấy phép
    # CDLA-Permissive-2.0). KHÔNG phải cào Facebook - xem `data_pipeline/sources/base.py`.
    socials: List[str] = field(default_factory=list)

    # --- trường bổ sung từ bản thu thập OSM mới --------------------------------
    # Đơn vị hành chính (OSM admin_level=6). Từ 2025 Việt Nam bỏ cấp quận/huyện nên
    # giá trị thực tế là "Phường ..." chứ không phải "Quận ...".
    district: Optional[str] = None
    dietary: List[str] = field(default_factory=list)    # vegetarian / vegan / halal
    amenities: List[str] = field(default_factory=list)  # outdoor_seating, wifi...
    phone: Optional[str] = None
    website: Optional[str] = None
    # Nguồn gốc dữ liệu - để giải thích được "quán này ở đâu ra, đáng tin tới đâu".
    source: Optional[str] = None
    data_confidence: Optional[str] = None

    # Cụm trải nghiệm (Lớp 1 đề án). None = CHƯA PHÂN CỤM, không phải "cụm kém".
    # Quy tắc Cold Start (rules/rules.md mục 3.3): khi tính điểm phải dùng giá trị TRUNG
    # LẬP toàn hệ thống cho quán chưa có cụm, TUYỆT ĐỐI không dùng 0 hay NULL.
    experience_cluster_id: Optional[int] = None
    experience_cluster_label: Optional[str] = None

    @property
    def is_visible(self) -> bool:
        """Có được hiện cho NGƯỜI DÙNG CUỐI không.

        Gộp hai lý do ẩn hoàn toàn khác nhau, và cố ý gộp ở ĐÂY thay vì ở từng use case:
          - `is_active = False`      : admin chủ động ẩn (rules/rules.md mục 3.2)
          - `permanently_closed`     : quán đã đóng hẳn theo dữ liệu nguồn

        Trang quản trị vẫn phải nhìn thấy cả hai loại, nên admin dùng `is_active` trực
        tiếp chứ KHÔNG dùng thuộc tính này - ẩn quán khỏi mắt admin thì chính admin cũng
        không bỏ ẩn lại được.

        Đóng TẠM thì vẫn hiện: quán nghỉ Tết hay sửa nhà vài tuần vẫn là quán có thật, và
        giấu đi thì người dùng tưởng quán biến mất luôn. Nhưng phải gắn nhãn cảnh báo -
        xem `temporarily_closed` trong response API.
        """
        return self.is_active and not self.permanently_closed

    @property
    def atmosphere_text(self) -> Optional[str]:
        """Các tag không gian gộp thành 1 chuỗi để so khớp văn bản."""
        return " ".join(self.atmosphere_tags) if self.atmosphere_tags else None

    def mood_score(self, column: str) -> float:
        """Điểm mood theo 1 cột. Thiếu dữ liệu -> 0.0.

        ⚠️ 0.0 ở đây KHÔNG phải "trung lập" - nó là giá trị THẤP NHẤT có thể. Docstring cũ
        ghi là "trung lập" và chính chữ đó đã che mất một lỗi thật suốt thời gian dài:
        quán không có chữ nào để dò (chỉ có tên + loại hình) bị chấm 0 ở cả 5 chiều, tức
        là bị phạt vì TA thiếu dữ liệu về nó, chứ không phải vì nó dở. Xem
        `has_mood_evidence` - nơi phân biệt "biết là không hợp" với "chưa biết gì".
        """
        value = self.mood_scores.get(column)
        return 0.0 if value is None else float(value)

    @property
    def has_mood_evidence(self) -> bool:
        """Có dò được BẤT KỲ tín hiệu cảm xúc nào không.

        Phân biệt hai chuyện mà điểm 0 gộp làm một:
          - Có chữ để dò, dò xong không thấy "ấm cúng"  -> quán này thật sự không ấm cúng.
          - Chẳng có chữ nào để dò                      -> ta CHƯA BIẾT.

        Đo ngày 2026-08-19: 40% quán rơi vào vế thứ hai (phần lớn từ Overture, chỉ có tên
        + loại hình, không review). Gộp chúng vào vế thứ nhất là đẩy 40% dataset xuống đáy
        bảng xếp hạng ở tín hiệu NẶNG NHẤT (W_MOOD = 0.26).
        """
        return any(v for v in self.mood_scores.values() if v)

    def weighted_mood_score(self, weights: Dict[str, float]) -> float:
        """Tổng có trọng số của nhiều cột mood-score. Xem domain/value_objects/mood.py."""
        return sum(self.mood_score(col) * w for col, w in weights.items())

    def rating_for_ranking(self) -> float:
        """Rating dùng ĐỂ XẾP HẠNG: quán chưa có rating coi như 0.

        Chỉ dùng nội bộ khi sort. KHÔNG được dùng giá trị này khi trả về cho client -
        client phải thấy None để hiển thị "chưa có đánh giá".
        """
        return 0.0 if self.rating is None else float(self.rating)


__all__ = ["Restaurant", "MOOD_SCORE_COLUMNS"]

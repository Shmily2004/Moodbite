"""Làm giàu MÓN ĂN từ Wikipedia tiếng Việt: GIỚI THIỆU NGẮN + ẢNH. Miễn phí, không cần khoá API.

Đổi hướng ngày 2026-08-19 (chủ dự án chốt): bỏ phần THÀNH PHẦN/nguyên liệu, thay bằng một
đoạn GIỚI THIỆU NGẮN về món. Lý do thực dụng: đoạn mở đầu bài Wikipedia vốn đã nói luôn
món đó là gì và thường kể cả nguyên liệu chính ngay trong câu văn, nên nó vừa dễ đọc hơn
một danh sách nguyên liệu rời rạc, vừa phủ được nhiều món hơn.

HAI BÀI HỌC ĐÃ TRẢ GIÁ, ĐỪNG LẶP LẠI
------------------------------------
1. KHÔNG dùng regex bắt câu "Thành phần chính là..." trong thân bài. Đã đo trên 18 món
   (2026-08-18) rồi BỎ, vì nó sinh dữ liệu SAI mà trông vẫn hợp lệ:
       "Bánh mì" -> "...dùng làm chất độn để chèn vào răng sâu"
       "Cơm tấm" -> "nguyên liệu khác."
   Hiển thị mấy dòng đó cho người dùng còn tệ hơn là để trống.

2. KHÔNG gộp nhiều trang vào một lần gọi `prop=extracts` kèm `exintro`. MediaWiki chỉ trả
   đoạn mở đầu cho ĐÚNG MỘT trang mỗi request khi bật `exintro` - gửi 50 title thì 49 món
   về tay không. Đây chính là lý do độ phủ mô tả đo được chỉ 51.9% dù mọi lần gọi mạng đều
   thành công. Nay dùng REST summary API: MỖI MÓN MỘT LẦN GỌI, có cache đĩa.

ẢNH: CHỈ LƯU ĐƯỜNG DẪN, TUYỆT ĐỐI KHÔNG TẢI VỀ
-----------------------------------------------
Máy chủ dự án là laptop cá nhân, dung lượng có hạn. Ảnh trên Wikimedia Commons cho phép
nhúng trực tiếp, nên lưu URL tốn ~100 byte/món thay vì ~200KB/món nếu tải ảnh về.
500 món = 50KB thay vì 100MB.

Lấy bản `thumbnail` (~320px) chứ KHÔNG phải `originalimage`: ảnh gốc có cái nặng 8MB, mà
chỗ hiển thị trên thẻ món chỉ 84px - tải ảnh gốc là phí băng thông của người dùng.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from data_pipeline.sources.base import utc_now_iso

logger = logging.getLogger("moodbite.sources.wikipedia_dish")

# REST summary API: một lần gọi trả đủ đoạn mở đầu + ảnh + QID.
SUMMARY_API = "https://vi.wikipedia.org/api/rest_v1/page/summary/{title}"

# Chính sách Wikimedia YÊU CẦU User-Agent nói rõ mình là ai và liên hệ ở đâu.
# Gửi User-Agent mặc định của requests là cách nhanh nhất để bị chặn IP.
USER_AGENT = "MoodBite/1.0 (academic graduation project; contact mungvu999@gmail.com)"

# Nghỉ giữa các lần gọi. Wikimedia không công bố hạn mức cứng cho đọc, nhưng gọi dồn dập
# từ một IP là cách nhanh nhất để bị chặn.
SLEEP_BETWEEN_CALLS = 0.15

DISH_SOURCE = "wikipedia_vi"

# Độ dài tối đa của đoạn giới thiệu. Thẻ món chỉ có chỗ cho vài dòng; dài hơn thì người
# dùng bỏ qua không đọc.
MAX_INTRO_CHARS = 320


@dataclass
class DishInfo:
    """Phần lấy được cho MỘT món. Trường nào không lấy được thì để None.

    KHÔNG có mặc định kiểu chuỗi rỗng: rỗng ở đây nghĩa là CHƯA TRA ĐƯỢC, và tầng trên
    phải phân biệt được điều đó với "món này không có gì để nói".
    """

    title: str
    qid: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    last_updated: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        return not (self.description or self.image_url)

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "qid": self.qid,
            "description": self.description,
            "image_url": self.image_url,
            "source": DISH_SOURCE,
            "source_url": self.source_url,
            "last_updated": self.last_updated or utc_now_iso(),
        }


class WikipediaDishSource:
    """Tra giới thiệu ngắn + ảnh cho một danh sách tên món.

    CÓ CACHE TRÊN ĐĨA: chạy lại lần hai gần như không tốn lần gọi mạng nào. Cache là JSON
    thuần, mỗi món ~400 byte - 1000 món vẫn chưa tới 1MB.
    """

    def __init__(
        self,
        cache_dir: Path | str = "data_pipeline/data_raw/.wikipedia_dish_cache",
        timeout_seconds: float = 20.0,
        sleep_between_calls: float = SLEEP_BETWEEN_CALLS,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.timeout_seconds = timeout_seconds
        self.sleep_between_calls = sleep_between_calls
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})

    @property
    def name(self) -> str:
        return DISH_SOURCE

    def is_available(self) -> tuple[bool, str]:
        """Có gọi được Wikipedia không.

        Người gọi PHẢI tôn trọng kết quả này và bỏ qua bước làm giàu, chứ không được để cả
        script dựng danh mục chết chỉ vì máy đang offline.
        """
        try:
            response = self._session.get(
                SUMMARY_API.format(title="Ph%E1%BB%9F"), timeout=self.timeout_seconds
            )
            if response.status_code == 200:
                return True, "OK"
            return False, f"Wikipedia tra HTTP {response.status_code}"
        except requests.RequestException as exc:
            return False, f"khong goi duoc Wikipedia: {exc}"

    def fetch_many(self, titles: List[str]) -> Dict[str, DishInfo]:
        """Tra nhiều món. Trả dict theo ĐÚNG tên đưa vào.

        Món không có bài Wikipedia vẫn có mặt trong kết quả với `DishInfo` rỗng - để phía
        gọi phân biệt "đã tra, không có" với "chưa tra".
        """
        result: Dict[str, DishInfo] = {}
        pending: List[str] = []

        for title in titles:
            cached = self._read_cache(title)
            if cached is not None:
                result[title] = cached
            else:
                pending.append(title)

        logger.info(
            "Lam giau mon: %d tu cache, %d can goi mang", len(result), len(pending)
        )

        for index, title in enumerate(pending, start=1):
            info = self._fetch_one(title)
            result[title] = info
            self._write_cache(title, info)
            if index % 25 == 0:
                logger.info("  ... %d/%d", index, len(pending))

        return result

    def _fetch_one(self, title: str) -> DishInfo:
        """MỘT món một lần gọi. Đây là khác biệt cốt lõi so với bản cũ - xem đầu file."""
        encoded = quote(title.replace(" ", "_"), safe="")
        try:
            response = self._session.get(
                SUMMARY_API.format(title=encoded), timeout=self.timeout_seconds
            )
            time.sleep(self.sleep_between_calls)
        except requests.RequestException as exc:
            # Một món hỏng KHÔNG được làm hỏng cả lượt.
            logger.debug("Bo qua '%s': %s", title, exc)
            return DishInfo(title=title)

        # 404 = không có bài. Đây là kết quả BÌNH THƯỜNG với món dân dã ("Bún nước",
        # "Đồ nhắm"), không phải lỗi cần cảnh báo ầm ĩ.
        if response.status_code != 200:
            return DishInfo(title=title)

        try:
            payload = response.json()
        except ValueError:
            return DishInfo(title=title)

        # Trang định hướng thì nội dung là danh sách liên kết, không mô tả món nào cả ->
        # coi như không có, để bản soạn tay điền vào.
        if payload.get("type") == "disambiguation":
            return DishInfo(title=title)

        thumbnail = payload.get("thumbnail") or {}
        page_url = (payload.get("content_urls") or {}).get("desktop", {}).get("page")

        return DishInfo(
            title=title,
            qid=payload.get("wikibase_item"),
            description=self._shorten(payload.get("extract")),
            # `thumbnail` chứ không phải `originalimage` - xem giải thích ở đầu file.
            image_url=thumbnail.get("source"),
            source_url=page_url,
            last_updated=utc_now_iso(),
        )

    @staticmethod
    def _shorten(extract: Optional[str]) -> Optional[str]:
        """Cắt ở RANH GIỚI CÂU, không cắt giữa chừng.

        Cắt cứng theo số ký tự tạo ra những câu cụt kiểu "Phở là món ăn truyền th" - đọc
        lên là biết hệ thống làm ẩu.
        """
        if not extract:
            return None
        text = " ".join(str(extract).split())
        if not text:
            return None
        if len(text) <= MAX_INTRO_CHARS:
            return text
        cut = text[:MAX_INTRO_CHARS]
        stop = cut.rfind(". ")
        return (cut[: stop + 1] if stop > 80 else cut).strip()

    # --- cache ----------------------------------------------------------------

    def _cache_file(self, title: str) -> Path:
        safe = "".join(c if c.isalnum() else "_" for c in title)[:80]
        return self.cache_dir / f"{safe}.json"

    def _read_cache(self, title: str) -> Optional[DishInfo]:
        path = self._cache_file(title)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            path.unlink(missing_ok=True)   # cache hỏng thì tra lại
            return None
        return DishInfo(
            title=raw.get("title", title),
            qid=raw.get("qid"),
            description=raw.get("description"),
            image_url=raw.get("image_url"),
            source_url=raw.get("source_url"),
            last_updated=raw.get("last_updated"),
        )

    def _write_cache(self, title: str, info: DishInfo) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file(title).write_text(
            json.dumps(info.to_record(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

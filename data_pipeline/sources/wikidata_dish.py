"""Nguồn MÓN ĂN thứ hai: WIKIDATA. Giấy phép CC0, miễn phí, không cần khoá API.

    python scripts/discover_dishes.py --source wikidata

VÌ SAO THÊM NGUỒN NÀY khi đã có Wikipedia
-----------------------------------------
`sources/wikipedia_dish.py` duyệt THỂ LOẠI của vi.wikipedia. Cách đó chỉ thấy món nào có
người Việt viết bài, và **không bao giờ cho biết TÊN GỌI KHÁC của một món**. Wikidata bù
đúng hai chỗ đó:

1. `aliases` — mỗi mục Wikidata có sẵn danh sách tên gọi khác ở từng ngôn ngữ. Đây chính
   là thứ `match_keywords` đang thiếu: quán ghi "bánh mỳ" (120 quán, đo 2026-08-24) trong
   khi danh mục chỉ có "bánh mì" nên không khớp được quán nào.
2. Món nước ngoài bán đầy Hà Nội nhưng chưa ai viết bài tiếng Việt (kimbap, tokbokki...)
   vẫn có mục Wikidata kèm nhãn tiếng Anh.

KHÔNG DÙNG SPARQL — ĐÃ THỬ VÀ HỎNG
----------------------------------
Đo ngày 2026-08-24: query đóng bao truyền ngôi (`wdt:P31/wdt:P279* wd:Q2095`) trên
`query.wikidata.org` trả **HTTP 504**, viết lại gọn hơn thì trả **HTTP 502**. Máy chủ
WDQS chia sẻ cho cả thế giới và hay quá tải — không dựa vào được cho một bước chạy lại
thường xuyên. Dùng **API tìm kiếm + `wbgetentities`** thay thế: chậm hơn chút nhưng ổn
định, có phân trang rõ ràng và trả về đúng những trường cần.

HAI RỔ ỨNG VIÊN, VÌ MỘT RỔ THÔI LÀ THIẾU (số đo 2026-08-24)
-----------------------------------------------------------
    haswbstatement:P495=Q881                     -> 1.222 mục  (gốc Việt Nam, đủ mọi loại)
    haswbstatement:P495=Q881 + P31=Q746549       ->    23 mục  (tự nhận là "món ăn")
    haswbstatement:P31=Q746549                   -> 3.697 mục  (món ăn toàn thế giới)

Con số 23 cho thấy thuộc tính "là món ăn" (P31=Q746549) bị dùng RẤT thưa trên các mục
tiếng Việt — lọc theo nó thì mất gần hết. Nên lấy hợp của rổ 1.222 (rộng, lọc lại bằng
mô tả) và rổ 3.697 (đã chắc là món, phủ ẩm thực Nhật/Hàn/Ý...).

LỌC "CÓ PHẢI MÓN ĂN KHÔNG" DÙNG CHUNG VỚI WIKIPEDIA
---------------------------------------------------
Module này CỐ Ý không tự viết bộ lọc. Nó chỉ trả về ứng viên kèm `description`;
`scripts/discover_dishes.py` gọi `looks_like_dish()` — đúng bộ lọc đã tinh chỉnh qua các
lượt chạy thật (chặn "Trà", "Chanh", "KFC", "Đuông"...). Hai nguồn dùng hai bộ lọc khác
nhau thì chắc chắn sẽ có lúc nói ngược nhau.

ẢNH: CHỈ LƯU ĐƯỜNG DẪN (giống `wikipedia_dish.py`) — xem lý do dung lượng ở file đó.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote

import requests

from data_pipeline.sources.wikipedia_dish import USER_AGENT, DishInfo

logger = logging.getLogger("moodbite.sources.wikidata_dish")

API = "https://www.wikidata.org/w/api.php"

DISH_SOURCE = "wikidata"

# Mục Wikidata dùng làm rổ ứng viên.
#   P495 = quốc gia xuất xứ, Q881 = Việt Nam
#   P31  = là một, Q746549 = món ăn
# Xem phần số đo ở đầu file để biết vì sao cần CẢ HAI.
SEARCH_QUERIES = (
    "haswbstatement:P495=Q881",
    "haswbstatement:P31=Q746549",
)

# Ngôn ngữ lấy nhãn và tên gọi khác. Tiếng Việt trước vì tên quán ở Hà Nội viết bằng
# tiếng Việt; tiếng Anh để phủ món ngoại chưa có nhãn Việt (sushi, kimbap, pizza).
LANGUAGES = ("vi", "en")

# `wbgetentities` nhận tối đa 50 mã mỗi lần — giới hạn của MediaWiki, không phải ta chọn.
ENTITY_BATCH = 50

# Nghỉ giữa hai lần gọi. Bằng với `discover_dishes.py` vì cùng một hạ tầng Wikimedia và
# đã có tiền lệ bị trả 429 hàng loạt khi gọi dồn (2026-08-19).
POLITE_DELAY_SECONDS = 0.4

# Mã lỗi TẠM THỜI — phải thử lại chứ không được coi là "không có kết quả". Bài học đã ghi
# ở `discover_dishes.py`: coi 429 là rỗng thì một lỗi mạng thoáng qua xoá sạch dữ liệu.
TRANSIENT_STATUS = frozenset({429, 500, 502, 503, 504})
MAX_RETRIES = 5
BACKOFF_SECONDS = 2.0

# Ảnh Commons: `Special:FilePath` tự chuyển hướng tới file thật và nhận tham số `width`,
# nên không phải gọi thêm API để tra đường dẫn. 320px khớp với cỡ ảnh Wikipedia đang lưu.
COMMONS_FILEPATH = "https://commons.wikimedia.org/wiki/Special:FilePath/{file}?width=320"

IMAGE_PROPERTY = "P18"


class WikidataUnavailable(RuntimeError):
    """Hỏi đủ số vòng vẫn không xong. Người gọi PHẢI xử lý, không được coi là rỗng."""


class WikidataDishSource:
    """Lấy ứng viên MÓN ĂN từ Wikidata. Có cache đĩa để chạy lại không tốn mạng."""

    def __init__(
        self,
        cache_dir: Path | str = "data_pipeline/data_raw/.wikidata_dish_cache",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.timeout_seconds = timeout_seconds
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})

    @property
    def name(self) -> str:
        return DISH_SOURCE

    def is_available(self) -> tuple[bool, str]:
        try:
            response = self._session.get(
                API,
                params={"action": "wbgetentities", "ids": "Q881", "format": "json"},
                timeout=self.timeout_seconds,
            )
            if response.status_code == 200:
                return True, "OK"
            return False, f"Wikidata tra HTTP {response.status_code}"
        except requests.RequestException as exc:
            return False, f"khong goi duoc Wikidata: {exc}"

    # --- gọi mạng ------------------------------------------------------------

    def _get(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Gọi API, thử lại khi gặp lỗi TẠM THỜI, NÉM LỖI nếu hết vòng thử."""
        wait = BACKOFF_SECONDS
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._session.get(
                    API, params=params, timeout=self.timeout_seconds
                )
                if response.status_code in TRANSIENT_STATUS:
                    raise requests.HTTPError(f"HTTP {response.status_code}")
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                if attempt == MAX_RETRIES:
                    raise WikidataUnavailable(
                        f"thu {MAX_RETRIES} lan van loi - {exc}"
                    ) from exc
                logger.warning(
                    "  Wikidata: %s -> cho %.0fs roi thu lai (lan %d/%d)",
                    exc, wait, attempt, MAX_RETRIES,
                )
                time.sleep(wait)
                wait *= 2
        raise WikidataUnavailable("khong toi day duoc")  # pragma: no cover

    def _search_qids(self, query: str) -> List[str]:
        """Mọi mã Q khớp một câu tìm kiếm, có phân trang.

        `srlimit=50` là mức tối đa cho tài khoản thường. Không tăng được, đừng thử.
        """
        qids: List[str] = []
        offset = 0
        while True:
            payload = self._get({
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": "50",
                "sroffset": str(offset),
                "srnamespace": "0",
                "format": "json",
            })
            batch = payload.get("query", {}).get("search", [])
            qids.extend(item["title"] for item in batch if item.get("title"))
            offset += len(batch)
            time.sleep(POLITE_DELAY_SECONDS)
            if not batch or "continue" not in payload:
                break
        logger.info("  %-40s -> %d muc", query, len(qids))
        return qids

    def _fetch_entities(self, qids: List[str]) -> Dict[str, Any]:
        """Nội dung chi tiết cho tối đa 50 mã. Có cache đĩa theo từng lô."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / f"batch_{qids[0]}_{len(qids)}.json"
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                cache_file.unlink(missing_ok=True)

        payload = self._get({
            "action": "wbgetentities",
            "ids": "|".join(qids),
            # Chỉ xin đúng thứ cần. Xin cả `claims` của mọi thuộc tính thì gói tin nặng
            # gấp nhiều lần mà ta chỉ dùng mỗi P18 (ảnh).
            "props": "labels|aliases|descriptions|claims",
            "languages": "|".join(LANGUAGES),
            "format": "json",
        })
        entities = payload.get("entities", {})
        cache_file.write_text(
            json.dumps(entities, ensure_ascii=False), encoding="utf-8"
        )
        time.sleep(POLITE_DELAY_SECONDS)
        return entities

    # --- chuyển đổi ----------------------------------------------------------

    @staticmethod
    def _first_language(block: Dict[str, Any]) -> Optional[str]:
        """Giá trị tiếng Việt nếu có, không thì tiếng Anh. None nếu không có gì."""
        for lang in LANGUAGES:
            value = (block or {}).get(lang, {}).get("value")
            if value and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _all_aliases(block: Dict[str, Any]) -> List[str]:
        """Mọi tên gọi khác ở các ngôn ngữ quan tâm, giữ thứ tự, không trùng."""
        seen: set[str] = set()
        result: List[str] = []
        for lang in LANGUAGES:
            for entry in (block or {}).get(lang, []) or []:
                value = (entry.get("value") or "").strip()
                key = value.lower()
                if value and key not in seen:
                    seen.add(key)
                    result.append(value)
        return result

    @staticmethod
    def _image_url(claims: Dict[str, Any]) -> Optional[str]:
        """Đường dẫn ảnh Commons từ P18. CHỈ LƯU ĐƯỜNG DẪN, không tải ảnh về."""
        for claim in (claims or {}).get(IMAGE_PROPERTY, []) or []:
            filename = (
                claim.get("mainsnak", {}).get("datavalue", {}).get("value")
            )
            if isinstance(filename, str) and filename.strip():
                return COMMONS_FILEPATH.format(file=quote(filename.replace(" ", "_")))
        return None

    def _to_dish_info(self, qid: str, entity: Dict[str, Any]) -> Optional[DishInfo]:
        title = self._first_language(entity.get("labels", {}))
        if not title:
            # Không có nhãn Việt lẫn Anh thì không hiển thị được, cũng không khớp tên
            # quán được. Bỏ, KHÔNG bịa tên từ mã Q.
            return None
        return DishInfo(
            title=title,
            qid=qid,
            description=self._first_language(entity.get("descriptions", {})),
            image_url=self._image_url(entity.get("claims", {})),
            source_url=f"https://www.wikidata.org/wiki/{qid}",
            aliases=self._all_aliases(entity.get("aliases", {})),
        )

    # --- lối vào chính -------------------------------------------------------

    def fetch_candidates(self) -> Dict[str, DishInfo]:
        """{tên món: thông tin}. Người gọi tự lọc "có phải món ăn không".

        Trả về theo TÊN chứ không theo mã Q để dùng lẫn được với
        `WikipediaDishSource.fetch_many()` ở `discover_dishes.py`.
        """
        qids: List[str] = []
        seen: set[str] = set()
        logger.info("Tim ung vien tren Wikidata:")
        for query in SEARCH_QUERIES:
            for qid in self._search_qids(query):
                if qid not in seen:
                    seen.add(qid)
                    qids.append(qid)
        logger.info("Tong ung vien (da khu trung): %d muc", len(qids))

        results: Dict[str, DishInfo] = {}
        for start in range(0, len(qids), ENTITY_BATCH):
            batch = qids[start:start + ENTITY_BATCH]
            for qid, entity in self._fetch_entities(batch).items():
                info = self._to_dish_info(qid, entity)
                if info is None:
                    continue
                # Hai mã Q khác nhau có thể cùng một nhãn (VD bản chuyển hướng). Giữ mục
                # có nhiều thông tin hơn thay vì để mục sau đè im lặng lên mục trước.
                current = results.get(info.title)
                if current is None or _richness(info) > _richness(current):
                    results[info.title] = info
            if (start // ENTITY_BATCH) % 10 == 0:
                logger.info("  ... da doc %d/%d muc", min(start + ENTITY_BATCH, len(qids)), len(qids))

        logger.info("Doc duoc %d muc co nhan dung duoc", len(results))
        return results


def _richness(info: DishInfo) -> int:
    """Mục này có bao nhiêu thông tin dùng được — để chọn khi hai mã Q trùng tên."""
    return sum((bool(info.description), bool(info.image_url), bool(info.aliases)))

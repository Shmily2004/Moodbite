"""ADAPTER: ghi sự kiện tương tác vào file JSONL (mỗi dòng 1 JSON).

Vì sao JSONL mà không phải CSV hay DB:
  - Ghi THÊM vào cuối file là thao tác an toàn, không phải đọc-sửa-ghi lại cả file.
  - Mỗi dòng độc lập: file hỏng giữa chừng vẫn đọc được các dòng trước đó.
  - pandas đọc trực tiếp bằng `pd.read_json(path, lines=True)` khi cần huấn luyện.

Khi chuyển sang PostgreSQL: viết PostgresInteractionRepository triển khai cùng port,
đổi một dòng trong dependencies.py. Use case không đổi.
"""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from src.domain.entities.interaction import ActionType, InteractionEvent
from src.domain.services.closure_reports import EVENT_CLEAR, EVENT_REPORT, ClosureEvent
from src.domain.services.interaction_stats import BanGhiTuongTac
from src.infrastructure.config.settings import describe_path

logger = logging.getLogger("moodbite.interactions")

# Dòng do QUẢN TRỊ ghi vào nhật ký (không phải hành vi người dùng). Cố ý KHÔNG là một giá
# trị của `ActionType`: enum đó là thứ client được gửi lên `POST /interactions`, mà để
# client tự gửi "gỡ lượt báo" thì ai cũng bỏ ẩn được quán.
EVENT_KIND_ADMIN = "admin"
ACTION_CLOSURE_REPORTS_CLEARED = "closure_reports_cleared"


class JsonlInteractionRepository:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._error: Optional[str] = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._error = f"Không tạo được thư mục {self.path.parent}: {exc}"

    @property
    def is_ready(self) -> bool:
        return self._error is None

    @property
    def load_error(self) -> Optional[str]:
        return self._error

    def append(self, event: InteractionEvent) -> str:
        event_id = str(uuid.uuid4())
        record = {
            "interaction_event_id": event_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "session_id": event.session_id,
            # Chỉ có khi người dùng đã đăng nhập. Bản ghi cũ (trước 2026-08-22) không có
            # khoá này — mọi chỗ đọc lại phải dùng `.get("user_id")`, không được `[...]`.
            "user_id": event.user_id,
            "search_query_id": event.search_query_id,
            "restaurant_id": event.restaurant_id,
            "action_type": event.action_type.value,
            "dwell_time_ms": event.dwell_time_ms,
            "rank_position": event.rank_position,
            # Tính sẵn ở server để dữ liệu huấn luyện sau này có nhãn nhất quán.
            "is_positive_signal": event.is_positive_signal,
        }
        # Chỉ lượt báo đóng cửa mới có khoá người báo; không ghi `null` vào mọi dòng khác
        # để nhật ký không mang một cột vô nghĩa cho 99% bản ghi.
        if event.reporter_key:
            record["reporter_key"] = event.reporter_key
        self._append_line(record)
        return event_id

    def append_closure_reports_cleared(self, restaurant_id: str, actor: str) -> str:
        """Ghi sự kiện "ADMIN GỠ MỌI LƯỢT BÁO ĐÓNG CỬA của quán này" (thêm 2026-10-06).

        VÌ SAO GHI VÀO CHÍNH NHẬT KÝ TƯƠNG TÁC: bộ đếm báo đóng cửa được dựng lại từ file
        này lúc khởi động. Gỡ chỉ trong RAM thì khởi động lại xong, các lượt báo cũ được
        phát lại và quán lại bị ẩn — đúng lỗi "ẩn vĩnh viễn" của bản trước. Ghi chung một
        file thì thứ tự "báo -> gỡ -> báo" được giữ nguyên khi phát lại.

        Dòng này mang `event_kind="admin"` và KHÔNG có `session_id`/`user_id`: nó không
        phải hành vi người dùng, nên `read_records()` (thống kê) và
        `replay_user_activity()` (cấp độ) đều phải bỏ qua nó.
        """
        event_id = str(uuid.uuid4())
        self._append_line({
            "interaction_event_id": event_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "event_kind": EVENT_KIND_ADMIN,
            "action_type": ACTION_CLOSURE_REPORTS_CLEARED,
            "restaurant_id": str(restaurant_id),
            "actor": actor,
        })
        return event_id

    def _append_line(self, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False)
        # Khoá vì uvicorn có thể xử lý nhiều request song song; hai lượt ghi cùng lúc
        # có thể xen kẽ nhau và tạo ra dòng JSON hỏng.
        with self._lock:
            try:
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
            except OSError as exc:
                self._error = f"Không ghi được {describe_path(self.path)}: {exc}"
                logger.error("Ghi nhật ký tương tác thất bại: %s", exc)
                raise

    def replay_closure_events(self) -> List[ClosureEvent]:
        """Các sự kiện BÁO ĐÓNG CỬA và ADMIN GỠ LƯỢT BÁO, đúng thứ tự đã ghi.

        Dùng để dựng lại bộ đếm lúc khởi động (`domain.services.closure_reports.
        tally_from_events`). Nhờ vậy bộ đếm trong RAM luôn suy được từ nhật ký trên đĩa.

        ⚠️ LƯỢT BÁO CŨ KHÔNG CÓ `reporter_key` (ghi trước 2026-10-06) bị BỎ QUA — quyết
        định có chủ đích: chúng chỉ có `session_id` do client tự đặt, tức là đúng loại dữ
        liệu đã bị lợi dụng để ẩn quán. Dòng vẫn nằm nguyên trong nhật ký (không xoá dữ
        liệu), chỉ không còn được dùng để ẩn quán. Đo 2026-10-06 trên nhật ký thật: 0
        lượt báo đóng cửa nào bị ảnh hưởng (nhật ký mới có 3 dòng view_detail).

        ĐỌC ĐÚNG MỘT LẦN lúc dựng container, không đọc ở mỗi request: nhật ký chỉ-ghi-thêm
        nên sẽ dài mãi, đọc lại mỗi lượt tìm kiếm là hỏng dần theo thời gian.

        Dòng JSON hỏng thì BỎ QUA dòng đó chứ không ném lỗi: một dòng ghi dở (mất điện
        giữa chừng) không được phép làm app không khởi động nổi.
        """
        if not self.path.exists():
            return []
        out: List[ClosureEvent] = []
        hong = 0
        bao_cu = 0
        try:
            with open(self.path, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        hong += 1
                        continue
                    if not isinstance(rec, dict):
                        continue
                    rid = rec.get("restaurant_id")
                    if not rid:
                        continue
                    action = rec.get("action_type")
                    if action == ACTION_CLOSURE_REPORTS_CLEARED:
                        out.append((EVENT_CLEAR, str(rid), None))
                    elif action == ActionType.REPORT_CLOSED.value:
                        key = rec.get("reporter_key")
                        if key:
                            out.append((EVENT_REPORT, str(rid), str(key)))
                        else:
                            bao_cu += 1
        except OSError as exc:
            logger.warning("Không đọc lại được nhật ký tương tác: %s", exc)
            return out
        if hong:
            logger.warning("Bỏ qua %d dòng hỏng trong %s", hong, describe_path(self.path))
        if bao_cu:
            logger.info(
                "Bỏ qua %d lượt báo đóng cửa CŨ không có khoá người báo (chỉ có session_id "
                "do client tự đặt) — không dùng để ẩn quán.", bao_cu,
            )
        return out

    def replay_user_activity(self) -> List[dict]:
        """Các tương tác CÓ `user_id`, để dựng lại bộ đếm hoạt động lúc khởi động.

        Cùng lý do và cùng cách làm với `replay_closure_events`: bộ đếm nằm trong RAM
        nhưng luôn suy được từ nhật ký trên đĩa, nên khởi động lại không mất cấp độ của
        ai. Dòng hỏng thì bỏ qua dòng đó — một dòng ghi dở không được làm app chết.

        ĐỌC ĐÚNG MỘT LẦN lúc dựng container. Nhật ký chỉ dài thêm nên đọc ở mỗi request
        là hỏng dần theo thời gian.
        """
        if not self.path.exists():
            return []
        out: List[dict] = []
        try:
            with open(self.path, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    if not rec.get("user_id"):
                        continue
                    out.append(rec)
        except OSError as exc:
            logger.warning("Không đọc lại được nhật ký tương tác: %s", exc)
        return out

    def read_records(self) -> List[BanGhiTuongTac]:
        """Toàn bộ nhật ký dưới dạng bản ghi thống kê — cho khối "Hệ thống gợi ý".

        ĐỌC LẠI FILE mỗi lần gọi, khác `replay_*` (đọc một lần lúc khởi động): màn quản
        trị gọi rất thưa, và người quản trị cần thấy số mới chứ không phải số lúc bật máy.
        Đo 2026-09-16: nhật ký thật có 3 dòng; kể cả 100.000 dòng thì một lượt đọc vẫn
        dưới một giây, chấp nhận được cho một màn chỉ admin mở.

        Dòng hỏng thì bỏ qua dòng đó — cùng quy ước với `replay_closure_events`.
        """
        if not self.path.exists():
            return []
        out: List[BanGhiTuongTac] = []
        try:
            with open(self.path, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(rec, dict) or not rec.get("action_type"):
                        continue
                    # Dòng của quản trị (VD gỡ lượt báo) không phải tương tác người dùng —
                    # đếm vào thì "Lượt tương tác" ở màn Tổng quan bị thổi phồng.
                    if rec.get("event_kind") == EVENT_KIND_ADMIN:
                        continue
                    nhan = rec.get("is_positive_signal")
                    out.append(
                        BanGhiTuongTac(
                            action_type=str(rec["action_type"]),
                            created_at=rec.get("created_at"),
                            session_id=rec.get("session_id"),
                            # Bản ghi trước 2026-08-22 không có khoá này -> `.get`.
                            user_id=rec.get("user_id"),
                            is_positive_signal=nhan if isinstance(nhan, bool) else None,
                        )
                    )
        except OSError as exc:
            logger.warning("Không đọc được nhật ký tương tác: %s", exc)
        return out

    def count(self) -> int:
        if not self.path.exists():
            return 0
        try:
            with open(self.path, encoding="utf-8") as fh:
                return sum(1 for line in fh if line.strip())
        except OSError:
            return 0

    def status(self) -> dict:
        return {
            "ready": self.is_ready,
            "source": describe_path(self.path),
            "count": self.count(),
            "error": self._error,
        }

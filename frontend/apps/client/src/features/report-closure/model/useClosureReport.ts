/**
 * VIEWMODEL của việc "báo quán đã đóng cửa".
 *
 * Backend đã sẵn sàng từ 2026-08-19: `POST /interactions` với `action_type=report_closed`,
 * đếm theo PHIÊN (bấm 50 lần từ một phiên vẫn chỉ tính 1 phiếu), đủ số phiên khác nhau
 * thì quán tự ẩn. Phần còn thiếu duy nhất là cái nút — đây là nó.
 *
 * ⚠️ NGƯỠNG ẨN QUÁN NẰM Ở BACKEND (`domain/services/closure_reports.py`), và phải ở
 * nguyên đó. Frontend cố tình KHÔNG biết con số ấy: viết lại nó ở đây là tạo nơi thứ hai
 * chứa cùng một quy tắc nghiệp vụ, và đổi ngưỡng sẽ phải sửa hai chỗ (CLAUDE.md mục 1b).
 * Vì vậy câu cảm ơn nói "cần thêm người xác nhận" chứ không nói "cần 3 người".
 */
import { useCallback, useState } from 'react';
import { api } from '@/shared/api';
import { getSessionId } from '@/shared/lib';

export type ClosureReportState = 'idle' | 'sending' | 'sent' | 'failed';

export interface UseClosureReportResult {
  state: ClosureReportState;
  report: (restaurantId: string) => Promise<void>;
}

export function useClosureReport(): UseClosureReportResult {
  const [state, setState] = useState<ClosureReportState>('idle');

  const report = useCallback(async (restaurantId: string) => {
    if (!restaurantId) return;
    setState('sending');
    const result = await api.logInteraction({
      session_id: getSessionId(),
      restaurant_id: restaurantId,
      action_type: 'report_closed',
      search_query_id: null,
      rank_position: null,
      dwell_time_ms: null,
    });
    // KHÁC với mọi tương tác khác: ở đây người dùng CHỦ ĐỘNG bấm và đang chờ phản hồi,
    // nên thất bại phải nói ra. `logInteraction` nuốt lỗi và trả `null` - đúng cho việc
    // ghi log ngầm, nhưng ở đây `null` chính là tín hiệu để báo "gửi không được".
    setState(result ? 'sent' : 'failed');
  }, []);

  return { state, report };
}

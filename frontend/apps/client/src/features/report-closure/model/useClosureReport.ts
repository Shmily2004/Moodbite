/**
 * VIEWMODEL của việc "báo quán đã đóng cửa".
 *
 * Backend đã sẵn sàng từ 2026-08-19: `POST /interactions` với `action_type=report_closed`,
 * đếm theo người báo. Theo biểu đồ UC06, lượt báo đưa quán vào hàng chờ quản trị và
 * KHÔNG tự ẩn quán: quản trị mới là người quyết định (UC21).
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

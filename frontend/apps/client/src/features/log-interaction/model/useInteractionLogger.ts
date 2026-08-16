/**
 * Ghi nhận tương tác người dùng — nguồn NHÃN cho mô hình xếp hạng có giám sát
 * (Lớp 3 đầy đủ của đề án).
 *
 * Hiện `interactions.jsonl` còn rỗng; mỗi lượt người dùng xem chi tiết hay bấm chỉ đường
 * đều là một nhãn huấn luyện tương lai. KHÔNG ghi từ bây giờ thì sau này không có gì để học.
 *
 * Mọi lỗi ghi log đều bị NUỐT có chủ đích: người dùng không cần biết, và không được
 * để việc ghi log làm hỏng trải nghiệm.
 */
import { useCallback, useRef } from 'react';
import type { ActionType } from '@moodbite/api-client';
import { api } from '@/shared/api';
import { getSessionId } from '@/shared/lib';

export interface LogInteractionInput {
  restaurantId: string;
  actionType: ActionType;
  searchQueryId?: string | null;
  rankPosition?: number | null;
  dwellTimeMs?: number | null;
}

export interface UseInteractionLoggerResult {
  log: (input: LogInteractionInput) => void;
  /** Bắt đầu đếm thời gian xem một quán. Trả về hàm dừng + ghi log. */
  startViewTimer: (restaurantId: string, rankPosition: number,
                   searchQueryId: string | null) => () => void;
}

export function useInteractionLogger(): UseInteractionLoggerResult {
  const timers = useRef<Map<string, number>>(new Map());

  const log = useCallback((input: LogInteractionInput) => {
    void api.logInteraction({
      session_id: getSessionId(),
      restaurant_id: input.restaurantId,
      action_type: input.actionType,
      search_query_id: input.searchQueryId ?? null,
      rank_position: input.rankPosition ?? null,
      dwell_time_ms: input.dwellTimeMs ?? null,
    });
  }, []);

  const startViewTimer = useCallback(
    (restaurantId: string, rankPosition: number, searchQueryId: string | null) => {
      timers.current.set(restaurantId, Date.now());
      return () => {
        const startedAt = timers.current.get(restaurantId);
        if (startedAt == null) return;
        timers.current.delete(restaurantId);
        // dwell_time THẬT = thời gian người dùng thực sự xem. Backend dùng nó để phân
        // biệt "xem thật" với "bấm nhầm rồi thoát" (ngưỡng 3 giây).
        log({
          restaurantId,
          actionType: 'view_detail',
          searchQueryId,
          rankPosition,
          dwellTimeMs: Date.now() - startedAt,
        });
      };
    },
    [log],
  );

  return { log, startViewTimer };
}

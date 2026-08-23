/**
 * Số liệu hoạt động + cấp độ + huy hiệu của người đang đăng nhập (`GET /me/stats`).
 *
 * Ở `entities/user` chứ không phải `features/`: đây là DỮ LIỆU MÔ TẢ thực thể người dùng,
 * không phải một hành động người dùng thực hiện. Widget nào cần vẽ thì import xuống.
 *
 * ⚠️ MỌI CON SỐ Ở ĐÂY DO SERVER ĐẾM. Frontend KHÔNG được tự cộng điểm hay tự suy ra cấp
 * độ — công thức nằm ở `src/domain/services/gamification.py` và phải chỉ có một bản
 * (CLAUDE.md mục 1b: business logic chỉ nằm ở backend). Tài khoản mới thì mọi số là 0;
 * đó là sự thật, không phải lỗi cần "sửa" bằng số minh hoạ.
 */
import { useCallback, useEffect, useState } from 'react';
import { authApi } from '@/shared/api';
import type { UserStatsData } from '@/shared/api';
import { useUserSessionContext } from './UserSessionContext';

export interface UseUserStatsResult {
  stats: UserStatsData | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useUserStats(): UseUserStatsResult {
  const session = useUserSessionContext();
  const [stats, setStats] = useState<UserStatsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lan, setLan] = useState(0);

  const reload = useCallback(() => setLan((n) => n + 1), []);

  useEffect(() => {
    if (!session.isLoggedIn) {
      setStats(null);
      return;
    }
    let con_song = true;
    setLoading(true);

    authApi
      .stats()
      .then((data) => {
        if (!con_song) return;
        setStats(data);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!con_song) return;
        // KHÔNG đặt số 0 giả khi lỗi: 0 và "không tải được" là hai chuyện khác nhau, và
        // hiện 0 sẽ khiến người dùng tưởng mình vừa mất hết điểm.
        setStats(null);
        setError(err instanceof Error ? err.message : 'Không tải được số liệu.');
      })
      .finally(() => {
        if (con_song) setLoading(false);
      });

    return () => {
      con_song = false;
    };
  }, [session.isLoggedIn, lan]);

  return { stats, loading, error, reload };
}

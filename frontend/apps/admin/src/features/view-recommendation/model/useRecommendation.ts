/**
 * VIEWMODEL của màn "Gợi ý & Hệ thống". CHỈ ĐỌC — không có hàm nào chỉnh mô hình.
 *
 * Trọng số xếp hạng là quy tắc nghiệp vụ và chỉ được nằm ở `domain/services/` (CLAUDE.md
 * mục 1b). Backend cũng không có endpoint ghi, nên chỗ này không thể "quên" mà thành
 * chỉnh được.
 */
import { useCallback, useEffect, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type { AdminRecommendationData } from '@/shared/api';

export interface UseRecommendationResult {
  data: AdminRecommendationData | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useRecommendation(): UseRecommendationResult {
  const [data, setData] = useState<AdminRecommendationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lan, setLan] = useState(0);

  useEffect(() => {
    let conSong = true;
    setLoading(true);

    adminApi
      .recommendation()
      .then((kq) => {
        if (!conSong) return;
        setData(kq);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!conSong) return;
        setError(err instanceof ApiError ? err.message : (err as Error).message);
      })
      .finally(() => {
        if (conSong) setLoading(false);
      });

    return () => {
      conSong = false;
    };
  }, [lan]);

  const reload = useCallback(() => setLan((n) => n + 1), []);

  return { data, loading, error, reload };
}

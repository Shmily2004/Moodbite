/**
 * VIEWMODEL của khối "Hệ thống gợi ý" ở màn Tổng quan — `GET /admin/interactions/stats`.
 *
 * Gọi RIÊNG, không gộp vào `/admin/overview`: số liệu tổng quan được đệm 5 phút ở server,
 * còn nhật ký tương tác đổi theo từng lượt người dùng bấm. Khối này hỏng thì các khối
 * khác của trang vẫn phải hiện.
 *
 * Không tính toán gì ở đây — tỷ lệ, số phiên, khung 7 ngày đều do backend đếm
 * (`domain/services/interaction_stats.py`).
 */
import { useEffect, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type { AdminInteractionStatsData } from '@/shared/api';

export interface UseInteractionStatsResult {
  data: AdminInteractionStatsData | null;
  loading: boolean;
  error: string | null;
}

export function useInteractionStats(lanTai = 0): UseInteractionStatsResult {
  const [data, setData] = useState<AdminInteractionStatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let conSong = true;
    setLoading(true);
    adminApi
      .interactionStats()
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
  }, [lanTai]);

  return { data, loading, error };
}

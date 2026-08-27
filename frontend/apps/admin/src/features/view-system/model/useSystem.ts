/**
 * VIEWMODEL của màn "Cài đặt hệ thống".
 *
 * CHỈ ĐỌC — không có hàm nào ghi. Cấu hình nằm ở biến môi trường / `.env.local`; cho sửa
 * qua HTTP nghĩa là một lỗ hổng ở trang quản trị đổi được cả khoá ký token. Backend cũng
 * không có endpoint ghi, nên chỗ này không thể "quên" mà thành ghi được.
 */
import { useCallback, useEffect, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type { AdminSystemData } from '@/shared/api';

export interface UseSystemResult {
  data: AdminSystemData | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useSystem(): UseSystemResult {
  const [data, setData] = useState<AdminSystemData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lan, setLan] = useState(0);

  useEffect(() => {
    let conSong = true;
    setLoading(true);

    adminApi
      .system()
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

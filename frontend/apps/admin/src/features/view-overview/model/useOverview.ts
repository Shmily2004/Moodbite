/**
 * VIEWMODEL của màn "Tổng quan" — tải số liệu vận hành từ `GET /admin/overview`.
 *
 * Chỉ điều phối: gọi API, giữ trạng thái tải/lỗi, cho phép tải lại. Không tính toán gì —
 * mọi con số và mọi phân loại ("tốt / trung bình / kém") do backend quyết
 * (`domain/services/data_quality.py`). Tính lại ở đây là đặt nghiệp vụ sai tầng và sẽ
 * lệch với backend ngay lần đầu ai đó sửa ngưỡng.
 */
import { useCallback, useEffect, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type { AdminOverviewData } from '@/shared/api';

export interface UseOverviewResult {
  data: AdminOverviewData | null;
  loading: boolean;
  error: string | null;
  /** Tải lại, bỏ qua bộ đệm 5 phút của server. */
  reload: () => void;
}

export function useOverview(): UseOverviewResult {
  const [data, setData] = useState<AdminOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Đổi số này để bắt effect chạy lại. Dùng cờ boolean thì bấm "tải lại" hai lần liên
  // tiếp chỉ chạy một lần, vì giá trị không đổi.
  const [lan, setLan] = useState(0);

  useEffect(() => {
    let conSong = true;
    setLoading(true);

    // `lan > 0` = người dùng chủ động bấm tải lại -> bỏ qua đệm của server.
    adminApi
      .overview(lan > 0)
      .then((kq) => {
        if (!conSong) return;
        setData(kq);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!conSong) return;
        // Giữ nguyên câu của backend: nó phân biệt "chưa chạy data_pipeline" với "mất
        // mạng", và hai tình huống đó cần hai hành động khác nhau.
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

/**
 * VIEWMODEL của màn "Chất lượng dữ liệu" — tải `GET /admin/quality`.
 *
 * Chỉ điều phối: gọi API, giữ trạng thái tải/lỗi, cho phép tải lại. KHÔNG tính toán gì —
 * mọi con số, mọi phân loại mức độ và cả phép so sánh với mốc quá khứ đều do backend
 * quyết (`domain/services/data_quality.py` · `data_quality_history.py`). Tính lại ở đây
 * là đặt nghiệp vụ sai tầng và sẽ lệch với backend ngay lần đầu ai đó sửa ngưỡng.
 *
 * ⚠️ Lượt gọi này khiến SERVER GHI một dòng ảnh chụp cho hôm nay (bất biến theo ngày).
 * Đó là chủ đích — xem `application/use_cases/get_data_quality.py`.
 */
import { useCallback, useEffect, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type { AdminDataQualityData } from '@/shared/api';

export interface UseDataQualityResult {
  data: AdminDataQualityData | null;
  loading: boolean;
  error: string | null;
  /** Tải lại, bỏ qua bộ đệm 5 phút của server. */
  reload: () => void;
}

export function useDataQuality(): UseDataQualityResult {
  const [data, setData] = useState<AdminDataQualityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Đổi số này để bắt effect chạy lại. Dùng cờ boolean thì bấm "tải lại" hai lần liên
  // tiếp chỉ chạy một lần, vì giá trị không đổi.
  const [lan, setLan] = useState(0);

  useEffect(() => {
    let conSong = true;
    setLoading(true);

    adminApi
      .dataQuality(lan > 0)
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

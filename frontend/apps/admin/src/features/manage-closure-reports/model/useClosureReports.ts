/**
 * VIEWMODEL "Quán bị khách báo đóng cửa" (thêm 2026-10-06).
 *
 * VÌ SAO CÓ: khách báo đủ `threshold` người (đếm theo IP đã băm) thì quán tự ẩn khỏi mọi
 * luồng. Trước ngày này admin KHÔNG có cách nào gỡ - nút "Khôi phục" chỉ bỏ ẩn do admin,
 * còn lượt báo được đọc lại từ nhật ký mỗi lần khởi động nên quán bị ẩn vĩnh viễn.
 *
 * Gỡ xong thì TẢI LẠI danh sách từ server thay vì tự sửa state: `is_hidden` còn phụ thuộc
 * trạng thái ẩn do admin - frontend không được tự suy (CLAUDE.md mục 1b).
 */
import { useCallback, useEffect, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type { AdminClosureReportItem } from '@/shared/api';

export interface UseClosureReportsResult {
  items: AdminClosureReportItem[];
  /** Số người báo cần để ẩn quán - do backend trả, không chép cứng. */
  threshold: number | null;
  loading: boolean;
  error: string | null;
  /** Quán đang được gỡ (để khoá nút, tránh bấm hai lần). */
  dangGo: string | null;
  goBaoCao: (restaurantId: string) => Promise<void>;
}

const thongBao = (err: unknown) =>
  err instanceof ApiError
    ? err.code === 'NETWORK'
      ? err.userMessage
      : err.message
    : (err as Error).message;

export function useClosureReports(): UseClosureReportsResult {
  const [items, setItems] = useState<AdminClosureReportItem[]>([]);
  const [threshold, setThreshold] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dangGo, setDangGo] = useState<string | null>(null);
  const [lan, setLan] = useState(0);

  useEffect(() => {
    let conSong = true;
    setLoading(true);
    adminApi
      .closureReports()
      .then((kq) => {
        if (!conSong) return;
        setItems(kq.items);
        setThreshold(kq.threshold);
        setError(null);
      })
      .catch((err: unknown) => {
        if (conSong) setError(thongBao(err));
      })
      .finally(() => {
        if (conSong) setLoading(false);
      });
    return () => {
      conSong = false;
    };
  }, [lan]);

  const goBaoCao = useCallback(async (restaurantId: string) => {
    setDangGo(restaurantId);
    try {
      await adminApi.clearClosureReports(restaurantId);
      setLan((n) => n + 1);
    } catch (err) {
      setError(thongBao(err));
    } finally {
      setDangGo(null);
    }
  }, []);

  return { items, threshold, loading, error, dangGo, goBaoCao };
}

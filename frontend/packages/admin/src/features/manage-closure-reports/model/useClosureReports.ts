/**
 * VIEWMODEL "Quán bị khách báo đóng cửa" (thêm 2026-10-06).
 *
 * THEO BIỂU ĐỒ UC21 (đổi 2026-11-12): khách báo quán đóng cửa thì quán vào HÀNG CHỜ, KHÔNG
 * tự ẩn. Quản trị kiểm tra rồi chọn: "Ẩn quán" (quán thật sự đã đóng) hoặc "Gỡ lượt báo"
 * (không thật sự đóng).
 *
 * Làm xong thì TẢI LẠI danh sách từ server thay vì tự sửa state: `is_hidden` là trạng thái
 * thật của quán, frontend không được tự suy (CLAUDE.md mục 1b).
 */
import { useCallback, useEffect, useState } from 'react';
import { adminApi, ApiError } from '@admin/shared/api';
import type { AdminClosureReportItem } from '@admin/shared/api';

export interface UseClosureReportsResult {
  items: AdminClosureReportItem[];
  loading: boolean;
  error: string | null;
  /** Quán đang được xử lý (để khoá nút, tránh bấm hai lần). */
  dangGo: string | null;
  anQuan: (restaurantId: string) => Promise<void>;
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

  /** UC21, nhánh "quán thật sự đã đóng cửa": ẩn quán (ghi nhật ký `hide_restaurant`). */
  const anQuan = useCallback(async (restaurantId: string) => {
    setDangGo(restaurantId);
    try {
      await adminApi.hideRestaurant(restaurantId);
      setLan((n) => n + 1);
    } catch (err) {
      setError(thongBao(err));
    } finally {
      setDangGo(null);
    }
  }, []);

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

  return { items, loading, error, dangGo, anQuan, goBaoCao };
}

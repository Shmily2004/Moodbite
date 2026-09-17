/**
 * VIEWMODEL của trang CHI TIẾT MÓN (`/mon-an/:dishId`).
 *
 * Ba lượt gọi ĐỘC LẬP, mỗi lượt có trạng thái riêng:
 *   1. `getDish`          — phần đầu trang + tab "Thông tin chi tiết"
 *   2. `dishRestaurants`  — tab "Danh sách quán"
 *   3. `activity`         — tab "Lịch sử cập nhật" (nhật ký lọc theo đúng món này)
 *
 * Tách trạng thái vì một khối hỏng không được làm trắng cả trang: nhật ký không mở được
 * thì người quản trị vẫn phải xem được món và danh sách quán.
 */
import { useEffect, useState } from 'react';
import { adminApi, ApiError } from '@/shared/api';
import type {
  AdminDishDetail,
  AdminDishRestaurantsData,
  AuditEntry,
} from '@/shared/api';

/** Tab "Danh sách quán" hiện tối đa ngần này quán; tổng thật nằm ở `total`. */
export const SO_QUAN_CUA_MON = 50;

function loiThanhChu(err: unknown): string {
  return err instanceof ApiError ? err.message : (err as Error).message;
}

interface KhoiTai<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export interface UseDishDetailResult {
  dish: KhoiTai<AdminDishDetail>;
  restaurants: KhoiTai<AdminDishRestaurantsData>;
  history: KhoiTai<AuditEntry[]> & { available: boolean };
}

function useTai<T>(tai: () => Promise<T>, khoa: string): KhoiTai<T> {
  const [trangThai, setTrangThai] = useState<KhoiTai<T>>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let conSong = true;
    setTrangThai({ data: null, loading: true, error: null });
    tai()
      .then((data) => {
        if (conSong) setTrangThai({ data, loading: false, error: null });
      })
      .catch((err: unknown) => {
        if (conSong) setTrangThai({ data: null, loading: false, error: loiThanhChu(err) });
      });
    return () => {
      conSong = false;
    };
    // `tai` là hàm mới mỗi lần render; chỉ tải lại khi ĐỐI TƯỢNG đổi (`khoa`).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [khoa]);

  return trangThai;
}

export function useDishDetail(dishId: string): UseDishDetailResult {
  const dish = useTai(() => adminApi.getDish(dishId), `mon:${dishId}`);
  const restaurants = useTai(
    () => adminApi.dishRestaurants(dishId, { limit: SO_QUAN_CUA_MON }),
    `quan:${dishId}`,
  );
  const nhatKy = useTai(
    () => adminApi.activity({ targetType: 'dish', targetId: dishId, limit: 50 }),
    `nhat-ky:${dishId}`,
  );

  return {
    dish,
    restaurants,
    history: {
      data: nhatKy.data ? nhatKy.data.entries : null,
      loading: nhatKy.loading,
      error: nhatKy.error,
      // `available=false` = KHO NHẬT KÝ HỎNG — khác hẳn "chưa có thay đổi nào".
      available: nhatKy.data ? nhatKy.data.available : false,
    },
  };
}

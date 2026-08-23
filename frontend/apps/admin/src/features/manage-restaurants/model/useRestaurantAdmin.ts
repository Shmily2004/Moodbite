/**
 * VIEWMODEL của việc quản lý quán: tải danh sách, ẩn/bỏ ẩn, sửa trường mô tả.
 *
 * KHÔNG chứa quy tắc nghiệp vụ. "Trường nào sửa được" do BACKEND quyết định
 * (`domain/value_objects/restaurant_edit.py`); ở đây chỉ gửi đi và hiển thị lỗi trả về.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  AdminCreateRestaurantRequest,
  AdminRestaurantSummary,
  AdminUpdateRestaurantRequest,
} from '@moodbite/api-client';
import { ApiError, adminApi } from '@/shared/api';
import { ADMIN_PAGE_SIZE } from '@/shared/config';

export interface UseRestaurantAdminOptions {
  /** Gọi khi backend trả 401 — token hết hạn giữa phiên làm việc. */
  onExpired: () => void;
}

export interface UseRestaurantAdminResult {
  restaurants: AdminRestaurantSummary[];
  total: number;
  query: string;
  setQuery: (value: string) => void;
  includeHidden: boolean;
  setIncludeHidden: (value: boolean) => void;
  loading: boolean;
  error: string | null;
  notice: string | null;
  reload: () => Promise<void>;
  toggleHidden: (restaurant: AdminRestaurantSummary) => Promise<void>;
  saveChanges: (
    restaurantId: string,
    changes: AdminUpdateRestaurantRequest,
  ) => Promise<boolean>;
  /** Thêm quán mới. Trả `true` khi thành công (form tự dọn), `false` khi lỗi. */
  createRestaurant: (body: AdminCreateRestaurantRequest) => Promise<boolean>;
}

export function useRestaurantAdmin({
  onExpired,
}: UseRestaurantAdminOptions): UseRestaurantAdminResult {
  const [restaurants, setRestaurants] = useState<AdminRestaurantSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState('');
  const [includeHidden, setIncludeHidden] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  /** Token hết hạn -> đưa người dùng về màn đăng nhập thay vì hiện lỗi khó hiểu. */
  const handleError = useCallback(
    (err: unknown) => {
      if (err instanceof ApiError && err.code === 'UNAUTHORIZED') {
        onExpired();
        return;
      }
      setError(err instanceof ApiError ? err.userMessage : (err as Error).message);
    },
    [onExpired],
  );

  const reload = useCallback(async () => {
    // Huỷ request cũ: gõ nhanh vào ô tìm kiếm sẽ tạo nhiều request, và request cũ về
    // sau có thể ghi đè kết quả mới. Đây đúng là bug bản frontend v1 từng mắc.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    try {
      const data = await adminApi.listRestaurants(
        { q: query || null, limit: ADMIN_PAGE_SIZE, includeHidden },
        { signal: controller.signal },
      );
      setRestaurants(data.results);
      setTotal(data.total);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      handleError(err);
    } finally {
      if (abortRef.current === controller) setLoading(false);
    }
  }, [query, includeHidden, handleError]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const toggleHidden = useCallback(
    async (restaurant: AdminRestaurantSummary) => {
      if (!restaurant.restaurant_id) return;
      setError(null);
      try {
        const updated = restaurant.is_active
          ? await adminApi.hideRestaurant(restaurant.restaurant_id)
          : await adminApi.restoreRestaurant(restaurant.restaurant_id);
        // Cập nhật tại chỗ thay vì tải lại cả danh sách: giữ nguyên vị trí cuộn và
        // ô tìm kiếm của người dùng.
        setRestaurants((current) =>
          current.map((r) => (r.restaurant_id === updated.restaurant_id ? updated : r)),
        );
        setNotice(
          updated.is_active
            ? `Đã bỏ ẩn "${updated.name}".`
            : `Đã ẩn "${updated.name}" khỏi kết quả tìm kiếm của người dùng.`,
        );
      } catch (err) {
        handleError(err);
      }
    },
    [handleError],
  );

  const saveChanges = useCallback(
    async (restaurantId: string, changes: AdminUpdateRestaurantRequest) => {
      setError(null);
      try {
        const updated = await adminApi.updateRestaurant(restaurantId, changes);
        setRestaurants((current) =>
          current.map((r) => (r.restaurant_id === updated.restaurant_id ? updated : r)),
        );
        setNotice(`Đã lưu thay đổi cho "${updated.name}".`);
        return true;
      } catch (err) {
        handleError(err);
        return false;
      }
    },
    [handleError],
  );

  const createRestaurant = useCallback(
    async (body: AdminCreateRestaurantRequest) => {
      setError(null);
      try {
        const created = await adminApi.createRestaurant(body);
        // Chèn lên ĐẦU danh sách để người nhập thấy ngay kết quả việc mình vừa làm,
        // thay vì phải đi tìm trong 50 dòng.
        setRestaurants((current) => [created, ...current]);
        setTotal((n) => n + 1);
        setNotice(
          `Đã thêm "${created.name}". Mã: ${created.restaurant_id} ` +
            '(tiền tố "manual:" cho biết quán này do người nhập tay).',
        );
        return true;
      } catch (err) {
        handleError(err);
        return false;
      }
    },
    [handleError],
  );

  return {
    restaurants,
    total,
    query,
    setQuery,
    includeHidden,
    setIncludeHidden,
    loading,
    error,
    notice,
    reload,
    toggleHidden,
    saveChanges,
    createRestaurant,
  };
}

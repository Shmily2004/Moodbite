/**
 * VIEWMODEL: tải chi tiết 1 quán (giá, review thật, ảnh).
 *
 * Chỉ 1310/4938 quán có chi tiết. Quán chưa có trả `has_details: false` kèm `reason` —
 * đó là trường hợp BÌNH THƯỜNG, không phải lỗi, và UI phải nói rõ điều đó.
 */
import { useCallback, useState } from 'react';
import type { RestaurantDetailData } from '@moodbite/api-client';
import { ApiError, api } from '@/shared/api';

export interface UseRestaurantDetailResult {
  detail: RestaurantDetailData | null;
  loading: boolean;
  error: string | null;
  load: (restaurantId: string) => Promise<void>;
  clear: () => void;
}

export function useRestaurantDetail(): UseRestaurantDetailResult {
  const [detail, setDetail] = useState<RestaurantDetailData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (restaurantId: string) => {
    setLoading(true);
    setError(null);
    try {
      setDetail(await api.restaurantDetail(restaurantId));
    } catch (err) {
      setError(err instanceof ApiError ? err.userMessage : (err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setDetail(null);
    setError(null);
  }, []);

  return { detail, loading, error, load, clear };
}

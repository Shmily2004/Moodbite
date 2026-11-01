/**
 * VIEWMODEL: tải chi tiết 1 quán (giá, review thật, ảnh).
 *
 * Chỉ 1310/4938 quán có chi tiết. Quán chưa có trả `has_details: false` kèm `reason` —
 * đó là trường hợp BÌNH THƯỜNG, không phải lỗi, và UI phải nói rõ điều đó.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type { RestaurantDetailData } from '@moodbite/api-client';
import { ApiError, api, apiErrorText } from '@/shared/api';
import { useT } from '@/shared/i18n';

export interface UseRestaurantDetailResult {
  detail: RestaurantDetailData | null;
  loading: boolean;
  error: string | null;
  /**
   * 404 - quán không tồn tại HOẶC đã bị ẩn. Tách khỏi `error` để trang chi tiết quán mời
   * người dùng đi chỗ khác, thay vì bảo "thử lại" một việc thử bao nhiêu lần cũng vậy.
   */
  notFound: boolean;
  load: (restaurantId: string) => Promise<void>;
  clear: () => void;
}

export function useRestaurantDetail(): UseRestaurantDetailResult {
  const [detail, setDetail] = useState<RestaurantDetailData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  // Request đang bay. Bấm quán A rồi quán B ngay: phản hồi của A về SAU từng đè chi tiết
  // của B, và `finally` của A tắt mất `loading` của B (audit 2026-10-06). Mỗi lượt mới
  // huỷ lượt cũ, và chỉ lượt còn là `abortRef.current` mới được ghi state.
  const abortRef = useRef<AbortController | null>(null);
  const t = useT();
  const tRef = useRef(t);
  tRef.current = t;
  useEffect(() => () => abortRef.current?.abort(), []);

  const load = useCallback(async (restaurantId: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const conHieuLuc = () => abortRef.current === controller;

    setLoading(true);
    setError(null);
    setNotFound(false);
    setDetail(null);
    try {
      const data = await api.restaurantDetail(restaurantId, { signal: controller.signal });
      if (conHieuLuc()) setDetail(data);
    } catch (err) {
      if (!conHieuLuc()) return;
      if (err instanceof Error && err.name === 'AbortError') return;
      if (err instanceof ApiError && err.status === 404) {
        setNotFound(true);
        return;
      }
      setError(apiErrorText(err, tRef.current));
    } finally {
      if (conHieuLuc()) setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setDetail(null);
    setError(null);
    setNotFound(false);
    setLoading(false);
  }, []);

  return { detail, loading, error, notFound, load, clear };
}

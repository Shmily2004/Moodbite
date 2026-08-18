/**
 * VIEWMODEL của trang chi tiết món: tải MÓN và QUÁN BÁN MÓN ĐÓ.
 *
 * Gọi hai endpoint SONG SONG chứ không tuần tự: chúng độc lập nhau, chờ nối đuôi chỉ làm
 * trang hiện chậm gấp đôi mà không được gì.
 *
 * Hai phần lỗi RIÊNG BIỆT (`error` và `restaurantsError`): tra được thành phần món nhưng
 * hỏng phần danh sách quán vẫn nên hiện được thành phần. Gộp một biến lỗi thì một nửa
 * hỏng sẽ xoá trắng cả trang.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type { DishItem, SearchResultItem } from '@/shared/api';
import { ApiError, api } from '@/shared/api';
import { getSessionId } from '@/shared/lib';

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface UseDishDetailResult {
  dish: DishItem | null;
  restaurants: SearchResultItem[];
  searchQueryId: string | null;
  warnings: string[];
  loading: boolean;
  error: string | null;
  restaurantsError: string | null;
  notFound: boolean;
  reload: () => void;
}

export function useDishDetail(
  dishId: string | undefined,
  position: Coordinates,
  maxDistanceKm: number | null,
): UseDishDetailResult {
  const [dish, setDish] = useState<DishItem | null>(null);
  const [restaurants, setRestaurants] = useState<SearchResultItem[]>([]);
  const [searchQueryId, setSearchQueryId] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [restaurantsError, setRestaurantsError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  const abortRef = useRef<AbortController | null>(null);
  useEffect(() => () => abortRef.current?.abort(), []);

  const reload = useCallback(() => setReloadToken((n) => n + 1), []);

  useEffect(() => {
    if (!dishId) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    setRestaurantsError(null);
    setNotFound(false);

    const params = {
      latitude: position.lat,
      longitude: position.lng,
      ...(maxDistanceKm != null ? { max_distance_km: maxDistanceKm } : {}),
    };

    const dishPromise = api
      .dishDetail(dishId, params, { signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted) return;
        setDish(data);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        // 404 DISH_NOT_FOUND là ca RIÊNG: trang phải mời quay về chọn món khác, chứ
        // không hiện "lỗi máy chủ" như thể hệ thống hỏng.
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true);
          setDish(null);
          return;
        }
        setError(
          err instanceof ApiError ? err.message : 'Không tải được thông tin món ăn.',
        );
        setDish(null);
      });

    const restaurantsPromise = api
      .restaurantsForDish(
        dishId,
        { session_id: getSessionId(), ...params, limit: 20 },
        { signal: controller.signal },
      )
      .then((data) => {
        if (controller.signal.aborted) return;
        setRestaurants(data.results);
        setSearchQueryId(data.search_query_id);
        setWarnings(data.warnings);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.status === 404) return; // đã xử lý ở trên
        setRestaurantsError(
          err instanceof ApiError ? err.message : 'Không tải được danh sách quán.',
        );
        setRestaurants([]);
      });

    Promise.all([dishPromise, restaurantsPromise]).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });

    return () => controller.abort();
  }, [dishId, position.lat, position.lng, maxDistanceKm, reloadToken]);

  return {
    dish,
    restaurants,
    searchQueryId,
    warnings,
    loading,
    error,
    restaurantsError,
    notFound,
    reload,
  };
}

/**
 * VIEWMODEL của trang chủ mới (vai trò "Controller" trong MVC cổ điển).
 *
 * Giữ state bộ lọc, gọi API, xử lý lỗi. KHÔNG chứa JSX, KHÔNG chấm điểm món -
 * việc xếp hạng nằm trọn ở backend (`domain/services/dish_ranking.py`).
 *
 * Bộ lọc TỰ ĐỘNG tìm lại khi đổi: người dùng bấm "trời mưa" là đã nói rõ ý định rồi,
 * bắt bấm thêm nút "Tìm" nữa là thừa một bước.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type { DishItem } from '@/shared/api';
import { ApiError, api } from '@/shared/api';
import { DEFAULT_RADIUS_KM } from '@/shared/config';
import { getSessionId } from '@/shared/lib';

export interface Coordinates {
  lat: number;
  lng: number;
}

/** Trạng thái bộ lọc mà người dùng nhìn thấy. Mã gửi lên backend giữ nguyên không dấu. */
export interface DishFilterState {
  cookingMethods: string[];
  temperatures: string[];
  mealTimes: string[];
  cuisines: string[];
  mood: string | null;
  /** null = để hệ thống tự đo thời tiết. 'rain'/'clear' = người dùng tự khai. */
  weather: string | null;
  maxDistanceKm: number | null;
}

export const EMPTY_FILTERS: DishFilterState = {
  cookingMethods: [],
  temperatures: [],
  mealTimes: [],
  cuisines: [],
  mood: null,
  weather: null,
  maxDistanceKm: DEFAULT_RADIUS_KM,
};

export interface UseDishSuggestionsResult {
  filters: DishFilterState;
  /** Bật/tắt một giá trị trong nhóm lọc nhiều lựa chọn. */
  toggle: (group: MultiSelectGroup, value: string) => void;
  /** Đặt giá trị cho nhóm chỉ chọn một (mood, weather) - bấm lại chính nó thì bỏ chọn. */
  setSingle: (group: SingleSelectGroup, value: string | null) => void;
  setMaxDistanceKm: (value: number | null) => void;
  reset: () => void;
  activeFilterCount: number;
  dishes: DishItem[] | null;
  context: string[];
  warnings: string[];
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export type MultiSelectGroup =
  | 'cookingMethods'
  | 'temperatures'
  | 'mealTimes'
  | 'cuisines';
export type SingleSelectGroup = 'mood' | 'weather';

export function useDishSuggestions(position: Coordinates): UseDishSuggestionsResult {
  const [filters, setFilters] = useState<DishFilterState>(EMPTY_FILTERS);
  const [dishes, setDishes] = useState<DishItem[] | null>(null);
  const [context, setContext] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const abortRef = useRef<AbortController | null>(null);

  // Huỷ request đang bay khi component bị gỡ, tránh setState trên component đã chết.
  useEffect(() => () => abortRef.current?.abort(), []);

  const toggle = useCallback((group: MultiSelectGroup, value: string) => {
    setFilters((current) => {
      const values = current[group];
      return {
        ...current,
        [group]: values.includes(value)
          ? values.filter((v) => v !== value)
          : [...values, value],
      };
    });
  }, []);

  const setSingle = useCallback((group: SingleSelectGroup, value: string | null) => {
    // Bấm lại đúng giá trị đang chọn = bỏ chọn. Không có cách nào khác để tắt "trời mưa"
    // nếu chỉ cho chọn mà không cho bỏ.
    setFilters((current) => ({
      ...current,
      [group]: current[group] === value ? null : value,
    }));
  }, []);

  const setMaxDistanceKm = useCallback((value: number | null) => {
    setFilters((current) => ({ ...current, maxDistanceKm: value }));
  }, []);

  const reset = useCallback(() => setFilters(EMPTY_FILTERS), []);
  const reload = useCallback(() => setReloadToken((n) => n + 1), []);

  useEffect(() => {
    // Request cũ phải bị huỷ: bấm nhanh 2 chip thì kết quả của lần bấm đầu có thể về sau
    // và ghi đè kết quả đúng - đây là bug bản JavaScript cũ đã mắc ở ô tìm kiếm.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);

    api
      .suggestDishes(
        {
          session_id: getSessionId(),
          latitude: position.lat,
          longitude: position.lng,
          cooking_methods: filters.cookingMethods,
          temperatures: filters.temperatures,
          meal_times: filters.mealTimes,
          cuisines: filters.cuisines,
          mood: filters.mood,
          weather: filters.weather,
          max_distance_km: filters.maxDistanceKm,
          limit: 30,
        },
        { signal: controller.signal },
      )
      .then((data) => {
        if (controller.signal.aborted) return;
        setDishes(data.results);
        setContext(data.context);
        setWarnings(data.warnings);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        // 503 DATA_NOT_READY kèm sẵn lệnh cần chạy - hiện nguyên văn cho người dùng,
        // vì với đồ án thì người dùng cũng chính là người chạy được lệnh đó.
        setError(
          // Lỗi MẠNG thì `message` là câu kỹ thuật của `fetch` ("Failed to fetch") — người
          // dùng đọc không hiểu gì, mà đây lại là lỗi hay gặp nhất (quên bật backend).
          // Các mã lỗi khác thì câu của backend đã viết cho người dùng đọc.
          err instanceof ApiError
            ? err.code === 'NETWORK'
              ? err.userMessage
              : err.message
            : 'Không gọi được máy chủ MoodBite.',
        );
        setDishes(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [filters, position.lat, position.lng, reloadToken]);

  const activeFilterCount =
    filters.cookingMethods.length +
    filters.temperatures.length +
    filters.mealTimes.length +
    filters.cuisines.length +
    (filters.mood ? 1 : 0) +
    (filters.weather ? 1 : 0);

  return {
    filters,
    toggle,
    setSingle,
    setMaxDistanceKm,
    reset,
    activeFilterCount,
    dishes,
    context,
    warnings,
    loading,
    error,
    reload,
  };
}

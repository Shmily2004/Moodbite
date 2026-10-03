/**
 * VIEWMODEL gợi ý món (vai trò "Controller" trong MVC cổ điển).
 *
 * Giữ state bộ lọc (qua `useDishFilterState`), gọi API, xử lý lỗi. KHÔNG chứa JSX, KHÔNG
 * chấm điểm món - việc xếp hạng nằm trọn ở backend (`domain/services/dish_ranking.py`).
 *
 * Bộ lọc TỰ ĐỘNG tìm lại khi đổi: người dùng bấm "trời mưa" là đã nói rõ ý định rồi,
 * bắt bấm thêm nút "Tìm" nữa là thừa một bước.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type { DishItem } from '@/shared/api';
import { ApiError, api } from '@/shared/api';
import { getSessionId } from '@/shared/lib';
import { useT } from '@/shared/i18n';
import { useDishFilterState } from './useDishFilterState';
import type { DishFilterState, UseDishFilterStateResult } from './useDishFilterState';

export { EMPTY_FILTERS } from './useDishFilterState';
export type {
  DishFilterState,
  FilterPreset,
  MultiSelectGroup,
  SingleSelectGroup,
} from './useDishFilterState';

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface UseDishSuggestionsResult extends UseDishFilterStateResult {
  dishes: DishItem[] | null;
  context: string[];
  warnings: string[];
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/**
 * @param boLocBanDau Bộ lọc khởi tạo. Dùng khi trang đọc bộ lọc từ URL
 *   (`/recommend?mood=relaxed&weather=rain`) — nhờ vậy chia sẻ đường dẫn được, F5 không
 *   mất lựa chọn, và nút Back của trình duyệt hoạt động đúng.
 */
export function useDishSuggestions(
  position: Coordinates,
  boLocBanDau?: Partial<DishFilterState>,
): UseDishSuggestionsResult {
  const boLoc = useDishFilterState(boLocBanDau);
  const { filters } = boLoc;
  const [dishes, setDishes] = useState<DishItem[] | null>(null);
  const [context, setContext] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  // `t` đi qua ref: đưa thẳng vào deps của effect gọi API thì đổi ngôn ngữ = gọi lại API.
  const t = useT();
  const tRef = useRef(t);
  tRef.current = t;

  const abortRef = useRef<AbortController | null>(null);

  // Huỷ request đang bay khi component bị gỡ, tránh setState trên component đã chết.
  useEffect(() => () => abortRef.current?.abort(), []);

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
          // Lưới món CHỈ hiện món cụ thể, không hiện danh mục ("Bún", "Phở", "Cơm").
          // Chủ dự án chốt 2026-08-24: "Bún — 2.370 quán" không giúp gì cho người đang
          // đói; họ gọi bún chả, bún cá, bún đậu. Danh mục lấy riêng qua
          // `only_categories: true` để dựng thanh điều hướng.
          only_categories: false,
          only_with_price: filters.onlyWithPrice,
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
            : tRef.current('suggest.serverDown'),
        );
        setDishes(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [filters, position.lat, position.lng, reloadToken]);

  return {
    ...boLoc,
    dishes,
    context,
    warnings,
    loading,
    error,
    reload,
  };
}

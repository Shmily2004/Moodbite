/**
 * STATE BỘ LỌC MÓN — tách khỏi `useDishSuggestions` (2026-09-16).
 *
 * VÌ SAO TÁCH: trang chi tiết món cần MỞ NGĂN KÉO BỘ LỌC với đúng các nút bấm đó, nhưng
 * KHÔNG được gọi `/dishes/suggest` (trang đó đã khoá vào một món, gọi gợi ý là tốn một
 * lượt xếp hạng vô ích). Trước đây state và lượt gọi API dính chung một hook, nên trang
 * chi tiết món đành mở một ngăn kéo RỖNG — đúng lỗi chủ dự án báo.
 *
 * Nay: hook này CHỈ giữ state + các hàm bật/tắt. `useDishSuggestions` dựng trên nó và
 * thêm phần gọi API. Một nguồn duy nhất cho quy tắc bật/tắt — không có bản chép thứ hai.
 *
 * KHÔNG chứa quy tắc nghiệp vụ: chỉ là trạng thái giao diện (ô nào đang được bấm).
 */
import { useCallback, useState } from 'react';
import { DEFAULT_RADIUS_KM } from '@/shared/config';

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

export type MultiSelectGroup =
  | 'cookingMethods'
  | 'temperatures'
  | 'mealTimes'
  | 'cuisines';
export type SingleSelectGroup = 'mood' | 'weather';

/**
 * Một "gợi ý nhanh": tổ hợp bộ lọc đặt sẵn, bấm một cái là tick sẵn nhiều ô bên dưới.
 *
 * CỐ Ý chỉ là `Partial<DishFilterState>` chứ không phải một loại lọc RIÊNG: gợi ý nhanh
 * không được là nguồn sự thật thứ hai. Nó chỉ ghi vào đúng những ô mà bộ lọc chi tiết
 * vẫn đang giữ, nên hai chỗ không bao giờ nói ngược nhau — đây chính là lỗi của bản
 * thiết kế ngày 2026-08-24, khi "Trời mưa" nằm ở CẢ nhóm trên lẫn nhóm "Thời tiết".
 */
export type FilterPreset = Partial<DishFilterState>;

export interface UseDishFilterStateResult {
  filters: DishFilterState;
  /** Bật/tắt một giá trị trong nhóm lọc nhiều lựa chọn. */
  toggle: (group: MultiSelectGroup, value: string) => void;
  /** Đặt giá trị cho nhóm chỉ chọn một (mood, weather) - bấm lại chính nó thì bỏ chọn. */
  setSingle: (group: SingleSelectGroup, value: string | null) => void;
  setMaxDistanceKm: (value: number | null) => void;
  /** Bật/tắt một gợi ý nhanh. Đang bật sẵn thì bấm lại là tắt. */
  applyPreset: (preset: FilterPreset) => void;
  /** Gợi ý nhanh này có đang bật đủ mọi vế của nó không (để tô sáng chip). */
  isPresetActive: (preset: FilterPreset) => boolean;
  reset: () => void;
  /** Số bộ lọc đang bật. KHÔNG đếm bán kính — bán kính luôn có một giá trị mặc định. */
  activeFilterCount: number;
}

/**
 * Một vế của gợi ý nhanh có đang bật không.
 *
 * Mảng thì đòi CHỨA ĐỦ (không đòi bằng nhau): bấm "Đồ nướng" rồi tự thêm "Chiên rán"
 * thì gợi ý "Đồ nướng" vẫn phải sáng — người dùng chưa hề tắt nó.
 */
function veDangBat(hien: DishFilterState, khoa: keyof DishFilterState, gia_tri: unknown) {
  const dang = hien[khoa];
  if (Array.isArray(dang) && Array.isArray(gia_tri)) {
    return gia_tri.every((v) => (dang as string[]).includes(v as string));
  }
  return dang === gia_tri;
}

/**
 * @param boLocBanDau Bộ lọc khởi tạo (đọc từ URL, hoặc suy từ món đang xem). Chỉ đọc MỘT
 *   LẦN lúc dựng: sau đó state trong hook là nguồn sự thật, nếu không mỗi lần URL đổi lại
 *   ghi đè thứ người dùng vừa bấm.
 */
export function useDishFilterState(
  boLocBanDau?: Partial<DishFilterState>,
): UseDishFilterStateResult {
  const [filters, setFilters] = useState<DishFilterState>(() => ({
    ...EMPTY_FILTERS,
    ...boLocBanDau,
  }));

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

  const isPresetActive = useCallback(
    (preset: FilterPreset) =>
      Object.entries(preset).every(([khoa, gia_tri]) =>
        veDangBat(filters, khoa as keyof DishFilterState, gia_tri),
      ),
    [filters],
  );

  const applyPreset = useCallback((preset: FilterPreset) => {
    setFilters((current) => {
      const dangBat = Object.entries(preset).every(([khoa, gia_tri]) =>
        veDangBat(current, khoa as keyof DishFilterState, gia_tri),
      );
      const moi: DishFilterState = { ...current };

      for (const [khoa, gia_tri] of Object.entries(preset)) {
        const k = khoa as keyof DishFilterState;
        if (Array.isArray(gia_tri)) {
          const hien = (current[k] as string[]) ?? [];
          // TẮT thì chỉ bỏ đúng những giá trị của gợi ý này, GIỮ những gì người dùng
          // tự thêm. Gán thẳng mảng rỗng sẽ xoá luôn lựa chọn họ tự bấm.
          (moi[k] as string[]) = dangBat
            ? hien.filter((v) => !(gia_tri as string[]).includes(v))
            : Array.from(new Set([...hien, ...(gia_tri as string[])]));
        } else {
          (moi[k] as unknown) = dangBat ? null : gia_tri;
        }
      }
      return moi;
    });
  }, []);

  const reset = useCallback(() => setFilters(EMPTY_FILTERS), []);

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
    applyPreset,
    isPresetActive,
    reset,
    activeFilterCount,
  };
}

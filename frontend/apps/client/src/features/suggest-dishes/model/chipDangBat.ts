/**
 * Liệt kê các BỘ LỌC ĐANG BẬT thành danh sách chip có thể gỡ từng cái.
 *
 * Thiết kế `Food recommend.jpg` hiện hàng chip "Trời mưa ✕ · Đồ nướng ✕ · Món nóng ✕".
 * Muốn gỡ đúng một chip thì phải biết nó thuộc NHÓM nào — nhãn tiếng Việt không đủ,
 * vì nhãn chỉ để hiển thị còn mã mới là thứ gửi lên backend.
 *
 * ⚠️ NHÃN Ở ĐÂY VÀ Ở `DishFilters.tsx` LÀ MỘT. Từ 2026-10-02 (song ngữ) bảng `NHAN` dưới
 * đây không chứa chữ nữa mà chứa KHOÁ TỪ ĐIỂN (`filterOpt.<nhóm>.<mã>`), và `DishFilters`
 * đọc nhãn qua chính `khoaNhan()` của file này — hai nơi không thể lệch nhau, ở cả tiếng
 * Việt lẫn tiếng Anh.
 */
import type { DishFilterState, MultiSelectGroup, SingleSelectGroup } from './useDishFilterState';
import { DEFAULT_RADIUS_KM } from '@/shared/config';
import { HAM_DICH_VI } from '@/shared/i18n';
import type { HamDich, Khoa } from '@/shared/i18n';

export interface ChipDangBat {
  /** Khoá duy nhất để React dựng danh sách. */
  khoa: string;
  nhan: string;
  /** Gỡ chip này: nhóm nhiều lựa chọn thì `toggle`, nhóm một lựa chọn thì `setSingle(null)`. */
  nhomNhieu?: MultiSelectGroup;
  nhomMot?: SingleSelectGroup;
  /**
   * Chip BÁN KÍNH (thêm 2026-09-16, theo `design/Filler.png`: "Trong vòng 3km ✕").
   * Gỡ chip này = trả bán kính về MẶC ĐỊNH, không phải "không giới hạn" — người dùng
   * bấm ✕ để bỏ điều kiện mình đã đặt, chứ không phải để tìm khắp thành phố.
   */
  khoangCach?: true;
  /**
   * Chip "Chỉ quán có ghi giá" (thêm 2026-10-02). Trước đó công tắc bật mà dòng "Đang lọc
   * theo" không hiện gì, trong khi đây là bộ lọc ĐẮT nhất (~1,3% quán có giá) - danh sách
   * tụt mạnh mà người dùng không thấy lý do. Gỡ = tắt công tắc.
   */
  chiCoGia?: true;
  giaTri: string;
}

/** Mã -> KHOÁ từ điển của nhãn. Mã là hợp đồng với backend, đừng đổi. */
const NHAN: Record<string, Record<string, Khoa>> = {
  weather: { rain: 'filterOpt.weather.rain', clear: 'filterOpt.weather.clear' },
  mood: {
    happy: 'filterOpt.mood.happy',
    sad: 'filterOpt.mood.sad',
    excited: 'filterOpt.mood.excited',
    relaxed: 'filterOpt.mood.relaxed',
  },
  temperatures: {
    hot: 'filterOpt.temperatures.hot',
    cold: 'filterOpt.temperatures.cold',
    room: 'filterOpt.temperatures.room',
  },
  cookingMethods: {
    nuong: 'filterOpt.cookingMethods.nuong',
    nuoc: 'filterOpt.cookingMethods.nuoc',
    chien: 'filterOpt.cookingMethods.chien',
    xao: 'filterOpt.cookingMethods.xao',
    hap: 'filterOpt.cookingMethods.hap',
    luoc: 'filterOpt.cookingMethods.luoc',
    tron: 'filterOpt.cookingMethods.tron',
  },
  mealTimes: {
    sang: 'filterOpt.mealTimes.sang',
    trua: 'filterOpt.mealTimes.trua',
    toi: 'filterOpt.mealTimes.toi',
    khuya: 'filterOpt.mealTimes.khuya',
    an_vat: 'filterOpt.mealTimes.an_vat',
  },
};

/**
 * Giá trị này có NHÃN trong bảng không — tức là có ô bấm tương ứng trong `DishFilters`.
 * Dùng khi suy bộ lọc từ món đang xem: đưa vào một mã không có ô bấm thì người dùng mở
 * ngăn kéo ra sẽ không thấy (và không tắt được) điều kiện đó.
 */
export function coNhan(nhom: string, gia_tri: string): boolean {
  return Boolean(NHAN[nhom]?.[gia_tri]);
}

/** Khoá từ điển của một mã — `DishFilters` dùng để vẽ chip, cùng nguồn với dòng "Đang lọc theo". */
export function khoaNhan(nhom: string, gia_tri: string): Khoa | null {
  return NHAN[nhom]?.[gia_tri] ?? null;
}

/** Mã lạ (backend thêm giá trị mới) thì hiện chính mã đó, đừng nuốt mất chip. */
function nhanCua(nhom: string, gia_tri: string, t: HamDich): string {
  const khoa = khoaNhan(nhom, gia_tri);
  return khoa ? t(khoa) : gia_tri;
}

/** `t` bỏ trống = tiếng Việt (giữ hành vi + test cũ); trang truyền `useT()` vào. */
export function chipDangBat(filters: DishFilterState, t: HamDich = HAM_DICH_VI): ChipDangBat[] {
  const ket_qua: ChipDangBat[] = [];

  // Thứ tự: thời tiết -> tâm trạng -> cách chế biến -> nhiệt độ -> bữa. Cùng thứ tự với
  // ảnh thiết kế, và cũng là thứ tự người dùng thường chọn.
  if (filters.weather) {
    ket_qua.push({
      khoa: `weather:${filters.weather}`,
      nhan: nhanCua('weather', filters.weather, t),
      nhomMot: 'weather',
      giaTri: filters.weather,
    });
  }
  if (filters.mood) {
    ket_qua.push({
      khoa: `mood:${filters.mood}`,
      nhan: nhanCua('mood', filters.mood, t),
      nhomMot: 'mood',
      giaTri: filters.mood,
    });
  }

  const nhomNhieu: MultiSelectGroup[] = [
    'cookingMethods',
    'temperatures',
    'mealTimes',
    'cuisines',
  ];
  for (const nhom of nhomNhieu) {
    for (const gia_tri of filters[nhom]) {
      ket_qua.push({
        khoa: `${nhom}:${gia_tri}`,
        // `cuisines` không có bảng nhãn: giá trị là tên ẩm thực backend trả sẵn (dữ liệu).
        nhan: nhanCua(nhom, gia_tri, t),
        nhomNhieu: nhom,
        giaTri: gia_tri,
      });
    }
  }

  // Bán kính chỉ thành chip khi KHÁC mặc định: chip "Trong vòng 10 km" luôn nằm đó mà
  // người dùng chưa từng chọn thì chỉ là nhiễu.
  if (filters.maxDistanceKm !== DEFAULT_RADIUS_KM) {
    ket_qua.push({
      khoa: 'km',
      nhan:
        filters.maxDistanceKm === null
          ? t('filters.chip.noKm')
          : t('filters.chip.km', { n: filters.maxDistanceKm }),
      khoangCach: true,
      giaTri: String(filters.maxDistanceKm ?? ''),
    });
  }

  if (filters.onlyWithPrice) {
    ket_qua.push({ khoa: 'gia', nhan: t('filters.chip.price'), chiCoGia: true, giaTri: '1' });
  }

  return ket_qua;
}

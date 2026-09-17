/**
 * Liệt kê các BỘ LỌC ĐANG BẬT thành danh sách chip có thể gỡ từng cái.
 *
 * Thiết kế `Food recommend.jpg` hiện hàng chip "Trời mưa ✕ · Đồ nướng ✕ · Món nóng ✕".
 * Muốn gỡ đúng một chip thì phải biết nó thuộc NHÓM nào — nhãn tiếng Việt không đủ,
 * vì nhãn chỉ để hiển thị còn mã mới là thứ gửi lên backend.
 *
 * ⚠️ NHÃN Ở ĐÂY PHẢI KHỚP `DishFilters.tsx`. Hai nơi cùng đặt tên cho một mã là chỗ
 * chắc chắn sẽ lệch nhau; nhưng gộp lại thì `DishFilters` phải xuất ra cả bảng nhãn,
 * mà nó là component "ngu" không nên gánh thêm việc đó. Chọn cách rẻ hơn: để chung một
 * file, và ghi rõ ràng buộc này ở cả hai đầu.
 */
import type { DishFilterState, MultiSelectGroup, SingleSelectGroup } from './useDishFilterState';
import { DEFAULT_RADIUS_KM } from '@/shared/config';

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
  giaTri: string;
}

const NHAN: Record<string, Record<string, string>> = {
  weather: { rain: 'Trời mưa', clear: 'Trời nắng' },
  mood: { happy: 'Vui', sad: 'Buồn', excited: 'Hào hứng', relaxed: 'Thư giãn' },
  temperatures: { hot: 'Đồ nóng', cold: 'Đồ mát', room: 'Nhiệt độ phòng' },
  cookingMethods: {
    nuong: 'Đồ nướng',
    nuoc: 'Món nước',
    chien: 'Chiên rán',
    xao: 'Xào',
    hap: 'Hấp',
    luoc: 'Luộc',
    tron: 'Trộn',
  },
  mealTimes: {
    sang: 'Bữa sáng',
    trua: 'Bữa trưa',
    toi: 'Bữa tối',
    khuya: 'Đêm khuya',
    an_vat: 'Ăn vặt',
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

/** Mã lạ (backend thêm giá trị mới) thì hiện chính mã đó, đừng nuốt mất chip. */
function nhanCua(nhom: string, gia_tri: string): string {
  return NHAN[nhom]?.[gia_tri] ?? gia_tri;
}

export function chipDangBat(filters: DishFilterState): ChipDangBat[] {
  const ket_qua: ChipDangBat[] = [];

  // Thứ tự: thời tiết -> tâm trạng -> cách chế biến -> nhiệt độ -> bữa. Cùng thứ tự với
  // ảnh thiết kế, và cũng là thứ tự người dùng thường chọn.
  if (filters.weather) {
    ket_qua.push({
      khoa: `weather:${filters.weather}`,
      nhan: nhanCua('weather', filters.weather),
      nhomMot: 'weather',
      giaTri: filters.weather,
    });
  }
  if (filters.mood) {
    ket_qua.push({
      khoa: `mood:${filters.mood}`,
      nhan: nhanCua('mood', filters.mood),
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
        nhan: nhanCua(nhom, gia_tri),
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
          ? 'Không giới hạn khoảng cách'
          : `Trong vòng ${filters.maxDistanceKm} km`,
      khoangCach: true,
      giaTri: String(filters.maxDistanceKm ?? ''),
    });
  }

  return ket_qua;
}

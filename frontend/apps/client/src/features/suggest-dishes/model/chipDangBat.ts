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
import type { DishFilterState, MultiSelectGroup, SingleSelectGroup } from './useDishSuggestions';

export interface ChipDangBat {
  /** Khoá duy nhất để React dựng danh sách. */
  khoa: string;
  nhan: string;
  /** Gỡ chip này: nhóm nhiều lựa chọn thì `toggle`, nhóm một lựa chọn thì `setSingle(null)`. */
  nhomNhieu?: MultiSelectGroup;
  nhomMot?: SingleSelectGroup;
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

  return ket_qua;
}

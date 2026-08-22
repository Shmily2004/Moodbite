/**
 * Danh sách SỞ THÍCH chọn được, và mỗi cái ánh xạ vào bộ lọc nào của backend.
 *
 * ⚠️ CHỈ ĐƯA VÀO ĐÂY THỨ BACKEND LỌC ĐƯỢC THẬT. Giá trị lấy từ đúng bảng mà
 * `useDishSuggestions` gửi lên (`cooking_methods`, `temperatures`, `mood`, `cuisines`).
 * Thêm dòng mới thì phải kiểm giá trị đó backend có nhận không, nếu không người dùng bấm
 * mà kết quả không đổi.
 */
export type NhomLoc = 'cookingMethods' | 'temperatures' | 'cuisines' | 'mood';

export interface SoThich {
  id: string;
  label: string;
  emoji: string;
  nhom: NhomLoc;
  gia_tri: string;
}

export const SO_THICH: SoThich[] = [
  { id: 'nuong', label: 'Đồ nướng', emoji: '🔥', nhom: 'cookingMethods', gia_tri: 'nuong' },
  { id: 'nuoc', label: 'Món nước', emoji: '🍜', nhom: 'cookingMethods', gia_tri: 'nuoc' },
  { id: 'chien', label: 'Chiên rán', emoji: '🍤', nhom: 'cookingMethods', gia_tri: 'chien' },
  { id: 'hap', label: 'Hấp / luộc', emoji: '☁️', nhom: 'cookingMethods', gia_tri: 'hap' },
  { id: 'tron', label: 'Món trộn', emoji: '🥗', nhom: 'cookingMethods', gia_tri: 'tron' },
  { id: 'nong', label: 'Món nóng', emoji: '🍲', nhom: 'temperatures', gia_tri: 'hot' },
  { id: 'mat', label: 'Đồ mát', emoji: '🧊', nhom: 'temperatures', gia_tri: 'cold' },
  { id: 'cay', label: 'Ăn cay', emoji: '🌶️', nhom: 'mood', gia_tri: 'excited' },
];

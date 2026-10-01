/**
 * Danh sách SỞ THÍCH chọn được, và mỗi cái ánh xạ vào bộ lọc nào của backend.
 *
 * ⚠️ CHỈ ĐƯA VÀO ĐÂY THỨ BACKEND LỌC ĐƯỢC THẬT. Giá trị lấy từ đúng bảng mà
 * `useDishSuggestions` gửi lên (`cooking_methods`, `temperatures`, `mood`, `cuisines`).
 * Thêm dòng mới thì phải kiểm giá trị đó backend có nhận không, nếu không người dùng bấm
 * mà kết quả không đổi.
 */
export type NhomLoc = 'cookingMethods' | 'temperatures' | 'cuisines' | 'mood';

/**
 * Không có trường icon ở đây (bỏ `emoji` 2026-09-29, checklist A9): hình vẽ là việc của
 * VIEW, nên icon SVG được gắn theo `id` ở `ui/TastePicker.tsx`. Giữ file này là dữ liệu
 * thuần — không phải `.tsx`, không kéo React vào tầng model.
 */
export interface SoThich {
  id: string;
  label: string;
  nhom: NhomLoc;
  gia_tri: string;
}

export const SO_THICH: SoThich[] = [
  { id: 'nuong', label: 'Đồ nướng', nhom: 'cookingMethods', gia_tri: 'nuong' },
  { id: 'nuoc', label: 'Món nước', nhom: 'cookingMethods', gia_tri: 'nuoc' },
  { id: 'chien', label: 'Chiên rán', nhom: 'cookingMethods', gia_tri: 'chien' },
  { id: 'hap', label: 'Hấp / luộc', nhom: 'cookingMethods', gia_tri: 'hap' },
  { id: 'tron', label: 'Món trộn', nhom: 'cookingMethods', gia_tri: 'tron' },
  { id: 'nong', label: 'Món nóng', nhom: 'temperatures', gia_tri: 'hot' },
  { id: 'mat', label: 'Đồ mát', nhom: 'temperatures', gia_tri: 'cold' },
  { id: 'cay', label: 'Ăn cay', nhom: 'mood', gia_tri: 'excited' },
];

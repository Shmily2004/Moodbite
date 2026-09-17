/**
 * Các kiểu SẮP XẾP HIỂN THỊ của lưới món ở `/recommend`.
 *
 * ⚠️ `/dishes/suggest` KHÔNG có tham số sắp xếp (đã kiểm `DishSuggestRequest`, 2026-09-16).
 * Thứ tự "Phù hợp nhất" là thứ tự BACKEND xếp hạng — frontend giữ nguyên, không chấm lại.
 * Hai kiểu còn lại chỉ SẮP LẠI ĐỂ XEM trên chính danh sách đã tải, bằng hai trường hiển thị
 * có sẵn (`name`, `restaurant_count`). Không kiểu nào tạo ra điểm hay thứ hạng mới, nên
 * không phải quy tắc nghiệp vụ (CLAUDE.md mục 1b).
 *
 * Hệ quả phải nói rõ: chỉ sắp trong SỐ MÓN ĐÃ TẢI (tối đa 30), không phải toàn danh mục.
 */
import type { DishItem } from '@/shared/api';

export const KIEU_SAP_XEP_MON = ['phu-hop', 'ten', 'so-quan'] as const;
export type KieuSapXepMon = (typeof KIEU_SAP_XEP_MON)[number];

export function sapXepMon(dishes: DishItem[], kieu: KieuSapXepMon): DishItem[] {
  // Luôn trả MẢNG MỚI khi sắp: `sort` sửa tại chỗ, sửa thẳng mảng của hook là làm hỏng
  // thứ tự "Phù hợp nhất" cho lần chọn lại sau.
  if (kieu === 'ten') {
    return [...dishes].sort((a, b) => a.name.localeCompare(b.name, 'vi'));
  }
  if (kieu === 'so-quan') {
    // `sort` của JS ổn định: hai món bằng số quán giữ nguyên thứ tự backend.
    return [...dishes].sort((a, b) => b.restaurant_count - a.restaurant_count);
  }
  return dishes;
}

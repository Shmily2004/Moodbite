/**
 * Suy BỘ LỌC BAN ĐẦU từ món đang xem — cho nút "Chỉnh sửa" ở trang chi tiết món.
 *
 * Nút "Chỉnh sửa" nằm NGAY CẠNH hàng thuộc tính của món (Nóng · Nướng · 🌶️). Người bấm
 * vào đó đang nói "tôi muốn món kiểu này nhưng đổi chút", nên ngăn kéo phải mở ra với
 * đúng những ô đó đã bật sẵn — mở ra một bộ lọc trống trơn là bắt họ chọn lại từ đầu.
 *
 * ⚠️ ĐÂY KHÔNG PHẢI QUY TẮC NGHIỆP VỤ. Không chấm điểm, không suy luận gì thêm: chỉ chép
 * nguyên mã backend trả (`temperature`, `cooking_method`) sang đúng ô bộ lọc cùng mã.
 * Backend vẫn là nơi quyết định món nào khớp.
 *
 * CỐ Ý BỎ `meal_times`: một món thường khai 3-4 bữa ("sáng · trưa · tối"). Bật sẵn cả bốn
 * ô bữa không thu hẹp được gì mà làm hàng chip "Đang lọc theo" dài ra vô ích.
 */
import type { DishItem } from '@/shared/api';
import { coNhan } from './chipDangBat';
import type { DishFilterState } from './useDishFilterState';

type ThuocTinhMon = Pick<DishItem, 'temperature' | 'cooking_method'>;

export function boLocTuMon(dish: ThuocTinhMon | null | undefined): Partial<DishFilterState> {
  if (!dish) return {};
  const ket_qua: Partial<DishFilterState> = {};

  // Chỉ nhận mã CÓ Ô BẤM trong `DishFilters` (xem `coNhan`). Mã như `nuong_lo` không có ô
  // nào — đưa vào thì người dùng không nhìn thấy và không tắt được điều kiện đó.
  if (dish.temperature && coNhan('temperatures', dish.temperature)) {
    ket_qua.temperatures = [dish.temperature];
  }
  if (dish.cooking_method && coNhan('cookingMethods', dish.cooking_method)) {
    ket_qua.cookingMethods = [dish.cooking_method];
  }
  return ket_qua;
}

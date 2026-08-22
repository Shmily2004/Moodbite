/**
 * "🕘 Xem gần đây" — nhớ những món người dùng vừa mở.
 *
 * VÌ SAO LƯU Ở TRÌNH DUYỆT CHỨ KHÔNG PHẢI Ở SERVER: backend hiện ghi tương tác theo QUÁN
 * (`POST /interactions` cần `restaurant_id`), và KHÔNG có endpoint nào đọc lại lịch sử.
 * Muốn làm ở server thì phải thêm cả bảng lẫn endpoint — việc lớn, phải chốt trước.
 *
 * Bản localStorage này đổi lại được ngay và không nói dối điều gì: nó chỉ hứa "món BẠN
 * vừa xem TRÊN MÁY NÀY", đúng thứ nó làm được. Đổi máy thì mất — chấp nhận, vì thà vậy
 * còn hơn vẽ ra một danh sách trống rỗng gắn nhãn "lịch sử của bạn".
 *
 * ⚠️ KHÔNG dùng cho việc chấm điểm gợi ý. Đây chỉ là lối tắt quay lại món vừa xem; mọi
 * việc xếp hạng vẫn do backend làm (CLAUDE.md mục 1b).
 */
import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'moodbite.recent_dishes';
/** 8 món: đủ một hàng ngang trên máy tính, không biến thành nhật ký dài vô tận. */
const GIU_TOI_DA = 8;

export interface RecentDish {
  dishId: string;
  name: string;
}

function doc(): RecentDish[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw);
    // Dữ liệu trong localStorage do NGƯỜI DÙNG sở hữu và sửa được — không tin cấu trúc.
    if (!Array.isArray(data)) return [];
    return data
      .filter(
        (x): x is RecentDish =>
          !!x && typeof x.dishId === 'string' && typeof x.name === 'string',
      )
      .slice(0, GIU_TOI_DA);
  } catch {
    // JSON hỏng hoặc storage bị chặn -> coi như chưa xem gì, không nổ.
    return [];
  }
}

export interface UseRecentDishesResult {
  recent: RecentDish[];
  remember: (dish: RecentDish) => void;
  clear: () => void;
}

export function useRecentDishes(): UseRecentDishesResult {
  const [recent, setRecent] = useState<RecentDish[]>([]);

  // Đọc SAU khi dựng xong (không đọc thẳng trong `useState`) để lần render đầu ở máy chủ
  // hay trong test không đụng vào localStorage.
  useEffect(() => {
    setRecent(doc());
  }, []);

  const remember = useCallback((dish: RecentDish) => {
    setRecent((truoc) => {
      // Món đã có thì ĐẨY LÊN ĐẦU chứ không thêm bản thứ hai.
      const con_lai = truoc.filter((x) => x.dishId !== dish.dishId);
      const moi = [dish, ...con_lai].slice(0, GIU_TOI_DA);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(moi));
      } catch {
        /* chế độ riêng tư: vẫn hiện trong phiên này, chỉ là không nhớ được lâu */
      }
      return moi;
    });
  }, []);

  const clear = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* bỏ qua */
    }
    setRecent([]);
  }, []);

  return { recent, remember, clear };
}

/**
 * Nút TIM trên thẻ món — lưu món yêu thích.
 *
 * ⚠️ LƯU Ở TRÌNH DUYỆT, KHÔNG PHẢI Ở SERVER.
 * Backend có `POST /interactions` với `action_type: 'save'`, nhưng nó ghi theo QUÁN
 * (`restaurant_id` là bắt buộc) và KHÔNG có endpoint nào đọc lại danh sách đã lưu. Nghĩa
 * là nếu gọi API đó cho một MÓN thì vừa sai kiểu dữ liệu, vừa không lấy lại được — trái
 * tim sẽ rỗng lại sau khi tải trang.
 *
 * Bản localStorage này đổi lại được ngay và nói đúng thứ nó làm: "món bạn đã lưu TRÊN MÁY
 * NÀY". Khi backend có bảng yêu thích + endpoint đọc, chỉ cần thay ruột hook này, phần
 * giao diện không phải sửa dòng nào.
 *
 * Cùng cách làm với `features/recent-dishes` — hai thứ này là cặp.
 */
import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'moodbite.saved_dishes';

function doc(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw);
    // Dữ liệu trong localStorage do NGƯỜI DÙNG sở hữu và sửa được — không tin cấu trúc.
    return Array.isArray(data) ? data.filter((x): x is string => typeof x === 'string') : [];
  } catch {
    return [];
  }
}

export interface UseSavedDishesResult {
  /** Danh sách `dish_id` đã lưu. */
  saved: string[];
  isSaved: (dishId: string) => boolean;
  /** Lưu nếu chưa có, bỏ lưu nếu đã có. */
  toggle: (dishId: string) => void;
}

export function useSavedDishes(): UseSavedDishesResult {
  const [saved, setSaved] = useState<string[]>([]);

  // Đọc SAU khi dựng xong để lần render đầu trong test không đụng localStorage.
  useEffect(() => {
    setSaved(doc());
  }, []);

  const toggle = useCallback((dishId: string) => {
    setSaved((truoc) => {
      const moi = truoc.includes(dishId)
        ? truoc.filter((x) => x !== dishId)
        : [dishId, ...truoc];
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(moi));
      } catch {
        /* chế độ riêng tư: vẫn đổi trong phiên này, chỉ là không nhớ được lâu */
      }
      return moi;
    });
  }, []);

  const isSaved = useCallback((dishId: string) => saved.includes(dishId), [saved]);

  return { saved, isSaved, toggle };
}

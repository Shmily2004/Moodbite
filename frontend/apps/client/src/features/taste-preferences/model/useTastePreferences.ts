/**
 * VIEWMODEL của "Sở thích của bạn". Lưu ở localStorage — xem lý do ở `ui/TastePicker.tsx`.
 */
import { useCallback, useState } from 'react';
import { SO_THICH } from './danh_sach';
import type { SoThich } from './danh_sach';

const STORAGE_KEY = 'moodbite.taste';

function doc(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw);
    if (!Array.isArray(data)) return [];
    // Chỉ nhận id CÓ THẬT trong bảng. Bỏ id lạ (người dùng sửa tay localStorage, hoặc ta
    // xoá bớt lựa chọn ở bản sau) thay vì đem đi lọc rồi backend từ chối.
    const hop_le = new Set(SO_THICH.map((x) => x.id));
    return data.filter((x): x is string => typeof x === 'string' && hop_le.has(x));
  } catch {
    return [];
  }
}

export interface UseTastePreferencesResult {
  /** Id các sở thích đang bật. */
  ids: string[];
  /** Bản đầy đủ của các sở thích đang bật — để nơi khác đọc ra bộ lọc. */
  daChon: SoThich[];
  soLuong: number;
  dangChon: (id: string) => boolean;
  chon: (id: string) => void;
  xoaHet: () => void;
}

export function useTastePreferences(): UseTastePreferencesResult {
  /**
   * Đọc NGAY lúc dựng, không đợi `useEffect` (đổi 2026-09-23).
   *
   * ⚠️ ĐÂY LÀ LÝ DO SỞ THÍCH TỪNG KHÔNG LỌC ĐƯỢC GÌ. Bản cũ khởi tạo `[]` rồi mới nạp ở
   * `useEffect`, nên ở lần dựng ĐẦU TIÊN danh sách luôn rỗng. Trang chủ lại dùng sở thích
   * làm bộ lọc BAN ĐẦU cho `useDishFilterState`, mà hook đó chỉ đọc giá trị khởi tạo đúng
   * một lần — nghĩa là nó luôn nhận đúng cái mảng rỗng đó và mọi lựa chọn của người dùng
   * rơi mất, đúng lúc câu chữ trên trang tài khoản đang hứa "sẽ bật sẵn các bộ lọc này".
   *
   * `localStorage` là API ĐỒNG BỘ nên không có lý do gì phải hoãn; `doc()` đã bọc
   * try/catch sẵn cho chế độ riêng tư.
   */
  const [ids, setIds] = useState<string[]>(doc);

  const luu = (moi: string[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(moi));
    } catch {
      /* chế độ riêng tư: vẫn đổi trong phiên này */
    }
    setIds(moi);
  };

  const chon = useCallback((id: string) => {
    setIds((truoc) => {
      const moi = truoc.includes(id) ? truoc.filter((x) => x !== id) : [...truoc, id];
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(moi));
      } catch {
        /* bỏ qua */
      }
      return moi;
    });
  }, []);

  const xoaHet = useCallback(() => luu([]), []);

  return {
    ids,
    daChon: SO_THICH.filter((x) => ids.includes(x.id)),
    soLuong: ids.length,
    dangChon: (id) => ids.includes(id),
    chon,
    xoaHet,
  };
}

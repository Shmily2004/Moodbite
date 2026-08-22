/**
 * VIEWMODEL của "Sở thích của bạn". Lưu ở localStorage — xem lý do ở `ui/TastePicker.tsx`.
 */
import { useCallback, useEffect, useState } from 'react';
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
  const [ids, setIds] = useState<string[]>([]);

  useEffect(() => {
    setIds(doc());
  }, []);

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

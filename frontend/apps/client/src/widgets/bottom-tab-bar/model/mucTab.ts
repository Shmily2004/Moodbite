/**
 * Các mục của THANH TAB DƯỚI ĐÁY (màn < 768px), theo `design/Home.jpg` bản điện thoại.
 *
 * ⚠️ CHỈ DẪN TỚI ROUTE CÓ THẬT (kiểm `shared/config/routes.ts`, 2026-09-16). Bản thiết kế
 * có 5 tab, trong đó "Lưu" trùng nghĩa với "Yêu thích" ở trang tài khoản và không có trang
 * riêng — bỏ, thay vì dẫn tới một chỗ không tồn tại.
 *
 * "Yêu thích" và "Cá nhân" cùng là `/account`, phân biệt bằng `?tab=saved` — đúng tham số
 * mà `AccountPage` đọc. Khách bấm vào sẽ được trang đó chuyển sang đăng nhập (không phải
 * link chết: route tồn tại, chỉ là cần tài khoản).
 */
import { ROUTES } from '@/shared/config';
import type { Khoa } from '@/shared/i18n';

export type MaTab = 'home' | 'suggest' | 'favorites' | 'me';

export interface MucTab {
  ma: MaTab;
  to: string;
  nhan: Khoa;
}

export const MUC_TAB: MucTab[] = [
  { ma: 'home', to: ROUTES.home, nhan: 'tabbar.home' },
  { ma: 'suggest', to: ROUTES.recommend, nhan: 'tabbar.suggest' },
  { ma: 'favorites', to: `${ROUTES.account}?tab=saved`, nhan: 'tabbar.favorites' },
  { ma: 'me', to: ROUTES.account, nhan: 'tabbar.me' },
];

/** Tab nào đang sáng. `null` = trang không thuộc tab nào (VD `/search`, `/dishes/…`). */
export function tabDangMo(pathname: string, search: string): MaTab | null {
  if (pathname === ROUTES.home) return 'home';
  if (pathname === ROUTES.recommend) return 'suggest';
  if (pathname === ROUTES.account) {
    return new URLSearchParams(search).get('tab') === 'saved' ? 'favorites' : 'me';
  }
  return null;
}

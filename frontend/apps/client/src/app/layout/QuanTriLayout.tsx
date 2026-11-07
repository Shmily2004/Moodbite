/**
 * Khung cho KHU QUẢN TRỊ (`/quan-tri/*`).
 *
 * Chỉ bọc ngôn ngữ và phiên khách — để đăng xuất quản trị đăng xuất cả khách (xem
 * `PHAT_DANG_XUAT_KHACH`). KHÔNG có chân trang hay thanh tab của app khách: khu quản trị
 * có khung riêng (`AdminLayout`).
 */
import { Outlet } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';

export function QuanTriLayout() {
  return (
    <LanguageProvider>
      <UserSessionProvider>
        <Outlet />
      </UserSessionProvider>
    </LanguageProvider>
  );
}

/**
 * VIEWMODEL của phiên QUẢN TRỊ (vai trò "Controller" trong MVC cổ điển).
 *
 * Từ 2026-11-01 KHÔNG còn trang đăng nhập riêng: đăng nhập diễn ra ở `/login` của app người
 * dùng, và khi tài khoản là admin thì app đó gọi `dangNhapQuanTri` (xem `phienQuanTri.ts`)
 * để lấy token quản trị. Ở đây chỉ còn: biết có phiên hay không, đăng xuất, và xử lý 401.
 */
import { useCallback, useEffect, useState } from 'react';
import { adminApi } from '@admin/shared/api';
import { clearToken, onSessionExpired, readToken } from '@admin/shared/lib';
import { PHAT_DANG_XUAT_KHACH } from './phienQuanTri';

export interface UseAdminSessionResult {
  isLoggedIn: boolean;
  logout: () => void;
  /** Gọi khi một request bất kỳ nhận 401 - token đã hết hạn giữa chừng. */
  handleExpired: () => void;
}

export function useAdminSession(): UseAdminSessionResult {
  const [isLoggedIn, setIsLoggedIn] = useState(() => readToken() !== null);

  const logout = useCallback(() => {
    // Báo server thu hồi token TRƯỚC khi xoá (`request` đọc token ngay lúc gọi). Không đợi
    // và nuốt lỗi: mất mạng thì vẫn phải đăng xuất khỏi máy này.
    adminApi.logout().catch(() => undefined);
    clearToken();
    setIsLoggedIn(false);
    // Phiên khách dùng chung trình duyệt với phiên quản trị: đăng xuất quản trị thì đăng
    // xuất luôn khách, để không còn một nửa phiên treo lại.
    window.dispatchEvent(new Event(PHAT_DANG_XUAT_KHACH));
  }, []);

  const handleExpired = useCallback(() => {
    clearToken();
    setIsLoggedIn(false);
  }, []);

  // Mọi 401 có token của `adminApi` (ở BẤT KỲ trang nào) đi về đây — xem
  // `shared/lib/sessionExpiry`. `RequireAuth` thấy `isLoggedIn=false` sẽ chuyển về trang
  // đăng nhập chung kèm `state.from`, đăng nhập lại là quay về đúng trang.
  useEffect(() => onSessionExpired(handleExpired), [handleExpired]);

  return { isLoggedIn, logout, handleExpired };
}

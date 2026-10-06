/**
 * VIEWMODEL của phiên đăng nhập admin (vai trò "Controller" trong MVC cổ điển).
 *
 * Giữ state đăng nhập, gọi API, xử lý lỗi. KHÔNG chứa JSX.
 */
import { useCallback, useEffect, useState } from 'react';
import { ApiError, adminApi } from '@/shared/api';
import { clearToken, onSessionExpired, readToken, writeToken } from '@/shared/lib';

export interface UseAdminSessionResult {
  isLoggedIn: boolean;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  /** Gọi khi một request bất kỳ nhận 401 - token đã hết hạn giữa chừng. */
  handleExpired: () => void;
}

export function useAdminSession(): UseAdminSessionResult {
  const [isLoggedIn, setIsLoggedIn] = useState(() => readToken() !== null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminApi.login({ username, password });
      writeToken(data.token);
      setIsLoggedIn(true);
    } catch (err) {
      // Backend cố tình không nói rõ sai tên hay sai mật khẩu, để không giúp người dò
      // tài khoản. Hiển thị đúng câu backend trả về (`message`), KHÔNG dùng `userMessage`:
      // câu soạn sẵn đó biến 401 sai mật khẩu thành "Phiên đăng nhập đã hết hạn" và che
      // mất hướng dẫn khắc phục của 503. Chỉ NETWORK mới dùng `userMessage` vì `message`
      // khi đó là "Failed to fetch". Cùng quy tắc với `useUserSession` của app client.
      setError(
        err instanceof ApiError
          ? err.code === 'NETWORK'
            ? err.userMessage
            : err.message
          : (err as Error).message,
      );
      setIsLoggedIn(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    // Báo server thu hồi token TRƯỚC khi xoá (`request` đọc token ngay lúc gọi). Không đợi
    // và nuốt lỗi: mất mạng thì vẫn phải đăng xuất khỏi máy này.
    adminApi.logout().catch(() => undefined);
    clearToken();
    setIsLoggedIn(false);
    setError(null);
  }, []);

  const handleExpired = useCallback(() => {
    clearToken();
    setIsLoggedIn(false);
    setError('Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.');
  }, []);

  // Mọi 401 có token của `adminApi` (ở BẤT KỲ trang nào) đi về đây — xem
  // `shared/lib/sessionExpiry`. `RequireAuth` thấy `isLoggedIn=false` sẽ chuyển sang
  // trang đăng nhập kèm `state.from`, đăng nhập lại là quay về đúng trang.
  useEffect(() => onSessionExpired(handleExpired), [handleExpired]);

  return { isLoggedIn, loading, error, login, logout, handleExpired };
}

/**
 * VIEWMODEL của phiên đăng nhập admin (vai trò "Controller" trong MVC cổ điển).
 *
 * Giữ state đăng nhập, gọi API, xử lý lỗi. KHÔNG chứa JSX.
 */
import { useCallback, useState } from 'react';
import { ApiError, adminApi } from '@/shared/api';
import { clearToken, readToken, writeToken } from '@/shared/lib';

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
      // tài khoản. Hiển thị đúng câu backend trả về, không tự suy diễn thêm.
      setError(err instanceof ApiError ? err.userMessage : (err as Error).message);
      setIsLoggedIn(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setIsLoggedIn(false);
    setError(null);
  }, []);

  const handleExpired = useCallback(() => {
    clearToken();
    setIsLoggedIn(false);
    setError('Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.');
  }, []);

  return { isLoggedIn, loading, error, login, logout, handleExpired };
}

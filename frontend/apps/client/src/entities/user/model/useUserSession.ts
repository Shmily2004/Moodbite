/**
 * VIEWMODEL của PHIÊN TÀI KHOẢN — trạng thái "đang đăng nhập hay chưa" của cả app.
 *
 * VÌ SAO NẰM Ở `entities/` CHỨ KHÔNG PHẢI `features/`:
 * đăng nhập và đăng ký là HAI hành động (hai feature), nhưng chúng dùng CHUNG một trạng
 * thái. Luật FSD cấm feature này import feature kia, nên nếu để state ở `features/
 * auth-login` thì trang đăng ký sẽ phải giữ một bản state RIÊNG — đăng ký xong app vẫn
 * tưởng chưa đăng nhập cho tới lúc tải lại trang. Khái niệm dùng chung thì đặt ở tầng
 * dùng chung: `entities/user` sở hữu "phiên của người dùng", hai feature chỉ gọi vào.
 *
 * ⚠️ KHÔNG có quy tắc nghiệp vụ ở đây: độ dài mật khẩu, ký tự cho phép trong tên đăng
 * nhập… đều do backend quyết (`src/domain/entities/user.py`). Chép luật xuống frontend là
 * tạo NƠI THỨ HAI chứa nghiệp vụ — đúng sai lầm CLAUDE.md mục 1b cấm.
 */
import { useCallback, useState } from 'react';
import { ApiError, authApi } from '@/shared/api';
import { clearToken, readToken, writeToken } from '@/shared/lib';

export interface UseUserSessionResult {
  isLoggedIn: boolean;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string, remember: boolean) => Promise<void>;
  register: (
    username: string,
    password: string,
    displayName: string,
    email: string,
  ) => Promise<void>;
  logout: () => void;
  /** Xoá câu báo lỗi cũ khi người dùng chuyển sang trang khác. */
  clearError: () => void;
}

/**
 * Chọn câu báo lỗi.
 *
 * Ưu tiên `message` của backend, KHÔNG dùng `userMessage`: `userMessage` là câu soạn sẵn
 * theo mã lỗi cho luồng tìm quán, nên với tài khoản nó nói sai hẳn — `UNAUTHORIZED` ra
 * "Phiên đăng nhập đã hết hạn" (thực tế là gõ sai mật khẩu), `DATA_NOT_READY` ra "chưa
 * nạp xong dữ liệu quán ăn" (thực tế là chưa đặt MOODBITE_AUTH_SECRET). Câu backend trả
 * về đã viết cho người dùng đọc, kể cả lỗi định dạng lúc đăng ký.
 *
 * Riêng `NETWORK` thì ngược lại: `message` là lỗi kỹ thuật của `fetch` ("Failed to
 * fetch"), người dùng đọc không hiểu gì.
 */
function authErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    return err.code === 'NETWORK' ? err.userMessage : err.message;
  }
  return (err as Error).message;
}

export function useUserSession(): UseUserSessionResult {
  // Đọc thẳng từ kho lúc dựng: mở lại tab mà token còn thì không bắt đăng nhập lại.
  // Token có thể đã hết hạn — chỗ đó lộ ra ở lần gọi API đầu tiên (401), chưa cần gọi
  // `/auth/me` để kiểm khi chưa trang nào hiển thị thông tin tài khoản.
  const [isLoggedIn, setIsLoggedIn] = useState(() => readToken() !== null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(
    async (username: string, password: string, remember: boolean) => {
      setLoading(true);
      setError(null);
      try {
        // Cắt khoảng trắng thừa ở tên đăng nhập (hay dính khi copy/paste). KHÔNG đụng
        // vào mật khẩu: khoảng trắng ở đó có thể là ký tự người dùng cố ý đặt.
        const data = await authApi.login({ username: username.trim(), password });
        writeToken(data.token, remember);
        setIsLoggedIn(true);
      } catch (err) {
        setError(authErrorMessage(err));
        setIsLoggedIn(false);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const register = useCallback(
    async (
      username: string,
      password: string,
      displayName: string,
      email: string,
    ) => {
      setLoading(true);
      setError(null);
      try {
        const ten = displayName.trim();
        const hopThu = email.trim();
        const data = await authApi.register({
          username: username.trim(),
          password,
          // Bỏ trống -> gửi `null`. Chuỗi rỗng sẽ được backend hiểu là "có khai email"
          // rồi ném lỗi định dạng, dù người dùng cố tình không muốn khai.
          email: hopThu === '' ? null : hopThu,
          // Bỏ trống thì gửi `null` chứ không gửi chuỗi rỗng: backend hiểu `null` là
          // "không có tên hiển thị" và sẽ dùng tên đăng nhập, còn chuỗi rỗng sẽ thành
          // một cái tên trống rỗng hiện ra màn hình.
          display_name: ten === '' ? null : ten,
        });
        // Đăng ký xong lưu phiên TẠM (sessionStorage): form đăng ký không có ô "ghi nhớ",
        // và mặc định nhớ lâu trên máy người khác là quyết định thay người dùng.
        writeToken(data.token, false);
        setIsLoggedIn(true);
      } catch (err) {
        setError(authErrorMessage(err));
        setIsLoggedIn(false);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const logout = useCallback(() => {
    // Backend CỐ TÌNH không có `/auth/logout`: token HMAC là stateless, server không giữ
    // danh sách token đang sống nên không có gì để xoá. Đăng xuất = client bỏ token của
    // mình đi. Xem đầu file `src/presentation/api/routers/auth.py`.
    clearToken();
    setIsLoggedIn(false);
    setError(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { isLoggedIn, loading, error, login, register, logout, clearError };
}

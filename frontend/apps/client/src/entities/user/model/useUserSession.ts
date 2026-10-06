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
import { useCallback, useEffect, useRef, useState } from 'react';
import type { UserSelf } from '@/shared/api';
import { ApiError, accountErrorText, authApi } from '@/shared/api';
import { useT } from '@/shared/i18n';
import { TOKEN_KEY, clearToken, onSessionExpired, readToken, writeToken } from '@/shared/lib';

export interface UseUserSessionResult {
  isLoggedIn: boolean;
  /**
   * Tài khoản đang đăng nhập, hoặc `null` khi chưa đăng nhập / chưa hỏi xong.
   *
   * `isLoggedIn` bật lên NGAY khi thấy token trong storage, còn `user` phải đợi một vòng
   * mạng. Hai thứ tách nhau có chủ đích: giao diện hiện được ngay phần "đã đăng nhập" mà
   * không nhấp nháy, chỗ nào cần tên thì tự chờ.
   */
  user: UserSelf | null;
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
 * Chọn câu báo lỗi: `accountErrorText` (shared/api).
 *
 * Ưu tiên `message` của backend, KHÔNG dùng câu soạn sẵn theo mã: câu đó viết cho luồng
 * tìm quán, nên với tài khoản nó nói sai hẳn — `UNAUTHORIZED` ra "Phiên đăng nhập đã hết
 * hạn" (thực tế là gõ sai mật khẩu), `DATA_NOT_READY` ra "chưa nạp xong dữ liệu quán ăn"
 * (thực tế là chưa đặt MOODBITE_AUTH_SECRET). Riêng `NETWORK` thì `message` là "Failed to
 * fetch" → dùng câu đã dịch theo ngôn ngữ đang chọn.
 */
export function useUserSession(): UseUserSessionResult {
  // Đọc thẳng từ kho lúc dựng: mở lại tab mà token còn thì không bắt đăng nhập lại.
  // Token có thể đã hết hạn — chỗ đó lộ ra ở lần gọi API đầu tiên (401), chưa cần gọi
  // `/auth/me` để kiểm khi chưa trang nào hiển thị thông tin tài khoản.
  const [isLoggedIn, setIsLoggedIn] = useState(() => readToken() !== null);
  const [user, setUser] = useState<UserSelf | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const t = useT();
  const tRef = useRef(t);
  tRef.current = t;

  /**
   * Mở lại tab mà token còn -> hỏi backend xem mình là ai.
   *
   * Chỉ chạy khi CÓ token và CHƯA biết tên: đăng nhập/đăng ký đã trả sẵn `user` nên không
   * cần hỏi thêm một vòng nữa.
   *
   * Token hỏng/hết hạn (401) -> xoá luôn. Đây cũng chính là chỗ phát hiện token quá hạn,
   * thứ mà trước đây chưa có gì kiểm.
   */
  useEffect(() => {
    if (!isLoggedIn || user !== null) return;
    let con_hieu_luc = true;

    authApi
      .me()
      .then((data) => {
        if (con_hieu_luc) setUser(data);
      })
      .catch((err) => {
        if (!con_hieu_luc) return;
        if (err instanceof ApiError && err.code === 'UNAUTHORIZED') {
          clearToken();
          setIsLoggedIn(false);
        }
        // Lỗi mạng thì KHÔNG đăng xuất: mất mạng tạm thời không có nghĩa là token hỏng.
      });

    return () => {
      con_hieu_luc = false;
    };
  }, [isLoggedIn, user]);

  /**
   * ĐĂNG XUẤT CỤC BỘ khi phiên chết GIỮA CHỪNG (2026-10-06):
   *   - một request `/me/*` hay `/auth/*` nhận 401 → `shared/lib/sessionExpiry` đã xoá
   *     token, ở đây chỉ dọn state;
   *   - tab KHÁC đăng xuất / đăng nhập (sự kiện `storage`, chỉ bắn cho localStorage ở
   *     các tab khác) → đồng bộ theo kho token.
   */
  useEffect(() => {
    const dangXuatCucBo = () => {
      setUser(null);
      setIsLoggedIn(false);
    };
    const boLang = onSessionExpired(dangXuatCucBo);
    const khiKhoDoi = (event: StorageEvent) => {
      // `key === null` = tab kia gọi `localStorage.clear()`.
      if (event.key !== null && event.key !== TOKEN_KEY) return;
      if (readToken() === null) {
        dangXuatCucBo();
      } else {
        // Tab kia đăng nhập (có thể tài khoản KHÁC) → hỏi lại `/auth/me`.
        setUser(null);
        setIsLoggedIn(true);
      }
    };
    window.addEventListener('storage', khiKhoDoi);
    return () => {
      boLang();
      window.removeEventListener('storage', khiKhoDoi);
    };
  }, []);

  const login = useCallback(
    async (username: string, password: string, remember: boolean) => {
      setLoading(true);
      setError(null);
      try {
        // Cắt khoảng trắng thừa ở tên đăng nhập (hay dính khi copy/paste). KHÔNG đụng
        // vào mật khẩu: khoảng trắng ở đó có thể là ký tự người dùng cố ý đặt.
        const data = await authApi.login({ username: username.trim(), password });
        writeToken(data.token, remember);
        setUser(data.user);
        setIsLoggedIn(true);
      } catch (err) {
        setError(accountErrorText(err, tRef.current));
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
          // Email BẮT BUỘC từ 2026-08-24 -> gửi thẳng chuỗi đã cắt khoảng trắng.
          // Bản cũ gửi `null` khi bỏ trống để backend hiểu là "cố tình không khai";
          // nay bỏ trống là LỖI, và backend trả 400 kèm câu giải thích cho người dùng.
          email: hopThu,
          // Bỏ trống thì gửi `null` chứ không gửi chuỗi rỗng: backend hiểu `null` là
          // "không có tên hiển thị" và sẽ dùng tên đăng nhập, còn chuỗi rỗng sẽ thành
          // một cái tên trống rỗng hiện ra màn hình.
          display_name: ten === '' ? null : ten,
        });
        // Đăng ký xong lưu phiên TẠM (sessionStorage): form đăng ký không có ô "ghi nhớ",
        // và mặc định nhớ lâu trên máy người khác là quyết định thay người dùng.
        writeToken(data.token, false);
        setUser(data.user);
        setIsLoggedIn(true);
      } catch (err) {
        setError(accountErrorText(err, tRef.current));
        setIsLoggedIn(false);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const logout = useCallback(() => {
    // Báo server THU HỒI token (mọi thiết bị - từ 2026-09-29). Gọi TRƯỚC `clearToken`:
    // `request` đọc token ngay lúc gọi, xoá trước thì server không biết thu hồi của ai.
    // KHÔNG đợi kết quả và nuốt lỗi: mất mạng hay token đã hết hạn thì người dùng vẫn
    // phải được đăng xuất khỏi máy này - chặn lại chỉ vì server không trả lời là sai.
    authApi.logout().catch(() => undefined);
    clearToken();
    setUser(null);
    setIsLoggedIn(false);
    setError(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { isLoggedIn, user, loading, error, login, register, logout, clearError };
}

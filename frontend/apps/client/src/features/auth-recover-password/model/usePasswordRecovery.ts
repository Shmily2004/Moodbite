/**
 * VIEWMODEL của luồng QUÊN MẬT KHẨU (hai bước, hai trang).
 *
 *   1. `/quen-mat-khau`     — gõ email/tên đăng nhập  -> backend gửi thư
 *   2. `/dat-lai-mat-khau`  — mở link trong thư       -> đặt mật khẩu mới
 *
 * VÌ SAO KHÔNG NẰM TRONG `entities/user` NHƯ PHIÊN ĐĂNG NHẬP: hai thao tác này KHÔNG đụng
 * tới phiên. Đổi mật khẩu xong người dùng vẫn chưa đăng nhập — cố tình như vậy, để đường
 * dẫn trong thư không trở thành một cách vào app mà không cần mật khẩu.
 */
import { useCallback, useState } from 'react';
import { ApiError, authApi } from '@/shared/api';

export type RecoveryStatus = 'idle' | 'loading' | 'sent' | 'done' | 'error';

export interface UsePasswordRecoveryResult {
  status: RecoveryStatus;
  /** Câu thông báo do BACKEND soạn — không tự chế ở frontend, xem ghi chú bên dưới. */
  message: string | null;
  error: string | null;
  requestReset: (identifier: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
}

/**
 * Chọn câu báo lỗi. Giống `entities/user`: ưu tiên câu của backend vì nó viết cho người
 * dùng đọc, chỉ riêng lỗi mạng mới dùng câu soạn sẵn (`message` khi đó là "Failed to
 * fetch", đọc không hiểu gì).
 */
function loiHienThi(err: unknown): string {
  if (err instanceof ApiError) {
    return err.code === 'NETWORK' ? err.userMessage : err.message;
  }
  return (err as Error).message;
}

export function usePasswordRecovery(): UsePasswordRecoveryResult {
  const [status, setStatus] = useState<RecoveryStatus>('idle');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const requestReset = useCallback(async (identifier: string) => {
    setStatus('loading');
    setError(null);
    try {
      const data = await authApi.forgotPassword({ identifier: identifier.trim() });
      // ⚠️ Hiển thị ĐÚNG câu backend trả về, không thay bằng "Đã gửi thư tới <email>".
      // Backend cố tình trả cùng một câu dù tài khoản có tồn tại hay không; viết lại câu
      // khẳng định hơn ở đây là làm hỏng chính chốt chặn chống dò tài khoản đó.
      setMessage(data.message);
      setStatus('sent');
    } catch (err) {
      setError(loiHienThi(err));
      setStatus('error');
    }
  }, []);

  const resetPassword = useCallback(async (token: string, newPassword: string) => {
    setStatus('loading');
    setError(null);
    try {
      const data = await authApi.resetPassword({ token, new_password: newPassword });
      setMessage(data.message);
      setStatus('done');
    } catch (err) {
      setError(loiHienThi(err));
      setStatus('error');
    }
  }, []);

  return { status, message, error, requestReset, resetPassword };
}

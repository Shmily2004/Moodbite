/**
 * VIEWMODEL của luồng XÁC MINH EMAIL.
 *
 *   1. đăng ký có khai email  -> backend tự gửi thư
 *   2. `/verify-email?token=` -> mở link trong thư, trang TỰ xác nhận, không cần bấm gì
 *   3. `/account`             -> xem trạng thái, bấm gửi lại thư nếu cần
 *
 * VÌ SAO TỰ CHẠY KHI MỞ TRANG thay vì bắt bấm một nút "Xác nhận": người dùng vừa bấm vào
 * đường dẫn trong thư rồi — đó CHÍNH LÀ hành động xác nhận. Bắt bấm thêm một lần nữa chỉ
 * tạo thêm một chỗ để bỏ cuộc giữa chừng.
 *
 * VÌ SAO KHÔNG ĐỤNG TỚI PHIÊN ĐĂNG NHẬP: xác minh email KHÔNG phải là đăng nhập. Nếu
 * trang này tự phát phiên thì đường dẫn trong thư trở thành một cách vào app mà không
 * cần mật khẩu — đúng điều mà luồng đặt lại mật khẩu đã cẩn thận tránh.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, authApi } from '@/shared/api';

export type VerifyStatus = 'idle' | 'loading' | 'done' | 'error';

export interface UseEmailVerificationResult {
  status: VerifyStatus;
  /** Câu do BACKEND soạn. Không tự chế ở frontend — xem ghi chú ở `usePasswordRecovery`. */
  message: string | null;
  error: string | null;
  /** Email vừa xác minh xong, để hiện lại cho người dùng thấy đúng địa chỉ nào. */
  email: string | null;
  resend: () => Promise<void>;
}

function loiHienThi(err: unknown): string {
  if (err instanceof ApiError) {
    return err.code === 'NETWORK' ? err.userMessage : err.message;
  }
  return (err as Error).message;
}

/**
 * @param token Lấy từ query string. Chuỗi rỗng = mở trang thẳng, không qua thư.
 */
export function useEmailVerification(token: string): UseEmailVerificationResult {
  const [status, setStatus] = useState<VerifyStatus>(token ? 'loading' : 'idle');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);

  // React 18 StrictMode chạy effect HAI LẦN ở môi trường phát triển. Không chặn thì lần
  // gọi thứ hai luôn thất bại — token chỉ dùng được một lần — và người dùng thấy
  // "đường dẫn đã dùng rồi" ngay ở lần đầu tiên họ bấm vào. Lỗi này rất dễ tưởng là bug
  // của backend.
  const daGoi = useRef(false);

  useEffect(() => {
    if (!token || daGoi.current) return;
    daGoi.current = true;

    let conHieuLuc = true;
    void (async () => {
      try {
        const nguoiDung = await authApi.confirmEmailVerification({ token });
        if (!conHieuLuc) return;
        setEmail(nguoiDung.email ?? null);
        setMessage('Đã xác minh email. Từ giờ bạn lấy lại được mật khẩu qua email.');
        setStatus('done');
      } catch (err) {
        if (!conHieuLuc) return;
        setError(loiHienThi(err));
        setStatus('error');
      }
    })();

    return () => {
      conHieuLuc = false;
    };
  }, [token]);

  const resend = useCallback(async () => {
    setStatus('loading');
    setError(null);
    try {
      const data = await authApi.requestEmailVerification();
      setMessage(data.message);
      setStatus('idle');
    } catch (err) {
      setError(loiHienThi(err));
      setStatus('error');
    }
  }, []);

  return { status, message, error, email, resend };
}

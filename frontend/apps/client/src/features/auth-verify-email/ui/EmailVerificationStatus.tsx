/**
 * VIEW của luồng xác minh email. Chỉ JSX — không gọi API, không giữ state.
 *
 * Dùng ở HAI chỗ với hai dáng khác nhau:
 *   - trang `/verify-email` (`variant="page"`)   — báo kết quả sau khi mở link trong thư
 *   - trang `/account`      (`variant="inline"`) — một dòng trạng thái + nút gửi lại
 */
import type { ReactNode } from 'react';
import type { VerifyStatus } from '../model/useEmailVerification';

export interface EmailVerificationStatusProps {
  status: VerifyStatus;
  message: string | null;
  error: string | null;
  /** Đã xác minh chưa. Ở dáng `inline` đây là thứ quyết định hiện nút gửi lại hay không. */
  verified: boolean;
  /** Có email để mà xác minh không. Không có thì không hiện nút gửi lại. */
  hasEmail: boolean;
  variant?: 'page' | 'inline';
  onResend?: () => void;
  footer?: ReactNode;
}

export function EmailVerificationStatus({
  status,
  message,
  error,
  verified,
  hasEmail,
  variant = 'page',
  onResend,
  footer,
}: EmailVerificationStatusProps) {
  const dangChay = status === 'loading';

  return (
    <div className={variant === 'page' ? 'xac-minh-email' : 'xac-minh-email xac-minh-email--gon'}>
      {variant === 'page' && <h1>Xác minh email</h1>}

      {dangChay && <p role="status">Đang xác minh…</p>}

      {/* Lỗi hiện TRƯỚC thông báo: khi cả hai cùng có, cái người dùng cần biết là lỗi. */}
      {error && (
        <p role="alert" className="xac-minh-email__loi">
          {error}
        </p>
      )}

      {!error && message && (
        <p role="status" className="xac-minh-email__ok">
          {message}
        </p>
      )}

      {variant === 'inline' && !message && !error && (
        <p className="xac-minh-email__trang-thai">
          {!hasEmail
            ? 'Chưa khai email — thêm email để lấy lại mật khẩu khi cần.'
            : verified
              ? '✓ Email đã xác minh'
              : 'Email chưa xác minh'}
        </p>
      )}

      {/* Chỉ hiện nút khi THỰC SỰ có việc để làm: có email và chưa xác minh. */}
      {onResend && hasEmail && !verified && (
        <button type="button" onClick={onResend} disabled={dangChay}>
          {dangChay ? 'Đang gửi…' : 'Gửi lại thư xác minh'}
        </button>
      )}

      {footer && <p className="xac-minh-email__chan">{footer}</p>}
    </div>
  );
}

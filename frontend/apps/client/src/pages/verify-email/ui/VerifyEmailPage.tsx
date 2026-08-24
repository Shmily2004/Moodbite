/**
 * Trang XÁC MINH EMAIL — mở từ đường dẫn trong thư.
 *
 * Token nằm ở query string `?token=...`. Đọc bằng `useSearchParams` của react-router chứ
 * không tự cắt chuỗi từ `window.location`: token là chuỗi base64url có thể chứa ký tự
 * cần mã hoá URL — đúng lý do đã ghi ở `ResetPasswordPage`.
 */
import { Link, useSearchParams } from 'react-router-dom';
import { AuthLayout } from '@/widgets/auth-layout';
import { EmailVerificationStatus, useEmailVerification } from '@/features/auth-verify-email';
import { Slogan } from '@/shared/ui';
import { ROUTES } from '@/shared/config';

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const xacMinh = useEmailVerification(token);

  return (
    <AuthLayout
      heading={<Slogan />}
      intro="Xác minh xong là bạn lấy lại được mật khẩu qua email khi cần."
    >
      <EmailVerificationStatus
        status={xacMinh.status}
        message={xacMinh.message}
        // Mở trang thẳng (không qua thư) thì nói rõ, đừng để trang trắng.
        error={
          token === ''
            ? 'Đường dẫn thiếu mã xác minh. Hãy mở lại đúng đường dẫn trong thư.'
            : xacMinh.error
        }
        verified={xacMinh.status === 'done'}
        hasEmail
        variant="page"
        footer={
          <>
            {xacMinh.status === 'done' ? 'Xong rồi! ' : ''}
            <Link to={ROUTES.home}>Về trang chủ</Link>
            {' · '}
            <Link to={ROUTES.account}>Trang tài khoản</Link>
          </>
        }
      />
    </AuthLayout>
  );
}

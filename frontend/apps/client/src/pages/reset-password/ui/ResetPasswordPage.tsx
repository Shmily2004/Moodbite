/**
 * Trang ĐẶT MẬT KHẨU MỚI (bước 2) — mở từ đường dẫn trong thư.
 *
 * Token nằm ở query string `?token=...`. Đọc bằng `useSearchParams` của react-router chứ
 * không tự cắt chuỗi từ `window.location`: cách đó bỏ sót mọi thứ về mã hoá URL, mà token
 * là chuỗi base64url có thể chứa ký tự cần mã hoá.
 */
import { Link, useSearchParams } from 'react-router-dom';
import { AuthLayout } from '@/widgets/auth-layout';
import { ResetPasswordForm, usePasswordRecovery } from '@/features/auth-recover-password';
import { Slogan } from '@/shared/ui';
import { ROUTES } from '@/shared/config';

export function ResetPasswordPage() {
  const recovery = usePasswordRecovery();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';

  return (
    <AuthLayout
      heading={<Slogan />}
      intro="Đặt mật khẩu mới xong là quay lại khám phá món ngon Hà Nội thôi."
    >
      <ResetPasswordForm
        loading={recovery.status === 'loading'}
        error={recovery.error}
        message={recovery.message}
        hasToken={token !== ''}
        onSubmit={(newPassword) => void recovery.resetPassword(token, newPassword)}
        footer={
          <>
            {recovery.status === 'done' ? 'Xong rồi! ' : 'Đổi ý? '}
            <Link to={ROUTES.login}>Về trang đăng nhập</Link>
          </>
        }
      />
    </AuthLayout>
  );
}

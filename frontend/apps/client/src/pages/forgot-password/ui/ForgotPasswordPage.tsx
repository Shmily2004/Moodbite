/**
 * Trang QUÊN MẬT KHẨU (bước 1) — chỉ nối khung, VIEW và VIEWMODEL.
 *
 * Dùng lại tranh của trang đăng nhập: đây là nhánh rẽ ra từ đó, đổi tranh chỉ làm người
 * dùng tưởng mình lạc sang chỗ khác.
 */
import { Link } from 'react-router-dom';
import { AuthLayout } from '@/widgets/auth-layout';
import { ForgotPasswordForm, usePasswordRecovery } from '@/features/auth-recover-password';
import { Slogan } from '@/shared/ui';
import { ROUTES } from '@/shared/config';

export function ForgotPasswordPage() {
  const recovery = usePasswordRecovery();

  return (
    <AuthLayout
      heading={<Slogan />}
      intro="Đừng lo, chuyện quên mật khẩu ai cũng gặp. Lấy lại chỉ mất một phút."
    >
      <ForgotPasswordForm
        loading={recovery.status === 'loading'}
        error={recovery.error}
        message={recovery.message}
        onSubmit={(identifier) => void recovery.requestReset(identifier)}
        footer={
          <>
            Nhớ ra rồi? <Link to={ROUTES.login}>Đăng nhập ngay</Link>
          </>
        }
      />
    </AuthLayout>
  );
}

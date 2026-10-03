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
import { useT } from '@/shared/i18n';

export function ForgotPasswordPage() {
  const recovery = usePasswordRecovery();
  const t = useT();

  return (
    <AuthLayout
      heading={<Slogan />}
      intro={t('forgot.intro')}
    >
      <ForgotPasswordForm
        loading={recovery.status === 'loading'}
        error={recovery.error}
        message={recovery.message}
        onSubmit={(identifier) => void recovery.requestReset(identifier)}
        footer={
          <>
            {t('forgot.remembered')} <Link to={ROUTES.login}>{t('register.loginNow')}</Link>
          </>
        }
      />
    </AuthLayout>
  );
}

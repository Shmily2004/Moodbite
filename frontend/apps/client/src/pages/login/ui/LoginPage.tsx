/**
 * Trang đăng nhập — tầng `pages`: chỉ NỐI khung (`AuthLayout`), VIEW (`LoginForm`) và
 * VIEWMODEL (`useUserSessionContext`) lại với nhau. Không có logic riêng.
 *
 * ⚠️ ĐĂNG NHẬP LÀ TUỲ CHỌN, không phải cửa vào bắt buộc: tìm quán và xem món vẫn chạy
 * khi chưa có tài khoản (SRS coi tài khoản là phần mở rộng). Vì vậy KHÔNG có route guard
 * nào chặn trang chủ, và trang này không tự bật lên.
 */
import { Link, Navigate, useLocation } from 'react-router-dom';
import { AuthLayout } from '@/widgets/auth-layout';
import { LoginForm } from '@/features/auth-login';
import { Slogan } from '@/shared/ui';
import { useUserSessionContext } from '@/entities/user';
import { ROUTES } from '@/shared/config';
import { useT } from '@/shared/i18n';

interface LocationState {
  from?: string;
}

export function LoginPage() {
  const session = useUserSessionContext();
  const location = useLocation();
  const t = useT();

  if (session.isLoggedIn) {
    // Đã đăng nhập mà vẫn mở /dang-nhap -> đưa về nơi định đến, không hiện lại form.
    const from = (location.state as LocationState | null)?.from;
    return <Navigate to={from || ROUTES.home} replace />;
  }

  return (
    <AuthLayout
      // Tiêu đề là ẢNH chứ không phải chữ — xem `shared/ui/Slogan`.
      heading={<Slogan />}
      intro={t('login.intro')}
    >
      <LoginForm
        loading={session.loading}
        error={session.error}
        onSubmit={(username, password, remember) =>
          void session.login(username, password, remember)
        }
        footer={
          <>
            {t('login.noAccount')} <Link to={ROUTES.register}>{t('login.registerNow')}</Link>
          </>
        }
      />
    </AuthLayout>
  );
}

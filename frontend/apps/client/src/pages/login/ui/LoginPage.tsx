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
import { LoginForm, quanTriSauDangNhap } from '@/features/auth-login';
import { Slogan } from '@/shared/ui';
import { useUserSessionContext } from '@/entities/user';
import { QUAN_TRI_ROUTES, coPhienQuanTri } from '@moodbite/admin';
import { ROUTES } from '@/shared/config';
import { useT } from '@/shared/i18n';
import { safeInternalPath } from '@/shared/lib';

interface LocationState {
  from?: string;
}

export function LoginPage() {
  const session = useUserSessionContext();
  const location = useLocation();
  const t = useT();

  // Chỉ nhận đường dẫn NỘI BỘ: react-router v6 dính open redirect qua `\`
  // (GHSA-wrjc-x8rr-h8h6) và không có bản vá cho v6 — xem `safeInternalPath`.
  const from = safeInternalPath((location.state as LocationState | null)?.from);
  // Vào khu quản trị mà THIẾU phiên quản trị trên máy này thì hiện form, KHÔNG tự chuyển
  // đi — nếu không sẽ lặp: khu quản trị đá về đây, đây lại đá vào khu quản trị.
  const vaoQuanTriDuoc = !from?.startsWith(QUAN_TRI_ROUTES.overview) || coPhienQuanTri();

  if (session.isLoggedIn && vaoQuanTriDuoc) {
    // Đã đăng nhập mà vẫn mở /login -> đưa về nơi định đến, không hiện lại form.
    // Tài khoản admin VÀO THẲNG khu quản trị, không qua trang chủ rồi bấm nút "Quản trị".
    // Chỉ tôn trọng `from` khi nó đã là một trang quản trị: nếu không, admin vừa đăng nhập
    // từ một trang khách (ví dụ /tim-kiem đá sang đăng nhập) sẽ bị đưa ngược ra ngoài.
    const noiDen = session.user?.role === 'admin'
      ? (from?.startsWith(QUAN_TRI_ROUTES.overview) ? from : QUAN_TRI_ROUTES.overview)
      : (from ?? ROUTES.home);
    return <Navigate to={noiDen} replace />;
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
          void session.login(
            username,
            password,
            remember,
            quanTriSauDangNhap(username, password),
          )
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

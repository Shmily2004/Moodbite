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
import { useUserSessionContext } from '@/entities/user';
import { ROUTES } from '@/shared/config';

interface LocationState {
  from?: string;
}

export function LoginPage() {
  const session = useUserSessionContext();
  const location = useLocation();

  if (session.isLoggedIn) {
    // Đã đăng nhập mà vẫn mở /dang-nhap -> đưa về nơi định đến, không hiện lại form.
    const from = (location.state as LocationState | null)?.from;
    return <Navigate to={from || ROUTES.home} replace />;
  }

  return (
    <AuthLayout
      heading={
        <>
          Ăn gì ở Hà Nội,
          <br />
          tùy <em className="auth__accent">mood</em> của bạn.
        </>
      }
      intro="MoodBite gợi ý những món ăn phù hợp với cảm xúc, thời tiết và thời điểm của bạn."
    >
      <LoginForm
        loading={session.loading}
        error={session.error}
        onSubmit={(username, password, remember) =>
          void session.login(username, password, remember)
        }
        footer={
          <>
            Chưa có tài khoản? <Link to={ROUTES.register}>Đăng ký ngay</Link>
          </>
        }
      />
    </AuthLayout>
  );
}

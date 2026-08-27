/**
 * Trang đăng nhập — tầng `pages`: nối VIEW (`LoginForm`) với VIEWMODEL (session).
 *
 * Đăng nhập xong tự quay lại đúng trang người dùng định vào trước đó.
 */
import { Navigate, useLocation } from 'react-router-dom';
import { LoginForm, useAdminSessionContext } from '@/features/admin-login';
import { ROUTES } from '@/shared/config';

interface LocationState {
  from?: string;
}

export function LoginPage() {
  const session = useAdminSessionContext();
  const location = useLocation();

  if (session.isLoggedIn) {
    // Đã đăng nhập mà vẫn mở /login -> đẩy về nơi định đến, không hiện lại form.
    //
    // Đích MẶC ĐỊNH là TỔNG QUAN (đổi 2026-08-26). Trước đó là danh sách quán, nên đăng
    // nhập xong đập thẳng vào bảng 52.854 dòng thay vì màn số liệu vận hành.
    const from = (location.state as LocationState | null)?.from;
    return <Navigate to={from || ROUTES.overview} replace />;
  }

  return (
    <div className="shell shell--centered">
      <LoginForm
        loading={session.loading}
        error={session.error}
        onSubmit={(username, password) => void session.login(username, password)}
      />
    </div>
  );
}

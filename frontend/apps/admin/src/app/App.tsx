/**
 * Gốc app quản trị.
 *
 * Chưa dùng router: app chỉ có hai trạng thái (chưa đăng nhập / đã đăng nhập). Thêm
 * `react-router` lúc này là phức tạp hoá mà không được gì.
 */
import { LoginForm, useAdminSession } from '@/features/admin-login';
import { RestaurantsPage } from '@/pages/restaurants';
import './styles.css';

export function App() {
  const session = useAdminSession();

  if (!session.isLoggedIn) {
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

  return (
    <div className="shell">
      <RestaurantsPage onExpired={session.handleExpired} onLogout={session.logout} />
    </div>
  );
}

/**
 * LAYOUT của app quản trị — khung dùng chung cho mọi trang SAU KHI đăng nhập.
 *
 * Thanh trên cùng (điều hướng + nút đăng xuất) nằm ở đây chứ không nằm trong từng trang:
 * thêm trang mới là tự có luôn, không phải chép lại và không sợ mỗi trang một kiểu.
 */
import { NavLink, Outlet } from 'react-router-dom';
import { useAdminSessionContext } from '@/features/admin-login';
import { ROUTES } from '@/shared/config';

export function AdminLayout() {
  const session = useAdminSessionContext();

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <h1>MoodBite — Quản trị</h1>
          <nav className="nav">
            {/* NavLink tự gắn class khi đang ở đúng trang -> người dùng biết mình ở đâu. */}
            <NavLink
              to={ROUTES.restaurants}
              end
              className={({ isActive }) => (isActive ? 'nav__link nav__link--active' : 'nav__link')}
            >
              Quán ăn
            </NavLink>
          </nav>
        </div>
        <button className="ghost" onClick={session.logout}>
          Đăng xuất
        </button>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  );
}

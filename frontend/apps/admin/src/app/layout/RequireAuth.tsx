/**
 * CHỐT CHẶN ĐỊNH TUYẾN: chưa đăng nhập thì không vào được trang quản trị.
 *
 * ⚠️ Đây CHỈ là lớp phòng vệ thứ hai, cho trải nghiệm người dùng. Chốt chặn THẬT nằm ở
 * backend (`require_admin` trong `dependencies.py`) — không có token thì mọi endpoint
 * `/api/v1/admin/*` trả 401, dù giao diện có vẽ ra gì đi nữa.
 * Tuyệt đối không được coi phần này là bảo mật.
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAdminSessionContext } from '@/features/admin-login';
import { ROUTES } from '@/shared/config';

export function RequireAuth() {
  const session = useAdminSessionContext();
  const location = useLocation();

  if (!session.isLoggedIn) {
    // `state.from`: đăng nhập xong quay lại đúng trang đang định vào, thay vì luôn về
    // trang chủ. `replace` để nút Back không kẹt trong vòng lặp chuyển hướng.
    return <Navigate to={ROUTES.login} replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

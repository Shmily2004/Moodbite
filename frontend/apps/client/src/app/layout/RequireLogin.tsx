/**
 * CHỐT CHẶN ĐỊNH TUYẾN CỦA APP NGƯỜI DÙNG: chưa đăng nhập thì không vào được các trang
 * bên trong (món, quán, tìm kiếm, tài khoản...). Chỉ đăng nhập, đăng ký và quên/đặt lại
 * mật khẩu là mở cho khách.
 *
 * Chốt 2026-11-10 theo `docs/UI_REQUIREMENTS.md` ("Khách phải đăng nhập mới dùng được
 * app"). Trước đó app cho khách xem và lưu trên máy — bỏ đi vì lưu trên máy không có ý
 * nghĩa khi đổi máy là mất.
 *
 * ⚠️ Đây CHỈ là lớp phòng vệ phía giao diện. Các endpoint `/api/v1/search`, `/dishes/*`,
 * `/restaurants/*` hiện vẫn công khai ở backend — người gọi API trực tiếp vẫn lấy được dữ
 * liệu. Muốn chặn thật phải thêm xác thực ở backend (việc đó đổi hợp đồng API, cần chủ dự
 * án duyệt riêng).
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useUserSessionContext } from '@/entities/user';
import { ROUTES } from '@/shared/config';

export function RequireLogin() {
  const session = useUserSessionContext();
  const location = useLocation();

  if (!session.isLoggedIn) {
    // `state.from`: đăng nhập xong quay lại đúng trang đang định vào. `replace` để nút Back
    // không kẹt trong vòng lặp chuyển hướng.
    return (
      <Navigate
        to={ROUTES.login}
        replace
        state={{ from: `${location.pathname}${location.search}` }}
      />
    );
  }

  return <Outlet />;
}

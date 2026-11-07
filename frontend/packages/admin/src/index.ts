/**
 * Khu QUẢN TRỊ — public API cho app người dùng (`apps/client`).
 *
 * App người dùng chỉ cần 3 thứ: gắn route vào router, đăng nhập quản trị khi tài khoản là
 * admin, và xoá phiên quản trị khi đăng xuất. Mọi chi tiết khác giữ kín trong package này.
 */
import './app/styles.css';

export { quanTriRoutes } from './app/routes';
export { ROUTES as QUAN_TRI_ROUTES } from './shared/config';
export {
  dangNhapQuanTri,
  coPhienQuanTri,
  xoaPhienQuanTri,
  PHAT_DANG_XUAT_KHACH,
} from './features/admin-login';

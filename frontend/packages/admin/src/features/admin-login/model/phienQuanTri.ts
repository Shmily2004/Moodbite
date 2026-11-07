/**
 * Lấy và xoá PHIÊN QUẢN TRỊ, dùng chung cho app người dùng (trang đăng nhập chung).
 *
 * Tài khoản admin đăng nhập ở `/login` như mọi người. Backend tách hai loại token: token
 * khách (`/auth/login`) không gọi được `/admin/*`. Nên sau khi đăng nhập khách thành công
 * với vai trò admin, app gọi thêm `dangNhapQuanTri` cùng mật khẩu để lấy token quản trị.
 * Cách này không đổi xác thực phía server.
 */
import { adminApi } from '@admin/shared/api';
import { writeToken, clearToken, readToken } from '@admin/shared/lib';

/** Tên sự kiện: app quản trị phát ra khi đăng xuất, app người dùng lắng nghe để đăng xuất theo. */
export const PHAT_DANG_XUAT_KHACH = 'moodbite:dang-xuat-khach';

/**
 * Đổi tên + mật khẩu lấy token quản trị và lưu lại. Lỗi (sai mật khẩu, máy chủ chưa cấu
 * hình quản trị 503...) được NÉM RA để người gọi báo đúng câu của backend.
 */
export async function dangNhapQuanTri(username: string, password: string): Promise<void> {
  const data = await adminApi.login({ username, password });
  writeToken(data.token);
}

/** Máy này đã có token quản trị chưa. Dùng để biết có cần đăng nhập quản trị lại không. */
export function coPhienQuanTri(): boolean {
  return readToken() !== null;
}

/** Xoá token quản trị ở máy này. Không gọi server (việc đó do khu quản trị lo khi đăng xuất). */
export function xoaPhienQuanTri(): void {
  clearToken();
}

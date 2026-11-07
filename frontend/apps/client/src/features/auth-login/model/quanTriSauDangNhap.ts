/**
 * Bước PHỤ sau khi đăng nhập khách thành công: tài khoản admin lấy thêm phiên quản trị.
 *
 * Vì sao cần: backend tách hai loại token. Token khách không gọi được `/admin/*`, nên
 * tài khoản admin phải có thêm token quản trị lấy từ `/admin/login` bằng cùng mật khẩu.
 * Tài khoản thường thì không làm gì cả.
 *
 * Nếu bước này thất bại (sai mật khẩu quản trị, máy chủ chưa cấu hình quản trị...) thì lỗi
 * được NÉM RA và phiên khách KHÔNG được lưu: admin không vào được app khách một nửa.
 */
import { dangNhapQuanTri } from '@moodbite/admin';
import type { UserSelf } from '@/shared/api';

export function quanTriSauDangNhap(username: string, password: string) {
  return async (user: UserSelf): Promise<void> => {
    if (user.role !== 'admin') return;
    await dangNhapQuanTri(username.trim(), password);
  };
}

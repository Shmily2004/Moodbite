/**
 * Đường dẫn của app quản trị, khai ở MỘT chỗ duy nhất.
 *
 * VÌ SAO Ở `shared/` CHỨ KHÔNG Ở `app/`: cả `app/` (đăng ký route, chuyển hướng) lẫn
 * `pages/` (link qua lại) đều cần. Luật FSD chỉ cho import đi XUỐNG, nên nếu để ở
 * `app/` thì `pages/` sẽ phải import ngược lên — `steiger` chặn ngay.
 *
 * Đặt ở đây rồi thì đổi đường dẫn chỉ sửa một chỗ, không phải đi tìm chuỗi '/login'
 * rải rác trong code.
 */
export const ROUTES = {
  login: '/login',
  restaurants: '/',
} as const;

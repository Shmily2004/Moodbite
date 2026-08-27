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
  // Trang chủ khu quản trị = TỔNG QUAN (đổi 2026-08-26 theo `design/Dashboard admin.png`).
  // Trước đó `/` là danh sách quán; đăng nhập xong đập ngay vào một bảng 52.854 dòng.
  overview: '/',
  restaurants: '/quan-an',
  dishes: '/mon-an',
  recommendation: '/goi-y',
  activity: '/nhat-ky',
  system: '/cai-dat',
} as const;

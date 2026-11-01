/**
 * Cấu hình đọc từ biến môi trường. MỘT nơi duy nhất - không rải `import.meta.env`
 * khắp nơi, vì khi đổi tên biến sẽ phải đi tìm từng chỗ.
 */
export const API_BASE: string =
  import.meta.env.VITE_API_BASE ?? 'http://localhost:8001/api/v1';

/**
 * Địa chỉ app QUẢN TRỊ. Tài khoản admin đăng nhập ở app này sẽ được chỉ sang đó, vì app
 * người dùng không có việc gì cho quản trị viên (xem `pages/account`).
 */
export const ADMIN_APP_URL: string =
  import.meta.env.VITE_ADMIN_URL ?? 'http://localhost:5174';

/** Hồ Hoàn Kiếm - phải khớp HANOI_CENTER ở src/domain/value_objects/location.py */
export const HANOI_CENTER = { lat: 21.0285, lng: 105.8542 } as const;

export const DEFAULT_SEARCH_LIMIT = 10;
export const DEFAULT_RADIUS_KM = 10;

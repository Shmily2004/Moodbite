/**
 * Đường dẫn của app, khai ở MỘT chỗ.
 *
 * VÌ SAO Ở `shared/config` MÀ KHÔNG PHẢI `app/routes.tsx`: luật import của FSD chỉ cho đi
 * XUỐNG (pages -> widgets -> features -> entities -> shared). Trang chi tiết món cần biết
 * đường về trang chủ, mà `pages` thì KHÔNG được import từ `app`. Đặt ở `shared` là chỗ duy
 * nhất mọi tầng đều với tới được.
 */
export const ROUTES = {
  home: '/',
  /** Chi tiết món. Tiếng Việt không dấu trên URL cho dễ đọc và dễ chia sẻ. */
  dish: '/mon/:dishId',
  login: '/dang-nhap',
  register: '/dang-ky',
  forgotPassword: '/quen-mat-khau',
  /**
   * Trang đặt mật khẩu mới. Đường dẫn này nằm TRONG THƯ gửi cho người dùng, do backend
   * dựng từ biến môi trường `MOODBITE_APP_URL` — xem `RequestPasswordResetUseCase`.
   * ⚠️ Đổi đường dẫn ở đây thì phải đổi cả bên đó, nếu không link trong thư sẽ ra 404.
   */
  resetPassword: '/dat-lai-mat-khau',
} as const;

/** Dựng đường dẫn tới một món cụ thể. Dùng hàm thay vì nối chuỗi tay để khỏi gõ sai. */
export function dishRoute(dishId: string): string {
  return `/mon/${encodeURIComponent(dishId)}`;
}

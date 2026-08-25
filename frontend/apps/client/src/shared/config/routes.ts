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
  /** Chi tiết món. `/dishes/pho-bo` — số nhiều theo thông lệ REST. */
  dish: '/dishes/:dishId',
  search: '/search',
  /**
   * Trang KẾT QUẢ GỢI Ý MÓN. Khác `search` (tìm QUÁN bằng câu tự nhiên + bản đồ).
   * Bộ lọc nằm trên query string — xem `pages/recommend/ui/boLocTuUrl.ts`.
   */
  recommend: '/recommend',
  login: '/login',
  register: '/register',
  forgotPassword: '/forgot-password',
  /**
   * Trang đặt mật khẩu mới. Đường dẫn này nằm TRONG THƯ gửi cho người dùng, do backend
   * dựng từ `MOODBITE_APP_URL` — xem `RequestPasswordResetUseCase`.
   * ⚠️ Đổi ở đây thì phải đổi cả bên đó, nếu không link trong thư sẽ ra 404.
   */
  resetPassword: '/reset-password',
  /**
   * Trang XÁC MINH EMAIL. Đường dẫn này nằm TRONG THƯ, do backend dựng từ
   * `MOODBITE_APP_URL` — xem `RequestEmailVerificationUseCase`.
   * ⚠️ Đổi ở đây thì phải đổi cả bên đó, nếu không link trong thư sẽ ra 404.
   */
  verifyEmail: '/verify-email',
  /** Trang tài khoản cá nhân. */
  account: '/account',
} as const;

/**
 * Đường dẫn CŨ (tiếng Việt) -> đường dẫn mới. Giữ để chuyển hướng, KHÔNG xoá.
 *
 * VÌ SAO PHẢI GIỮ: link `/dat-lai-mat-khau?token=…` đã nằm trong hộp thư của người dùng
 * từ trước khi đổi. Xoá thẳng là những lá thư đó chết, mà người nhận không hiểu vì sao.
 * Chuyển hướng giữ nguyên query string nên token vẫn đi kèm.
 *
 * Bỏ được bảng này khi chắc chắn không còn thư cũ nào còn hạn (token sống 30 phút, nên
 * thực tế là sau vài giờ kể từ lúc đổi).
 */
export const DUONG_DAN_CU: Record<string, string> = {
  '/mon/:dishId': '/dishes/:dishId',
  '/tim-kiem': '/search',
  '/dang-nhap': '/login',
  '/dang-ky': '/register',
  '/quen-mat-khau': '/forgot-password',
  '/dat-lai-mat-khau': '/reset-password',
};

/** Dựng đường dẫn tới một món cụ thể. Dùng hàm thay vì nối chuỗi tay để khỏi gõ sai. */
export function dishRoute(dishId: string): string {
  return `/dishes/${encodeURIComponent(dishId)}`;
}

/**
 * Endpoint TÀI KHOẢN NGƯỜI DÙNG CUỐI — `/api/v1/auth/*`.
 *
 * VÌ SAO LÀ LỚP RIÊNG, KHÔNG NHÉT VÀO `MoodbiteApi` HAY `MoodbiteAdminApi`:
 *
 * 1. `MoodbiteApi` là phần dùng được KHI CHƯA ĐĂNG NHẬP (tìm quán, xem món). Toàn bộ
 *    luồng chính của app vẫn chạy mà không cần tài khoản, và ranh giới đó nên nhìn
 *    thấy được ngay trong mã nguồn.
 * 2. `MoodbiteAdminApi` là tài khoản QUẢN TRỊ, dùng `/admin/login` và secret KHÁC
 *    (`MOODBITE_ADMIN_SECRET`). Gộp chung sẽ có ngày ai đó gửi token nhầm cửa.
 *
 * Cả ba lớp dùng chung `HttpClient`, nên quy ước envelope `{data}`/`{error}` vẫn chỉ
 * có đúng MỘT nơi định nghĩa.
 */
import type { components } from './schema';
import type { HttpClient, RequestOptions } from './http';

/** Kiểu lấy TRỰC TIẾP từ OpenAPI - không gõ tay, không lệch được với backend. */
export type LoginRequest = components['schemas']['LoginRequest'];
export type RegisterRequest = components['schemas']['RegisterRequest'];
export type ForgotPasswordRequest = components['schemas']['ForgotPasswordRequest'];
export type ResetPasswordRequest = components['schemas']['ResetPasswordRequest'];
/** Kết quả của các thao tác không trả về tài nguyên nào — chỉ một câu cho người dùng đọc. */
export type MessageData = components['schemas']['MessageData'];
export type AuthData = components['schemas']['AuthData'];
export type UserPublic = components['schemas']['UserPublic'];

export class MoodbiteAuthApi {
  constructor(private readonly http: HttpClient) {}

  /**
   * Đổi tài khoản/mật khẩu lấy token.
   *
   * Sai tên HAY sai mật khẩu đều trả CÙNG một lỗi 401 — backend cố tình không nói rõ
   * cái nào sai, để không thành công cụ dò xem tên nào đã tồn tại. Đừng "cải thiện"
   * thông báo lỗi ở frontend bằng cách đoán thêm.
   */
  login(body: LoginRequest, options?: RequestOptions): Promise<AuthData> {
    return this.http.request<AuthData>('/auth/login', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /**
   * Tạo tài khoản mới. Backend trả LUÔN token, nên đăng ký xong là vào thẳng app —
   * không bắt người dùng gõ lại tài khoản/mật khẩu ngay sau đó.
   *
   * Vai LUÔN là `user`: router không nhận trường `role` từ client. Đừng gửi lên.
   * Tên trùng -> 409 USERNAME_TAKEN. Sai định dạng -> 400 INVALID_REQUEST kèm câu nói rõ
   * sai chỗ nào (quy tắc nằm ở `src/domain/entities/user.py`, KHÔNG chép xuống frontend).
   */
  register(body: RegisterRequest, options?: RequestOptions): Promise<AuthData> {
    return this.http.request<AuthData>('/auth/register', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /**
   * Xin thư đặt lại mật khẩu. `identifier` là email HOẶC tên đăng nhập.
   *
   * ⚠️ LUÔN trả về cùng một câu, kể cả khi tài khoản không tồn tại — backend cố tình như
   * vậy để trang này không thành công cụ dò xem ai đã đăng ký. ĐỪNG "cải thiện" bằng cách
   * hiện thông báo khác nhau ở frontend.
   */
  forgotPassword(
    body: ForgotPasswordRequest,
    options?: RequestOptions,
  ): Promise<MessageData> {
    return this.http.request<MessageData>('/auth/forgot-password', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /**
   * Đổi mật khẩu bằng token lấy từ đường dẫn trong thư.
   *
   * Token hỏng / hết hạn / đã dùng -> 401. Đổi xong KHÔNG tự đăng nhập: người dùng phải
   * gõ mật khẩu mới một lần ở trang đăng nhập.
   */
  resetPassword(
    body: ResetPasswordRequest,
    options?: RequestOptions,
  ): Promise<MessageData> {
    return this.http.request<MessageData>('/auth/reset-password', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /**
   * Thông tin tài khoản đang đăng nhập. Cần `getAuthToken` khi tạo client.
   *
   * Dùng để biết mình là AI sau khi tải lại trang: token nằm trong storage nhưng tên hiển
   * thị thì không. Trả 401 nghĩa là token hết hạn/bị thu hồi — người gọi phải xoá token
   * chứ đừng thử lại.
   *
   * Vai (`role`) đọc từ CSDL ở mỗi lần gọi chứ không nằm trong token, nên admin vừa bị hạ
   * quyền sẽ thấy ngay ở lần gọi kế tiếp.
   */
  me(options?: RequestOptions): Promise<UserPublic> {
    return this.http.request<UserPublic>('/auth/me', options);
  }
}

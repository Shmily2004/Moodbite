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
export type ChangePasswordRequest = components['schemas']['ChangePasswordRequest'];
export type VerifyEmailRequest = components['schemas']['VerifyEmailRequest'];
/** Kết quả của các thao tác không trả về tài nguyên nào — chỉ một câu cho người dùng đọc. */
export type MessageData = components['schemas']['MessageData'];
export type AuthData = components['schemas']['AuthData'];
/**
 * Hồ sơ CHÍNH CHỦ: có thêm email, ngày tham gia và trạng thái xác minh email.
 *
 * Trả về bởi `/auth/me`, và từ 2026-08-24 cả `/auth/login` + `/auth/register` — người
 * nhận vừa chứng minh xong họ là chủ tài khoản. Không bao giờ chứa `password_hash`.
 *
 * `UserPublic` (bản rút gọn) đã BỎ khỏi tệp này vì không endpoint nào còn trả về nó;
 * giữ một kiểu không ai dùng chỉ tạo chỗ để chọn nhầm.
 */
export type UserSelf = components['schemas']['UserSelf'];
/** Một mục đã lưu: quán hoặc món. `item_type` là 'restaurant' | 'dish'. */
export type SavedItem = components['schemas']['SavedItemSchema'];
export type SaveFavoriteRequest = components['schemas']['SaveFavoriteRequest'];
export type FavoritesData = components['schemas']['FavoritesData'];
/** Số liệu hoạt động + cấp độ + huy hiệu của chính chủ. MỌI SỐ Ở ĐÂY LÀ SỐ ĐẾM THẬT. */
export type UserStatsData = components['schemas']['UserStatsData'];
export type BadgeData = components['schemas']['BadgeSchema'];

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
  /**
   * Đổi mật khẩu khi ĐANG đăng nhập. Khác `resetPassword` (dùng token trong thư).
   *
   * Vẫn phải gửi mật khẩu hiện tại dù đã có token — token nằm trong trình duyệt và sống
   * 24 giờ, ai mượn được máy là đổi được mật khẩu.
   * ⚠️ Đổi xong KHÔNG thu hồi token ở máy khác (token HMAC là stateless). Câu trả về của
   * server đã nói rõ điều này — hãy hiện nguyên văn cho người dùng.
   */
  changePassword(
    body: ChangePasswordRequest,
    options?: RequestOptions,
  ): Promise<MessageData> {
    return this.http.request<MessageData>('/auth/change-password', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /**
   * Gửi LẠI thư xác minh email cho tài khoản đang đăng nhập.
   *
   * Luôn trả 200 kèm một câu để hiện cho người dùng, kể cả khi không có gì để gửi
   * ("đã xác minh rồi", "chưa khai email"). Khác `forgotPassword`: ở đây người gọi đã
   * đăng nhập nên backend nói thẳng được, không phải giấu để chống dò tài khoản.
   */
  requestEmailVerification(options?: RequestOptions): Promise<MessageData> {
    return this.http.request<MessageData>('/auth/verify-email/request', {
      ...options,
      method: 'POST',
    });
  }

  /**
   * Xác nhận email bằng token trong thư. KHÔNG cần đăng nhập — người dùng hay mở thư ở
   * máy khác, bắt đăng nhập trước sẽ chặn đúng lúc họ vừa bấm vào link.
   *
   * Trả về hồ sơ chính chủ với `email_verified = true`.
   * Token hỏng / hết hạn / đã dùng / email đã đổi -> 401.
   */
  confirmEmailVerification(
    body: VerifyEmailRequest,
    options?: RequestOptions,
  ): Promise<UserSelf> {
    return this.http.request<UserSelf>('/auth/verify-email/confirm', {
      ...options,
      method: 'POST',
      body,
    });
  }

  me(options?: RequestOptions): Promise<UserSelf> {
    return this.http.request<UserSelf>('/auth/me', options);
  }

  // --- Quán & món đã lưu · cấp độ · huy hiệu (`/me/*`) ---------------------
  //
  // Không endpoint nào ở đây nhận `user_id`: server luôn lấy id từ token. Nhờ vậy
  // frontend KHÔNG THỂ vô tình (hay cố ý) đọc dữ liệu của người khác.

  /** Danh sách đã lưu, mới nhất đứng đầu. Bỏ `itemType` để lấy cả quán lẫn món. */
  favorites(
    itemType?: 'restaurant' | 'dish',
    options?: RequestOptions,
  ): Promise<FavoritesData> {
    const query = itemType ? `?item_type=${encodeURIComponent(itemType)}` : '';
    return this.http.request<FavoritesData>(`/me/favorites${query}`, options);
  }

  /**
   * Lưu một quán hoặc món.
   *
   * `name` là BẮT BUỘC và được chụp lại lúc lưu, để danh sách hiện được ngay mà không
   * phải gọi thêm một request tra tên cho từng mục.
   * Lưu lại thứ đã lưu KHÔNG lỗi — server cố tình làm idempotent.
   */
  saveFavorite(body: SaveFavoriteRequest, options?: RequestOptions): Promise<SavedItem> {
    return this.http.request<SavedItem>('/me/favorites', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /** Bỏ lưu. Bỏ thứ vốn không có vẫn trả 200 — kết quả cuối cùng giống hệt nhau. */
  removeFavorite(
    itemType: 'restaurant' | 'dish',
    itemId: string,
    options?: RequestOptions,
  ): Promise<MessageData> {
    return this.http.request<MessageData>(
      `/me/favorites/${itemType}/${encodeURIComponent(itemId)}`,
      { ...options, method: 'DELETE' },
    );
  }

  /**
   * Số liệu hoạt động + cấp độ + huy hiệu.
   *
   * ⚠️ Tài khoản mới thì MỌI SỐ LÀ 0 và cấp là 1. Đó là sự thật — đừng thay bằng số
   * minh hoạ trên bản thiết kế.
   */
  stats(options?: RequestOptions): Promise<UserStatsData> {
    return this.http.request<UserStatsData>('/me/stats', options);
  }
}

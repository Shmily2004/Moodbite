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
}

/*
 * CHƯA khai `me()`, dù backend đã có `/auth/me`: chưa trang nào hiển thị thông tin tài
 * khoản nên chưa ai gọi. Thêm method không ai dùng thì không cách nào biết nó còn chạy
 * đúng hay không. Làm trang hồ sơ thì thêm cùng lúc.
 */

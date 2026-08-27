/**
 * Endpoint QUẢN TRỊ — tách hẳn khỏi `endpoints.ts` của người dùng cuối.
 *
 * VÌ SAO LÀ FILE VÀ LỚP RIÊNG, KHÔNG PHẢI THÊM METHOD VÀO `MoodbiteApi`:
 *
 * 1. `apps/client` import `createApi()` và KHÔNG THỂ vô tình gọi endpoint quản trị —
 *    lớp nó cầm không hề có các method đó. Ranh giới client/admin được cưỡng chế bằng
 *    KIỂU DỮ LIỆU, không phải bằng lời dặn trong tài liệu.
 * 2. `apps/admin` import `createAdminApi()` và phải truyền hàm lấy token. Quên truyền
 *    thì TypeScript báo lỗi ngay, không phải đợi tới lúc nhận 401 trên trình duyệt.
 *
 * Hai lớp DÙNG CHUNG `HttpClient`, nên quy ước envelope `{data}`/`{error}` vẫn chỉ có
 * đúng MỘT nơi định nghĩa.
 */
import type { components } from './schema';
import type { HttpClient, RequestOptions } from './http';

export type AdminLoginRequest = components['schemas']['AdminLoginRequest'];
export type AdminLoginData = components['schemas']['AdminLoginData'];
export type AdminRestaurantSummary = components['schemas']['AdminRestaurantSummary'];
export type AdminRestaurantListData = components['schemas']['AdminRestaurantListData'];
export type AdminCreateRestaurantRequest =
  components['schemas']['AdminCreateRestaurantRequest'];
export type AdminUpdateRestaurantRequest =
  components['schemas']['AdminUpdateRestaurantRequest'];
export type AdminOverviewData = components['schemas']['AdminOverviewData'];
export type DoPhuTruong = components['schemas']['DoPhuTruongSchema'];
export type ThongKeNguon = components['schemas']['ThongKeNguonSchema'];
export type ViecCanXuLy = components['schemas']['ViecCanXuLySchema'];
export type AdminDishRow = components['schemas']['AdminDishRow'];
export type AdminDishListData = components['schemas']['AdminDishListData'];
export type AdminSystemData = components['schemas']['AdminSystemData'];
export type AdminSystemService = components['schemas']['AdminSystemService'];
export type AuditEntry = components['schemas']['AuditEntrySchema'];
export type AuditLogData = components['schemas']['AuditLogData'];
export type AdminRecommendationData = components['schemas']['AdminRecommendationData'];
export type LopMoHinh = components['schemas']['LopMoHinhSchema'];

/** Bộ lọc của bảng món quản trị. Giữ đồng bộ với `BO_LOC` ở `list_dishes_admin.py`. */
export type LocMon =
  | 'all'
  | 'with_restaurants'
  | 'without_restaurants'
  | 'missing_image'
  | 'missing_description';

export interface AdminListParams {
  q?: string | null;
  limit?: number;
  includeHidden?: boolean;
}

export class MoodbiteAdminApi {
  constructor(private readonly http: HttpClient) {}

  /** Đổi tài khoản/mật khẩu lấy token ngắn hạn. Endpoint DUY NHẤT không cần token. */
  login(body: AdminLoginRequest, options?: RequestOptions): Promise<AdminLoginData> {
    return this.http.request<AdminLoginData>('/admin/login', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /**
   * Số liệu màn "Tổng quan": đếm quán/món, độ phủ dữ liệu, việc cần xử lý.
   *
   * Server đệm 5 phút. `refresh` để tính lại ngay sau khi vừa sửa dữ liệu.
   *
   * ⚠️ KHÔNG có trường xu hướng ("so với tuần trước", CTR, sparkline) dù bản thiết kế
   * có vẽ: dự án không lưu ảnh chụp dữ liệu theo ngày nên không tính được. Đừng thêm
   * vào ở frontend — có test backend chặn đúng chuyện này.
   */
  overview(refresh = false, options?: RequestOptions): Promise<AdminOverviewData> {
    return this.http.request<AdminOverviewData>(
      `/admin/overview${refresh ? '?refresh=true' : ''}`,
      options,
    );
  }

  /**
   * Danh mục MÓN cho quản trị.
   *
   * ⚠️ KHÁC `/dishes/suggest` của app người dùng: ở đây thấy CẢ món chưa có quán và CẢ
   * danh mục ("Bún"). Đó là chủ đích — việc của admin là tìm món đang thiếu.
   */
  listDishes(
    params: { q?: string | null; filter?: LocMon; limit?: number } = {},
    options?: RequestOptions,
  ): Promise<AdminDishListData> {
    const t = new URLSearchParams();
    if (params.q) t.set('q', params.q);
    if (params.filter) t.set('filter', params.filter);
    if (params.limit) t.set('limit', String(params.limit));
    const q = t.toString();
    return this.http.request<AdminDishListData>(
      `/admin/dishes${q ? `?${q}` : ''}`,
      options,
    );
  }

  /** Nhật ký hoạt động quản trị, mới nhất đứng đầu. */
  activity(
    params: { limit?: number; action?: string | null } = {},
    options?: RequestOptions,
  ): Promise<AuditLogData> {
    const t = new URLSearchParams();
    if (params.limit) t.set('limit', String(params.limit));
    if (params.action) t.set('action', params.action);
    const q = t.toString();
    return this.http.request<AuditLogData>(`/admin/activity${q ? `?${q}` : ''}`, options);
  }

  /**
   * Trạng thái NĂM LỚP MÔ HÌNH. Để XEM và KIỂM TRA, không phải để chỉnh.
   * Trọng số xếp hạng là quy tắc nghiệp vụ, chỉ được nằm ở `domain/services/`.
   */
  recommendation(options?: RequestOptions): Promise<AdminRecommendationData> {
    return this.http.request<AdminRecommendationData>('/admin/recommendation', options);
  }

  /** Cấu hình đang chạy + trạng thái từng kho. CHỈ ĐỌC, không có secret nào. */
  system(options?: RequestOptions): Promise<AdminSystemData> {
    return this.http.request<AdminSystemData>('/admin/system', options);
  }

  /** Danh sách quán. MẶC ĐỊNH kèm cả quán đã ẩn — admin cần thấy để bỏ ẩn lại. */
  listRestaurants(
    params: AdminListParams = {},
    options?: RequestOptions,
  ): Promise<AdminRestaurantListData> {
    const search = new URLSearchParams();
    if (params.q) search.set('q', params.q);
    if (params.limit != null) search.set('limit', String(params.limit));
    if (params.includeHidden != null) {
      search.set('include_hidden', String(params.includeHidden));
    }
    const query = search.toString();
    return this.http.request<AdminRestaurantListData>(
      `/admin/restaurants${query ? `?${query}` : ''}`,
      options,
    );
  }

  /**
   * Thêm một quán HOÀN TOÀN MỚI (nhập tay).
   *
   * Chỉ `name` + `lat` + `lng` bắt buộc. `place_id` do SERVER sinh với tiền tố
   * `manual:` — client KHÔNG được tự đặt mã.
   * Toạ độ ngoài Hà Nội -> 400 (phạm vi dự án chỉ có Hà Nội).
   */
  createRestaurant(
    body: AdminCreateRestaurantRequest,
    options?: RequestOptions,
  ): Promise<AdminRestaurantSummary> {
    return this.http.request<AdminRestaurantSummary>('/admin/restaurants', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /**
   * Sửa các trường mô tả.
   *
   * Chỉ gửi trường muốn đổi. Gửi `null` = XOÁ giá trị; không gửi = giữ nguyên.
   */
  updateRestaurant(
    restaurantId: string,
    changes: AdminUpdateRestaurantRequest,
    options?: RequestOptions,
  ): Promise<AdminRestaurantSummary> {
    return this.http.request<AdminRestaurantSummary>(
      `/admin/restaurants/${encodeURIComponent(restaurantId)}`,
      { ...options, method: 'PATCH', body: changes },
    );
  }

  /** Ẩn quán (soft-delete). Dữ liệu KHÔNG bị xoá. */
  hideRestaurant(
    restaurantId: string,
    options?: RequestOptions,
  ): Promise<AdminRestaurantSummary> {
    return this.http.request<AdminRestaurantSummary>(
      `/admin/restaurants/${encodeURIComponent(restaurantId)}/hide`,
      { ...options, method: 'POST' },
    );
  }

  /** Bỏ ẩn quán đã ẩn. */
  restoreRestaurant(
    restaurantId: string,
    options?: RequestOptions,
  ): Promise<AdminRestaurantSummary> {
    return this.http.request<AdminRestaurantSummary>(
      `/admin/restaurants/${encodeURIComponent(restaurantId)}/restore`,
      { ...options, method: 'POST' },
    );
  }
}

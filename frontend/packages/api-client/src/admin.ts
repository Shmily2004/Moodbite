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
export type AdminDishDetail = components['schemas']['AdminDishDetail'];
export type AdminSystemData = components['schemas']['AdminSystemData'];
export type AdminSystemService = components['schemas']['AdminSystemService'];
export type AuditEntry = components['schemas']['AuditEntrySchema'];
export type AuditLogData = components['schemas']['AuditLogData'];
export type AdminRecommendationData = components['schemas']['AdminRecommendationData'];

// --- Màn "Chất lượng dữ liệu" và màn "Cần xử lý" ---
export type AdminDataQualityData = components['schemas']['AdminDataQualityData'];
export type AdminIssuesData = components['schemas']['AdminIssuesData'];
export type AdminIssueDetailData = components['schemas']['AdminIssueDetailData'];
export type VanDeNhom = components['schemas']['VanDeNhomSchema'];
export type BanGhiVanDe = components['schemas']['BanGhiVanDeSchema'];
export type AnhChupChatLuong = components['schemas']['AnhChupChatLuongSchema'];
export type ThayDoi = components['schemas']['ThayDoiSchema'];
export type AdminResolveIssueData = components['schemas']['AdminResolveIssueData'];

/**
 * Mức GẤP của một vấn đề — khác `severity` ("có phải việc phải làm không").
 * Do backend đặt ở `domain/services/data_issues.py`; đừng khai lại danh sách này ở nơi khác.
 */
export type UuTienVanDe = 'nghiem_trong' | 'quan_trong' | 'can_kiem_tra';
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
  /**
   * Lọc VIỆC CẦN XỬ LÝ: `dong_tam` | `thieu_lien_he`.
   * Khoá do `domain/services/data_quality.py` đặt tên — giữ đồng bộ với nó.
   */
  loc?: string | null;
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
   * ⚠️ KHÔNG có trường xu hướng ở endpoint NÀY, và đừng tự tính ở frontend.
   *
   * Cập nhật 2026-09-08: xu hướng theo ngày và "so với tháng trước" NAY CÓ THẬT, nhưng
   * ở `dataQuality()` bên dưới — chúng dựa trên bảng `quality_snapshot` ghi mỗi ngày
   * một dòng. Màn Tổng quan cố ý không lấy, để nó không phải chờ một lượt ghi đĩa.
   *
   * Vẫn KHÔNG có nguồn cho: CTR, "lượt gợi ý hôm nay". Đừng bịa (CLAUDE.md mục 4).
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

  /**
   * Chi tiết MỘT món cho quản trị.
   *
   * ⚠️ KHÁC `GET /dishes/{id}` của app client: món đang TẮT vẫn trả 200 ở đây. Đó là
   * chủ đích — admin mở trang món chính là để xem 557 món chưa có quán.
   */
  getDish(dishId: string, options?: RequestOptions): Promise<AdminDishDetail> {
    return this.http.request<AdminDishDetail>(
      `/admin/dishes/${encodeURIComponent(dishId)}`,
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
    if (params.loc) search.set('loc', params.loc);
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

  /**
   * Số liệu màn "Chất lượng dữ liệu".
   *
   * ⚠️ Lượt gọi này khiến SERVER GHI một dòng ảnh chụp cho hôm nay (bất biến theo ngày:
   * gọi 50 lần vẫn một dòng). Đó là cách biểu đồ xu hướng có dữ liệu mà không cần máy
   * chủ chạy nền — xem `application/use_cases/get_data_quality.py`.
   *
   * `restaurants_total.delta === null` nghĩa là CHƯA đủ dữ liệu để so sánh. Phải hiện
   * "chưa đủ dữ liệu", KHÔNG được coi là 0 và vẽ mũi tên đi ngang.
   */
  dataQuality(refresh = false, options?: RequestOptions): Promise<AdminDataQualityData> {
    return this.http.request<AdminDataQualityData>(
      `/admin/quality${refresh ? '?refresh=true' : ''}`,
      options,
    );
  }

  /**
   * Bảng các NHÓM vấn đề + năm thẻ số của màn "Cần xử lý".
   *
   * Năm thẻ số luôn tính trên TOÀN BỘ dữ liệu, không đổi theo `priority` — bấm tab lọc
   * mà các thẻ kia tụt về 0 là hiểu sai con số.
   */
  issues(
    params: { priority?: UuTienVanDe | null } = {},
    options?: RequestOptions,
  ): Promise<AdminIssuesData> {
    const t = new URLSearchParams();
    if (params.priority) t.set('priority', params.priority);
    const q = t.toString();
    return this.http.request<AdminIssuesData>(`/admin/issues${q ? `?${q}` : ''}`, options);
  }

  /** Các bản ghi CỤ THỂ của một nhóm vấn đề — nút "Xem danh sách". */
  issueDetail(
    key: string,
    params: { limit?: number } = {},
    options?: RequestOptions,
  ): Promise<AdminIssueDetailData> {
    const t = new URLSearchParams();
    if (params.limit != null) t.set('limit', String(params.limit));
    const q = t.toString();
    return this.http.request<AdminIssueDetailData>(
      `/admin/issues/${encodeURIComponent(key)}${q ? `?${q}` : ''}`,
      options,
    );
  }

  /**
   * Đánh dấu một bản ghi ĐÃ XỬ LÝ.
   *
   * ⚠️ KHÔNG sửa dữ liệu quán/món — chỉ ghi lại "tôi đã xem, không phải làm gì thêm".
   */
  resolveIssue(
    body: { key: string; target_id: string; note?: string | null },
    options?: RequestOptions,
  ): Promise<AdminResolveIssueData> {
    return this.http.request<AdminResolveIssueData>('/admin/issues/resolve', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /** Gỡ đánh dấu — người ta bấm nhầm được. Gỡ dòng chưa từng đánh dấu vẫn thành công. */
  unresolveIssue(
    key: string,
    targetId: string,
    options?: RequestOptions,
  ): Promise<AdminResolveIssueData> {
    const t = new URLSearchParams({ key, target_id: targetId });
    return this.http.request<AdminResolveIssueData>(`/admin/issues/resolve?${t}`, {
      ...options,
      method: 'DELETE',
    });
  }
}

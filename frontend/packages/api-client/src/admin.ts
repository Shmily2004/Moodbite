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
import type { HttpClient, RequestOptions } from './http';
import type { PostDetailData, PostListData, PostStatus, PostWriteRequest } from './posts';
import type {
  AdminLoginRequest,
  AdminLoginData,
  AdminRestaurantSummary,
  AdminRestaurantListData,
  AdminCreateRestaurantRequest,
  AdminUpdateRestaurantRequest,
  AdminUpdateDishRequest,
  AdminOverviewData,
  AdminDishListData,
  AdminDishDetail,
  AdminSystemData,
  AuditLogData,
  AdminRecommendationData,
  AdminDataQualityData,
  AdminIssuesData,
  AdminIssueDetailData,
  AdminResolveIssueData,
  AdminResolvedIssuesData,
  AdminRestaurantStatsData,
  AdminBulkVisibilityData,
  AdminDishRestaurantsData,
  AdminInteractionStatsData,
  UuTienVanDe,
  LocMon,
  AdminListParams,
  AdminClosureReportsData,
  AdminClearedClosureReports,
} from './admin-types';

// Re-export: `index.ts` và mọi nơi khác vẫn import kiểu quản trị từ `./admin`.
export type * from './admin-types';

export class MoodbiteAdminApi {
  constructor(private readonly http: HttpClient) {}

  /** Đổi tài khoản/mật khẩu lấy token ngắn hạn. Endpoint DUY NHẤT không cần token. */
  login(body: AdminLoginRequest, options?: RequestOptions): Promise<AdminLoginData> {
    return this.http.request<AdminLoginData>('/admin/login', {
      ...options,
      credentialCheck: true,
      method: 'POST',
      body,
    });
  }

  /**
   * Đăng xuất THẬT: server thu hồi token (tăng `token_version` của tài khoản, nên cũng
   * đăng xuất tài khoản đó khỏi app người dùng). Thêm 2026-10-02.
   */
  logout(options?: RequestOptions): Promise<{ message: string }> {
    return this.http.request<{ message: string }>('/admin/logout', {
      ...options,
      credentialCheck: true,
      method: 'POST',
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
    params: {
      q?: string | null;
      filter?: LocMon;
      limit?: number;
      page?: number;
      pageSize?: number;
    } = {},
    options?: RequestOptions,
  ): Promise<AdminDishListData> {
    const t = new URLSearchParams();
    if (params.q) t.set('q', params.q);
    if (params.filter) t.set('filter', params.filter);
    if (params.limit) t.set('limit', String(params.limit));
    if (params.page) t.set('page', String(params.page));
    if (params.pageSize) t.set('page_size', String(params.pageSize));
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

  /**
   * Sửa mô tả món. `description: null` (hoặc chuỗi rỗng) = GỠ bản sửa, trở về mô tả gốc.
   * Trả lại chi tiết món đã cập nhật để giao diện hiện đúng ngay, không cần tải lại trang.
   */
  updateDish(
    dishId: string,
    changes: AdminUpdateDishRequest,
    options?: RequestOptions,
  ): Promise<AdminDishDetail> {
    return this.http.request<AdminDishDetail>(
      `/admin/dishes/${encodeURIComponent(dishId)}`,
      { ...options, method: 'PATCH', body: changes },
    );
  }

  /**
   * Quán khớp một món (tab "Danh sách quán" ở trang chi tiết món).
   *
   * Món là SUY LUẬN theo tên quán, không phải thực đơn thật — mỗi dòng có `matched_by`.
   */
  dishRestaurants(
    dishId: string,
    params: { limit?: number } = {},
    options?: RequestOptions,
  ): Promise<AdminDishRestaurantsData> {
    const t = new URLSearchParams();
    if (params.limit) t.set('limit', String(params.limit));
    const q = t.toString();
    return this.http.request<AdminDishRestaurantsData>(
      `/admin/dishes/${encodeURIComponent(dishId)}/restaurants${q ? `?${q}` : ''}`,
      options,
    );
  }

  /** Nhật ký hoạt động quản trị, mới nhất đứng đầu. `targetId` = lịch sử của MỘT bản ghi. */
  activity(
    params: {
      limit?: number;
      action?: string | null;
      targetType?: string | null;
      targetId?: string | null;
    } = {},
    options?: RequestOptions,
  ): Promise<AuditLogData> {
    const t = new URLSearchParams();
    if (params.limit) t.set('limit', String(params.limit));
    if (params.action) t.set('action', params.action);
    if (params.targetType) t.set('target_type', params.targetType);
    if (params.targetId) t.set('target_id', params.targetId);
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
    if (params.page) search.set('page', String(params.page));
    if (params.pageSize) search.set('page_size', String(params.pageSize));
    if (params.district) search.set('district', params.district);
    if (params.source) search.set('source', params.source);
    if (params.status) search.set('status', params.status);
    const query = search.toString();
    return this.http.request<AdminRestaurantListData>(
      `/admin/restaurants${query ? `?${query}` : ''}`,
      options,
    );
  }

  /** Thẻ số + giá trị ô chọn (khu vực, nguồn) của trang quản lý quán — toàn bộ bảng. */
  restaurantStats(options?: RequestOptions): Promise<AdminRestaurantStatsData> {
    return this.http.request<AdminRestaurantStatsData>('/admin/restaurants/stats', options);
  }

  /**
   * Ẩn / bỏ ẩn NHIỀU quán một lần (tối đa 200). Server ghi nhật ký TỪNG quán.
   * `not_found` = mã gửi lên nhưng không có trong CSDL — phải báo lại cho người dùng.
   */
  bulkSetVisibility(
    restaurantIds: string[],
    isActive: boolean,
    options?: RequestOptions,
  ): Promise<AdminBulkVisibilityData> {
    return this.http.request<AdminBulkVisibilityData>('/admin/restaurants/bulk-visibility', {
      ...options,
      method: 'POST',
      body: { restaurant_ids: restaurantIds, is_active: isActive },
    });
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
  /**
   * Hàng chờ UC21: quán bị KHÁCH báo đóng cửa. Lượt báo KHÔNG tự ẩn quán; quản trị ẩn
   * (`hideRestaurant`) hoặc gỡ (`clearClosureReports`). Đếm theo người báo (IP đã băm).
   */
  closureReports(options?: RequestOptions): Promise<AdminClosureReportsData> {
    return this.http.request<AdminClosureReportsData>('/admin/closure-reports', options);
  }

  /**
   * Gỡ mọi lượt báo đóng cửa của một quán. Ghi vào nhật ký nên vẫn đúng sau khi khởi động
   * lại. ⚠️ KHÁC "Khôi phục" (bỏ ẩn do admin): hai cơ chế ẩn độc lập nhau.
   */
  clearClosureReports(
    restaurantId: string,
    options?: RequestOptions,
  ): Promise<AdminClearedClosureReports> {
    return this.http.request<AdminClearedClosureReports>(
      `/admin/restaurants/${encodeURIComponent(restaurantId)}/closure-reports/clear`,
      { ...options, method: 'POST' },
    );
  }

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

  /** Tab "Đã xử lý" — các bản ghi đã được đánh dấu, mới nhất đứng đầu. */
  resolvedIssues(
    params: { limit?: number } = {},
    options?: RequestOptions,
  ): Promise<AdminResolvedIssuesData> {
    const t = new URLSearchParams();
    if (params.limit != null) t.set('limit', String(params.limit));
    const q = t.toString();
    return this.http.request<AdminResolvedIssuesData>(
      `/admin/issues/resolved${q ? `?${q}` : ''}`,
      options,
    );
  }

  /** Khối "Hệ thống gợi ý" ở màn Tổng quan. Không có CTR — xem kiểu dữ liệu. */
  interactionStats(options?: RequestOptions): Promise<AdminInteractionStatsData> {
    return this.http.request<AdminInteractionStatsData>('/admin/interactions/stats', options);
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

  /** Mọi bài viết, kể cả nháp. `status` để lọc; bỏ trống = tất cả. */
  listPosts(status?: PostStatus, options?: RequestOptions): Promise<PostListData> {
    const q = status ? `?status=${status}` : '';
    return this.http.request<PostListData>(`/admin/posts${q}`, options);
  }

  getPost(postId: string, options?: RequestOptions): Promise<PostDetailData> {
    return this.http.request<PostDetailData>(
      `/admin/posts/${encodeURIComponent(postId)}`,
      options,
    );
  }

  /** Tạo bài. Mặc định là nháp nếu không chọn `published`. */
  createPost(body: PostWriteRequest, options?: RequestOptions): Promise<PostDetailData> {
    return this.http.request<PostDetailData>('/admin/posts', { ...options, method: 'POST', body });
  }

  /** Sửa bài — gửi ĐỦ mọi trường (xem `PostWriteRequest`). */
  updatePost(
    postId: string,
    body: PostWriteRequest,
    options?: RequestOptions,
  ): Promise<PostDetailData> {
    return this.http.request<PostDetailData>(
      `/admin/posts/${encodeURIComponent(postId)}`,
      { ...options, method: 'PUT', body },
    );
  }

  deletePost(postId: string, options?: RequestOptions): Promise<{ message: string }> {
    return this.http.request<{ message: string }>(
      `/admin/posts/${encodeURIComponent(postId)}`,
      { ...options, method: 'DELETE' },
    );
  }
}

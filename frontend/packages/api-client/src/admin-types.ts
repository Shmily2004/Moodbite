/**
 * KIỂU DỮ LIỆU của các endpoint QUẢN TRỊ — tách khỏi `admin.ts` ngày 2026-10-06 khi file
 * đó vượt ~300 dòng (CLAUDE.md mục 6). Phần lớn là bí danh của schema sinh từ OpenAPI;
 * `admin.ts` giữ lớp `MoodbiteAdminApi` và RE-EXPORT toàn bộ ở đây, nên nơi khác vẫn
 * import từ `./admin` như cũ.
 */
import type { components } from './schema';

export type AdminLoginRequest = components['schemas']['AdminLoginRequest'];
export type AdminLoginData = components['schemas']['AdminLoginData'];
export type AdminRestaurantSummary = components['schemas']['AdminRestaurantSummary'];
export type AdminRestaurantListData = components['schemas']['AdminRestaurantListData'];
export type AdminCreateRestaurantRequest =
  components['schemas']['AdminCreateRestaurantRequest'];
export type AdminUpdateRestaurantRequest =
  components['schemas']['AdminUpdateRestaurantRequest'];
export type AdminUpdateDishRequest = components['schemas']['AdminUpdateDishRequest'];
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
export type AdminResolvedIssuesData = components['schemas']['AdminResolvedIssuesData'];
export type AdminResolvedIssue = components['schemas']['AdminResolvedIssueSchema'];

// --- Phân trang, thẻ số, thao tác hàng loạt, khối "Hệ thống gợi ý" (2026-09-16) ---
export type AdminRestaurantStatsData = components['schemas']['AdminRestaurantStatsData'];
export type FacetValue = components['schemas']['FacetValueSchema'];
export type AdminBulkVisibilityData = components['schemas']['AdminBulkVisibilityData'];
export type AdminDishRestaurantsData = components['schemas']['AdminDishRestaurantsData'];
export type AdminDishRestaurant = components['schemas']['AdminDishRestaurant'];
/**
 * Thống kê nhật ký tương tác. ⚠️ KHÔNG có CTR: dự án không ghi lượt hiển thị (impression),
 * nên không có mẫu số — xem `domain/services/interaction_stats.py`.
 */
export type AdminInteractionStatsData = components['schemas']['AdminInteractionStatsData'];

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
  /** Trang, bắt đầu từ 1. Có `page` thì server trả `total_matched` để phân trang. */
  page?: number;
  pageSize?: number;
  /** Khu vực — giá trị lấy từ `restaurantStats().districts`. */
  district?: string | null;
  /** Nguồn. `manual` gộp cả quán nhập tay (manual/admin). */
  source?: string | null;
  /** `visible` | `hidden`. */
  status?: 'visible' | 'hidden' | null;
  includeHidden?: boolean;
  /**
   * Lọc VIỆC CẦN XỬ LÝ: `dong_tam` | `thieu_lien_he`.
   * Khoá do `domain/services/data_quality.py` đặt tên — giữ đồng bộ với nó.
   */
  loc?: string | null;
}

// Báo đóng cửa do khách gửi (thêm 2026-10-06) - xem `MoodbiteAdminApi.closureReports`.
export type AdminClosureReportsData = components['schemas']['ClosureReportListData'];
export type AdminClosureReportItem = components['schemas']['ClosureReportItem'];
export type AdminClearedClosureReports = components['schemas']['ClearedClosureReportsData'];

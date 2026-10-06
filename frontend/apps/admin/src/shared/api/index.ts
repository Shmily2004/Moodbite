/**
 * Client API dùng chung cho toàn app quản trị.
 *
 * Đây là `createAdminApi`, KHÔNG phải `createApi` của app client. Lớp trả về chỉ có
 * method quản trị — không tìm kiếm, không ghi tương tác. Ranh giới client/admin được
 * cưỡng chế bằng kiểu dữ liệu.
 */
import { createAdminApi } from '@moodbite/api-client';
import { API_BASE } from '../config';
import { handleUnauthorized, readToken } from '../lib';

// Truyền HÀM chứ không phải chuỗi: token đổi khi đăng nhập / đăng xuất / hết hạn, và
// client phải luôn đọc giá trị mới nhất chứ không giữ bản chụp lúc khởi tạo.
// 401 có token ở BẤT KỲ trang nào → `handleUnauthorized` → về trang đăng nhập (2026-10-06).
export const adminApi = createAdminApi(API_BASE, readToken, ({ token }) =>
  handleUnauthorized(token),
);

export { ApiError } from '@moodbite/api-client';
export type {
  AdminRestaurantSummary,
  AdminOverviewData,
  DoPhuTruong,
  ThongKeNguon,
  ViecCanXuLy,
  AdminDishRow,
  AdminDishDetail,
  AdminSystemData,
  AdminSystemService,
  AuditEntry,
  AdminClosureReportItem,
  LocMon,
  AdminRecommendationData,
  LopMoHinh,
  // Màn "Chất lượng dữ liệu" + "Cần xử lý"
  AdminDataQualityData,
  AdminIssuesData,
  AdminIssueDetailData,
  AdminResolveIssueData,
  VanDeNhom,
  BanGhiVanDe,
  AnhChupChatLuong,
  ThayDoi,
  UuTienVanDe,
  // Phân trang, thẻ số, hàng loạt, "Hệ thống gợi ý" (2026-09-16)
  AdminResolvedIssuesData,
  AdminResolvedIssue,
  AdminRestaurantStatsData,
  FacetValue,
  AdminBulkVisibilityData,
  AdminDishRestaurantsData,
  AdminDishRestaurant,
  AdminInteractionStatsData,
  AdminRestaurantListData,
  AdminListParams,
} from '@moodbite/api-client';

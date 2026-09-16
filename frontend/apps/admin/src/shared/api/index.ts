/**
 * Client API dùng chung cho toàn app quản trị.
 *
 * Đây là `createAdminApi`, KHÔNG phải `createApi` của app client. Lớp trả về chỉ có
 * method quản trị — không tìm kiếm, không ghi tương tác. Ranh giới client/admin được
 * cưỡng chế bằng kiểu dữ liệu.
 */
import { createAdminApi } from '@moodbite/api-client';
import { API_BASE } from '../config';
import { readToken } from '../lib';

// Truyền HÀM chứ không phải chuỗi: token đổi khi đăng nhập / đăng xuất / hết hạn, và
// client phải luôn đọc giá trị mới nhất chứ không giữ bản chụp lúc khởi tạo.
export const adminApi = createAdminApi(API_BASE, readToken);

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
} from '@moodbite/api-client';

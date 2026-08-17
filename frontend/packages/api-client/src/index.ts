/**
 * @moodbite/api-client — tầng gọi API DÙNG CHUNG cho app client và app admin.
 *
 * VÌ SAO LÀ PACKAGE RIÊNG: nếu mỗi app tự viết lớp gọi API, sẽ có hai bản định nghĩa
 * cùng một hợp đồng và chúng sẽ lệch nhau. Đó chính là sai lầm "hai nơi cùng mô tả một
 * thứ" đã suýt giết dự án này ở phía backend.
 *
 * Cách dùng:
 *     import { createApi } from '@moodbite/api-client';
 *     const api = createApi(import.meta.env.VITE_API_BASE);
 *     const data = await api.search({ session_id, query_text: 'phở bò' });
 */
export { ApiError, HttpClient } from './http';
export type { ApiErrorCode, HttpClientOptions, RequestOptions } from './http';

export { MoodbiteApi } from './endpoints';
export type {
  ActionType,
  HealthData,
  InteractionRequest,
  InteractionResponseData,
  MoodsData,
  RestaurantDetailData,
  SearchRequest,
  SearchResponseData,
  SearchResultItem,
  SuggestedDish,
} from './endpoints';

export { MoodbiteAdminApi } from './admin';
export type {
  AdminListParams,
  AdminLoginData,
  AdminLoginRequest,
  AdminRestaurantListData,
  AdminRestaurantSummary,
  AdminUpdateRestaurantRequest,
} from './admin';

export type { components, paths } from './schema';

import { HttpClient } from './http';
import { MoodbiteApi } from './endpoints';
import { MoodbiteAdminApi } from './admin';

export const DEFAULT_API_BASE = 'http://localhost:8001/api/v1';

/**
 * Client cho app NGƯỜI DÙNG CUỐI (`apps/client`).
 *
 * Cố tình KHÔNG nhận token: luồng người dùng cuối không có đăng nhập, và lớp trả về
 * không hề có method quản trị nào.
 */
export function createApi(baseUrl: string = DEFAULT_API_BASE): MoodbiteApi {
  return new MoodbiteApi(new HttpClient({ baseUrl }));
}

/**
 * Client cho app QUẢN TRỊ (`apps/admin`).
 *
 * `getAuthToken` là BẮT BUỘC: mọi endpoint quản trị (trừ /admin/login) đều cần token,
 * nên bắt truyền ngay tại đây sẽ bắt lỗi lúc biên dịch thay vì lúc nhận 401.
 */
export function createAdminApi(
  baseUrl: string = DEFAULT_API_BASE,
  getAuthToken: () => string | null,
): MoodbiteAdminApi {
  return new MoodbiteAdminApi(new HttpClient({ baseUrl, getAuthToken }));
}

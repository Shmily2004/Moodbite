/**
 * Thực thể API dùng chung cho toàn app.
 *
 * Component KHÔNG được import trực tiếp từ đây - phải đi qua tầng api của feature
 * hoặc entity, đúng luật import của FSD.
 */
import { createApi, createAuthApi, createMyPlacesApi } from '@moodbite/api-client';
import { API_BASE } from '../config/env';
import { readToken } from '../lib/tokenStorage';
import { handleUnauthorized } from '../lib/sessionExpiry';

/**
 * Client chính (tìm quán, món, gợi ý). Phải gắn token: từ 2026-11-13 các endpoint này yêu
 * cầu đăng nhập. Cùng cách lấy token và xử lý 401 như `authApi` bên dưới.
 */
export const api = createApi(API_BASE, readToken, ({ token }) => handleUnauthorized(token));

/**
 * Client cho phần TÀI KHOẢN (`/auth/*`). Tách khỏi `api` ở trên có chủ đích: luồng chính
 * của MoodBite vẫn chạy khi chưa đăng nhập, nên hai thứ này không nên dính vào nhau.
 *
 * 401 giữa phiên (token bị thu hồi ở thiết bị khác) → `handleUnauthorized` xoá token và
 * báo `entities/user` đăng xuất cục bộ — một chỗ cho mọi trang (2026-10-06).
 *
 * Truyền `readToken` chứ không truyền chuỗi token: token đổi theo thời gian (đăng nhập,
 * hết hạn, đăng xuất), truyền chuỗi thì client giữ mãi giá trị của lần dựng đầu tiên.
 */
export const authApi = createAuthApi(API_BASE, readToken, ({ token }) =>
  handleUnauthorized(token),
);

/** "Bộ sưu tập" + "Địa chỉ của tôi" (2026-09-29). Cùng cách lấy token như `authApi`. */
export const myPlacesApi = createMyPlacesApi(API_BASE, readToken, ({ token }) =>
  handleUnauthorized(token),
);

export { ApiError } from '@moodbite/api-client';
export type {
  AuthData,
  BadgeData,
  FavoritesData,
  LoginRequest,
  SavedItem,
  UserSelf,
  UserStatsData,
} from '@moodbite/api-client';
export type {
  SearchRequest,
  SearchResponseData,
  SearchResultItem,
  RestaurantDetailData,
  SuggestedDish,
  ActionType,
  DishItem,
  DishSuggestRequest,
  DishSuggestResponseData,
} from '@moodbite/api-client';
export type {
  CollectionData,
  CollectionItemData,
  UserAddressData,
} from '@moodbite/api-client';
export type { PostPublic, PostListData, PostDetailData } from '@moodbite/api-client';
export { accountErrorText, apiErrorText } from './loiApi';

/**
 * Thực thể API dùng chung cho toàn app.
 *
 * Component KHÔNG được import trực tiếp từ đây - phải đi qua tầng api của feature
 * hoặc entity, đúng luật import của FSD.
 */
import { createApi, createAuthApi } from '@moodbite/api-client';
import { API_BASE } from '../config/env';
import { readToken } from '../lib/tokenStorage';

export const api = createApi(API_BASE);

/**
 * Client cho phần TÀI KHOẢN (`/auth/*`). Tách khỏi `api` ở trên có chủ đích: luồng chính
 * của MoodBite vẫn chạy khi chưa đăng nhập, nên hai thứ này không nên dính vào nhau.
 *
 * Truyền `readToken` chứ không truyền chuỗi token: token đổi theo thời gian (đăng nhập,
 * hết hạn, đăng xuất), truyền chuỗi thì client giữ mãi giá trị của lần dựng đầu tiên.
 */
export const authApi = createAuthApi(API_BASE, readToken);

export { ApiError } from '@moodbite/api-client';
export type {
  AuthData,
  BadgeData,
  FavoritesData,
  LoginRequest,
  SavedItem,
  UserPublic,
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

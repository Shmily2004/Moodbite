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

export type { components, paths } from './schema';

import { HttpClient } from './http';
import { MoodbiteApi } from './endpoints';

export const DEFAULT_API_BASE = 'http://localhost:8001/api/v1';

export function createApi(baseUrl: string = DEFAULT_API_BASE): MoodbiteApi {
  return new MoodbiteApi(new HttpClient({ baseUrl }));
}

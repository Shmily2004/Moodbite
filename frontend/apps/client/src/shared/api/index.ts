/**
 * Thực thể API dùng chung cho toàn app.
 *
 * Component KHÔNG được import trực tiếp từ đây - phải đi qua tầng api của feature
 * hoặc entity, đúng luật import của FSD.
 */
import { createApi } from '@moodbite/api-client';
import { API_BASE } from '../config/env';

export const api = createApi(API_BASE);

export { ApiError } from '@moodbite/api-client';
export type {
  SearchRequest,
  SearchResponseData,
  SearchResultItem,
  RestaurantDetailData,
  SuggestedDish,
  ActionType,
} from '@moodbite/api-client';

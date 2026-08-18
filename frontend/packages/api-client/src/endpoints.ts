/**
 * Các endpoint của MoodBite, gắn KIỂU sinh tự động từ OpenAPI.
 *
 * Đổi field ở `src/presentation/api/schemas.py` -> chạy `npm run gen:api` -> TypeScript
 * chỉ thẳng ra mọi chỗ frontend phải sửa. Đây là cơ chế ngăn "sửa backend, frontend vỡ
 * mà không ai biết".
 */
import type { components } from './schema';
import type { HttpClient, RequestOptions } from './http';

/** Kiểu lấy TRỰC TIẾP từ OpenAPI - không gõ tay, không lệch được với backend. */
export type SearchRequest = components['schemas']['SearchRequest'];
export type SearchResponseData = components['schemas']['SearchResponseData'];
export type SearchResultItem = components['schemas']['SearchResultItemSchema'];
export type SuggestedDish = components['schemas']['SuggestedDishSchema'];
export type RestaurantDetailData = components['schemas']['RestaurantDetailData'];
export type InteractionRequest = components['schemas']['InteractionRequest'];
export type InteractionResponseData = components['schemas']['InteractionResponseData'];
export type HealthData = components['schemas']['HealthData'];
export type MoodsData = components['schemas']['MoodsData'];
export type ActionType = components['schemas']['ActionType'];
/** Luồng "chọn món trước, tìm quán sau". */
export type DishSuggestRequest = components['schemas']['DishSuggestRequest'];
export type DishSuggestResponseData = components['schemas']['DishSuggestResponseData'];
export type DishItem = components['schemas']['DishItemSchema'];

/** Tham số chung cho hai endpoint tính theo vị trí người dùng. */
export interface DishLocationParams {
  latitude?: number;
  longitude?: number;
  max_distance_km?: number;
}

export interface RestaurantsForDishParams extends DishLocationParams {
  session_id: string;
  mood?: string | null;
  limit?: number;
}

/** Bỏ tham số rỗng để URL không dính `?mood=undefined`. */
function toQuery(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : '';
}

export class MoodbiteApi {
  constructor(private readonly http: HttpClient) {}

  /** Tìm kiếm + xếp hạng. Mỗi kết quả đã kèm sẵn `suggested_dish`. */
  search(body: SearchRequest, options?: RequestOptions): Promise<SearchResponseData> {
    return this.http.request<SearchResponseData>('/search', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /**
   * Bước 1 của luồng mới: bộ lọc -> danh sách MÓN (không phải quán).
   *
   * Món không có quán nào trong bán kính bị backend ẩn đi, và số món bị ẩn nằm ở
   * `warnings` - UI phải hiện ra, đừng nuốt.
   */
  suggestDishes(
    body: DishSuggestRequest,
    options?: RequestOptions,
  ): Promise<DishSuggestResponseData> {
    return this.http.request<DishSuggestResponseData>('/dishes/suggest', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /** Bước 2: chi tiết một món, kèm THÀNH PHẦN cơ bản. */
  dishDetail(
    dishId: string,
    params: DishLocationParams = {},
    options?: RequestOptions,
  ): Promise<DishItem> {
    return this.http.request<DishItem>(
      `/dishes/${encodeURIComponent(dishId)}${toQuery({ ...params })}`,
      options,
    );
  }

  /**
   * Bước 3: quán gần đây bán món đã chọn.
   *
   * Trả về ĐÚNG kiểu `SearchResponseData` của `/search`, nên `RestaurantList` dùng lại
   * được nguyên vẹn - không cần component thẻ quán thứ hai.
   */
  restaurantsForDish(
    dishId: string,
    params: RestaurantsForDishParams,
    options?: RequestOptions,
  ): Promise<SearchResponseData> {
    return this.http.request<SearchResponseData>(
      `/dishes/${encodeURIComponent(dishId)}/restaurants${toQuery({ ...params })}`,
      options,
    );
  }

  restaurantDetail(
    restaurantId: string,
    options?: RequestOptions,
  ): Promise<RestaurantDetailData> {
    return this.http.request<RestaurantDetailData>(
      `/restaurants/${encodeURIComponent(restaurantId)}`,
      options,
    );
  }

  /**
   * Ghi tương tác - nguồn NHÃN cho mô hình xếp hạng ở giai đoạn sau.
   *
   * Cố tình KHÔNG ném lỗi: ghi log thất bại không được làm hỏng trải nghiệm người dùng.
   */
  async logInteraction(
    body: InteractionRequest,
  ): Promise<InteractionResponseData | null> {
    try {
      return await this.http.request<InteractionResponseData>('/interactions', {
        method: 'POST',
        body,
      });
    } catch (err) {
      console.warn('Không ghi được tương tác:', (err as Error).message);
      return null;
    }
  }

  health(options?: RequestOptions): Promise<HealthData> {
    return this.http.request<HealthData>('/health', options);
  }

  moods(options?: RequestOptions): Promise<MoodsData> {
    return this.http.request<MoodsData>('/moods', options);
  }
}

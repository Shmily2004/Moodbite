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

/**
 * Các lệnh gọi API của MoodBite. Component KHÔNG được gọi fetch trực tiếp - luôn đi qua đây.
 *
 * Đây cũng là nơi DUY NHẤT biết tên field của backend (snake_case theo đặc tả API mục 1.3).
 * Backend đổi tên field thì chỉ phải sửa file này, không phải đi sửa từng component.
 */
import { request } from './httpClient'
import { getSessionId } from '../domain/session'

/**
 * Tìm kiếm & xếp hạng nhà hàng.
 * @returns {{searchQueryId: string, results: Array, context: string[], warnings: string[]}}
 */
export async function search(
  { queryText, mood, latitude, longitude, maxDistanceKm, limit = 10 },
  signal,
) {
  const data = await request('/search', {
    method: 'POST',
    signal,
    body: {
      session_id: getSessionId(),
      query_text: queryText || null,
      mood: mood || null,
      latitude,
      longitude,
      max_distance_km: maxDistanceKm ?? null,
      limit,
    },
  })

  return {
    searchQueryId: data.search_query_id,
    context: data.context ?? [],
    warnings: data.warnings ?? [],
    results: (data.results ?? []).map(toRestaurant),
  }
}

/** Ánh xạ JSON của API -> model của giao diện. Chỗ duy nhất đọc tên field thô. */
function toRestaurant(item) {
  return {
    id: item.restaurant_id,
    name: item.name,
    category: item.category,
    address: item.address,
    lat: item.latitude,
    lng: item.longitude,
    distanceM: item.distance_m,
    // null = CHƯA CÓ dữ liệu, không phải 0 sao / miễn phí.
    priceRange: item.price_range,
    rating: item.rating,
    ratingsTotal: item.user_ratings_total,
    rankPosition: item.rank_position,
    score: item.predicted_score,
    matchSource: item.match_source,
    suggestedDish: item.suggested_dish
      ? {
          id: item.suggested_dish.dish_id,
          name: item.suggested_dish.name,
          cuisine: item.suggested_dish.cuisine,
          confidence: item.suggested_dish.confidence,
          reason: item.suggested_dish.reason,
        }
      : null,
  }
}

export async function getRestaurantDetail(restaurantId, signal) {
  const data = await request(`/restaurants/${encodeURIComponent(restaurantId)}`, { signal })
  return {
    hasDetails: data.has_details,
    reason: data.reason,
    name: data.name,
    priceRange: data.price_range,
    atmosphere: data.atmosphere,
    openingHours: data.opening_hours,
    images: data.images ?? [],
    reviews: data.reviews ?? [],
    menuUrl: data.menu_url,
    website: data.website,
    googleMapsUrl: data.google_maps_url,
  }
}

/**
 * Ghi nhận tương tác - nguồn nhãn cho mô hình xếp hạng ở giai đoạn sau.
 *
 * Cố tình KHÔNG ném lỗi ra ngoài: ghi log thất bại không được làm hỏng trải nghiệm
 * người dùng, họ vẫn phải xem được quán.
 */
export async function logInteraction({
  restaurantId,
  actionType,
  searchQueryId,
  dwellTimeMs,
  rankPosition,
}) {
  try {
    return await request('/interactions', {
      method: 'POST',
      body: {
        session_id: getSessionId(),
        restaurant_id: restaurantId,
        action_type: actionType,
        search_query_id: searchQueryId ?? null,
        dwell_time_ms: dwellTimeMs ?? null,
        rank_position: rankPosition ?? null,
      },
    })
  } catch (err) {
    console.warn('Không ghi được tương tác:', err.message)
    return null
  }
}

import type { Restaurant } from "../../domain/entities/Restaurant";
import type { IRestaurantRepository } from "../../application/ports/IRestaurantRepository";

/**
 * Adapter in-memory cho IRestaurantRepository.
 * Dữ liệu mẫu khớp với restaurant_id đã được dùng trong InMemoryDishRepository
 * (restaurant-1, restaurant-2, restaurant-3), để luồng "đề xuất món ăn -> tra quán" có dữ liệu thật để test.
 */
export class InMemoryRestaurantRepository implements IRestaurantRepository {
  private readonly restaurants: Restaurant[] = [
    {
      id: "restaurant-1",
      name: "Phở Long Hòa",
      address: "12 Hàng Bún, Ba Đình, Hà Nội",
      latitude: 21.0388,
      longitude: 105.8383,
      location: null,
      opening_hours: { mon_sun: "06:00-22:00" },
      price_range: 1,
      price_range_vo: null,
      rating: 4.5,
      user_ratings_total: 320,
      description_embedding: null,
      is_active: true,
      deleted_at: null,
      experience_cluster_id: null,
      source: "crawler",
      external_place_id: "gplace-restaurant-1",
      updated_by: "crawler",
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-01T00:00:00.000Z",
    },
    {
      id: "restaurant-2",
      name: "Quán Chay An Lạc",
      address: "45 Tây Sơn, Đống Đa, Hà Nội",
      latitude: 21.0069,
      longitude: 105.8228,
      location: null,
      opening_hours: { mon_sun: "07:00-21:00" },
      price_range: 1,
      price_range_vo: null,
      rating: 4.2,
      user_ratings_total: 128,
      description_embedding: null,
      is_active: true,
      deleted_at: null,
      experience_cluster_id: 2,
      source: "crawler",
      external_place_id: "gplace-restaurant-2",
      updated_by: "crawler",
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-01T00:00:00.000Z",
    },
    {
      id: "restaurant-3",
      name: "Bếp Ấn Độ Saffron",
      address: "88 Xuân Diệu, Tây Hồ, Hà Nội",
      latitude: 21.0553,
      longitude: 105.8221,
      location: null,
      opening_hours: { mon_sun: "10:00-22:30" },
      price_range: 2,
      price_range_vo: null,
      rating: 4.7,
      user_ratings_total: 210,
      description_embedding: null,
      is_active: true,
      deleted_at: null,
      experience_cluster_id: null,
      source: "crawler",
      external_place_id: "gplace-restaurant-3",
      updated_by: "crawler",
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-01T00:00:00.000Z",
    },
  ];

  async save(restaurant: Restaurant): Promise<Restaurant> {
    const index = this.restaurants.findIndex((r) => r.id === restaurant.id);
    if (index >= 0) {
      this.restaurants[index] = restaurant;
    } else {
      this.restaurants.push(restaurant);
    }
    return restaurant;
  }

  async findById(id: string): Promise<Restaurant | null> {
    return this.restaurants.find((r) => r.id === id) ?? null;
  }

  async findAll(): Promise<Restaurant[]> {
    return [...this.restaurants];
  }

  async findActive(): Promise<Restaurant[]> {
    return this.restaurants.filter((r) => r.is_active && !r.deleted_at);
  }

  async findByName(name: string): Promise<Restaurant[]> {
    const normalized = name.toLowerCase();
    return this.restaurants.filter((r) => r.name.toLowerCase().includes(normalized));
  }

  async findByExternalPlaceId(externalPlaceId: string): Promise<Restaurant | null> {
    return this.restaurants.find((r) => r.external_place_id === externalPlaceId) ?? null;
  }

  async findNearby(latitude: number, longitude: number, radiusKm: number): Promise<Restaurant[]> {
    return this.restaurants.filter((r) => {
      const distanceKm = this.haversineDistanceKm(latitude, longitude, r.latitude, r.longitude);
      return distanceKm <= radiusKm;
    });
  }

  async findByExperienceCluster(clusterId: number): Promise<Restaurant[]> {
    return this.restaurants.filter((r) => r.experience_cluster_id === clusterId);
  }

  async findByPriceRange(minPrice: number, maxPrice: number): Promise<Restaurant[]> {
    return this.restaurants.filter(
      (r) => r.price_range != null && r.price_range >= minPrice && r.price_range <= maxPrice
    );
  }

  async searchByKeyword(query: string): Promise<Restaurant[]> {
    const normalized = query.toLowerCase();
    return this.restaurants.filter(
      (r) =>
        r.name.toLowerCase().includes(normalized) ||
        (r.address ?? "").toLowerCase().includes(normalized)
    );
  }

  async delete(id: string): Promise<void> {
    const index = this.restaurants.findIndex((r) => r.id === id);
    if (index >= 0) {
      this.restaurants.splice(index, 1);
    }
  }

  async softDelete(id: string): Promise<void> {
    const restaurant = this.restaurants.find((r) => r.id === id);
    if (restaurant) {
      restaurant.is_active = false;
      restaurant.deleted_at = new Date().toISOString();
    }
  }

  /**
   * Công thức Haversine để tính khoảng cách (km) giữa 2 tọa độ.
   * Dùng cho findNearby() thay vì phụ thuộc thư viện ngoài, giữ đúng nguyên tắc
   * adapter in-memory không kéo thêm dependency hạ tầng.
   */
  private haversineDistanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const toRad = (deg: number) => (deg * Math.PI) / 180;
    const R = 6371;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }
}

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse } from "csv-parse/sync";
import type { Restaurant } from "../../domain/entities/Restaurant";
import type { IRestaurantRepository } from "../../application/ports/IRestaurantRepository";

const DEFAULT_CSV_PATH = "data_pipeline/data_cleaned/dataset_moodbite_features.csv";

type CsvRow = {
  title: string;
  placeId: string;
  "location/lat": string;
  "location/lng": string;
  totalScore: string;
  categoryName: string;
  address: string;
  [key: string]: string;
};

/**
 * Adapter đọc dữ liệu quán ăn THẬT từ file CSV do data_pipeline (Python) tạo ra
 * (data_pipeline/data_cleaned/dataset_moodbite_features.csv).
 *
 * File này KHÔNG nằm trong git (đã .gitignore đúng vì là dữ liệu dẫn xuất) — để có nó,
 * phải chạy trước trên máy: 
 *   python -m data_pipeline.merge_and_prepare_raw
 *   python -m data_pipeline.data_cleaning
 *   python -m data_pipeline.feature_engineering
 *
 * Nếu file chưa tồn tại, constructor sẽ throw lỗi rõ ràng — nơi gọi (diContainer)
 * chịu trách nhiệm bắt lỗi và fallback về InMemoryRestaurantRepository thay vì crash
 * toàn bộ app, đúng nguyên tắc "graceful degradation" đã dùng xuyên suốt các script Python.
 */
export class CsvRestaurantRepository implements IRestaurantRepository {
  private readonly restaurants: Restaurant[];

  constructor(csvPath: string = DEFAULT_CSV_PATH) {
    const absolutePath = resolve(process.cwd(), csvPath);
    let content: string;
    try {
      content = readFileSync(absolutePath, "utf-8");
    } catch (error) {
      throw new Error(
        `Không đọc được file dữ liệu quán ăn tại ${absolutePath}. ` +
          `Hãy chạy pipeline Python trước: python -m data_pipeline.merge_and_prepare_raw && ` +
          `python -m data_pipeline.data_cleaning && python -m data_pipeline.feature_engineering. ` +
          `Lỗi gốc: ${error instanceof Error ? error.message : String(error)}`
      );
    }

    const rows: CsvRow[] = parse(content, {
      columns: true,
      skip_empty_lines: true,
      bom: true, // file được ghi bằng utf-8-sig (pandas), cần bỏ qua BOM
    });

    const nowIso = new Date().toISOString();

    this.restaurants = rows
      .map((row): Restaurant | null => {
        const latitude = Number(row["location/lat"]);
        const longitude = Number(row["location/lng"]);
        if (!row.placeId || Number.isNaN(latitude) || Number.isNaN(longitude)) {
          // Bỏ qua dòng thiếu id hoặc tọa độ không hợp lệ, không để 1 dòng lỗi làm crash cả app.
          return null;
        }

        const rating = row.totalScore ? Number(row.totalScore) : null;

        return {
          id: row.placeId,
          name: row.title,
          address: row.address || null,
          latitude,
          longitude,
          location: null,
          opening_hours: null,
          price_range: null, // Không cào được price level từ nguồn dữ liệu hiện tại.
          price_range_vo: null,
          rating: rating !== null && !Number.isNaN(rating) ? rating : null,
          user_ratings_total: null,
          description_embedding: null,
          is_active: true,
          deleted_at: null,
          experience_cluster_id: null,
          source: "data_pipeline",
          external_place_id: row.placeId,
          updated_by: "batch_pipeline",
          created_at: nowIso,
          updated_at: nowIso,
        };
      })
      .filter((r): r is Restaurant => r !== null);
  }

  getAllSync(): Restaurant[] {
    return this.restaurants;
  }

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

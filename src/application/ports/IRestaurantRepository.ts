import type { Restaurant } from "../../domain/entities/Restaurant";

export interface IRestaurantRepository {
  save(restaurant: Restaurant): Promise<Restaurant>;
  findById(id: string): Promise<Restaurant | null>;
  findAll(): Promise<Restaurant[]>;
  findActive(): Promise<Restaurant[]>;
  findByName(name: string): Promise<Restaurant[]>;
  findByExternalPlaceId(externalPlaceId: string): Promise<Restaurant | null>;
  findNearby(latitude: number, longitude: number, radiusKm: number): Promise<Restaurant[]>;
  findByExperienceCluster(clusterId: number): Promise<Restaurant[]>;
  findByPriceRange(minPrice: number, maxPrice: number): Promise<Restaurant[]>;
  searchByKeyword(query: string): Promise<Restaurant[]>;
  delete(id: string): Promise<void>;
  softDelete(id: string): Promise<void>;
}

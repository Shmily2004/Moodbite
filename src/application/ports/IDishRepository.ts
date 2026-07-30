import type { Dish } from "../../domain/entities/Dish";

export interface IDishRepository {
  save(dish: Dish): Promise<Dish>;
  findById(id: string): Promise<Dish | null>;
  findAll(): Promise<Dish[]>;
  findActive(): Promise<Dish[]>;
  findByRestaurantId(restaurantId: string): Promise<Dish[]>;
  findByCategory(category: string): Promise<Dish[]>;
  findByMoodKeywords(keywords: string[]): Promise<Dish[]>;
  findByPriceRange(minPrice: number, maxPrice: number): Promise<Dish[]>;
  findBySpiceAndTemperature(
    spiceLevel: number,
    temperature: Dish["temperature"]
  ): Promise<Dish[]>;
  searchByNameOrCategory(query: string): Promise<Dish[]>;
  delete(id: string): Promise<void>;
  softDelete(id: string): Promise<void>;
}

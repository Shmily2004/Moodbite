import type { Dish } from "../../domain/entities/Dish";
import type { IDishRepository } from "../../application/ports/IDishRepository";

export class InMemoryDishRepository implements IDishRepository {
  private readonly dishes: Dish[] = [
    {
      id: "dish-1",
      restaurant_id: "restaurant-1",
      name: "Phở bò",
      category: "soup",
      spice_level: 1,
      temperature: "hot",
      portion_size: "regular",
      mood_keywords: ["comfort", "cozy"],
      price: 45000,
      is_active: true,
      updated_by: "crawler",
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-01T00:00:00.000Z",
    },
    {
      id: "dish-2",
      restaurant_id: "restaurant-2",
      name: "Bánh mì chay",
      category: "sandwich",
      spice_level: 0,
      temperature: "neutral",
      portion_size: "light",
      mood_keywords: ["fresh", "quick"],
      price: 30000,
      is_active: true,
      updated_by: "batch_pipeline",
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-01T00:00:00.000Z",
    },
    {
      id: "dish-3",
      restaurant_id: "restaurant-3",
      name: "Cà ri đậu phụ",
      category: "curry",
      spice_level: 2,
      temperature: "hot",
      portion_size: "regular",
      mood_keywords: ["spicy", "comfort"],
      price: 55000,
      is_active: true,
      updated_by: "manual",
      created_at: "2026-01-01T00:00:00.000Z",
      updated_at: "2026-01-01T00:00:00.000Z",
    },
  ];

  async save(dish: Dish): Promise<Dish> {
    const existingIndex = this.dishes.findIndex((item) => item.id === dish.id);
    if (existingIndex >= 0) {
      this.dishes[existingIndex] = dish;
      return dish;
    }

    this.dishes.push(dish);
    return dish;
  }

  async findById(id: string): Promise<Dish | null> {
    return this.dishes.find((dish) => dish.id === id) ?? null;
  }

  async findAll(): Promise<Dish[]> {
    return this.dishes.filter((dish) => dish.is_active);
  }

  async findActive(): Promise<Dish[]> {
    return this.findAll();
  }

  async findByRestaurantId(restaurantId: string): Promise<Dish[]> {
    return this.dishes.filter((dish) => dish.restaurant_id === restaurantId && dish.is_active);
  }

  async findByCategory(category: string): Promise<Dish[]> {
    return this.dishes.filter((dish) => dish.category?.toLowerCase() === category.toLowerCase() && dish.is_active);
  }

  async findByMoodKeywords(keywords: string[]): Promise<Dish[]> {
    const normalizedKeywords = keywords.map((keyword) => keyword.toLowerCase());
    return this.dishes.filter((dish) => {
      const dishKeywords = (dish.mood_keywords ?? []).map((keyword) => keyword.toLowerCase());
      return normalizedKeywords.some((keyword) => dishKeywords.includes(keyword)) && dish.is_active;
    });
  }

  async findByPriceRange(minPrice: number, maxPrice: number): Promise<Dish[]> {
    return this.dishes.filter((dish) => {
      const price = dish.price ?? Number.POSITIVE_INFINITY;
      return dish.is_active && price >= minPrice && price <= maxPrice;
    });
  }

  async findBySpiceAndTemperature(spiceLevel: number, temperature: Dish["temperature"]): Promise<Dish[]> {
    return this.dishes.filter(
      (dish) => dish.is_active && dish.spice_level === spiceLevel && dish.temperature === temperature
    );
  }

  async searchByNameOrCategory(query: string): Promise<Dish[]> {
    const normalizedQuery = query.toLowerCase();
    return this.dishes.filter((dish) => {
      const haystack = `${dish.name} ${dish.category ?? ""}`.toLowerCase();
      return dish.is_active && haystack.includes(normalizedQuery);
    });
  }

  async delete(id: string): Promise<void> {
    const index = this.dishes.findIndex((dish) => dish.id === id);
    if (index >= 0) {
      this.dishes.splice(index, 1);
    }
  }

  async softDelete(id: string): Promise<void> {
    const dish = this.dishes.find((item) => item.id === id);
    if (dish) {
      dish.is_active = false;
    }
  }
}

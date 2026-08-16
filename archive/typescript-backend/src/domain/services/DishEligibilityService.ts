import type { Dish } from "../entities/Dish";

/**
 * Enforces ranking rule: only active dishes may enter the candidate pool.
 * Filtering must happen before ranking, never after.
 */
export class DishEligibilityService {
  filterActiveCandidates(dishes: Dish[]): Dish[] {
    return dishes.filter((dish) => dish.is_active);
  }

  isEligible(dish: Dish): boolean {
    return dish.is_active;
  }
}

import { SuggestDishForUserUseCase } from "../application/use-cases/SuggestDishForUserUseCase";
import { InMemoryDishRepository } from "../infrastructure/adapters/InMemoryDishRepository";
import { InMemoryUserContextRepository } from "../infrastructure/adapters/InMemoryUserContextRepository";
import { InMemoryRestaurantRepository } from "../infrastructure/adapters/InMemoryRestaurantRepository";
import { SuggestDishController } from "../presentation/controllers/SuggestDishController";

export function buildAppContainer() {
  const dishRepository = new InMemoryDishRepository();
  const userContextRepository = new InMemoryUserContextRepository();
  const restaurantRepository = new InMemoryRestaurantRepository();
  const suggestDishUseCase = new SuggestDishForUserUseCase(
    userContextRepository,
    dishRepository,
    restaurantRepository
  );
  const suggestDishController = new SuggestDishController(suggestDishUseCase);

  return {
    dishRepository,
    userContextRepository,
    restaurantRepository,
    suggestDishUseCase,
    suggestDishController,
  };
}
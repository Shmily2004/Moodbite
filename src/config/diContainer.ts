import { SuggestDishForUserUseCase } from "../application/use-cases/SuggestDishForUserUseCase";
import { InMemoryDishRepository } from "../infrastructure/adapters/InMemoryDishRepository";
import { InMemoryUserContextRepository } from "../infrastructure/adapters/InMemoryUserContextRepository";
import { SuggestDishController } from "../presentation/controllers/SuggestDishController";

export function buildAppContainer() {
  const dishRepository = new InMemoryDishRepository();
  const userContextRepository = new InMemoryUserContextRepository();
  const suggestDishUseCase = new SuggestDishForUserUseCase(userContextRepository, dishRepository);
  const suggestDishController = new SuggestDishController(suggestDishUseCase);

  return {
    dishRepository,
    userContextRepository,
    suggestDishUseCase,
    suggestDishController,
  };
}

import { SuggestDishForUserUseCase } from "../../application/use-cases/SuggestDishForUserUseCase";

export class SuggestDishController {
  constructor(private readonly useCase: SuggestDishForUserUseCase) {}

  async handle(userId: string) {
    return this.useCase.execute(userId);
  }
}

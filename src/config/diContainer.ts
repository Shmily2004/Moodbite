import { SuggestDishForUserUseCase } from "../application/use-cases/SuggestDishForUserUseCase";
import { InMemoryDishRepository } from "../infrastructure/adapters/InMemoryDishRepository";
import { InMemoryUserContextRepository } from "../infrastructure/adapters/InMemoryUserContextRepository";
import { InMemoryRestaurantRepository } from "../infrastructure/adapters/InMemoryRestaurantRepository";
import { CsvDishRepository } from "../infrastructure/adapters/CsvDishRepository";
import { CsvRestaurantRepository } from "../infrastructure/adapters/CsvRestaurantRepository";
import { SuggestDishController } from "../presentation/controllers/SuggestDishController";
import type { IDishRepository } from "../application/ports/IDishRepository";
import type { IRestaurantRepository } from "../application/ports/IRestaurantRepository";

export function buildAppContainer() {
  const userContextRepository = new InMemoryUserContextRepository();

  // Ưu tiên dữ liệu thật từ data_pipeline (546+ quán ăn Hà Nội đã cào + xử lý).
  // Nếu chưa chạy pipeline Python (file CSV chưa tồn tại), fallback về dữ liệu mẫu
  // in-memory thay vì crash toàn bộ app - đúng nguyên tắc graceful degradation đã
  // áp dụng nhất quán trong toàn bộ data_pipeline (Python).
  let dishRepository: IDishRepository;
  let restaurantRepository: IRestaurantRepository;
  try {
    dishRepository = new CsvDishRepository();
    restaurantRepository = new CsvRestaurantRepository();
    console.log("[diContainer] Đã tải dữ liệu thật từ data_pipeline (CSV).");
  } catch (error) {
    console.warn(
      "[diContainer] Chưa có dữ liệu thật từ data_pipeline, dùng dữ liệu mẫu (InMemory). " +
        "Chạy `python -m data_pipeline.merge_and_prepare_raw && python -m data_pipeline.data_cleaning " +
        "&& python -m data_pipeline.feature_engineering` để có dữ liệu thật.\n" +
        (error instanceof Error ? error.message : String(error))
    );
    dishRepository = new InMemoryDishRepository();
    restaurantRepository = new InMemoryRestaurantRepository();
  }

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
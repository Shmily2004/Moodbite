import type { IDishRepository } from "../ports/IDishRepository";
import type { IUserContextRepository } from "../ports/IUserContextRepository";
import type { SuggestDishForUserResponseDto } from "../dtos/SuggestDishForUserResponseDto";

/**
 * DTO phản hồi cho use case đề xuất món ăn.
 *
 * Vì use case là lớp điều phối ứng dụng, nó không nên trả về Entity trực tiếp ra ngoài vì:
 * - Entity thuộc tầng domain, có thể chứa dữ liệu raw và đủ trường để biểu diễn mô hình nghiệp vụ.
 * - Controller/API layer cần một cấu trúc dữ liệu ổn định, dễ serialize, và có thể đổi khác mà không ảnh hưởng
 *   trực tiếp đến domain model.
 * - DTO giúp tách interface giữa tầng application và presentation, tránh “rò” cấu trúc domain ra khỏi API.
 */
/**
 * Use case đầu tiên cho Moodbite: đề xuất món ăn cho một người dùng dựa trên ngữ cảnh tìm kiếm.
 *
 * Luồng chạy của use case này:
 * 1. Controller hoặc một tầng presentation gọi use case bằng cách truyền userId.
 * 2. Use case nhận đầu vào và dùng IUserContextRepository để lấy ngữ cảnh của người dùng.
 * 3. Nếu không tìm thấy ngữ cảnh, use case trả về kết quả rỗng để controller có thể quyết định
 *    cách hiển thị cho phía client.
 * 4. Nếu có ngữ cảnh, use case dùng IDishRepository để tìm các món ăn phù hợp với mood/context.
 *    - Trong triển khai hiện tại, việc “phù hợp” được mô tả bằng cách kết hợp các tiêu chí nghiệp vụ:
 *      + mood keywords
 *      + khoảng giá
 *      + hạn chế dinh dưỡng
 *      + điều kiện thời gian/điều kiện sử dụng.
 *    - Đây là nơi logic điều phối diễn ra: use case phối hợp nhiều repository lại với nhau và chuyển
 *      dữ liệu từ domain sang một cấu trúc dễ dùng cho application/presentation.
 * 5. Use case trả về DTO, không trả Entity trực tiếp, để tầng ngoài không phụ thuộc vào cấu trúc domain.
 *
 * Vì sao use case là nơi điều phối logic mà không phải Entity hay Controller?
 * - Entity: chỉ chứa trạng thái và quy tắc nghiệp vụ cốt lõi của chính nó. Entity không nên biết
 *   về việc “lấy dữ liệu từ repository”, “ghép dữ liệu từ nhiều nguồn” hay “định hình output cho API”.
 * - Controller: chỉ chịu trách nhiệm nhận request và chuyển tiếp tới use case. Controller không nên có
 *   logic nghiệp vụ phức tạp, bởi nó chỉ là lớp điều phối giao tiếp.
 * - Use case: là điểm nối giữa các dependency và nghiệp vụ. Nó orchestrates các bước thực hiện, quyết định
 *   flow, gọi đúng repository, và biến kết quả thành một contract phù hợp cho ứng dụng.
 *
 * Nói ngắn gọn: Entity mô tả “điều gì là đúng” cho domain, Controller mô tả “đầu vào/đầu ra giao tiếp”,
 * còn Use Case mô tả “một quy trình nghiệp vụ cụ thể sẽ diễn ra như thế nào”.
 */
export class SuggestDishForUserUseCase {
  constructor(
    private readonly userContextRepository: IUserContextRepository,
    private readonly dishRepository: IDishRepository
  ) {}

  /**
   * Thực thi use case.
   */
  async execute(userId: string): Promise<SuggestDishForUserResponseDto> {
    const userContext = await this.userContextRepository.findByUserId(userId);

    if (!userContext) {
      return {
        userId,
        context: null,
        suggestedDishes: [],
      };
    }

    const moodKeywords = userContext.review_summary
      ? this.extractMoodKeywords(userContext.review_summary)
      : [];

    const keywordMatches = moodKeywords.length > 0
      ? await this.dishRepository.findByMoodKeywords(moodKeywords)
      : [];

    const budgetMatches = userContext.budget_constraint
      ? await this.dishRepository.findByPriceRange(0, userContext.budget_constraint)
      : [];

    const dietaryConstraints = userContext.dietary_constraint ?? [];
    const dietaryMatches = dietaryConstraints.length > 0
      ? this.filterByDietaryConstraints(await this.dishRepository.findAll(), dietaryConstraints)
      : [];

    const combinedDishes = this.mergeDishResults(keywordMatches, budgetMatches, dietaryMatches);

    return {
      userId,
      context: {
        sessionId: userContext.session_id,
        queryText: userContext.query_text,
        latitude: userContext.latitude,
        longitude: userContext.longitude,
        budgetConstraint: userContext.budget_constraint,
        dietaryConstraints: userContext.dietary_constraint,
        hoursConstraint: userContext.hours_constraint,
        weatherSignal: userContext.weather_signal,
        trafficSignal: userContext.traffic_signal,
        timeSignal: userContext.time_signal,
        experienceClusterId: userContext.experience_cluster_id,
        reviewSummary: userContext.review_summary,
      },
      suggestedDishes: combinedDishes.map((dish) => ({
        id: dish.id,
        name: dish.name,
        category: dish.category,
        spiceLevel: dish.spice_level,
        temperature: dish.temperature,
        portionSize: dish.portion_size,
        moodKeywords: dish.mood_keywords,
        price: dish.price,
      })),
    };
  }

  /**
   * Trích xuất các từ khóa cảm xúc từ review_summary.
   * Đây là một quy tắc đơn giản ở tầng application để chuyển ngữ cảnh text thành dữ liệu có thể dùng cho repository.
   */
  private extractMoodKeywords(reviewSummary: string): string[] {
    const normalized = reviewSummary.toLowerCase();
    const keywords = new Set<string>();

    if (normalized.includes("comfort")) keywords.add("comfort");
    if (normalized.includes("cozy")) keywords.add("cozy");
    if (normalized.includes("spicy")) keywords.add("spicy");
    if (normalized.includes("fresh")) keywords.add("fresh");
    if (normalized.includes("sweet")) keywords.add("sweet");
    if (normalized.includes("cheap")) keywords.add("cheap");
    if (normalized.includes("quick")) keywords.add("quick");

    return Array.from(keywords);
  }

  /**
   * Lọc các món ăn phù hợp với các hạn chế dinh dưỡng.
   */
  private filterByDietaryConstraints(dishes: Array<{ name: string; category?: string | null }>, dietaryConstraints: string[]): Array<{ name: string; category?: string | null }> {
    if (dietaryConstraints.length === 0) {
      return dishes;
    }

    return dishes.filter((dish) => {
      const dishText = `${dish.name} ${dish.category ?? ""}`.toLowerCase();
      return dietaryConstraints.every((constraint) => {
        const normalizedConstraint = constraint.toLowerCase();
        return dishText.includes(normalizedConstraint);
      });
    });
  }

  /**
   * Gộp và làm sạch kết quả từ các nguồn lọc khác nhau.
   */
  private mergeDishResults(
    keywordMatches: Array<{ id: string; name: string; category?: string | null; spice_level?: number | null; temperature?: "hot" | "cold" | "neutral" | null; portion_size?: "light" | "regular" | "heavy" | null; mood_keywords?: string[] | null; price?: number | null; }>,
    budgetMatches: Array<{ id: string; name: string; category?: string | null; spice_level?: number | null; temperature?: "hot" | "cold" | "neutral" | null; portion_size?: "light" | "regular" | "heavy" | null; mood_keywords?: string[] | null; price?: number | null; }>,
    dietaryMatches: Array<{ name: string; category?: string | null }>
  ) {
    const seen = new Map<string, { id: string; name: string; category?: string | null; spice_level?: number | null; temperature?: "hot" | "cold" | "neutral" | null; portion_size?: "light" | "regular" | "heavy" | null; mood_keywords?: string[] | null; price?: number | null; }>;

    const addDish = (dish: { id: string; name: string; category?: string | null; spice_level?: number | null; temperature?: "hot" | "cold" | "neutral" | null; portion_size?: "light" | "regular" | "heavy" | null; mood_keywords?: string[] | null; price?: number | null; }) => {
      if (!seen.has(dish.id)) {
        seen.set(dish.id, dish);
      }
    };

    keywordMatches.forEach(addDish);
    budgetMatches.forEach(addDish);

    const dietaryDishIds = new Set(dietaryMatches.map((dish) => dish.name.toLowerCase()));
    const result = Array.from(seen.values());

    return result.filter((dish) => {
      if (dietaryMatches.length === 0) {
        return true;
      }

      return dietaryDishIds.has(dish.name.toLowerCase());
    });
  }
}

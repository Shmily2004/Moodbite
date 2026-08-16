import type { IDishRepository } from "../ports/IDishRepository";
import type { IUserContextRepository } from "../ports/IUserContextRepository";
import type { IRestaurantRepository } from "../ports/IRestaurantRepository";
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
 * 5. Sau khi có danh sách món ăn đề xuất, use case dùng restaurant_id của từng món để tra
 *    IRestaurantRepository và trả về danh sách quán tương ứng (chỉ lấy quán is_active = true).
 *    Đây là bước "món ăn trước, quán sau" đúng theo luồng UX: người dùng thấy món phù hợp trước,
 *    sau đó mới thấy quán nào đang bán món đó.
 * 6. Use case trả về DTO, không trả Entity trực tiếp, để tầng ngoài không phụ thuộc vào cấu trúc domain.
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
/**
 * Kiểu dữ liệu rút gọn cho món ăn dùng nội bộ trong use case (không phải Entity đầy đủ).
 * restaurant_id bắt buộc có mặt vì đây là khóa để tra ra quán ở bước 5 của luồng use case.
 */
type DishSummary = {
  id: string;
  name: string;
  category?: string | null;
  spice_level?: number | null;
  temperature?: "hot" | "cold" | "neutral" | null;
  portion_size?: "light" | "regular" | "heavy" | null;
  mood_keywords?: string[] | null;
  price?: number | null;
  restaurant_id: string;
};

/**
 * Giới hạn mặc định số lượng món ăn/quán trả về trong 1 lần gọi. Không giới hạn sẽ
 * trả về TẤT CẢ món khớp ít nhất 1 tiêu chí (mood HOẶC budget HOẶC dietary) - với
 * dataset nhỏ (vài quán mẫu) không thấy vấn đề, nhưng với dataset thật (3711 quán ở
 * Hà Nội) có thể trả về hàng nghìn kết quả trong 1 response, vừa vô dụng cho UX
 * (không ai xem hết 1000+ gợi ý) vừa nặng cho payload API.
 */
const DEFAULT_MAX_RESULTS = 20;

export class SuggestDishForUserUseCase {
  constructor(
    private readonly userContextRepository: IUserContextRepository,
    private readonly dishRepository: IDishRepository,
    private readonly restaurantRepository: IRestaurantRepository
  ) {}

  /**
   * Thực thi use case.
   */
  async execute(userId: string, maxResults: number = DEFAULT_MAX_RESULTS): Promise<SuggestDishForUserResponseDto> {
    const userContext = await this.userContextRepository.findByUserId(userId);

    if (!userContext) {
      return {
        userId,
        context: null,
        suggestedDishes: [],
        suggestedRestaurants: [],
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

    const combinedDishes = this.mergeDishResults(keywordMatches, budgetMatches, dietaryMatches, maxResults);

    const suggestedRestaurants = await this.resolveRestaurantsForDishes(combinedDishes);

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
        restaurantId: dish.restaurant_id,
      })),
      suggestedRestaurants,
    };
  }

  /**
   * Từ danh sách món ăn đã được đề xuất, gom nhóm theo restaurant_id rồi tra IRestaurantRepository
   * để lấy thông tin quán. Chỉ trả về quán đang is_active = true, đúng nguyên tắc lọc TRƯỚC khi
   * đưa vào kết quả hiển thị (không hiển thị quán đã ngừng hoạt động dù món của nó khớp tiêu chí).
   */
  private async resolveRestaurantsForDishes(
    dishes: Array<{ id: string; restaurant_id: string }>
  ): Promise<SuggestDishForUserResponseDto["suggestedRestaurants"]> {
    const dishIdsByRestaurant = new Map<string, string[]>();
    // dishes đã được sắp xếp theo mức độ khớp giảm dần (từ mergeDishResults) - dùng
    // VỊ TRÍ trong mảng làm đại diện cho thứ hạng khớp (nhỏ hơn = khớp tốt hơn),
    // không cần truyền riêng điểm số ra khỏi mergeDishResults.
    const bestRankByRestaurant = new Map<string, number>();

    dishes.forEach((dish, index) => {
      const existing = dishIdsByRestaurant.get(dish.restaurant_id);
      if (existing) {
        existing.push(dish.id);
      } else {
        dishIdsByRestaurant.set(dish.restaurant_id, [dish.id]);
      }

      const currentBest = bestRankByRestaurant.get(dish.restaurant_id);
      if (currentBest === undefined || index < currentBest) {
        bestRankByRestaurant.set(dish.restaurant_id, index);
      }
    });

    const restaurantIds = Array.from(dishIdsByRestaurant.keys());
    const restaurants = await Promise.all(
      restaurantIds.map((id) => this.restaurantRepository.findById(id))
    );

    type RankedRestaurant = SuggestDishForUserResponseDto["suggestedRestaurants"][number] & {
      rank: number;
    };
    const ranked: RankedRestaurant[] = [];

    restaurants.forEach((restaurant, index) => {
      if (!restaurant || !restaurant.is_active || restaurant.deleted_at) {
        return;
      }

      ranked.push({
        id: restaurant.id,
        name: restaurant.name,
        address: restaurant.address,
        latitude: restaurant.latitude,
        longitude: restaurant.longitude,
        rating: restaurant.rating,
        priceRange: restaurant.price_range,
        dishIds: dishIdsByRestaurant.get(restaurantIds[index]) ?? [],
        rank: bestRankByRestaurant.get(restaurant.id) ?? Number.MAX_SAFE_INTEGER,
      });
    });

    // Sắp xếp 2 cấp: (1) thứ hạng khớp mood/budget của món TỐT NHẤT quán đó có (rank
    // nhỏ hơn = khớp tốt hơn, giữ đúng thứ tự ưu tiên chính), (2) khi bằng rank, ưu
    // tiên rating cao hơn (quán không có rating xếp cuối trong nhóm hòa, KHÔNG bị
    // coi là 0 sao thật). Cần bước (2) vì ~48% dataset có categoryName chung chung
    // ("Nhà hàng") không tạo được tín hiệu mood rõ ràng -> rất nhiều quán hòa rank,
    // rating là tiêu chí phân biệt duy nhất còn lại trong nhóm đó.
    ranked.sort((a, b) => {
      const rankDiff = a.rank - b.rank;
      if (rankDiff !== 0) return rankDiff;
      return (b.rating ?? -1) - (a.rating ?? -1);
    });

    return ranked.map(({ rank, ...rest }) => rest);
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
  /**
   * Gộp kết quả từ các nguồn lọc khác nhau, xếp hạng theo mức độ khớp (món khớp
   * càng nhiều tiêu chí - mood/budget - càng được ưu tiên lên đầu), rồi giới hạn
   * số lượng trả về theo maxResults. Trước đây hàm này trả về TOÀN BỘ union không
   * giới hạn, gây ra response khổng lồ (1332+ quán) khi chạy trên dataset thật.
   */
  private mergeDishResults(
    keywordMatches: DishSummary[],
    budgetMatches: DishSummary[],
    dietaryMatches: Array<{ name: string; category?: string | null }>,
    maxResults: number
  ): DishSummary[] {
    const dishById = new Map<string, DishSummary>();
    const matchScoreById = new Map<string, number>();

    const addDish = (dish: DishSummary) => {
      if (!dishById.has(dish.id)) {
        dishById.set(dish.id, dish);
      }
      matchScoreById.set(dish.id, (matchScoreById.get(dish.id) ?? 0) + 1);
    };

    keywordMatches.forEach(addDish);
    budgetMatches.forEach(addDish);

    const dietaryDishNames = new Set(dietaryMatches.map((dish) => dish.name.toLowerCase()));

    let candidates = Array.from(dishById.values());

    // Dietary constraint là điều kiện LỌC CỨNG (loại hẳn nếu không khớp), không phải
    // điểm cộng thêm - món không đáp ứng hạn chế dinh dưỡng thì loại khỏi kết quả.
    if (dietaryMatches.length > 0) {
      candidates = candidates.filter((dish) => dietaryDishNames.has(dish.name.toLowerCase()));
    }

    candidates.sort((a, b) => (matchScoreById.get(b.id) ?? 0) - (matchScoreById.get(a.id) ?? 0));

    return candidates.slice(0, maxResults);
  }
}
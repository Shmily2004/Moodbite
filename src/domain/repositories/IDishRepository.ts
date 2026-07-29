import type { Dish } from "../entities/Dish";

/**
 * Interface repository cho thực thể Dish.
 *
 * Đây là một Port trong Clean Architecture, tức là một hợp đồng nghiệp vụ mà tầng Application
 * có thể phụ thuộc vào. Nó nói lên: “các use case cần thao tác với Dish bằng những thao tác nào?”
 * nhưng không nói lên cách lưu trữ dữ liệu sẽ diễn ra như thế nào.
 *
 * Vì sao phải tách thành interface thay vì viết class truy vấn trực tiếp ngay trong domain?
 * - Bởi vì Domain phải thuần khiết: nó không nên biết có đang dùng PostgreSQL, MongoDB, file JSON,
 *   hay một adapter nào khác để lưu Dish.
 * - Bởi vì use case chỉ cần biết “tôi có thể lấy món ăn, lưu món ăn, tìm theo điều kiện nghiệp vụ”
 *   chứ không cần biết SQL/ORM được viết ra như thế nào.
 * - Bởi vì khi đổi công nghệ hoặc thay cơ sở dữ liệu, chúng ta chỉ cần viết một adapter mới implement
 *   interface này mà không phải chỉnh lại toàn bộ logic nghiệp vụ.
 * - Bởi vì việc mock interface trong unit test trở nên rất dễ dàng, giúp test logic nghiệp vụ độc lập
 *   khỏi hạ tầng.
 *
 * Khi một người mới học Clean Architecture nhìn vào interface này, họ nên hiểu rằng đây là “bản hợp đồng
 * giữa nghiệp vụ và hạ tầng”, không phải là implementation cụ thể.
 */
export interface IDishRepository {
  /**
   * Lưu một Dish mới hoặc cập nhật Dish đã tồn tại.
   * Cách thức lưu trữ được giao cho adapter ở Infrastructure.
   */
  save(dish: Dish): Promise<Dish>;

  /**
   * Tìm Dish theo id.
   */
  findById(id: string): Promise<Dish | null>;

  /**
   * Lấy toàn bộ Dish đang hoạt động và chưa bị xóa logic.
   */
  findAll(): Promise<Dish[]>;

  /**
   * Lấy các Dish đang hoạt động.
   */
  findActive(): Promise<Dish[]>;

  /**
   * Lấy các Dish thuộc một nhà hàng cụ thể.
   * Đây là truy vấn rất phổ biến trong hệ thống gợi ý món ăn theo nơi đang mở.
   */
  findByRestaurantId(restaurantId: string): Promise<Dish[]>;

  /**
   * Lấy các Dish theo category.
   * Phù hợp cho việc duyệt theo nhóm món ăn như “dessert”, “viet”, “drink”.
   */
  findByCategory(category: string): Promise<Dish[]>;

  /**
   * Tìm các Dish phù hợp với các từ khóa cảm xúc hoặc mood.
   * Đây là một truy vấn “nghiệp vụ” đặc thù cho Moodbite vì hệ thống đánh giá món ăn
   * dựa trên cảm xúc và ngữ cảnh người dùng.
   */
  findByMoodKeywords(keywords: string[]): Promise<Dish[]>;

  /**
   * Tìm Dish theo mức giá.
   * Trong ứng dụng recommendation, điều này giúp lọc những món phù hợp với ngân sách.
   */
  findByPriceRange(minPrice: number, maxPrice: number): Promise<Dish[]>;

  /**
   * Tìm Dish theo mức độ cay và nhiệt độ phục vụ.
   * Đây là ví dụ cho các truy vấn đặc thù hơn, không chỉ CRUD cơ bản.
   */
  findBySpiceAndTemperature(
    spiceLevel: number,
    temperature: Dish["temperature"]
  ): Promise<Dish[]>;

  /**
   * Tìm kiếm Dish theo tên hoặc danh mục một cách linh hoạt.
   */
  searchByNameOrCategory(query: string): Promise<Dish[]>;

  /**
   * Xóa Dish khỏi hệ thống.
   * Ở tầng domain, chúng ta chỉ cần contract “xóa”, không cần biết xóa thật hay xóa logic.
   */
  delete(id: string): Promise<void>;

  /**
   * Xóa logic Dish bằng cách đánh dấu trạng thái không hoạt động.
   */
  softDelete(id: string): Promise<void>;
}

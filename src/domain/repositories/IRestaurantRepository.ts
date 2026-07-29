import type { Restaurant } from "../entities/Restaurant";

/**
 * Interface repository cho thực thể Restaurant.
 *
 * Restaurant là một aggregate core trong hệ thống Moodbite vì các gợi ý món ăn và trải nghiệm đều
 * bắt đầu từ nhà hàng. Interface này định nghĩa những gì use case cần từ một “nguồn dữ liệu nhà hàng”
 * mà không làm lộ chi tiết công nghệ lưu trữ.
 *
 * Việc tách thành interface giúp:
 * - Use case có thể lấy nhà hàng theo vị trí, mức giá, cụm trải nghiệm mà không cần biết hệ thống dùng
 *   PostgreSQL, vector search, Elasticsearch, hay cache.
 * - Logic nghiệp vụ có thể được test bằng mock repository độc lập với hạ tầng.
 * - Phần triển khai trong Infrastructure có thể dùng nhiều adapter khác nhau cho nhiều mục đích như
 *   runtime API, offline crawler, hoặc dữ liệu thử nghiệm.
 */
export interface IRestaurantRepository {
  /**
   * Lưu một Restaurant mới hoặc cập nhật một Restaurant đã tồn tại.
   */
  save(restaurant: Restaurant): Promise<Restaurant>;

  /**
   * Tìm Restaurant theo id.
   */
  findById(id: string): Promise<Restaurant | null>;

  /**
   * Lấy toàn bộ Restaurant đang hoạt động và chưa bị xóa logic.
   */
  findAll(): Promise<Restaurant[]>;

  /**
   * Lấy các Restaurant đang hoạt động.
   */
  findActive(): Promise<Restaurant[]>;

  /**
   * Tìm Restaurant theo tên.
   */
  findByName(name: string): Promise<Restaurant[]>;

  /**
   * Tìm Restaurant theo id bên ngoài từ nguồn dữ liệu ban đầu.
   * Đây là truy vấn rất hữu ích để tránh tạo bản ghi trùng trong quá trình crawl hoặc đồng bộ dữ liệu.
   */
  findByExternalPlaceId(externalPlaceId: string): Promise<Restaurant | null>;

  /**
   * Tìm các nhà hàng gần một vị trí cho trước, theo bán kính km.
   * Đây là truy vấn nghiệp vụ cốt lõi cho Moodbite vì hệ thống hết sức quan trọng với việc gợi ý theo vị trí.
   */
  findNearby(latitude: number, longitude: number, radiusKm: number): Promise<Restaurant[]>;

  /**
   * Lấy các nhà hàng thuộc một cụm trải nghiệm cụ thể.
   * Truy vấn này phù hợp với hệ thống phân cụm trải nghiệm người dùng và recommendation theo nhóm nhu cầu.
   */
  findByExperienceCluster(clusterId: number): Promise<Restaurant[]>;

  /**
   * Lọc nhà hàng theo mức giá.
   */
  findByPriceRange(minPrice: number, maxPrice: number): Promise<Restaurant[]>;

  /**
   * Tìm kiếm theo từ khóa chữ, có thể dùng cho tìm kiếm tên hoặc mô tả ngắn.
   */
  searchByKeyword(query: string): Promise<Restaurant[]>;

  /**
   * Xóa Restaurant khỏi hệ thống.
   */
  delete(id: string): Promise<void>;

  /**
   * Xóa logic Restaurant bằng cách đánh dấu không hoạt động.
   */
  softDelete(id: string): Promise<void>;
}

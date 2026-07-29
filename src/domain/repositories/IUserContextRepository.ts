import type { UserContext } from "../entities/UserContext";

/**
 * Interface repository cho thực thể UserContext.
 *
 * UserContext là ngữ cảnh tìm kiếm của người dùng tại một thời điểm nhất định. Nó không phải là một
 * “entity kinh doanh” theo cách truyền thống như Restaurant hay Dish, nhưng nó vẫn là một loại dữ liệu
 * cốt lõi trong Moodbite vì hệ thống recommendation phụ thuộc rất nhiều vào bối cảnh người dùng:
 * ngân sách, hạn chế dinh dưỡng, thời tiết, lưu lượng giao thông và thời gian.
 *
 * Interface này định nghĩa các thao tác cần thiết để capture và truy xuất ngữ cảnh người dùng mà không
 * làm lộ cách dữ liệu này được lưu trữ. Điều này rất quan trọng vì một ngày nào đó hệ thống có thể dùng
 * event store, log, cache, hoặc database phân tích khác nhau cho UserContext.
 *
 * Nếu không tách interface, logic use case sẽ bị gắn chặt vào cách lưu ngữ cảnh, và rất khó để đổi sang
 * model phân tích khác hoặc test các quy tắc recommendation mà không cần phụ thuộc vào hạ tầng.
 */
export interface IUserContextRepository {
  /**
   * Lưu một ngữ cảnh tìm kiếm mới hoặc cập nhật chuỗi hành vi của một phiên.
   */
  save(context: UserContext): Promise<UserContext>;

  /**
   * Tìm ngữ cảnh theo userId.
   * Đây là thao tác phù hợp cho use case phân tích đề xuất món ăn cho một người dùng cụ thể.
   */
  findByUserId(userId: string): Promise<UserContext | null>;

  /**
   * Tìm ngữ cảnh theo session_id.
   * Đây là thao tác cơ bản nhất để lấy lại bối cảnh của một lượt tìm kiếm cụ thể.
   */
  findBySessionId(sessionId: string): Promise<UserContext | null>;

  /**
   * Lấy lịch sử gần đây của một session.
   * Trong Moodbite, việc theo dõi chuỗi tìm kiếm của người dùng có thể giúp hệ thống hiểu xu hướng và
   * cải thiện gợi ý theo thời gian.
   */
  findRecentBySession(sessionId: string, limit: number): Promise<UserContext[]>;

  /**
   * Tìm các UserContext gần một vị trí cho trước.
   * Điều này hữu ích cho các phân tích địa lý hoặc phục vụ recommendation theo vùng lân cận.
   */
  findRecentByLocation(
    latitude: number,
    longitude: number,
    radiusKm: number,
    limit: number
  ): Promise<UserContext[]>;

  /**
   * Tìm các ngữ cảnh có ràng buộc ngân sách phù hợp với một mức tối đa cho trước.
   */
  findByBudgetConstraint(maxBudget: number): Promise<UserContext[]>;

  /**
   * Tìm các ngữ cảnh có các hạn chế dinh dưỡng cụ thể.
   */
  findByDietaryConstraint(dietaryConstraints: string[]): Promise<UserContext[]>;

  /**
   * Xóa toàn bộ ngữ cảnh của một session nếu cần.
   */
  deleteBySessionId(sessionId: string): Promise<void>;
}

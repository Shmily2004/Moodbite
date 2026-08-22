/**
 * Danh sách MÓN ĂN. Tầng `widgets`: ghép entity lại, KHÔNG tự gọi API.
 *
 * HAI KIỂU BÀY, theo `design/Home.jpg`:
 *   - `row`  (mặc định) — một HÀNG NGANG trượt được, đúng như bản thiết kế.
 *   - `grid` — lưới nhiều dòng, hiện ra khi người dùng bấm "Xem tất cả".
 *
 * VÌ SAO HÀNG NGANG LÀ MẶC ĐỊNH: trang chủ có nhiều khối (mood, nhu cầu, kết quả). Một
 * lưới 30 món đẩy mọi thứ phía dưới ra khỏi màn hình, người dùng không biết còn gì nữa.
 */
import type { DishItem } from '@/shared/api';
import { DishCard } from '@/entities/dish';

interface DishListProps {
  dishes: DishItem[];
  onOpen: (dish: DishItem) => void;
  layout?: 'row' | 'grid';
  isSaved?: (dish: DishItem) => boolean;
  onToggleSave?: (dish: DishItem) => void;
}

export function DishList({
  dishes,
  onOpen,
  layout = 'row',
  isSaved,
  onToggleSave,
}: DishListProps) {
  return (
    <ul className={layout === 'row' ? 'dishes dishes--row' : 'dishes dishes--grid'}>
      {dishes.map((dish) => (
        <DishCard
          key={dish.dish_id}
          dish={dish}
          onOpen={onOpen}
          saved={isSaved?.(dish) ?? false}
          onToggleSave={onToggleSave}
        />
      ))}
    </ul>
  );
}

/** Vệt xương lúc đang tải - báo "sắp có nội dung" thay vì để chỗ trống trơn. */
export function DishListSkeleton({ layout = 'row' }: { layout?: 'row' | 'grid' }) {
  return (
    <ul
      className={layout === 'row' ? 'dishes dishes--row' : 'dishes dishes--grid'}
      aria-busy="true"
      aria-label="Đang tìm món"
    >
      {[0, 1, 2, 3, 4].map((i) => (
        <li key={i} className="dishcard-wrap">
          <div className="dishcard dishcard--skeleton">
            <div className="dishcard__media">
              <div className="dishcard__thumb dishcard__thumb--skeleton" />
            </div>
            <div className="dishcard__body">
              <span className="skeleton-line skeleton-line--title" />
              <span className="skeleton-line" />
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

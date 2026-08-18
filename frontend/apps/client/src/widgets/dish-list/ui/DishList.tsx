/**
 * Lưới MÓN ĂN. Tầng `widgets`: ghép entity lại, KHÔNG tự gọi API.
 *
 * Tách khỏi trang để trang chủ chỉ còn lo bố cục và điều phối, còn việc "một danh sách
 * món trông thế nào" nằm đúng một chỗ.
 */
import type { DishItem } from '@/shared/api';
import { DishCard } from '@/entities/dish';

interface DishListProps {
  dishes: DishItem[];
  onOpen: (dish: DishItem) => void;
}

export function DishList({ dishes, onOpen }: DishListProps) {
  return (
    <ul className="dishes">
      {dishes.map((dish) => (
        <DishCard key={dish.dish_id} dish={dish} onOpen={onOpen} />
      ))}
    </ul>
  );
}

/** Vệt xương lúc đang tải - báo "sắp có nội dung" thay vì để lưới trống trơn. */
export function DishListSkeleton() {
  return (
    <ul className="dishes" aria-busy="true" aria-label="Đang tìm món">
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <li key={i}>
          <div className="dish dish--skeleton">
            <div className="skeleton__box" />
            <div className="dish__body">
              <div className="skeleton__line" />
              <div className="skeleton__line skeleton__line--short" />
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

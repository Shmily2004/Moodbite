/**
 * Thẻ hiển thị 1 quán — component "NGU" (dumb): chỉ nhận props và render.
 *
 * KHÔNG gọi API, KHÔNG giữ state phức tạp, KHÔNG chứa quy tắc nghiệp vụ.
 * Mọi hành động được báo lên trên qua callback. Nhờ vậy test được mà không cần mock mạng.
 */
import type { ReactNode } from 'react';
import type { SearchResultItem } from '@moodbite/api-client';
import {
  describeCluster,
  describeDishConfidence,
  describeMatchSource,
  formatDistance,
  formatPrice,
  formatRating,
} from '../model/format';

interface RestaurantCardProps {
  restaurant: SearchResultItem;
  onOpenDetail?: (restaurant: SearchResultItem) => void;
  children?: ReactNode;
}

export function RestaurantCard({
  restaurant,
  onOpenDetail,
  children,
}: RestaurantCardProps) {
  const dish = restaurant.suggested_dish;
  const price = formatPrice(restaurant.price_range);

  return (
    <li className="card">
      <div className="card__head">
        <span className="card__rank">#{restaurant.rank_position}</span>
        <strong>{restaurant.name}</strong>
      </div>

      <div className="card__meta">
        {restaurant.category && <span>{restaurant.category}</span>}
        <span>{formatDistance(restaurant.distance_m)}</span>
        <span>{formatRating(restaurant.rating, restaurant.user_ratings_total)}</span>
        {price && <span>{price}</span>}
      </div>

      {restaurant.address && <div className="card__address">{restaurant.address}</div>}

      <div className="card__why">
        Khớp theo: {describeMatchSource(restaurant.match_source)}
        <span className="card__score">
          {' '}
          · điểm {restaurant.predicted_score.toFixed(2)}
        </span>
        {restaurant.district && <span> · {restaurant.district}</span>}
      </div>

      {/* Cụm trải nghiệm (Lớp 1). null = chưa phân cụm, hiện "Đang cập nhật". */}
      <div className="card__cluster">
        Nhóm trải nghiệm: {describeCluster(restaurant.experience_cluster_label)}
      </div>

      {dish && (
        <div className="dish">
          <strong>Gợi ý món:</strong> {dish.name}
          {/* Món là SUY LUẬN - luôn hiện mức tin cậy để không nói dối người dùng. */}
          <span className={`dish__confidence dish__confidence--${dish.confidence}`}>
            {describeDishConfidence(dish.confidence)}
          </span>
        </div>
      )}

      {onOpenDetail && (
        <button className="btn btn--link" onClick={() => onOpenDetail(restaurant)}>
          Xem giá, đánh giá &amp; ảnh
        </button>
      )}

      {children}
    </li>
  );
}

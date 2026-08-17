/**
 * Thẻ hiển thị 1 quán — component "NGU" (dumb): chỉ nhận props và render.
 *
 * KHÔNG gọi API, KHÔNG giữ state phức tạp, KHÔNG chứa quy tắc nghiệp vụ.
 * Mọi hành động được báo lên trên qua callback. Nhờ vậy test được mà không cần mock mạng.
 *
 * THỨ TỰ THÔNG TIN theo đúng thứ người dùng cần khi đang đói:
 *   tên quán → đánh giá + khoảng cách → loại hình/giá → gợi ý món → vì sao khớp
 * "Vì sao khớp" và điểm số để CUỐI và làm nhạt: hữu ích để giải thích, nhưng không
 * phải thứ người ta đọc đầu tiên.
 */
import type { ReactNode } from 'react';
import type { SearchResultItem } from '@moodbite/api-client';
import {
  describeCluster,
  describeDishConfidence,
  describeMatchSource,
  formatDistance,
  formatPrice,
} from '../model/format';
import { RestaurantThumb } from './RestaurantThumb';

interface RestaurantCardProps {
  restaurant: SearchResultItem;
  /** Quán đang được chọn trên bản đồ -> tô nền để nối bản đồ với danh sách. */
  active?: boolean;
  onOpenDetail?: (restaurant: SearchResultItem) => void;
  children?: ReactNode;
}

export function RestaurantCard({
  restaurant,
  active = false,
  onOpenDetail,
  children,
}: RestaurantCardProps) {
  const dish = restaurant.suggested_dish;
  const price = formatPrice(restaurant.price_range);
  const distance = formatDistance(restaurant.distance_m);

  return (
    <li data-id={restaurant.restaurant_id ?? undefined}>
      <div
        className={active ? 'card card--active' : 'card'}
        onClick={() => onOpenDetail?.(restaurant)}
        role={onOpenDetail ? 'button' : undefined}
        tabIndex={onOpenDetail ? 0 : undefined}
        onKeyDown={(event) => {
          if (onOpenDetail && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            onOpenDetail(restaurant);
          }
        }}
      >
        <RestaurantThumb
          name={restaurant.name}
          category={restaurant.category}
          thumbnailUrl={restaurant.thumbnail_url}
        />

        <div className="card__body">
          <h3 className="card__title">
            <span className="card__name">{restaurant.name}</span>
            <span className="card__rank tnum">#{restaurant.rank_position}</span>
          </h3>

          <div className="card__stats tnum">
            {/* null = CHƯA CÓ đánh giá. Không bao giờ hiện "0 sao". */}
            {restaurant.rating != null ? (
              <span className="card__rating">
                <span className="card__star">★</span> {restaurant.rating}
                {restaurant.user_ratings_total != null && (
                  <span className="muted"> ({restaurant.user_ratings_total})</span>
                )}
              </span>
            ) : (
              <span className="card__norating">chưa có đánh giá</span>
            )}
            {distance && <span>{distance}</span>}
            {price && <span>{price}</span>}
          </div>

          {restaurant.address && <p className="card__address">{restaurant.address}</p>}

          <div className="tags">
            {restaurant.category && <span className="tag">{restaurant.category}</span>}
            {dish && (
              <span
                className={
                  dish.confidence === 'specific' ? 'tag tag--dish' : 'tag tag--guess'
                }
              >
                🍽 {dish.name}
              </span>
            )}
          </div>

          {/* Món ăn là SUY LUẬN từ loại hình quán, KHÔNG phải thực đơn thật.
              Mức tin cậy phải HIỆN RA CHỮ (CLAUDE.md mục 4 quy tắc 4) — để trong
              thuộc tính `title` là không đủ: không rê chuột thì không thấy, và trên
              điện thoại thì không bao giờ thấy. */}
          {dish && (
            <p className="card__why">Món: {describeDishConfidence(dish.confidence)}</p>
          )}

          {/* Gộp một dòng: khớp nhờ đâu · cụm trải nghiệm (Lớp 1) · điểm.
              Cụm để ở đây chứ không làm thẻ tag, vì nhãn cụm dài làm hàng tag xuống
              tới 3 dòng và đẩy thẻ cao lên hẳn. */}
          <p className="card__why">
            Khớp nhờ: {describeMatchSource(restaurant.match_source)}
            {' · '}
            {describeCluster(restaurant.experience_cluster_label)}
            <span className="tnum"> · {restaurant.predicted_score.toFixed(2)}</span>
          </p>
        </div>
      </div>

      {children}
    </li>
  );
}

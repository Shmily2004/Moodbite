/**
 * Thẻ ĐỀ XUẤT — component "NGU" (dumb): chỉ nhận props và render.
 *
 * KHÔNG gọi API, KHÔNG giữ state phức tạp, KHÔNG chứa quy tắc nghiệp vụ.
 *
 * THỨ TỰ THÔNG TIN — đây là USP của MoodBite, không phải danh sách quán thường:
 *   1. tên quán
 *   2. MỨC PHÙ HỢP  ← thứ hai người đọc nhìn thấy, vì đó là giá trị của sản phẩm
 *   3. đánh giá · khoảng cách · giá
 *   4. VÌ SAO được đề xuất (mood + khớp nội dung + món)
 *
 * Mọi thứ ở đây là quy tắc HIỂN THỊ. Việc chấm điểm và xếp hạng nằm hoàn toàn ở backend
 * (`domain/services/search_ranking.py`) - xem CLAUDE.md mục 1b.
 */
import type { ReactNode } from 'react';
import type { SearchResultItem } from '@moodbite/api-client';
import {
  describeCluster,
  describeDishConfidence,
  describeFit,
  describeReasons,
  formatDistance,
  formatPrice,
} from '../model/format';
import { RestaurantThumb } from './RestaurantThumb';

interface RestaurantCardProps {
  restaurant: SearchResultItem;
  /** Câu người dùng gõ - để nói "Hợp với ..." bằng chính lời của họ. */
  queryText?: string | null;
  /** Quán đang được chọn trên bản đồ -> tô nền để nối bản đồ với danh sách. */
  active?: boolean;
  onOpenDetail?: (restaurant: SearchResultItem) => void;
  children?: ReactNode;
}

export function RestaurantCard({
  restaurant,
  queryText,
  active = false,
  onOpenDetail,
  children,
}: RestaurantCardProps) {
  const dish = restaurant.suggested_dish;
  const price = formatPrice(restaurant.price_range);
  const distance = formatDistance(restaurant.distance_m);
  const fit = describeFit(restaurant.predicted_score);
  const reasons = describeReasons(restaurant.match_source, queryText);

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

          {/* MỨC PHÙ HỢP. Nhãn chữ là phần nói thật; thanh chỉ để so tương đối giữa
              các quán. KHÔNG hiện `predicted_score × 100` - xem giải thích dài ở
              `model/format.ts`, điểm thật dồn quanh 0.6 nên hiện % sẽ gây hiểu nhầm. */}
          <div className={`fit fit--${fit.level}`}>
            <span className="fit__label">{fit.label}</span>
            <span className="fit__bar">
              <i style={{ width: `${fit.barPercent}%` }} />
            </span>
          </div>

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

          {/* VÌ SAO QUÁN NÀY - phần làm nên khác biệt so với một danh sách quán thường. */}
          <ul className="why">
            {reasons.map((reason) => (
              <li className="why__row" key={reason.icon + reason.text}>
                <span aria-hidden="true">{reason.icon}</span>
                <span>{reason.text}</span>
              </li>
            ))}

            {dish && (
              <li className="why__row">
                <span aria-hidden="true">🍽</span>
                <span>
                  <span
                    className={
                      dish.confidence === 'specific' ? 'tag tag--dish' : 'tag tag--guess'
                    }
                  >
                    {dish.name}
                  </span>{' '}
                  {/* Món là SUY LUẬN, không phải thực đơn thật. Mức tin cậy PHẢI hiện
                      ra chữ (CLAUDE.md mục 4 quy tắc 4) - để trong tooltip là không đủ,
                      trên điện thoại sẽ không bao giờ thấy. */}
                  <span className="muted">{describeDishConfidence(dish.confidence)}</span>
                </span>
              </li>
            )}
          </ul>

          <p className="card__meta-foot">
            {describeCluster(restaurant.experience_cluster_label)}
            {restaurant.category && ` · ${restaurant.category}`}
          </p>
        </div>
      </div>

      {children}
    </li>
  );
}

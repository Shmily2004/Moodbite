/**
 * Danh sách kết quả + panel chi tiết. Ghép `entities/restaurant` với
 * `features/view-restaurant-detail` và `features/log-interaction`.
 *
 * Đây là tầng `widgets`: được phép dùng nhiều feature/entity, nhưng KHÔNG tự gọi API.
 */
import { useState } from 'react';
import type { SearchResultItem } from '@moodbite/api-client';
import { RestaurantCard } from '@/entities/restaurant';
import { useRestaurantDetail } from '@/features/view-restaurant-detail';
import { useInteractionLogger } from '@/features/log-interaction';

interface RestaurantListProps {
  restaurants: SearchResultItem[];
  searchQueryId: string | null;
}

export function RestaurantList({ restaurants, searchQueryId }: RestaurantListProps) {
  const { detail, loading, error, load, clear } = useRestaurantDetail();
  const { log, startViewTimer } = useInteractionLogger();
  const [openId, setOpenId] = useState<string | null>(null);
  const [stopTimer, setStopTimer] = useState<(() => void) | null>(null);

  const open = async (restaurant: SearchResultItem) => {
    if (!restaurant.restaurant_id) return;
    setOpenId(restaurant.restaurant_id);
    setStopTimer(() =>
      startViewTimer(restaurant.restaurant_id!, restaurant.rank_position, searchQueryId),
    );
    await load(restaurant.restaurant_id);
  };

  const close = () => {
    stopTimer?.();          // ghi dwell_time thật khi người dùng đóng
    setStopTimer(null);
    setOpenId(null);
    clear();
  };

  return (
    <ul className="results">
      {restaurants.map((restaurant) => (
        <RestaurantCard
          key={restaurant.restaurant_id ?? restaurant.rank_position}
          restaurant={restaurant}
          onOpenDetail={openId === restaurant.restaurant_id ? undefined : open}
        >
          {openId === restaurant.restaurant_id && (
            <DetailPanel
              detail={detail}
              loading={loading}
              error={error}
              onClose={close}
              onDirections={() =>
                restaurant.restaurant_id &&
                log({
                  restaurantId: restaurant.restaurant_id,
                  actionType: 'get_directions',
                  searchQueryId,
                  rankPosition: restaurant.rank_position,
                })
              }
            />
          )}
        </RestaurantCard>
      ))}
    </ul>
  );
}

interface DetailPanelProps {
  detail: ReturnType<typeof useRestaurantDetail>['detail'];
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onDirections: () => void;
}

function DetailPanel({ detail, loading, error, onClose, onDirections }: DetailPanelProps) {
  if (loading) return <div className="detail">Đang tải…</div>;
  if (error) return <div className="detail error">{error}</div>;
  if (!detail) return null;

  // Quán chưa cào được chi tiết là chuyện BÌNH THƯỜNG (chỉ 1310/4938 quán có).
  if (!detail.has_details) {
    return (
      <div className="detail">
        <p className="muted">{detail.reason}</p>
        <button className="btn btn--link" onClick={onClose}>
          Đóng
        </button>
      </div>
    );
  }

  const atmosphere = Array.isArray(detail.atmosphere)
    ? (detail.atmosphere as Array<Record<string, unknown>>).flatMap((entry) =>
        entry && typeof entry === 'object' ? Object.keys(entry) : [],
      )
    : [];

  return (
    <div className="detail">
      {detail.price_range && (
        <div>
          <strong>Giá:</strong> {detail.price_range}
        </div>
      )}
      {atmosphere.length > 0 && (
        <div>
          <strong>Không gian:</strong> {atmosphere.join(', ')}
        </div>
      )}

      {detail.images.length > 0 && (
        <div className="detail__images">
          {detail.images.slice(0, 6).map((src, index) => (
            <img key={index} src={src} alt="" loading="lazy" />
          ))}
        </div>
      )}

      {detail.reviews.length > 0 && (
        <div className="detail__reviews">
          <strong>Đánh giá ({detail.reviews.length}):</strong>
          {detail.reviews
            .filter((review) => (review as { text?: string }).text)
            .slice(0, 4)
            .map((review, index) => {
              const item = review as { text?: string; stars?: number; name?: string };
              return (
                <blockquote key={index}>
                  <span className="stars">{'★'.repeat(item.stars ?? 0)}</span> {item.name}
                  <p>{item.text}</p>
                </blockquote>
              );
            })}
        </div>
      )}

      <div className="detail__links">
        {detail.menu_url && (
          <a href={detail.menu_url} target="_blank" rel="noreferrer">
            Xem menu
          </a>
        )}
        {detail.website && (
          <a href={detail.website} target="_blank" rel="noreferrer">
            Website
          </a>
        )}
        {detail.google_maps_url && (
          <a
            href={detail.google_maps_url}
            target="_blank"
            rel="noreferrer"
            onClick={onDirections}
          >
            Chỉ đường
          </a>
        )}
      </div>

      <button className="btn btn--link" onClick={onClose}>
        Đóng
      </button>
    </div>
  );
}

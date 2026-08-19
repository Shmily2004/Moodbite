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
  /** Câu người dùng gõ - thẻ dùng để nói "Hợp với ..." bằng chính lời của họ. */
  queryText?: string | null;
  /** placeId quán đang chọn trên bản đồ - thẻ tương ứng được tô sáng. */
  activeId?: string | null;
  /** Báo lên trên khi người dùng bấm một thẻ, để bản đồ làm nổi ghim tương ứng. */
  onActivate?: (id: string | null) => void;
}

export function RestaurantList({
  restaurants,
  searchQueryId,
  queryText,
  activeId,
  onActivate,
}: RestaurantListProps) {
  const { detail, loading, error, load, clear } = useRestaurantDetail();
  const { log, startViewTimer } = useInteractionLogger();
  const [openId, setOpenId] = useState<string | null>(null);
  const [stopTimer, setStopTimer] = useState<(() => void) | null>(null);

  const open = async (restaurant: SearchResultItem) => {
    if (!restaurant.restaurant_id) return;
    onActivate?.(restaurant.restaurant_id);
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
          queryText={queryText}
          active={activeId != null && restaurant.restaurant_id === activeId}
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

      {/* LỚP 4 — nhận xét tổng hợp từ review, backend đã tính sẵn offline.
          Đặt TRƯỚC danh sách review thô: người dùng đọc kết luận trước, ai muốn kiểm
          chứng thì đọc tiếp review gốc bên dưới. */}
      {detail.review_summary && <ReviewSummary summary={detail.review_summary} />}

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


/** Kiểu của `review_summary` do backend trả về (Lớp 4). */
interface ReviewSummaryData {
  summary?: string[];
  positive?: string[];
  negative?: string[];
  review_count?: number;
  average_stars?: number | null;
  method?: string;
}

/**
 * Nhận xét tổng hợp từ review.
 *
 * PHẢI NÓI RÕ đây là câu TRÍCH NGUYÊN VĂN từ review thật, không phải hệ thống tự nhận xét.
 * Người đọc thấy một đoạn nhận xét gọn gàng rất dễ tưởng là máy viết ra, mà máy viết thì
 * có thể bịa - trong khi ở đây mọi câu đều truy được về một review có thật.
 */
function ReviewSummary({ summary }: { summary: unknown }) {
  const data = summary as ReviewSummaryData;
  const chinh = data.summary ?? [];
  const manh = data.positive ?? [];
  const yeu = data.negative ?? [];

  if (chinh.length === 0 && manh.length === 0 && yeu.length === 0) return null;

  return (
    <div className="rsum">
      <div className="rsum__head">
        <strong>Người ăn nói gì</strong>
        {data.review_count != null && (
          <span className="muted small">
            {data.review_count} đánh giá
            {/* null = CHƯA CÓ dữ liệu sao, không phải 0 sao. */}
            {data.average_stars != null && ` · TB ${data.average_stars}★`}
          </span>
        )}
      </div>

      {chinh.map((cau, i) => (
        <p className="rsum__line" key={`s${i}`}>{cau}</p>
      ))}

      {manh.length > 0 && (
        <ul className="rsum__points rsum__points--good">
          {manh.map((cau, i) => <li key={`p${i}`}>{cau}</li>)}
        </ul>
      )}
      {yeu.length > 0 && (
        <ul className="rsum__points rsum__points--bad">
          {yeu.map((cau, i) => <li key={`n${i}`}>{cau}</li>)}
        </ul>
      )}

      <p className="rsum__note muted small">
        Các câu trên được trích nguyên văn từ đánh giá của người dùng, không phải nhận xét
        của MoodBite.
      </p>
    </div>
  );
}

/**
 * Danh sách kết quả + panel chi tiết. Ghép `entities/restaurant` với
 * `features/view-restaurant-detail` và `features/log-interaction`.
 *
 * Đây là tầng `widgets`: được phép dùng nhiều feature/entity, nhưng KHÔNG tự gọi API.
 */
import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import type { SearchResultItem } from '@moodbite/api-client';
import { RestaurantCard } from '@/entities/restaurant';
import { useRestaurantDetail } from '@/features/view-restaurant-detail';
import { useInteractionLogger } from '@/features/log-interaction';
import { ReportClosureButton } from '@/features/report-closure';
import { useT } from '@/shared/i18n';
import { safeHttpUrl } from '@/shared/lib';
import { restaurantRoute } from '@/shared/config';
import type { RestaurantPageState } from '@/shared/config';

interface RestaurantListProps {
  restaurants: SearchResultItem[];
  searchQueryId: string | null;
  /** Câu người dùng gõ - thẻ dùng để nói "Hợp với ..." bằng chính lời của họ. */
  queryText?: string | null;
  /** placeId quán đang chọn trên bản đồ - thẻ tương ứng được tô sáng. */
  activeId?: string | null;
  /** Báo lên trên khi người dùng bấm một thẻ, để bản đồ làm nổi ghim tương ứng. */
  onActivate?: (id: string | null) => void;
  /** Đánh số 1, 2, 3… trên từng thẻ, khớp với ghim cùng số trên bản đồ. */
  danhSo?: boolean;
  /** Thẻ dáng gọn một hàng (trang chi tiết món). Xem `RestaurantCard.gon`. */
  gon?: boolean;
  /** Món đang xem (trang chi tiết món) - để trang quán dựng breadcrumb quay về đúng món. */
  fromDish?: { id: string; name: string };
  /** Xem `RestaurantCard.hienKhoangCach`. Tắt khi chưa có vị trí thật của người dùng. */
  hienKhoangCach?: boolean;
}

export function RestaurantList({
  restaurants,
  searchQueryId,
  queryText,
  activeId,
  onActivate,
  danhSo = false,
  gon = false,
  fromDish,
  hienKhoangCach = true,
}: RestaurantListProps) {
  const { detail, loading, error, load, clear } = useRestaurantDetail();
  const { log, startViewTimer } = useInteractionLogger();
  const [openId, setOpenId] = useState<string | null>(null);
  // Ref chứ không phải state: hàm dừng chỉ cần GỌI, không cần render lại. Trước đây chỉ
  // `close()` gọi nó → mở quán khác hoặc rời trang thì lượt xem quán cũ mất dwell_time
  // (audit 2026-10-06) — đúng loại nhãn huấn luyện ta cần nhất.
  const stopTimerRef = useRef<(() => void) | null>(null);
  const dungDemGio = () => {
    stopTimerRef.current?.();
    stopTimerRef.current = null;
  };
  // Rời trang khi panel còn mở → vẫn ghi lượt xem đang dở.
  useEffect(() => () => dungDemGio(), []);

  const open = async (restaurant: SearchResultItem) => {
    if (!restaurant.restaurant_id) return;
    dungDemGio(); // chốt lượt xem quán ĐANG mở trước khi chuyển sang quán mới
    onActivate?.(restaurant.restaurant_id);
    setOpenId(restaurant.restaurant_id);
    stopTimerRef.current = startViewTimer(
      restaurant.restaurant_id,
      restaurant.rank_position,
      searchQueryId,
    );
    await load(restaurant.restaurant_id);
  };

  const close = () => {
    dungDemGio(); // ghi dwell_time thật khi người dùng đóng
    setOpenId(null);
    clear();
  };

  return (
    <ul className="results">
      {restaurants.map((restaurant, chiSo) => (
        <RestaurantCard
          key={restaurant.restaurant_id ?? restaurant.rank_position}
          restaurant={restaurant}
          // Số theo VỊ TRÍ TRONG DANH SÁCH ĐANG NHÌN, không phải `rank_position` — sắp
          // lại theo "gần nhất" thì số phải đổi theo, để còn khớp với ghim bản đồ.
          soThuTu={danhSo ? chiSo + 1 : undefined}
          gon={gon}
          hienKhoangCach={hienKhoangCach}
          queryText={queryText}
          active={activeId != null && restaurant.restaurant_id === activeId}
          onOpenDetail={openId === restaurant.restaurant_id ? undefined : open}
          // "Xem chi tiết" = sang trang quán đầy đủ (2026-10-28). Thân thẻ vẫn xem nhanh.
          detailLink={
            restaurant.restaurant_id
              ? {
                  to: restaurantRoute(restaurant.restaurant_id),
                  state: {
                    fromDish,
                    searchQueryId,
                    rankPosition: restaurant.rank_position,
                  } satisfies RestaurantPageState,
                }
              : undefined
          }
        >
          {openId === restaurant.restaurant_id && (
            <DetailPanel
              detail={detail}
              loading={loading}
              error={error}
              restaurantId={restaurant.restaurant_id}
              restaurantName={restaurant.name}
              trangQuanState={{
                fromDish,
                searchQueryId,
                rankPosition: restaurant.rank_position,
              }}
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
  /** Cần cho nút báo đóng cửa - `null` thì không báo được (quán chưa có placeId). */
  restaurantId: string | null;
  restaurantName: string;
  /** Ngữ cảnh mang sang trang quán đầy đủ - xem `RestaurantPageState`. */
  trangQuanState: RestaurantPageState;
  onClose: () => void;
  onDirections: () => void;
}

function DetailPanel({
  detail,
  loading,
  error,
  restaurantId,
  restaurantName,
  trangQuanState,
  onClose,
  onDirections,
}: DetailPanelProps) {
  const t = useT();
  if (loading) return <div className="detail">{t('common.loading')}</div>;
  if (error) return <div className="detail error">{error}</div>;
  if (!detail) return null;

  // Lối sang trang quán ĐẦY ĐỦ (2026-10-28). Panel này chỉ là bản xem nhanh; trang riêng
  // có bản đồ, giờ mở cửa, nguồn dữ liệu - và có link chia sẻ được.
  const moTrangQuan = restaurantId && (
    <Link className="btn btn--link detail__mo-trang" to={restaurantRoute(restaurantId)} state={trangQuanState}>
      {t('restPage.openMap')} →
    </Link>
  );

  const menuUrl = safeHttpUrl(detail.menu_url);
  const websiteUrl = safeHttpUrl(detail.website);
  const mapsUrl = safeHttpUrl(detail.google_maps_url);

  // Quán chưa cào được chi tiết là chuyện BÌNH THƯỜNG (chỉ 1310/4938 quán có).
  if (!detail.has_details) {
    return (
      <div className="detail">
        <p className="muted">{detail.reason}</p>
        {moTrangQuan}
        {/* Quán CHƯA cào được chi tiết vẫn phải báo đóng cửa được - đây đúng là nhóm
            dữ liệu mỏng nhất, tức là nhóm dễ đã đóng mà ta không biết nhất. */}
        {restaurantId && (
          <ReportClosureButton restaurantId={restaurantId} restaurantName={restaurantName} />
        )}
        <button className="btn btn--link" onClick={onClose}>
          {t('restDetail.close')}
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
          <strong>{t('restDetail.price')}</strong> {detail.price_range}
        </div>
      )}
      {atmosphere.length > 0 && (
        <div>
          <strong>{t('restDetail.atmosphere')}</strong> {atmosphere.join(', ')}
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
          <strong>{t('restDetail.reviews', { n: detail.reviews.length })}</strong>
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
        {/* Link đến từ dữ liệu CÀO → chỉ render khi là http/https (chặn `javascript:`). */}
        {menuUrl && (
          <a href={menuUrl} target="_blank" rel="noopener noreferrer">
            {t('restDetail.menu')}
          </a>
        )}
        {websiteUrl && (
          <a href={websiteUrl} target="_blank" rel="noopener noreferrer">
            {t('restDetail.website')}
          </a>
        )}
        {mapsUrl && (
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onDirections}
          >
            {t('restDetail.directions')}
          </a>
        )}
      </div>

      {moTrangQuan}

      {/* BÁO ĐÓNG CỬA - backend đã đếm theo phiên từ 2026-08-19, đây là cái nút còn
          thiếu. Đặt CUỐI và nhạt màu: nó là lối thoát hiểm, không phải hành động chính. */}
      {restaurantId && (
        <ReportClosureButton restaurantId={restaurantId} restaurantName={restaurantName} />
      )}

      <button className="btn btn--link" onClick={onClose}>
        {t('restDetail.close')}
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
export function ReviewSummary({ summary }: { summary: unknown }) {
  const data = summary as ReviewSummaryData;
  const chinh = data.summary ?? [];
  const manh = data.positive ?? [];
  const yeu = data.negative ?? [];
  const t = useT();

  if (chinh.length === 0 && manh.length === 0 && yeu.length === 0) return null;

  return (
    <div className="rsum">
      <div className="rsum__head">
        <strong>{t('restDetail.summaryTitle')}</strong>
        {data.review_count != null && (
          <span className="muted small">
            {t('restDetail.reviewCount', { n: data.review_count })}
            {/* null = CHƯA CÓ dữ liệu sao, không phải 0 sao. */}
            {data.average_stars != null && t('restDetail.avgStars', { n: data.average_stars })}
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
        {t('restDetail.summaryNote')}
      </p>
    </div>
  );
}

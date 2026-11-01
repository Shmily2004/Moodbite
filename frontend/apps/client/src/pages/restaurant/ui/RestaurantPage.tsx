/**
 * TRANG CHI TIẾT QUÁN - `/restaurants/:restaurantId` (dựng 2026-10-28).
 *
 * CHƯA CÓ BẢN VẼ RIÊNG. Chủ dự án duyệt hướng "suy từ các bản thiết kế khác":
 *   - đầu trang lấy từ `restaurance recommend.png` (ảnh · tên · hàng chip · tranh Hà Nội)
 *   - thân trang lấy từ `profile.png` (các THẺ TRẮNG bo góc, tiêu đề viết hoa; cột nội dung
 *     rộng bên trái, cột phụ hẹp bên phải)
 *
 * Trang này là bản ĐẦY ĐỦ của panel chi tiết thu gọn trong `RestaurantList` - panel đó
 * vẫn giữ (xem nhanh không rời danh sách) và có link sang đây.
 *
 * ⚠️ MỌI HOOK ĐỨNG TRƯỚC MỌI `return` SỚM - xem bug thật ở đầu `DishPage.tsx`.
 */
import { useEffect, useRef } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { SiteHeader } from '@/widgets/site-header';
import { useRestaurantDetail } from '@/features/view-restaurant-detail';
import { useInteractionLogger } from '@/features/log-interaction';
import { useFavorites } from '@/features/save-favorite';
import { ROUTES, dishRoute } from '@/shared/config';
import type { RestaurantPageState } from '@/shared/config';
import { useT } from '@/shared/i18n';
import { linkChiDuong } from '../model/lienKet';
import { RestaurantHero } from './RestaurantHero';
import { RestaurantReviews } from './RestaurantReviews';
import { RestaurantSidebar } from './RestaurantSidebar';

export function RestaurantPage() {
  const t = useT();
  const { restaurantId = '' } = useParams<{ restaurantId: string }>();
  const state = (useLocation().state ?? {}) as RestaurantPageState;
  const { detail, loading, error, notFound, load } = useRestaurantDetail();
  const { log, startViewTimer } = useInteractionLogger();
  const favorites = useFavorites();

  useEffect(() => {
    if (restaurantId) void load(restaurantId);
  }, [restaurantId, load]);

  // GHI LƯỢT XEM kèm thời gian xem thật - đây là NHÃN cho mô hình xếp hạng (checklist
  // mục 13, đang thiếu nhất). Bắt đầu khi tải xong, chốt khi rời trang hoặc đổi quán.
  const searchQueryId = state.searchQueryId ?? null;
  const rankPosition = state.rankPosition ?? null;
  const stopRef = useRef<(() => void) | null>(null);
  const daTai = detail?.restaurant_id === restaurantId;
  useEffect(() => {
    if (!daTai) return;
    stopRef.current = startViewTimer(restaurantId, rankPosition, searchQueryId);
    return () => {
      stopRef.current?.();
      stopRef.current = null;
    };
  }, [daTai, restaurantId, rankPosition, searchQueryId, startViewTimer]);

  const vo = (noiDung: JSX.Element) => (
    <div className="page">
      <SiteHeader />
      <main className="dish-page rest-page">{noiDung}</main>
    </div>
  );

  if (notFound) {
    return vo(
      <div className="state">
        <p className="state__title">{t('restPage.notFoundTitle')}</p>
        <p>{t('restPage.notFoundHint')}</p>
        <Link className="btn btn--primary" to={ROUTES.home}>
          {t('restPage.backHome')}
        </Link>
      </div>,
    );
  }

  const info = detail?.info ?? null;

  return vo(
    <>
      <nav className="breadcrumb" aria-label={t('dishPage.breadcrumb')}>
        <Link to={ROUTES.home}>{t('dishPage.home')}</Link>
        {state.fromDish && (
          <>
            <span aria-hidden="true">›</span>
            <Link to={dishRoute(state.fromDish.id)}>{state.fromDish.name}</Link>
          </>
        )}
        <span aria-hidden="true">›</span>
        <span>{t('restPage.crumb')}</span>
        <span aria-hidden="true">›</span>
        <span className="breadcrumb__hien-tai">
          {info?.name ?? detail?.name ?? t('dishPage.loading')}
        </span>
      </nav>

      {error && <p className="notice notice--error">{error}</p>}
      {loading && <p className="muted rest-page__tai" role="status">{t('restPage.loading')}</p>}

      {detail && info && (
        <>
          <RestaurantHero
            info={info}
            anhUngVien={[...detail.images, info.thumbnail_url].filter(
              (x): x is string => Boolean(x),
            )}
            // Đổi quán (cùng component) -> thử lại ảnh từ đầu.
            key={restaurantId}
            daLuu={favorites.isSaved('restaurant', restaurantId, 'favorite')}
            onToggleLuu={() =>
              favorites.toggle({
                itemType: 'restaurant',
                itemId: restaurantId,
                name: info.name,
                listType: 'favorite',
              })
            }
            chiDuong={linkChiDuong(detail, info)}
            onChiDuong={() =>
              log({ restaurantId, actionType: 'get_directions', searchQueryId, rankPosition })
            }
          />

          <div className="rest-body">
            <div className="rest-main">
              <RestaurantReviews detail={detail} />
            </div>
            <RestaurantSidebar restaurantId={restaurantId} info={info} detail={detail} />
          </div>
        </>
      )}

      {/* Kho quán chưa sẵn sàng -> backend trả `info: null`. Vẫn hiện phần làm giàu nếu
          có, thay vì trắng trang vì thiếu một nguồn (CLAUDE.md mục 4 quy tắc 3). */}
      {detail && !info && (
        <div className="rest-body rest-body--mot-cot">
          <div className="rest-main">
            <RestaurantReviews detail={detail} />
          </div>
        </div>
      )}
    </>,
  );
}

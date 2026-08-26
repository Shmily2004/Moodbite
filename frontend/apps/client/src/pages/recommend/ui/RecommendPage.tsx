/**
 * TRANG KẾT QUẢ GỢI Ý MÓN — `/recommend`.
 *
 * VÌ SAO TÁCH KHỎI TRANG CHỦ (chủ dự án chốt 2026-08-24):
 * Trước đó trang chủ ôm cả hai việc — khám phá (hero, mood, nhu cầu) VÀ kết quả lọc — và
 * nút "Xem tất cả" chỉ đổi bố cục row→grid TẠI CHỖ, khiến trang dài thêm hàng chục hàng
 * thẻ. Người dùng phải cuộn qua toàn bộ phần khám phá mỗi lần muốn xem lại kết quả.
 * Nay: trang chủ lo KHÁM PHÁ, trang này lo KẾT QUẢ.
 *
 * ⚠️ KHÔNG PHẢI `/search`. Trang đó tìm QUÁN bằng câu tự nhiên và có bản đồ; trang này
 * xếp hạng MÓN theo bộ lọc + ngữ cảnh. Hai luồng khác nhau, đừng gộp.
 *
 * BỘ LỌC NẰM TRÊN URL, không phải trong bộ nhớ — xem `boLocTuUrl.ts`.
 */
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { SiteHeader } from '@/widgets/site-header';
import { DishList, DishListSkeleton } from '@/widgets/dish-list';
import { FilterDrawer } from '@/widgets/filter-drawer';
import { AssistantBubble } from '@/widgets/assistant-bubble';
import {
  DishFilters,
  docBoLocTuUrl,
  ghiBoLocLenUrl,
  useDishSuggestions,
} from '@/features/suggest-dishes';
import { useUserLocation } from '@/features/pick-location';
import { useFavorites } from '@/features/save-favorite';
import { ROUTES } from '@/shared/config';
import { useT } from '@/shared/i18n';

export function RecommendPage() {
  const t = useT();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useUserLocation();

  // Đọc bộ lọc từ URL đúng MỘT LẦN lúc dựng. Sau đó state trong hook là nguồn sự thật;
  // đọc lại mỗi lần URL đổi sẽ ghi đè thứ người dùng vừa bấm.
  const [boLocBanDau] = useState(() => docBoLocTuUrl(searchParams));
  const suggestions = useDishSuggestions(location.position, boLocBanDau);
  const savedDishes = useFavorites();
  const [moBoLoc, setMoBoLoc] = useState(false);

  // Bộ lọc đổi -> ghi ngược lên URL. `replace` để mỗi lần bấm chip KHÔNG tạo một mục
  // mới trong lịch sử: bấm 5 chip rồi bấm Back 5 lần mới ra khỏi trang là rất khó chịu.
  useEffect(() => {
    setSearchParams(ghiBoLocLenUrl(suggestions.filters), { replace: true });
  }, [suggestions.filters, setSearchParams]);

  const dishes = suggestions.dishes ?? [];
  const coMon = dishes.length > 0;

  return (
    <div className="page">
      <SiteHeader />

      <main className="page__body recommend">
        <div className="recommend__head">
          <div>
            <h1 className="section-title">
              {suggestions.loading
                ? t('recommend.loading')
                : t('recommend.title', { count: dishes.length })}
            </h1>
            {/* Ngữ cảnh do BACKEND đo (giờ + thời tiết), không phải frontend đoán. */}
            {suggestions.context.length > 0 && (
              <p className="section-sub">{suggestions.context.join(' · ')}</p>
            )}
          </div>

          <button
            type="button"
            className={
              suggestions.activeFilterCount > 0
                ? 'btn btn--sm btn--filter btn--filter-on'
                : 'btn btn--sm btn--filter'
            }
            onClick={() => setMoBoLoc(true)}
          >
            {t('filters.open')}
            {suggestions.activeFilterCount > 0 && (
              <span className="btn__badge">{suggestions.activeFilterCount}</span>
            )}
          </button>
        </div>

        {/* Điều server KHÔNG làm được — hiện lên thay vì im lặng bỏ qua.
            VD "đã ẩn 48 món có quán bán nhưng nằm ngoài bán kính 3 km". */}
        {suggestions.warnings.map((canh_bao, i) => (
          <p key={i} className="notice notice--warn">
            {canh_bao}
          </p>
        ))}

        {suggestions.error && (
          <div className="notice notice--error">
            <p>{suggestions.error}</p>
            <button className="btn" onClick={suggestions.reload}>
              {t('results.retry')}
            </button>
          </div>
        )}

        {suggestions.loading && <DishListSkeleton layout="grid" />}

        {!suggestions.loading && !suggestions.error && !coMon && (
          <div className="notice">
            <p>{t('recommend.empty')}</p>
            {suggestions.activeFilterCount > 0 && (
              <button className="btn" onClick={suggestions.reset}>
                {t('results.clearFilters')}
              </button>
            )}
          </div>
        )}

        {!suggestions.loading && coMon && (
          <DishList
            dishes={dishes}
            layout="grid"
            onOpen={(dish) => navigate(ROUTES.dish.replace(':dishId', dish.dish_id))}
            isSaved={(dish) => savedDishes.isSaved('dish', dish.dish_id)}
            onToggleSave={(dish) =>
              savedDishes.toggle({
                itemType: 'dish',
                itemId: dish.dish_id,
                name: dish.name,
              })
            }
          />
        )}

        {/* Bong bóng trợ lý — chỉ đặt ở trang CÓ MÓN. Xem `widgets/assistant-bubble`. */}
        <AssistantBubble
          onOpen={() => setMoBoLoc(true)}
          activeCount={suggestions.activeFilterCount}
        />

        <FilterDrawer
          open={moBoLoc}
          onClose={() => setMoBoLoc(false)}
          activeCount={suggestions.activeFilterCount}
          onReset={suggestions.reset}
        >
          <p className="section-sub">{t('filters.sub')}</p>
          <DishFilters
            filters={suggestions.filters}
            onToggle={suggestions.toggle}
            onSetSingle={suggestions.setSingle}
            onSetMaxDistanceKm={suggestions.setMaxDistanceKm}
            onReset={suggestions.reset}
            activeFilterCount={suggestions.activeFilterCount}
            locationIsDefault={location.isDefault}
            locationLoading={location.loading}
            onRequestLocation={location.request}
          />
        </FilterDrawer>
      </main>
    </div>
  );
}

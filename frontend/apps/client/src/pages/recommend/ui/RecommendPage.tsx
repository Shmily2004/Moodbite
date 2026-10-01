/**
 * TRANG KẾT QUẢ GỢI Ý MÓN — `/recommend`.
 *
 * Dựng theo `frontend/design/Filler.png` (đổi 2026-09-16, thay bố cục `Food recommend.jpg`):
 *
 *   ← Quay lại trang chủ
 *   ┌ BỘ LỌC ─────────┐  24 món ăn phù hợp                  Sắp xếp: [Phù hợp nhất ▾]
 *   │ (cột cố định,   │  Đang lọc theo: [3 km ✕] [Tối ✕]  Xoá tất cả
 *   │  chỉ ≥1024px)   │  [món][món][món]
 *   │                 │  [món][món][món]      <- 3 cột / 2 cột máy tính bảng / 1 cột
 *   └─────────────────┘  [Xem thêm N món]
 *   ♥ Dành riêng cho bạn · dải mời đăng ký (chỉ khách)
 *
 * CỘT LỌC VÀ NGĂN KÉO LÀ CÙNG MỘT `FilterDrawer` (xem lý do ở chính widget đó). Màn rộng
 * hiện `variant="inline"`, màn hẹp ẩn cột bằng CSS và dùng nút "Lọc" mở ngăn kéo.
 *
 * ⚠️ KHÔNG hiện ⭐ rating và km trên thẻ món, dù bản thiết kế có. Chủ dự án chốt
 * 2026-08-25 rằng đó là lỗi thiết kế: MÓN không có trường rating, còn km là của quán gần
 * nhất nên đặt trên thẻ món thì đọc thành "món này cách 1,2 km" — vô nghĩa.
 *
 * ⛔ CHƯA LÀM "Chỉ hiện quán có ghi giá (x%)" của bản thiết kế: `/dishes/suggest` không có
 * tham số lọc theo giá (đã kiểm `DishSuggestRequest`, 2026-09-16). Vẽ một công tắc bấm
 * vào mà kết quả không đổi là nói dối người dùng.
 *
 * ⚠️ KHÔNG PHẢI `/search`. Trang đó tìm QUÁN bằng câu tự nhiên và có bản đồ.
 */
import { Link } from 'react-router-dom';
import { SiteHeader } from '@/widgets/site-header';
import { DishList, DishListSkeleton } from '@/widgets/dish-list';
import { FilterDrawer } from '@/widgets/filter-drawer';
import { AssistantBubble } from '@/widgets/assistant-bubble';
import { ForYou } from '@/widgets/for-you';
import { SignupCta } from '@/widgets/signup-cta';
import { DishFilters } from '@/features/suggest-dishes';
import { ROUTES } from '@/shared/config';
import { useT } from '@/shared/i18n';
import { useRecommendPage } from '../model/useRecommendPage';
import { ResultsToolbar } from './ResultsToolbar';

/** Cột lọc luôn hiển thị nên không có gì để "đóng". */
const KHONG_DONG = () => undefined;

export function RecommendPage() {
  const t = useT();
  const vm = useRecommendPage();
  const { suggestions, location } = vm;

  // Nội dung bộ lọc dựng MỘT LẦN, đặt được ở hai chỗ (cột trái và ngăn kéo).
  const noiDungBoLoc = (
    <DishFilters
      filters={suggestions.filters}
      onToggle={suggestions.toggle}
      onSetSingle={suggestions.setSingle}
      onSetMaxDistanceKm={suggestions.setMaxDistanceKm}
      onSetOnlyWithPrice={suggestions.setOnlyWithPrice}
      onReset={suggestions.reset}
      activeFilterCount={suggestions.activeFilterCount}
      locationIsDefault={location.isDefault}
      locationLabel={location.label}
      locationLoading={location.loading}
      onRequestLocation={location.request}
    />
  );

  const coMon = vm.monHien.length > 0;

  return (
    <div className="page">
      <SiteHeader />

      <main className="page__body recommend">
        <Link className="recommend__quay-lai" to={ROUTES.home}>
          ← {t('recommend.back')}
        </Link>

        <div className="recommend-layout">
          <FilterDrawer
            variant="inline"
            open
            onClose={KHONG_DONG}
            activeCount={suggestions.activeFilterCount}
            onReset={suggestions.reset}
          >
            {noiDungBoLoc}
          </FilterDrawer>

          <section id="ket-qua" className="recommend__ket-qua">
            <ResultsToolbar
              loading={suggestions.loading}
              count={vm.tongSoMon}
              chips={vm.chips}
              onRemoveChip={vm.goChip}
              onClearAll={suggestions.reset}
              sort={vm.sapXep}
              onSortChange={vm.setSapXep}
              onOpenFilters={() => vm.setMoBoLoc(true)}
              activeFilterCount={suggestions.activeFilterCount}
            />

            {suggestions.warnings.map((canhBao, i) => (
              <p key={i} className="notice notice--warn">
                {canhBao}
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
                {vm.chips.length > 0 && (
                  <button className="btn" onClick={suggestions.reset}>
                    {t('results.clearFilters')}
                  </button>
                )}
              </div>
            )}

            {!suggestions.loading && coMon && (
              <div className="recommend__luoi">
                <DishList
                  dishes={vm.monHien}
                  layout="grid"
                  onOpen={vm.moMon}
                  isSaved={(dish) => vm.daLuu(dish, 'favorite')}
                  onToggleSave={(dish) => vm.doiLuu(dish, 'favorite')}
                  isBookmarked={(dish) => vm.daLuu(dish, 'bookmark')}
                  onToggleBookmark={(dish) => vm.doiLuu(dish, 'bookmark')}
                />
              </div>
            )}

            {!suggestions.loading && vm.conLai > 0 && (
              <button type="button" className="btn btn--rong" onClick={vm.xemThem}>
                {t('recommend.showMore', { n: vm.conLai })} ▾
              </button>
            )}
          </section>
        </div>

        {/* Món & quán đã lưu — widget tự ẩn khi chưa lưu gì. */}
        <ForYou favorites={vm.savedDishes} />

        {/* Dải mời đăng ký, CHỈ cho khách — giống hệt trang chủ. */}
        {!vm.daDangNhap && <SignupCta onExplore={vm.keoToiKetQua} />}

        <AssistantBubble
          onOpen={() => vm.setMoBoLoc(true)}
          activeCount={suggestions.activeFilterCount}
        />

        <FilterDrawer
          open={vm.moBoLoc}
          onClose={() => vm.setMoBoLoc(false)}
          activeCount={suggestions.activeFilterCount}
          onReset={suggestions.reset}
        >
          <p className="section-sub">{t('filters.sub')}</p>
          {noiDungBoLoc}
        </FilterDrawer>
      </main>
    </div>
  );
}

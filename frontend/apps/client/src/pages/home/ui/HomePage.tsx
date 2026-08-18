/**
 * TRANG CHỦ - bước 1 của luồng "chọn món trước, tìm quán sau".
 *
 *   [bộ lọc: trời mưa · đồ nướng · đồ nóng]  ->  LƯỚI MÓN  ->  bấm món  ->  /mon/:dishId
 *
 * Tầng `pages`: GHÉP widget/feature và giữ state điều phối. Không gọi API trực tiếp
 * (việc đó ở `useDishSuggestions`), không chấm điểm món (việc đó ở backend).
 *
 * VÌ SAO KHÔNG CÒN BẢN ĐỒ Ở ĐÂY: ở bước này người dùng chưa chọn món, nên chưa có gì để
 * đặt lên bản đồ. Bản đồ xuất hiện ở trang chi tiết món, khi đã có một tập quán cụ thể.
 */
import { useNavigate } from 'react-router-dom';
import type { DishItem } from '@/shared/api';
import { DishList, DishListSkeleton } from '@/widgets/dish-list';
import { DishFilters, useDishSuggestions } from '@/features/suggest-dishes';
import { useUserLocation } from '@/features/pick-location';
import { dishRoute } from '@/shared/config';

export function HomePage() {
  const navigate = useNavigate();
  const location = useUserLocation();
  const suggestions = useDishSuggestions(location.position);

  const dishes = suggestions.dishes ?? [];
  const hasDishes = dishes.length > 0;

  const openDish = (dish: DishItem) => navigate(dishRoute(dish.dish_id));

  return (
    <div className="shell">
      <header className="topbar topbar--home">
        <span className="brand">
          <span className="brand__dot" />
          <span className="brand__name">MoodBite</span>
        </span>
        <p className="topbar__tagline">
          Hôm nay bạn muốn ăn gì? Chọn vài điều kiện, chúng tôi gợi ý món.
        </p>
        {suggestions.context.length > 0 && (
          <span className="topbar__ctx">{suggestions.context.join(' · ')}</span>
        )}
      </header>

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

      <main className="results-pane">
        {location.error && <p className="notice notice--warn">{location.error}</p>}

        {suggestions.error && (
          <div className="notice notice--error">
            <p>{suggestions.error}</p>
            <button className="btn" onClick={suggestions.reload}>
              Thử lại
            </button>
          </div>
        )}

        {/* Điều server KHÔNG làm được - hiện lên thay vì im lặng bỏ qua.
            VD "đã ẩn 12 món không có quán nào trong bán kính 2 km". */}
        {suggestions.warnings.map((warning, index) => (
          <p key={index} className="notice notice--warn">
            {warning}
          </p>
        ))}

        {suggestions.loading && <DishListSkeleton />}

        {!suggestions.loading && !suggestions.error && hasDishes && (
          <>
            <p className="results-pane__count">
              {dishes.length} món gợi ý cho bạn
            </p>
            <DishList dishes={dishes} onOpen={openDish} />
          </>
        )}

        {!suggestions.loading && !suggestions.error && !hasDishes && (
          <div className="state">
            <p className="state__title">Không có món nào khớp</p>
            <p>Điều kiện đang hơi chặt. Thử bỏ bớt một vài bộ lọc.</p>
            {suggestions.activeFilterCount > 0 && (
              <button className="chip" onClick={suggestions.reset}>
                Xoá hết bộ lọc
              </button>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

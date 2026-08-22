/**
 * TRANG CHỦ - bước 1 của luồng "chọn món trước, tìm quán sau".
 *
 *   [thanh trên] → [lời chào + ô tìm] → [mood nhanh] → LƯỚI MÓN → bấm món → /mon/:dishId
 *
 * Dựng lại theo `design/Home.jpg` (2026-08-22). Tầng `pages`: GHÉP widget/feature và giữ
 * state điều phối. Không gọi API trực tiếp (việc đó ở `useDishSuggestions`), không chấm
 * điểm món (việc đó ở backend).
 *
 * VÌ SAO KHÔNG CÒN BẢN ĐỒ Ở ĐÂY: ở bước này người dùng chưa chọn món, nên chưa có gì để
 * đặt lên bản đồ. Bản đồ xuất hiện ở trang chi tiết món, khi đã có một tập quán cụ thể.
 *
 * ⚠️ NHỮNG THỨ TRONG BẢN THIẾT KẾ CỐ TÌNH KHÔNG DỰNG (không có dữ liệu thật phía sau):
 *   - ⭐ điểm sao từng món      -> món KHÔNG có trường rating. Vẽ ra là bịa số.
 *   - "~1,2 km" từng món        -> món KHÔNG có khoảng cách; chỉ QUÁN mới có.
 *   - chuông thông báo          -> không có API nào.
 *   - "Bộ sưu tập" / "Blog"     -> chưa có trang.
 * Bốn thứ này khi nào có dữ liệu thì thêm sau. CLAUDE.md mục 4: thiếu thì để trống, tuyệt
 * đối không bịa.
 */
import { useNavigate } from 'react-router-dom';
import type { DishItem } from '@/shared/api';
import { DishList, DishListSkeleton } from '@/widgets/dish-list';
import { SiteHeader } from '@/widgets/site-header';
import { HomeHero } from '@/widgets/home-hero';
import { MoodQuickPick } from '@/widgets/mood-quick-pick';
import type { MoodChoice } from '@/widgets/mood-quick-pick';
import { DishFilters, useDishSuggestions } from '@/features/suggest-dishes';
import { useUserLocation } from '@/features/pick-location';
import { useUserSessionContext } from '@/entities/user';
import { dishRoute, ROUTES } from '@/shared/config';

export function HomePage() {
  const navigate = useNavigate();
  const location = useUserLocation();
  const suggestions = useDishSuggestions(location.position);
  const session = useUserSessionContext();

  const dishes = suggestions.dishes ?? [];
  const hasDishes = dishes.length > 0;

  const openDish = (dish: DishItem) => navigate(dishRoute(dish.dish_id));

  /** Bấm thẻ mood: đang bật thì tắt, chưa bật thì bật. Không cộng dồn cả hàng. */
  const chonNhanh = (choice: MoodChoice) => {
    if (choice.group === 'mood' || choice.group === 'weather') {
      const dangCo = suggestions.filters[choice.group] === choice.value;
      suggestions.setSingle(choice.group, dangCo ? null : choice.value);
    } else {
      suggestions.toggle(choice.group, choice.value);
    }
  };

  const dangChon = (choice: MoodChoice) => {
    if (choice.group === 'mood' || choice.group === 'weather') {
      return suggestions.filters[choice.group] === choice.value;
    }
    return suggestions.filters[choice.group].includes(choice.value);
  };

  return (
    <div className="page">
      <SiteHeader />

      <main className="page__body">
        <HomeHero
          userName={session.user?.display_name || session.user?.username || null}
          context={suggestions.context}
          // Ô tìm ở đây chỉ CHUYỂN TRANG sang luồng tìm bằng câu tự nhiên; trang đó mới là
          // nơi gọi `/search`. Trang chủ không ôm hai đường gọi API cùng lúc.
          onSearch={(query) =>
            navigate(`/tim-kiem?q=${encodeURIComponent(query)}`)
          }
        />

        <MoodQuickPick
          dangChon={dangChon}
          onPick={chonNhanh}
          onShowAll={() => {
            document
              .getElementById('bo-loc-day-du')
              ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }}
        />

        <section id="bo-loc-day-du" className="filters-block">
          <h2 className="section-title">Lọc chi tiết</h2>
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
        </section>

        <section className="results">
          <div className="results__head">
            <h2 className="section-title">
              <span aria-hidden="true">🔥</span> Món phù hợp với bạn hôm nay
            </h2>
            {hasDishes && (
              <p className="results__count">{dishes.length} món</p>
            )}
          </div>
          <p className="results__sub">
            Dựa trên mood, thời tiết và lựa chọn của bạn.
          </p>

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
            <DishList dishes={dishes} onOpen={openDish} />
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
        </section>

        {/*
          Dải mời đăng nhập ở cuối trang.

          Bản thiết kế viết "Chưa có đủ dữ liệu lịch sử?". Ta KHÔNG biết người dùng có bao
          nhiêu lịch sử — chưa có endpoint nào trả về điều đó. Thứ biết chắc là ĐÃ ĐĂNG
          NHẬP HAY CHƯA, và chưa đăng nhập thì đúng là không cá nhân hoá được. Nên chỉ hiện
          cho khách, và nói đúng lý do thay vì đoán bừa về lịch sử của họ.
        */}
        {!session.isLoggedIn && (
          <section className="cta">
            <div>
              <p className="cta__title">Muốn gợi ý sát ý bạn hơn?</p>
              <p className="cta__sub">
                Đăng nhập để MoodBite ghi nhớ món bạn thích và gợi ý chính xác hơn ở những
                lần sau.
              </p>
            </div>
            <button
              type="button"
              className="btn btn--accent"
              onClick={() => navigate(ROUTES.login)}
            >
              Đăng nhập ngay →
            </button>
          </section>
        )}
      </main>
    </div>
  );
}

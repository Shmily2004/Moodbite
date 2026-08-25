/**
 * TRANG CHỦ - bước 1 của luồng "chọn món trước, tìm quán sau".
 *
 * HAI BẢN, theo chốt của chủ dự án 2026-08-22:
 *
 *   KHÁCH (chưa đăng nhập)              | ĐÃ ĐĂNG NHẬP
 *   ------------------------------------|---------------------------------------
 *   khẩu hiệu + dải mời đăng nhập nhẹ   | "Chào buổi …, <tên> 👋"
 *   "Gợi ý nhanh theo mood"             | "Mood của bạn hôm nay là gì?"
 *   "🔥 Món phổ biến hôm nay"           | "✨ Gợi ý hôm nay dành cho <tên>"
 *   "🧭 Khám phá theo nhu cầu"          | "🕘 Xem gần đây"
 *   dải mời đăng ký ở cuối              | (không có)
 *
 * ⚠️ NGUYÊN TẮC PHÂN BIỆT HAI BẢN: chỉ đổi những gì hệ thống BIẾT THẬT.
 * Với khách, mọi câu "phù hợp với bạn" đều là nói dối — chưa có gì để cá nhân hoá, nên
 * tiêu đề phải nói đúng cơ sở xếp hạng (phổ biến / hợp thời điểm). Đây cũng chính là lý
 * do phần "Dành riêng cho bạn" của bản đã đăng nhập CHƯA làm: xem bảng bên dưới.
 *
 * ⚠️ NHỮNG THỨ TRONG SPEC CỐ TÌNH CHƯA DỰNG (không có dữ liệu thật phía sau):
 *   - ⭐ điểm sao + "0.8 km" mỗi món  -> món KHÔNG có rating cũng KHÔNG có khoảng cách.
 *   - "❤️ Dành riêng cho bạn"          -> chưa có endpoint đọc lại lịch sử/sở thích.
 *   - "❤️ Quán & món đã lưu" ĐÃ CÓ    -> `GET/POST /me/favorites` (2026-08-22). Khách
 *                                        vẫn lưu ở máy; đăng nhập thì đồng bộ lên server.
 *   - "98% phù hợp với bạn"            -> `predicted_score` là điểm XẾP HẠNG, không phải
 *                                        xác suất. Hiện ra thành % là hiểu sai (đã có
 *                                        tiền lệ, xem PROJECT_CHECKLIST).
 *   - 🔔 thông báo, Bộ sưu tập, Blog   -> chưa có API/trang.
 * CLAUDE.md mục 4: thiếu thì để trống, tuyệt đối không bịa.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { DishItem } from '@/shared/api';
import { DishList, DishListSkeleton } from '@/widgets/dish-list';
import { FilterDrawer } from '@/widgets/filter-drawer';
import { SiteHeader } from '@/widgets/site-header';
import { HomeHero } from '@/widgets/home-hero';
import { MoodQuickPick } from '@/widgets/mood-quick-pick';
import type { MoodChoice } from '@/widgets/mood-quick-pick';
import { ExploreNeeds } from '@/widgets/explore-needs';
import type { NeedPreset } from '@/widgets/explore-needs';
import { DishFilters, ghiBoLocLenUrl, useDishSuggestions } from '@/features/suggest-dishes';
import { useUserLocation } from '@/features/pick-location';
import { useRecentDishes } from '@/features/recent-dishes';
import { useFavorites } from '@/features/save-favorite';
import { ForYou } from '@/widgets/for-you';
import { useUserSessionContext } from '@/entities/user';
import { ANH_GIAO_DIEN, dishRoute, ROUTES } from '@/shared/config';
import { useT } from '@/shared/i18n';

export function HomePage() {
  const t = useT();
  const navigate = useNavigate();
  const location = useUserLocation();
  const suggestions = useDishSuggestions(location.position);
  const session = useUserSessionContext();
  const recent = useRecentDishes();
  const savedDishes = useFavorites();
  /**
   * Hàng ngang (như bản thiết kế) hay lưới đầy đủ.
   *
   * Mặc định hàng ngang: lưới 30 món đẩy mọi khối phía dưới ra khỏi màn hình, người dùng
   * không biết còn gì nữa. "Xem tất cả" mở lưới ra.
   */
  /** Ngăn kéo bộ lọc (phương án A, chủ dự án chốt 2026-08-23). */
  const [moBoLoc, setMoBoLoc] = useState(false);

  const dishes = suggestions.dishes ?? [];
  const hasDishes = dishes.length > 0;
  const ten = session.user?.display_name || session.user?.username || null;
  const daDangNhap = session.isLoggedIn;

  const openDish = (dish: DishItem) => {
    // Ghi lại TRƯỚC khi chuyển trang: sau khi `navigate` thì component này đã tháo.
    recent.remember({ dishId: dish.dish_id, name: dish.name });
    navigate(dishRoute(dish.dish_id));
  };

  /** Bấm thẻ mood: đang bật thì tắt, chưa bật thì bật. Không cộng dồn cả hàng. */
  const chonNhanh = (choice: MoodChoice) => {
    if (choice.group === 'mood' || choice.group === 'weather') {
      const dangCo = suggestions.filters[choice.group] === choice.value;
      suggestions.setSingle(choice.group, dangCo ? null : choice.value);
    } else {
      suggestions.toggle(choice.group, choice.value);
    }
    keoToiKetQua();
  };

  const dangChon = (choice: MoodChoice) => {
    if (choice.group === 'mood' || choice.group === 'weather') {
      return suggestions.filters[choice.group] === choice.value;
    }
    return suggestions.filters[choice.group].includes(choice.value);
  };

  /**
   * Áp một "nhu cầu" -> bật đúng các bộ lọc của nhu cầu đó, bấm lại là tắt.
   *
   * Dùng `applyPreset` (2026-08-24) thay cho `reset()` + nhiều lần `toggle()`. Bản cũ có
   * hai vấn đề: (1) `reset()` xoá luôn những bộ lọc người dùng TỰ bấm trước đó, (2) mỗi
   * `toggle` là một lần đặt state nên một cú bấm sinh 3-4 lần dựng lại, và vì `toggle`
   * lật giá trị nên bấm lại cùng một nhu cầu cho kết quả khó đoán.
   */
  const chonNhuCau = (preset: NeedPreset) => {
    suggestions.applyPreset(preset.apply);
    keoToiKetQua();
  };

  /** Bấm lọc ở trên mà kết quả nằm dưới màn hình thì người dùng tưởng không có gì xảy ra. */
  const keoToiKetQua = () => {
    document
      .getElementById('ket-qua')
      ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  /**
   * Nội dung bộ lọc — dựng MỘT LẦN, đặt được ở hai chỗ.
   *
   * Chủ dự án chốt 2026-08-24: màn rộng hiện thành CỘT TRÁI (kiểu TopCV), màn hẹp vẫn là
   * ngăn kéo. Chỗ đặt khác nhau nhưng phải là CÙNG MỘT component — nếu tách làm hai bản
   * thì mỗi lần thêm/bớt một bộ lọc phải sửa hai nơi, và sẽ có ngày quên một nơi.
   * Trạng thái vẫn nằm ở `useDishSuggestions`, nên hai chỗ luôn nói cùng một chuyện.
   */
  const noiDungBoLoc = (
    <>
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
    </>
  );

  return (
    <div className="page">
      <SiteHeader />

      <main className="page__body">
        <HomeHero
          userName={ten}
          context={suggestions.context}
          // Ô tìm chỉ CHUYỂN TRANG sang luồng tìm bằng câu tự nhiên; trang đó mới gọi
          // `/search`. Trang chủ không ôm hai đường gọi API cùng lúc.
          onSearch={(query) => navigate(`${ROUTES.search}?q=${encodeURIComponent(query)}`)}
        />

        <MoodQuickPick
          title={daDangNhap ? t('mood.titleLoggedIn') : t('mood.titleGuest')}
          dangChon={dangChon}
          onPick={chonNhanh}
          onShowAll={() => setMoBoLoc(true)}
        />

        {/* Khách: 6 lối vào không cần tài khoản. Người đã đăng nhập không cần hàng này —
            họ đã có mood riêng + lịch sử xem ở dưới. */}
        {!daDangNhap && <ExploreNeeds onPick={chonNhuCau} />}

        {daDangNhap && recent.recent.length > 0 && (
          <section className="recent">
            <div className="results__head">
              <h2 className="section-title">
                <span aria-hidden="true">🕘</span> {t('account.recent.title')}
              </h2>
              <button type="button" className="linkish" onClick={recent.clear}>
                {t('account.recent.clear')}
              </button>
            </div>
            <p className="section-sub">
              Món bạn vừa mở trên máy này. Lưu ngay trong trình duyệt, không gửi lên máy chủ.
            </p>
            <ul className="recent__row">
              {recent.recent.map((mon) => (
                <li key={mon.dishId}>
                  <button
                    type="button"
                    className="chip"
                    onClick={() => navigate(dishRoute(mon.dishId))}
                  >
                    {mon.name}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* ⚠️ KHÔNG đặt cột lọc vào TRANG CHỦ. Đã thử và gỡ ngày 2026-08-24.
            Bản thiết kế `frontend/design/Filler.png` là TRANG KẾT QUẢ sau khi lọc, không
            phải trang chủ. Trang chủ có luồng riêng và đang chạy tốt: hero -> ô tìm ->
            "Gợi ý nhanh theo mood" -> "Khám phá theo nhu cầu". Nhét thêm một cột lọc
            luôn hiển thị vào đây làm hỏng đúng cái luồng đó. Bộ lọc chi tiết vẫn mở được
            bằng nút "Lọc" (ngăn kéo) ngay cạnh tiêu đề kết quả. */}
        {/* "Dành riêng cho bạn" đặt TRƯỚC lưới gợi ý: với người đã lưu vài món, thứ của
            chính họ đáng lên trước gợi ý chung. Widget tự ẩn khi chưa lưu gì. */}
        <ForYou favorites={savedDishes} />

        <section id="ket-qua" className="results">
          <div className="results__head">
            <h2 className="section-title">
              {daDangNhap ? (
                <>
                  <span aria-hidden="true">✨</span>{' '}
                  {t('results.titleLoggedIn', { name: ten ?? '' })}
                </>
              ) : (
                <>
                  <span aria-hidden="true">🔥</span> {t('results.titleGuest')}
                </>
              )}
            </h2>
            <div className="results__actions">
              {/* Nút mở bộ lọc đặt NGAY CẠNH tiêu đề kết quả, không phải cuối trang:
                  lọc là việc lặp (bấm -> nhìn kết quả -> bấm tiếp), nút phải nằm trong
                  tầm mắt của chính danh sách mà nó lọc. */}
              <button
                type="button"
                className={
                  suggestions.activeFilterCount > 0
                    ? 'btn btn--sm btn--filter btn--filter-on'
                    : 'btn btn--sm btn--filter'
                }
                onClick={() => setMoBoLoc(true)}
              >
                <span aria-hidden="true">⚙️</span> {t('filters.open')}
                {suggestions.activeFilterCount > 0 && (
                  <span className="btn__badge">{suggestions.activeFilterCount}</span>
                )}
              </button>
              {hasDishes && (
              <button
                type="button"
                className="linkish"
                onClick={() => {
                  // CHUYỂN TRANG, không còn đổi bố cục tại chỗ (đổi 2026-08-25).
                  // Bản cũ bung lưới ngay trên trang chủ, khiến trang dài thêm hàng chục
                  // hàng thẻ và người dùng phải cuộn qua toàn bộ phần khám phá mỗi lần
                  // muốn xem lại kết quả. Bộ lọc đang chọn đi kèm qua query string nên
                  // sang trang mới vẫn giữ nguyên.
                  navigate({
                    pathname: ROUTES.recommend,
                    search: ghiBoLocLenUrl(suggestions.filters).toString(),
                  });
                }}
              >
                {`${t('results.showAll', { count: dishes.length })} →`}
              </button>
              )}
            </div>
          </div>

          {/*
            Câu phụ nói ĐÚNG cơ sở xếp hạng, khác nhau giữa hai bản.
            Với khách không được viết "phù hợp với bạn" — hệ thống chưa biết họ là ai; thứ
            có thật là món đó được nhiều quán ở Hà Nội bán và hợp thời điểm hiện tại.
          */}
          <p className="section-sub">
            {daDangNhap ? t('results.subLoggedIn') : t('results.subGuest')}
          </p>

          {location.error && <p className="notice notice--warn">{location.error}</p>}

          {suggestions.error && (
            <div className="notice notice--error">
              <p>{suggestions.error}</p>
              <button className="btn" onClick={suggestions.reload}>
                {t('results.retry')}
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

          {/* Trang chủ LUÔN là hàng ngang: nó lo phần KHÁM PHÁ, xem đầy đủ thì sang
              `/recommend`. Trước 2026-08-25 chỗ này bung thành lưới ngay tại trang. */}
          {suggestions.loading && <DishListSkeleton layout="row" />}

          {!suggestions.loading && !suggestions.error && hasDishes && (
            <DishList
              dishes={dishes}
              onOpen={openDish}
              layout="row"
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

          {!suggestions.loading && !suggestions.error && !hasDishes && (
            <div className="state">
              <p className="state__title">{t('results.emptyTitle')}</p>
              <p>{t('results.emptyHint')}</p>
              {suggestions.activeFilterCount > 0 && (
                <button className="chip" onClick={suggestions.reset}>
                  {t('results.clearFilters')}
                </button>
              )}
            </div>
          )}
        </section>

        {/* Bộ lọc nay nằm trong NGĂN KÉO, không còn là một khối cố định cuối trang.
            Khối cũ đẩy mọi thứ khác xuống và người dùng phải cuộn lên cuộn xuống giữa
            "bấm chip" và "xem kết quả". */}
        <FilterDrawer
          open={moBoLoc}
          onClose={() => setMoBoLoc(false)}
          activeCount={suggestions.activeFilterCount}
          onReset={suggestions.reset}
        >
          {noiDungBoLoc}
        </FilterDrawer>

        {/*
          Chỗ "bán" việc đăng ký — đặt ở CUỐI, sau khi người dùng đã thấy app có ích.
          Chủ dự án chốt: không ép ngay từ đầu.

          Nội dung nói đúng thứ đăng ký ĐEM LẠI THẬT (lưu mood, gợi ý theo lựa chọn), không
          hứa "98% phù hợp" hay "dành riêng cho bạn" — những thứ chưa có ở backend.
        */}
        {!daDangNhap && (
          <section className="cta">
            {ANH_GIAO_DIEN.mascot && (
              <img
                className="cta__mascot"
                src={ANH_GIAO_DIEN.mascot.src}
                alt=""
                width={ANH_GIAO_DIEN.mascot.width}
                height={ANH_GIAO_DIEN.mascot.height}
                aria-hidden="true"
              />
            )}
            <div className="cta__text">
              <p className="cta__title">
                <span aria-hidden="true">🎯</span> {t('cta.title')}
              </p>
              <p className="cta__sub">{t('cta.sub')}</p>
            </div>
            <div className="cta__actions">
              <button type="button" className="btn" onClick={keoToiKetQua}>
                {t('cta.explore')}
              </button>
              <button
                type="button"
                className="btn btn--accent"
                onClick={() => navigate(ROUTES.register)}
              >
                {t('cta.register')}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

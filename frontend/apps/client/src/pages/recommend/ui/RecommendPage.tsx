/**
 * TRANG KẾT QUẢ GỢI Ý MÓN — `/recommend`.
 *
 * Dựng theo `frontend/design/Food recommend.jpg` (chủ dự án chốt 2026-08-26):
 *
 *   ← Quay lại trang chủ
 *   Món phù hợp với bạn hôm nay
 *   [Trời mưa ✕] [Đồ nướng ✕] [Món nóng ✕]  [Chỉnh sửa]
 *
 *   ★ NHỮNG MÓN PHÙ HỢP NHẤT VỚI BẠN
 *     ┌────────┐  Bún chả              ┌──────────────┐
 *     │ ảnh to │  86 quán gần bạn      │ vì sao gợi ý │
 *     └────────┘  [Khám phá Bún chả]   └──────────────┘
 *     [nhỏ][nhỏ][nhỏ][nhỏ][nhỏ]
 *
 *   ♥ CÓ THỂ BẠN SẼ THÍCH
 *     [nhỏ][nhỏ][nhỏ][nhỏ][nhỏ]
 *
 * ⚠️ KHÔNG hiện ⭐ rating và km trên thẻ món, dù bản thiết kế có. Chủ dự án chốt
 * 2026-08-25 rằng đó là lỗi thiết kế: MÓN không có trường rating (chỉ QUÁN mới có, và
 * chỉ 2,2% quán có), còn km là của quán gần nhất nên đặt trên thẻ món thì đọc thành
 * "món này cách 1,2 km" — vô nghĩa.
 *
 * ⚠️ KHÔNG PHẢI `/search`. Trang đó tìm QUÁN bằng câu tự nhiên và có bản đồ.
 *
 * BỘ LỌC NẰM TRÊN URL — xem `features/suggest-dishes/model/boLocTuUrl.ts`.
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { SiteHeader } from '@/widgets/site-header';
import { DishList, DishListSkeleton } from '@/widgets/dish-list';
import { FilterDrawer } from '@/widgets/filter-drawer';
import { AssistantBubble } from '@/widgets/assistant-bubble';
import { DishCard } from '@/entities/dish';
import type { ChipDangBat } from '@/features/suggest-dishes';
import {
  DishFilters,
  chipDangBat,
  docBoLocTuUrl,
  ghiBoLocLenUrl,
  useDishSuggestions,
} from '@/features/suggest-dishes';
import { useUserLocation } from '@/features/pick-location';
import { useFavorites } from '@/features/save-favorite';
import { ANH_GIAO_DIEN, ROUTES } from '@/shared/config';
import { IconClose, IconFilter, IconHeart, IconStar } from '@/shared/ui';
import { useT } from '@/shared/i18n';

/** Số món trong khối "phù hợp nhất": 1 thẻ lớn + 5 thẻ nhỏ, đúng như thiết kế. */
const SO_MON_NOI_BAT = 6;

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

  // Bộ lọc đổi -> ghi ngược lên URL. `replace` để mỗi lần bấm chip KHÔNG tạo một mục mới
  // trong lịch sử: bấm 5 chip rồi phải bấm Back 5 lần mới ra khỏi trang là rất khó chịu.
  useEffect(() => {
    setSearchParams(ghiBoLocLenUrl(suggestions.filters), { replace: true });
  }, [suggestions.filters, setSearchParams]);

  const dishes = suggestions.dishes ?? [];
  const noiBat = dishes.slice(0, SO_MON_NOI_BAT);
  const monDau = noiBat[0] ?? null;
  const monPhu = noiBat.slice(1);

  // "Có thể bạn sẽ thích" = phần còn lại của danh sách ĐÃ XẾP HẠNG.
  //
  // ⚠️ ĐÂY KHÔNG PHẢI GỢI Ý CÁ NHÂN HOÁ, và câu phụ dưới tiêu đề nói đúng như vậy.
  // Cá nhân hoá thật cần lịch sử hành vi, mà `interactions.jsonl` mới có vài bản ghi.
  // Đặt tên "dành riêng cho bạn" lúc này là hứa thứ chưa có.
  const coTheThich = dishes.slice(SO_MON_NOI_BAT);

  const chips = chipDangBat(suggestions.filters);
  const goChip = (chip: ChipDangBat) => {
    if (chip.nhomNhieu) suggestions.toggle(chip.nhomNhieu, chip.giaTri);
    else if (chip.nhomMot) suggestions.setSingle(chip.nhomMot, null);
  };

  const moMon = (dishId: string) => navigate(ROUTES.dish.replace(':dishId', dishId));
  const daLuu = (dishId: string) => savedDishes.isSaved('dish', dishId);
  const luuMon = (dishId: string, ten: string) =>
    savedDishes.toggle({ itemType: 'dish', itemId: dishId, name: ten });

  return (
    <div className="page">
      <SiteHeader />

      <main className="page__body recommend">
        <Link className="recommend__quay-lai" to={ROUTES.home}>
          ← {t('recommend.back')}
        </Link>

        <div className="recommend__dau">
          <div className="recommend__dau-chu">
            <h1 className="recommend__tieu-de">{t('recommend.heading')}</h1>
            <p className="recommend__phu-de">{t('recommend.sub')}</p>

            {/* Chip bộ lọc đang bật, gỡ được TỪNG CÁI — đúng như thiết kế. */}
            <div className="recommend__chips">
              {chips.map((chip) => (
                <button
                  key={chip.khoa}
                  type="button"
                  className="chip chip--active chip--go"
                  onClick={() => goChip(chip)}
                >
                  {chip.nhan}
                  <IconClose className="chip__go" />
                </button>
              ))}
              <button
                type="button"
                className="chip chip--flat"
                onClick={() => setMoBoLoc(true)}
              >
                <IconFilter /> {t('recommend.edit')}
              </button>
            </div>
          </div>

          {ANH_GIAO_DIEN.banner_trang_chu && (
            <img
              className="recommend__banner"
              src={ANH_GIAO_DIEN.banner_trang_chu.src}
              alt=""
              loading="lazy"
            />
          )}
        </div>

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

        {!suggestions.loading && !suggestions.error && dishes.length === 0 && (
          <div className="notice">
            <p>{t('recommend.empty')}</p>
            {suggestions.activeFilterCount > 0 && (
              <button className="btn" onClick={suggestions.reset}>
                {t('results.clearFilters')}
              </button>
            )}
          </div>
        )}

        {!suggestions.loading && monDau && (
          <section className="recommend__khoi">
            <h2 className="recommend__nhan-khoi">
              <IconStar filled /> {t('recommend.bestTitle')}
            </h2>
            <p className="section-sub">{t('recommend.bestSub')}</p>

            <div className="mon-noi-bat">
              <DishCard
                dish={monDau}
                onOpen={() => moMon(monDau.dish_id)}
                saved={daLuu(monDau.dish_id)}
                onToggleSave={() => luuMon(monDau.dish_id, monDau.name)}
              />

              <div className="mon-noi-bat__info">
                <h3 className="mon-noi-bat__ten">{monDau.name}</h3>
                {monDau.has_description && (
                  <p className="mon-noi-bat__mo-ta">{monDau.description}</p>
                )}
                <p className="mon-noi-bat__so-quan">
                  {t('recommend.nearbyCount', { count: monDau.restaurant_count })}
                </p>
                <button
                  type="button"
                  className="btn btn--accent"
                  onClick={() => moMon(monDau.dish_id)}
                >
                  {t('recommend.explore', { name: monDau.name })} →
                </button>
              </div>

              {/* Ô "vì sao gợi ý" — dùng `reasons` do BACKEND trả, không phải câu quảng
                  cáo tự chế. Thiết kế để một câu marketing ở đây; ta thay bằng lý do
                  thật, vì đó mới là thứ giải thích được và không bịa. */}
              {monDau.reasons.length > 0 && (
                <blockquote className="mon-noi-bat__ly-do">
                  {monDau.reasons.join(' · ')}
                </blockquote>
              )}
            </div>

            {monPhu.length > 0 && (
              <DishList
                dishes={monPhu}
                layout="row"
                onOpen={(dish) => moMon(dish.dish_id)}
                isSaved={(dish) => daLuu(dish.dish_id)}
                onToggleSave={(dish) => luuMon(dish.dish_id, dish.name)}
              />
            )}
          </section>
        )}

        {!suggestions.loading && coTheThich.length > 0 && (
          <section className="recommend__khoi">
            <h2 className="recommend__nhan-khoi">
              <IconHeart /> {t('recommend.mayLikeTitle')}
            </h2>
            <p className="section-sub">{t('recommend.mayLikeSub')}</p>

            <DishList
              dishes={coTheThich}
              layout="grid"
              onOpen={(dish) => moMon(dish.dish_id)}
              isSaved={(dish) => daLuu(dish.dish_id)}
              onToggleSave={(dish) => luuMon(dish.dish_id, dish.name)}
            />
          </section>
        )}

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

/**
 * Tab TỔNG QUAN của trang tài khoản — theo `design/profile.png`:
 *
 *   cột giữa : Sở thích · Quán & món đã lưu (thẻ ngang) · Đã xem gần đây (thẻ ngang)
 *              · dải "Cải thiện gợi ý cho bạn"
 *   cột phải : Cấp độ · Huy hiệu · Khẩu vị của bạn (radar)
 *
 * Mọi "Xem tất cả" / "Cập nhật" CHUYỂN TAB (qua `onDoiTab`), không dẫn đi trang khác —
 * nội dung đầy đủ đã nằm ở chính các tab đó.
 */
import { BadgeGrid, LevelCard, TasteRadar } from '@/widgets/user-progress';
import { ItemStrip } from '@/widgets/item-strip';
import type { AnhMon } from '@/entities/dish';
import { TastePicker, trucRadar } from '@/features/taste-preferences';
import type { UseTastePreferencesResult } from '@/features/taste-preferences';
import type { UseFavoritesResult } from '@/features/save-favorite';
import type { UseRecentDishesResult } from '@/features/recent-dishes';
import type { UserStatsData } from '@/shared/api';
import { ANH_GIAO_DIEN } from '@/shared/config';
import { IconClock, IconHeart } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { theTuMonDaXem, theTuMucDaLuu } from './savedTabs';

/** Số thẻ tối đa mỗi hàng ở Tổng quan. Còn lại xem ở tab riêng qua "Xem tất cả". */
const SO_THE_TOI_DA = 10;

export type TabDich = 'saved' | 'recent' | 'taste';

export interface OverviewTabProps {
  favorites: UseFavoritesResult;
  recent: UseRecentDishesResult;
  taste: UseTastePreferencesResult;
  anh: AnhMon;
  stats: UserStatsData | null;
  dangTaiStats: boolean;
  onDoiTab: (tab: TabDich) => void;
}

export function OverviewTab(props: OverviewTabProps) {
  const t = useT();

  // Một món có thể nằm ở CẢ "yêu thích" lẫn "đã lưu". Ở hàng tổng quan chỉ hiện một thẻ
  // cho mỗi món/quán — hai thẻ giống hệt nhau đứng cạnh nhau trông như lỗi.
  const daThay = new Set<string>();
  const daLuu = props.favorites.items
    .filter((m) => {
      const khoa = `${m.itemType}:${m.itemId}`;
      if (daThay.has(khoa)) return false;
      daThay.add(khoa);
      return true;
    })
    .slice(0, SO_THE_TOI_DA)
    .map((m) => theTuMucDaLuu(m, props.anh, t));

  const daXem = props.recent.recent
    .slice(0, SO_THE_TOI_DA)
    .map((mon) => theTuMonDaXem(mon, props.anh, t));

  return (
    <div className="account-body account-body--two">
      <div className="account-col">
        <TastePicker prefs={props.taste} />

        <ItemStrip
          title={
            <>
              <IconHeart /> {t('account.overview.savedTitle')}
            </>
          }
          items={daLuu}
          emptyText={t('account.saved.empty')}
          onSeeAll={() => props.onDoiTab('saved')}
        />

        <ItemStrip
          title={
            <>
              <IconClock /> {t('account.recent.title')}
            </>
          }
          items={daXem}
          emptyText={t('account.recent.empty')}
          onSeeAll={() => props.onDoiTab('recent')}
        />

        {/* Dải "Cải thiện gợi ý cho bạn" — dẫn về đúng chỗ làm được việc đó: tab sở thích. */}
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
            <p className="cta__title">{t('account.improve.title')}</p>
            <p className="cta__sub">{t('account.improve.sub')}</p>
          </div>
          <div className="cta__actions">
            <button
              type="button"
              className="btn btn--accent"
              onClick={() => props.onDoiTab('taste')}
            >
              {t('account.improve.cta')} →
            </button>
          </div>
        </section>
      </div>

      <aside className="account-aside">
        <LevelCard stats={props.stats} loading={props.dangTaiStats} />
        <BadgeGrid stats={props.stats} loading={props.dangTaiStats} />
        <TasteRadar truc={trucRadar(props.taste.ids)} onUpdate={() => props.onDoiTab('taste')} />
      </aside>
    </div>
  );
}

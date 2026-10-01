/**
 * Tab "Yêu thích" và "Đã xem gần đây" của trang tài khoản — dạng THẺ NHỎ có ảnh
 * (`design/profile.png`), thay cho chip chữ (2026-09-16).
 *
 * Tách khỏi `tabs.tsx` để file đó giữ dưới ~300 dòng. Các hàm `the…` dựng dữ liệu cho thẻ
 * được tab Tổng quan dùng lại, nên thẻ ở hai nơi luôn giống nhau.
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ItemRow } from '@/widgets/item-strip';
import type { ItemStripItem } from '@/widgets/item-strip';
import type { AnhMon } from '@/entities/dish';
import type { MucYeuThich, UseFavoritesResult } from '@/features/save-favorite';
import type { RecentDish, UseRecentDishesResult } from '@/features/recent-dishes';
import { IconBookmark, IconClock, IconDining, IconHeart, IconPin } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import type { HamDich } from '@/shared/i18n';
import { dishRoute, ROUTES } from '@/shared/config';

/** Một mục đã lưu -> dữ liệu thẻ. `onBo` có thì thẻ có nút bỏ khỏi danh sách. */
export function theTuMucDaLuu(
  muc: MucYeuThich,
  anh: AnhMon,
  t: HamDich,
  onBo?: { nhanDanhSach: string; bo: (muc: MucYeuThich) => void },
): ItemStripItem {
  const laMon = muc.itemType === 'dish';
  return {
    key: `${muc.listType ?? 'favorite'}:${muc.itemType}:${muc.itemId}`,
    name: muc.name,
    typeLabel: laMon ? t('account.item.dish') : t('account.item.restaurant'),
    typeIcon: laMon ? <IconDining /> : <IconPin />,
    imageUrl: laMon ? anh[muc.itemId] : null,
    // Quán CHƯA có trang riêng — panel chi tiết nằm trong trang bản đồ. Làm một link chết
    // chỉ để "cho đủ" thì tệ hơn là không có link.
    to: laMon ? dishRoute(muc.itemId) : null,
    onRemove: onBo ? () => onBo.bo(muc) : undefined,
    removeLabel: onBo
      ? t('account.item.remove', { name: muc.name, list: onBo.nhanDanhSach })
      : undefined,
  };
}

export function theTuMonDaXem(mon: RecentDish, anh: AnhMon, t: HamDich): ItemStripItem {
  return {
    key: mon.dishId,
    name: mon.name,
    typeLabel: t('account.item.dish'),
    typeIcon: <IconDining />,
    imageUrl: anh[mon.dishId],
    to: dishRoute(mon.dishId),
  };
}

// ---------------------------------------------------------------------------
// Món & quán YÊU THÍCH
// ---------------------------------------------------------------------------

export interface SavedTabProps {
  favorites: UseFavoritesResult;
  anh: AnhMon;
  /**
   * Khối gắn dưới MỖI thẻ — trang tài khoản dùng để đặt ô "Thêm vào bộ sưu tập"
   * (`features/manage-collections`). Không truyền = thẻ như cũ (tab Tổng quan).
   */
  renderFooter?: (muc: MucYeuThich) => ReactNode;
}

export function SavedTab({ favorites, anh, renderFooter }: SavedTabProps) {
  const t = useT();

  return (
    <section className="panel">
      <div className="results__head">
        <h2 className="panel__title">
          <IconHeart /> {t('account.saved.title')}
        </h2>
        {favorites.items.length > 0 && (
          <p className="results__count">
            {t('account.saved.count', { n: favorites.items.length })}
          </p>
        )}
      </div>

      {/* Nói ĐÚNG dữ liệu đang nằm ở đâu. Khách lưu trên máy, đăng nhập thì ở tài khoản. */}
      <p className="section-sub">
        {favorites.dongBo ? t('account.saved.synced') : t('account.saved.local')}
      </p>

      {favorites.error && <p className="notice notice--warn">{favorites.error}</p>}

      {favorites.items.length === 0 ? (
        <p className="section-sub">
          {t('account.saved.empty')} <Link to={ROUTES.home}>MoodBite</Link>
        </p>
      ) : (
        <>
          {/* HAI DANH SÁCH TÁCH BẠCH (2026-08-26). Ở ĐÂY danh sách rỗng VẪN hiện, kèm
              câu hướng dẫn: người dùng vào tab này là ĐANG đi tìm nó. */}
          <NhomDaLuu
            nhan={t('forYou.favorites')}
            icon={<IconHeart filled />}
            goiY={t('account.saved.hintFavorite')}
            muc={favorites.favorite.items}
            anh={anh}
            onBo={favorites.toggle}
            renderFooter={renderFooter}
          />
          <NhomDaLuu
            nhan={t('forYou.bookmarks')}
            icon={<IconBookmark filled />}
            goiY={t('account.saved.hintBookmark')}
            muc={favorites.bookmark.items}
            anh={anh}
            onBo={favorites.toggle}
            renderFooter={renderFooter}
          />
        </>
      )}
    </section>
  );
}

function NhomDaLuu(props: {
  nhan: string;
  icon: ReactNode;
  goiY: string;
  muc: MucYeuThich[];
  anh: AnhMon;
  onBo: (muc: MucYeuThich) => void;
  renderFooter?: (muc: MucYeuThich) => ReactNode;
}) {
  const t = useT();
  // Truyền NGUYÊN mục (kèm `listType`) khi bỏ: thiếu `listType` là bỏ nhầm khỏi danh sách kia.
  const the = props.muc.map((m) => ({
    ...theTuMucDaLuu(m, props.anh, t, { nhanDanhSach: props.nhan, bo: props.onBo }),
    footer: props.renderFooter?.(m),
  }));

  return (
    <div className="for-you__danh-sach">
      <p className="for-you__ten-danh-sach">
        {props.icon} {props.nhan}
      </p>
      {the.length === 0 ? <p className="section-sub">{props.goiY}</p> : <ItemRow items={the} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Đã xem gần đây
// ---------------------------------------------------------------------------

export interface RecentTabProps {
  recent: Pick<UseRecentDishesResult, 'recent' | 'clear'>;
  anh: AnhMon;
}

export function RecentTab({ recent, anh }: RecentTabProps) {
  const t = useT();

  return (
    <section className="panel">
      <div className="results__head">
        <h2 className="panel__title">
          <IconClock /> {t('account.recent.title')}
        </h2>
        {recent.recent.length > 0 && (
          <button type="button" className="linkish" onClick={recent.clear}>
            {t('account.recent.clear')}
          </button>
        )}
      </div>

      {recent.recent.length === 0 ? (
        <p className="section-sub">{t('account.recent.empty')}</p>
      ) : (
        <ItemRow items={recent.recent.map((mon) => theTuMonDaXem(mon, anh, t))} />
      )}
    </section>
  );
}

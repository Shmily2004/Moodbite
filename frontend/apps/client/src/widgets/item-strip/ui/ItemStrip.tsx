/**
 * HÀNG THẺ NGANG có tiêu đề + "Xem tất cả" — khối "Quán & món đã lưu" / "Đã xem gần đây"
 * ở tab Tổng quan (`design/profile.png`).
 *
 * `ItemRow` tách riêng để tab chi tiết dùng lại đúng hàng thẻ đó mà không kèm khung panel.
 */
import type { ReactNode } from 'react';
import { useT } from '@/shared/i18n';
import { ItemCard } from './ItemCard';
import type { ItemCardProps } from './ItemCard';

export interface ItemStripItem extends ItemCardProps {
  key: string;
}

export function ItemRow({ items }: { items: ItemStripItem[] }) {
  return (
    <ul className="item-strip">
      {items.map(({ key, ...the }) => (
        <ItemCard key={key} {...the} />
      ))}
    </ul>
  );
}

export interface ItemStripProps {
  title: ReactNode;
  items: ItemStripItem[];
  emptyText: string;
  /** Chuyển sang tab tương ứng. Không truyền thì không hiện "Xem tất cả". */
  onSeeAll?: () => void;
}

export function ItemStrip({ title, items, emptyText, onSeeAll }: ItemStripProps) {
  const t = useT();

  return (
    <section className="panel">
      <div className="results__head">
        <h2 className="panel__title">{title}</h2>
        {onSeeAll && items.length > 0 && (
          <button type="button" className="linkish" onClick={onSeeAll}>
            {t('common.viewAll')} →
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <p className="section-sub">{emptyText}</p>
      ) : (
        <ItemRow items={items} />
      )}
    </section>
  );
}

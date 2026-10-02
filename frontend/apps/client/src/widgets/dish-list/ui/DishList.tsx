/**
 * Danh sách MÓN ĂN. Tầng `widgets`: ghép entity lại, KHÔNG tự gọi API.
 *
 * HAI KIỂU BÀY, theo `design/Home.jpg`:
 *   - `row`  (mặc định) — một HÀNG NGANG trượt được, đúng như bản thiết kế.
 *   - `grid` — lưới nhiều dòng, hiện ra khi người dùng bấm "Xem tất cả".
 *
 * VÌ SAO HÀNG NGANG LÀ MẶC ĐỊNH: trang chủ có nhiều khối (mood, nhu cầu, kết quả). Một
 * lưới 30 món đẩy mọi thứ phía dưới ra khỏi màn hình, người dùng không biết còn gì nữa.
 */
import { useEffect } from 'react';
import type { DishItem } from '@/shared/api';
import { DishCard } from '@/entities/dish';
import { IconChevronLeft, IconChevronRight } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { useHorizontalScroll } from '../model/useHorizontalScroll';

interface DishListProps {
  dishes: DishItem[];
  onOpen: (dish: DishItem) => void;
  layout?: 'row' | 'grid';
  isSaved?: (dish: DishItem) => boolean;
  onToggleSave?: (dish: DishItem) => void;
  /** Danh sách "Đã lưu" (dấu trang) — tách bạch với trái tim. Xem `DishCard`. */
  isBookmarked?: (dish: DishItem) => boolean;
  onToggleBookmark?: (dish: DishItem) => void;
}

export function DishList({
  dishes,
  onOpen,
  layout = 'row',
  isSaved,
  onToggleSave,
  isBookmarked,
  onToggleBookmark,
}: DishListProps) {
  const t = useT();
  const cuonNgang = useHorizontalScroll<HTMLUListElement>();
  const { doLai } = cuonNgang;

  // Số thẻ đổi (lọc lại) thì bề rộng NỘI DUNG đổi mà khung ngoài vẫn y nguyên — thứ
  // `ResizeObserver` không bắt được. Đo lại tay để nút mũi tên hiện/ẩn cho đúng.
  useEffect(() => {
    doLai();
  }, [dishes.length, doLai]);

  const danhSach = (
    <ul
      ref={layout === 'row' ? cuonNgang.ref : undefined}
      className={layout === 'row' ? 'dishes dishes--row' : 'dishes dishes--grid'}
    >
      {dishes.map((dish) => (
        <DishCard
          key={dish.dish_id}
          dish={dish}
          onOpen={onOpen}
          // Nhãn thuộc tính (Món nước · Việt Nam…) chỉ ở LƯỚI `/recommend`, như
          // `design/Filler.png`. Dải ngang trang chủ giữ thẻ gọn như `design/Home.jpg`.
          showTags={layout === 'grid'}
          saved={isSaved?.(dish) ?? false}
          onToggleSave={onToggleSave}
          bookmarked={isBookmarked?.(dish) ?? false}
          onToggleBookmark={onToggleBookmark}
        />
      ))}
    </ul>
  );

  if (layout !== 'row') return danhSach;

  return (
    <div className="dish-strip">
      {/* Nút cuộn CHỈ hiện khi còn thẻ bị khuất ở phía đó. Là <button> thật có nhãn chữ,
          nên dùng được bằng bàn phím và trình đọc màn hình — vuốt/lăn chuột thì không. */}
      {cuonNgang.tranTrai && (
        <button
          type="button"
          className="dish-strip__nut dish-strip__nut--trai"
          aria-label={t('dishList.prev')}
          onClick={() => cuonNgang.cuon(-1)}
        >
          <IconChevronLeft />
        </button>
      )}
      {danhSach}
      {cuonNgang.tranPhai && (
        <button
          type="button"
          className="dish-strip__nut dish-strip__nut--phai"
          aria-label={t('dishList.next')}
          onClick={() => cuonNgang.cuon(1)}
        >
          <IconChevronRight />
        </button>
      )}
    </div>
  );
}

/** Vệt xương lúc đang tải - báo "sắp có nội dung" thay vì để chỗ trống trơn. */
export function DishListSkeleton({ layout = 'row' }: { layout?: 'row' | 'grid' }) {
  return (
    <ul
      className={layout === 'row' ? 'dishes dishes--row' : 'dishes dishes--grid'}
      aria-busy="true"
      aria-label="Đang tìm món"
    >
      {[0, 1, 2, 3, 4].map((i) => (
        <li key={i} className="dishcard-wrap">
          <div className="dishcard dishcard--skeleton">
            <div className="dishcard__media">
              <div className="dishcard__thumb dishcard__thumb--skeleton" />
            </div>
            <div className="dishcard__body">
              <span className="skeleton-line skeleton-line--title" />
              <span className="skeleton-line" />
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

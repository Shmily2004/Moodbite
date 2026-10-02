/**
 * Mảnh dùng chung của thẻ quán - tách khỏi `RestaurantCard.tsx` ngày 2026-10-02 khi file đó
 * vượt ~300 dòng (CLAUDE.md mục 6). Chỉ là quy tắc HIỂN THỊ, không có nghiệp vụ.
 */
import type { SearchResultItem } from '@moodbite/api-client';
import type { ReasonKind } from '../model/format';
import { IconSearch, IconSmile } from '@/shared/ui';

/**
 * Icon cho từng LOẠI lý do (thay emoji 😌 / 🔎 / 🍽 ngày 2026-09-29, checklist A9).
 * `icon-inline` cỡ theo `em` nên vừa khít cột 16px của `.why__row`.
 */
export const REASON_ICON: Record<ReasonKind, JSX.Element> = {
  feel: <IconSmile className="icon-inline" />,
  match: <IconSearch className="icon-inline" />,
};

/**
 * NÚT "XEM CHI TIẾT" — có trong bản thiết kế.
 *
 * Cả thẻ vốn đã bấm được, nhưng một nút NHÌN THẤY ĐƯỢC là thứ nói cho người dùng biết bấm
 * vào thì có gì. Không có nó thì thẻ trông như một khối chữ tĩnh và rất nhiều người không
 * thử bấm. Người gọi chỉ dựng nút khi thật sự có chỗ để mở — không bày nút chết.
 */
export function NutXemChiTiet({
  restaurant,
  onOpenDetail,
}: {
  restaurant: SearchResultItem;
  onOpenDetail: (restaurant: SearchResultItem) => void;
}) {
  return (
    <button
      type="button"
      className="card__xem"
      // Thẻ cha cũng bắt click; không chặn nổi bọt thì một cú bấm thành hai lần mở, và bộ
      // đếm thời gian xem bị ghi hai lượt.
      onClick={(event) => {
        event.stopPropagation();
        onOpenDetail(restaurant);
      }}
    >
      Xem chi tiết →
    </button>
  );
}

/** Đánh giá. `null` = CHƯA CÓ đánh giá - không bao giờ hiện "0 sao" (CLAUDE.md mục 4). */
export function DanhGia({ restaurant, chip = false }: { restaurant: SearchResultItem; chip?: boolean }) {
  const lop = chip ? 'card__chip ' : '';
  const The = chip ? 'li' : 'span';
  if (restaurant.rating == null) {
    return <The className={`${lop}card__norating`}>chưa có đánh giá</The>;
  }
  return (
    <The className={`${lop}card__rating`}>
      <span className="card__star">★</span> {restaurant.rating}
      {restaurant.user_ratings_total != null && (
        <span className="muted"> ({restaurant.user_ratings_total})</span>
      )}
    </The>
  );
}

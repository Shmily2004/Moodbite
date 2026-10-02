/**
 * Thân thẻ quán dáng GỌN (trang chi tiết món, 2026-10-02, theo `design/restaurance
 * recommend.png`): địa chỉ + MỘT hàng chip lý do + một dòng nguồn/tuổi dữ liệu.
 *
 * ⚠️ GỌN LẠI CHỨ KHÔNG BỎ BỚT: mức phù hợp, lý do khớp, món suy luận + MỨC TIN CẬY,
 * "chưa có đánh giá" và dòng nguồn/tuổi dữ liệu vẫn hiện đủ (CLAUDE.md mục 4 quy tắc 4).
 */
import type { SearchResultItem } from '@moodbite/api-client';
import type { describeFit, describeReasons } from '../model/format';
import { describeDishConfidence } from '../model/format';
import { IconDining, IconPin } from '@/shared/ui';
import { DanhGia, REASON_ICON } from './phanTheQuan';

interface Props {
  restaurant: SearchResultItem;
  fit: ReturnType<typeof describeFit>;
  reasons: ReturnType<typeof describeReasons>;
  /** Cụm · loại hình · tuổi dữ liệu · bằng chứng - đã lọc rỗng ở thẻ cha. */
  dongNguon: string;
}

export function ThanTheGon({ restaurant, fit, reasons, dongNguon }: Props) {
  const dish = restaurant.suggested_dish;
  return (
    <>
      {restaurant.address && (
        <p className="card__address">
          <IconPin className="icon-inline" /> {restaurant.address}
        </p>
      )}

      {/* MỌI tín hiệu "vì sao" dồn vào MỘT hàng chip thay cho 4-5 dòng. */}
      <ul className="card__chips">
        <li className={`card__chip fit--${fit.level}`}>
          <span className="fit__label">{fit.label}</span>
        </li>
        {reasons.map((reason) => (
          <li className="card__chip" key={reason.kind + reason.text}>
            {REASON_ICON[reason.kind]} {reason.text}
          </li>
        ))}
        {dish && (
          <li
            className={
              dish.confidence === 'specific'
                ? 'card__chip card__chip--dish'
                : 'card__chip card__chip--guess'
            }
          >
            <IconDining className="icon-inline" /> <strong>{dish.name}</strong>{' '}
            {/* Mức tin cậy vẫn là CHỮ, không giấu vào tooltip. */}
            <span>{describeDishConfidence(dish.confidence)}</span>
          </li>
        )}
        <DanhGia restaurant={restaurant} chip />
      </ul>

      {/* Cụm + loại hình gộp chung một dòng với tuổi dữ liệu. */}
      <p className="card__meta-foot">{dongNguon}</p>
    </>
  );
}

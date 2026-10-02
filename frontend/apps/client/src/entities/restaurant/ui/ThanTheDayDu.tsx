/**
 * Thân thẻ quán dáng ĐẦY ĐỦ (trang tìm kiếm bằng câu tự nhiên).
 *
 * THỨ TỰ: mức phù hợp → đánh giá · khoảng cách · giá → địa chỉ → VÌ SAO → nguồn.
 */
import type { SearchResultItem } from '@moodbite/api-client';
import type { describeFit, describeFreshness, describeReasons } from '../model/format';
import { describeCluster, describeDishConfidence } from '../model/format';
import { IconDining } from '@/shared/ui';
import { DanhGia, REASON_ICON } from './phanTheQuan';

interface Props {
  restaurant: SearchResultItem;
  fit: ReturnType<typeof describeFit>;
  reasons: ReturnType<typeof describeReasons>;
  distance: string | null;
  price: string | null;
  freshness: ReturnType<typeof describeFreshness>;
  /** Bằng chứng nguồn + khảo sát - đã lọc rỗng ở thẻ cha. */
  bangChung: string[];
}

export function ThanTheDayDu({
  restaurant,
  fit,
  reasons,
  distance,
  price,
  freshness,
  bangChung,
}: Props) {
  const dish = restaurant.suggested_dish;
  const dongNguon = [freshness?.text, ...bangChung].filter(Boolean).join(' · ');
  return (
    <>
      {/* MỨC PHÙ HỢP. Nhãn chữ là phần nói thật; thanh chỉ để so tương đối giữa các quán.
          KHÔNG hiện `predicted_score × 100` - xem giải thích dài ở `model/format.ts`, điểm
          thật dồn quanh 0.6 nên hiện % sẽ gây hiểu nhầm. */}
      <div className={`fit fit--${fit.level}`}>
        <span className="fit__label">{fit.label}</span>
        <span className="fit__bar">
          <i style={{ width: `${fit.barPercent}%` }} />
        </span>
      </div>

      <div className="card__stats tnum">
        <DanhGia restaurant={restaurant} />
        {distance && <span>{distance}</span>}
        {price && <span>{price}</span>}
      </div>

      {restaurant.address && <p className="card__address">{restaurant.address}</p>}

      {/* VÌ SAO QUÁN NÀY - phần làm nên khác biệt so với một danh sách quán thường. */}
      <ul className="why">
        {reasons.map((reason) => (
          <li className="why__row" key={reason.kind + reason.text}>
            {REASON_ICON[reason.kind]}
            <span>{reason.text}</span>
          </li>
        ))}

        {dish && (
          <li className="why__row">
            <IconDining className="icon-inline" />
            <span>
              <span className={dish.confidence === 'specific' ? 'tag tag--dish' : 'tag tag--guess'}>
                {dish.name}
              </span>{' '}
              {/* Món là SUY LUẬN, không phải thực đơn thật. Mức tin cậy PHẢI hiện ra chữ
                  (CLAUDE.md mục 4 quy tắc 4) - để trong tooltip là không đủ, trên điện
                  thoại sẽ không bao giờ thấy. */}
              <span className="muted">{describeDishConfidence(dish.confidence)}</span>
            </span>
          </li>
        )}
      </ul>

      <p className="card__meta-foot">
        {describeCluster(restaurant.experience_cluster_label)}
        {restaurant.category && ` · ${restaurant.category}`}
      </p>

      {/* TUỔI THẬT & BẰNG CHỨNG. Cố ý để ở dòng cuối, chữ nhỏ: đây là phần MINH BẠCH về
          nguồn, không phải thứ người dùng đọc đầu tiên. Nhưng im lặng hoàn toàn thì người
          dùng mặc định cho rằng dữ liệu vừa được kiểm hôm qua - trong khi 71,5% bản ghi OSM
          được sửa lần cuối từ 2025 trở về trước. */}
      {dongNguon && (
        <p className={freshness?.stale ? 'card__origin card__origin--stale' : 'card__origin'}>
          {dongNguon}
        </p>
      )}
    </>
  );
}

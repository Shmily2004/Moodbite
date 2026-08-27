/**
 * Thẻ ĐỀ XUẤT — component "NGU" (dumb): chỉ nhận props và render.
 *
 * KHÔNG gọi API, KHÔNG giữ state phức tạp, KHÔNG chứa quy tắc nghiệp vụ.
 *
 * THỨ TỰ THÔNG TIN — đây là USP của MoodBite, không phải danh sách quán thường:
 *   1. tên quán
 *   2. MỨC PHÙ HỢP  ← thứ hai người đọc nhìn thấy, vì đó là giá trị của sản phẩm
 *   3. đánh giá · khoảng cách · giá
 *   4. VÌ SAO được đề xuất (mood + khớp nội dung + món)
 *
 * Mọi thứ ở đây là quy tắc HIỂN THỊ. Việc chấm điểm và xếp hạng nằm hoàn toàn ở backend
 * (`domain/services/search_ranking.py`) - xem CLAUDE.md mục 1b.
 */
import type { ReactNode } from 'react';
import type { SearchResultItem } from '@moodbite/api-client';
import {
  describeCluster,
  describeDishConfidence,
  describeFit,
  describeFreshness,
  describeReasons,
  describeSurvey,
  describeTemporaryClosure,
  describeVerification,
  formatDistance,
  formatPrice,
} from '../model/format';
import { RestaurantThumb } from './RestaurantThumb';

interface RestaurantCardProps {
  restaurant: SearchResultItem;
  /** Câu người dùng gõ - để nói "Hợp với ..." bằng chính lời của họ. */
  queryText?: string | null;
  /** Quán đang được chọn trên bản đồ -> tô nền để nối bản đồ với danh sách. */
  active?: boolean;
  onOpenDetail?: (restaurant: SearchResultItem) => void;
  children?: ReactNode;
  /**
   * Số thứ tự 1, 2, 3… KHỚP với ghim cùng số trên bản đồ.
   *
   * Chủ dự án chốt 2026-08-27 theo `design/restaurance recommend.png`. Bỏ trống thì
   * không hiện số — trang tìm kiếm giữ nguyên như cũ.
   *
   * ⚠️ KHÁC `rank_position`: `rank_position` là THỨ HẠNG do backend chấm và không đổi
   * khi người dùng sắp lại danh sách; số này là VỊ TRÍ TRONG DANH SÁCH ĐANG NHÌN, nên
   * sắp theo "gần nhất" thì nó đổi theo. Hai thứ khác nhau, đừng dùng lẫn.
   */
  soThuTu?: number;
}

export function RestaurantCard({
  restaurant,
  queryText,
  active = false,
  onOpenDetail,
  children,
  soThuTu,
}: RestaurantCardProps) {
  const dish = restaurant.suggested_dish;
  const price = formatPrice(restaurant.price_range);
  const distance = formatDistance(restaurant.distance_m);
  const fit = describeFit(restaurant.predicted_score);
  const reasons = describeReasons(restaurant.match_source, queryText);
  // TRẠNG THÁI & TUỔI THẬT - backend cào về từ 2026-08-19 nhưng giao diện chưa dùng,
  // nên người dùng vẫn bị gợi ý quán đang nghỉ mà không hề được báo trước.
  const closure = describeTemporaryClosure(restaurant.temporarily_closed);
  const freshness = describeFreshness(restaurant.source_updated_at);
  const verification = describeVerification(restaurant.source_datasets);
  const survey = describeSurvey(restaurant.surveyed_at);

  return (
    <li data-id={restaurant.restaurant_id ?? undefined}>
      <div
        className={active ? 'card card--active' : 'card'}
        onClick={() => onOpenDetail?.(restaurant)}
        role={onOpenDetail ? 'button' : undefined}
        tabIndex={onOpenDetail ? 0 : undefined}
        onKeyDown={(event) => {
          if (onOpenDetail && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            onOpenDetail(restaurant);
          }
        }}
      >
        <div className="card__anh">
          <RestaurantThumb
            name={restaurant.name}
            category={restaurant.category}
            thumbnailUrl={restaurant.thumbnail_url}
          />
          {soThuTu != null && (
            <span className="card__so" aria-hidden="true">
              {soThuTu}
            </span>
          )}
        </div>

        <div className="card__body">
          <h3 className="card__title">
            <span className="card__name">{restaurant.name}</span>
            {/* NHÃN "NỔI TIẾNG" — quy tắc ở `domain/services/restaurant_badges.py`.
                ⚠️ Không có nhãn KHÔNG có nghĩa là "quán không nổi tiếng": chỉ 2,4% quán
                có dữ liệu review. Nhãn này chỉ để KHẲNG ĐỊNH, không bao giờ để phủ định,
                và không được đem đi sắp xếp hay lọc. */}
            {restaurant.is_famous && <span className="card__noi-tieng">Nổi tiếng</span>}
            <span className="card__rank tnum">#{restaurant.rank_position}</span>
          </h3>

          {/* ĐANG TẠM ĐÓNG - phải nằm TRƯỚC mức phù hợp: quán đang nghỉ thì "Rất phù
              hợp" là thông tin vô nghĩa, và người đọc lướt thẻ từ trên xuống. */}
          {closure && (
            <p className="card__alert" role="status">
              <span aria-hidden="true">⚠</span> {closure}
            </p>
          )}

          {/* MỨC PHÙ HỢP. Nhãn chữ là phần nói thật; thanh chỉ để so tương đối giữa
              các quán. KHÔNG hiện `predicted_score × 100` - xem giải thích dài ở
              `model/format.ts`, điểm thật dồn quanh 0.6 nên hiện % sẽ gây hiểu nhầm. */}
          <div className={`fit fit--${fit.level}`}>
            <span className="fit__label">{fit.label}</span>
            <span className="fit__bar">
              <i style={{ width: `${fit.barPercent}%` }} />
            </span>
          </div>

          <div className="card__stats tnum">
            {/* null = CHƯA CÓ đánh giá. Không bao giờ hiện "0 sao". */}
            {restaurant.rating != null ? (
              <span className="card__rating">
                <span className="card__star">★</span> {restaurant.rating}
                {restaurant.user_ratings_total != null && (
                  <span className="muted"> ({restaurant.user_ratings_total})</span>
                )}
              </span>
            ) : (
              <span className="card__norating">chưa có đánh giá</span>
            )}
            {distance && <span>{distance}</span>}
            {price && <span>{price}</span>}
          </div>

          {restaurant.address && <p className="card__address">{restaurant.address}</p>}

          {/* VÌ SAO QUÁN NÀY - phần làm nên khác biệt so với một danh sách quán thường. */}
          <ul className="why">
            {reasons.map((reason) => (
              <li className="why__row" key={reason.icon + reason.text}>
                <span aria-hidden="true">{reason.icon}</span>
                <span>{reason.text}</span>
              </li>
            ))}

            {dish && (
              <li className="why__row">
                <span aria-hidden="true">🍽</span>
                <span>
                  <span
                    className={
                      dish.confidence === 'specific' ? 'tag tag--dish' : 'tag tag--guess'
                    }
                  >
                    {dish.name}
                  </span>{' '}
                  {/* Món là SUY LUẬN, không phải thực đơn thật. Mức tin cậy PHẢI hiện
                      ra chữ (CLAUDE.md mục 4 quy tắc 4) - để trong tooltip là không đủ,
                      trên điện thoại sẽ không bao giờ thấy. */}
                  <span className="muted">{describeDishConfidence(dish.confidence)}</span>
                </span>
              </li>
            )}
          </ul>

          <p className="card__meta-foot">
            {describeCluster(restaurant.experience_cluster_label)}
            {restaurant.category && ` · ${restaurant.category}`}
          </p>

          {/* TUỔI THẬT & BẰNG CHỨNG. Cố ý để ở dòng cuối, chữ nhỏ: đây là phần MINH BẠCH
              về nguồn, không phải thứ người dùng đọc đầu tiên. Nhưng im lặng hoàn toàn
              thì người dùng mặc định cho rằng dữ liệu vừa được kiểm hôm qua - trong khi
              71,5% bản ghi OSM được sửa lần cuối từ 2025 trở về trước. */}
          {(freshness || verification || survey) && (
            <p className={freshness?.stale ? 'card__origin card__origin--stale' : 'card__origin'}>
              {[freshness?.text, verification, survey].filter(Boolean).join(' · ')}
            </p>
          )}

          {/* NÚT "XEM CHI TIẾT" — có trong bản thiết kế.
              Cả thẻ vốn đã bấm được, nhưng một nút NHÌN THẤY ĐƯỢC là thứ nói cho người
              dùng biết bấm vào thì có gì. Không có nó thì thẻ trông như một khối chữ
              tĩnh và rất nhiều người không thử bấm.
              Chỉ hiện khi thật sự có chỗ để mở — không bày nút chết. */}
          {onOpenDetail && (
            <button
              type="button"
              className="card__xem"
              // Thẻ cha cũng bắt click; không chặn nổi bọt thì một cú bấm thành hai lần
              // mở, và bộ đếm thời gian xem bị ghi hai lượt.
              onClick={(event) => {
                event.stopPropagation();
                onOpenDetail(restaurant);
              }}
            >
              Xem chi tiết →
            </button>
          )}
        </div>
      </div>

      {children}
    </li>
  );
}

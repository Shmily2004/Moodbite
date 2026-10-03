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
 *
 * File này chỉ giữ KHUNG thẻ (ảnh, tiêu đề, cảnh báo đóng cửa, cột phải). Thân thẻ tách
 * thành `ThanTheGon` / `ThanTheDayDu` ngày 2026-10-02 khi file vượt ~300 dòng.
 */
import type { ReactNode } from 'react';
import type { SearchResultItem } from '@moodbite/api-client';
import {
  describeCluster,
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
import { ThanTheDayDu } from './ThanTheDayDu';
import { ThanTheGon } from './ThanTheGon';
import { NutXemChiTiet } from './phanTheQuan';
import { IconPin } from '@/shared/ui';
import { useT } from '@/shared/i18n';

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
  /** Dáng GỌN một hàng (trang chi tiết món) - xem `ThanTheGon`. */
  gon?: boolean;
}

export function RestaurantCard({
  restaurant,
  queryText,
  active = false,
  onOpenDetail,
  children,
  soThuTu,
  gon = false,
}: RestaurantCardProps) {
  const t = useT();
  const price = formatPrice(restaurant.price_range);
  const distance = formatDistance(restaurant.distance_m);
  const fit = describeFit(restaurant.predicted_score, t);
  const reasons = describeReasons(restaurant.match_source, queryText, t);
  // TRẠNG THÁI & TUỔI THẬT - backend cào về từ 2026-08-19 nhưng giao diện chưa dùng,
  // nên người dùng vẫn bị gợi ý quán đang nghỉ mà không hề được báo trước.
  const closure = describeTemporaryClosure(restaurant.temporarily_closed, t);
  const freshness = describeFreshness(restaurant.source_updated_at, undefined, t);
  const bangChung = [
    describeVerification(restaurant.source_datasets, t),
    describeSurvey(restaurant.surveyed_at, t),
  ].filter((x): x is string => Boolean(x));

  return (
    <li data-id={restaurant.restaurant_id ?? undefined}>
      <div
        className={['card', gon && 'card--gon', active && 'card--active']
          .filter(Boolean)
          .join(' ')}
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
                ⚠ Không có nhãn KHÔNG có nghĩa là "quán không nổi tiếng": chỉ 2,4% quán
                có dữ liệu review. Nhãn này chỉ để KHẲNG ĐỊNH, không bao giờ để phủ định,
                và không được đem đi sắp xếp hay lọc. */}
            {restaurant.is_famous && <span className="card__noi-tieng">{t('rest.famous')}</span>}
            {/* Có số thứ tự trên ảnh (khớp ghim bản đồ) thì KHÔNG in thêm "#1" cạnh tên —
                hai con số đứng cạnh nhau, lại có thể KHÁC nhau khi sắp theo "gần nhất",
                chỉ làm người đọc rối (bỏ 2026-10-02). Trang tìm kiếm không đánh số nên
                vẫn giữ thứ hạng ở đây. */}
            {soThuTu == null && (
              <span className="card__rank tnum">#{restaurant.rank_position}</span>
            )}
          </h3>

          {/* ĐANG TẠM ĐÓNG - phải nằm TRƯỚC mức phù hợp: quán đang nghỉ thì "Rất phù
              hợp" là thông tin vô nghĩa, và người đọc lướt thẻ từ trên xuống. */}
          {closure && (
            <p className="card__alert" role="status">
              <span aria-hidden="true">⚠</span> {closure}
            </p>
          )}

          {gon ? (
            <ThanTheGon
              restaurant={restaurant}
              fit={fit}
              reasons={reasons}
              dongNguon={[
                describeCluster(restaurant.experience_cluster_label, t),
                restaurant.category,
                freshness?.text,
                ...bangChung,
              ]
                .filter(Boolean)
                .join(' · ')}
            />
          ) : (
            <ThanTheDayDu
              restaurant={restaurant}
              fit={fit}
              reasons={reasons}
              distance={distance}
              price={price}
              freshness={freshness}
              bangChung={bangChung}
            />
          )}

          {!gon && onOpenDetail && (
            <NutXemChiTiet restaurant={restaurant} onOpenDetail={onOpenDetail} />
          )}
        </div>

        {/* CỘT PHẢI của dáng gọn: khoảng cách / giá / nút — canh phải như bản thiết kế.
            Thiếu giá thì KHÔNG in gì (không bao giờ "0 ₫"). */}
        {gon && (
          <div className="card__ben tnum">
            {distance && (
              <span className="card__ben-km">
                {distance} <IconPin className="icon-inline" />
              </span>
            )}
            {price && <span className="card__ben-gia">{price}</span>}
            {onOpenDetail && <NutXemChiTiet restaurant={restaurant} onOpenDetail={onOpenDetail} />}
          </div>
        )}
      </div>

      {children}
    </li>
  );
}

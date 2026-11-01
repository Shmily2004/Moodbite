/**
 * Phần ĐẦU trang chi tiết quán - component "ngu", chỉ nhận dữ liệu và báo khi bấm.
 *
 * BỐ CỤC SUY TỪ `design/restaurance recommend.png` (chưa có bản vẽ riêng cho màn này):
 * ảnh bo góc bên trái · tên lớn + hàng chip bên giữa · tranh Hà Nội mờ dần bên phải.
 * Dùng LẠI class `dish-detail__*` / `dish-attr` để hai trang chi tiết nhìn cùng một họ.
 */
import { useState } from 'react';
import type { RestaurantInfo } from '@moodbite/api-client';
import { RestaurantThumb, describeTemporaryClosure, formatPrice } from '@/entities/restaurant';
import { IconDining, IconHeart, IconPin, IconStar, IconStore } from '@/shared/ui';
import { ANH_GIAO_DIEN } from '@/shared/config';
import { useT } from '@/shared/i18n';

interface RestaurantHeroProps {
  info: RestaurantInfo;
  /**
   * Ảnh ứng viên theo thứ tự ưu tiên (ảnh quán Apify trước, `thumbnail_url` sau).
   * Link ảnh Google HẾT HẠN theo thời gian (đo 2026-10-28: cả 8 ảnh một quán đều hỏng),
   * nên phải thử lần lượt - và hỏng hết thì về ô màu có biểu tượng, không để khung trắng.
   */
  anhUngVien: string[];
  daLuu: boolean;
  onToggleLuu: () => void;
  chiDuong: string | null;
  onChiDuong: () => void;
}

export function RestaurantHero({
  info,
  anhUngVien,
  daLuu,
  onToggleLuu,
  chiDuong,
  onChiDuong,
}: RestaurantHeroProps) {
  const t = useT();
  const gia = formatPrice(info.price_range);
  const dongTam = describeTemporaryClosure(info.temporarily_closed, t);
  const tranh = ANH_GIAO_DIEN.banner_trang_chu;
  const [soAnhLoi, setSoAnhLoi] = useState(0);
  const anh = anhUngVien[soAnhLoi] ?? null;

  return (
    <section className="dish-detail rest-hero">
      <div className="rest-hero__anh">
        {anh ? (
          <img
            key={anh}
            className="rest-hero__img"
            src={anh}
            alt={t('rest.photoAlt', { name: info.name })}
            onError={() => setSoAnhLoi((n) => n + 1)}
          />
        ) : (
          <RestaurantThumb name={info.name} category={info.category} thumbnailUrl={null} />
        )}
      </div>

      <div className="dish-detail__info">
        <h1 className="dish-detail__name rest-hero__ten">
          {info.name}
          {/* Chỉ KHẲNG ĐỊNH - không có nhãn nghĩa là CHƯA BIẾT, không phải "không nổi tiếng". */}
          {info.is_famous && <span className="card__noi-tieng">{t('rest.famous')}</span>}
        </h1>

        {dongTam && <p className="notice notice--warn rest-hero__dong">{dongTam}</p>}

        <ul className="dish__tags dish-attrs">
          {info.category && (
            <li className="dish-attr">
              <IconStore />
              {info.category}
            </li>
          )}
          {/* `null` = CHƯA CÓ đánh giá - không bao giờ vẽ "0 sao" (CLAUDE.md mục 4). */}
          <li className="dish-attr">
            <IconStar />
            {info.rating == null
              ? t('rest.noRating')
              : `${info.rating}${info.user_ratings_total != null ? ` (${info.user_ratings_total})` : ''}`}
          </li>
          {gia && (
            <li className="dish-attr">
              <IconDining />
              {gia}
            </li>
          )}
          {info.district && (
            <li className="dish-attr dish-attr--phu">
              <IconPin />
              {info.district}
            </li>
          )}
        </ul>

        {info.address && <p className="rest-hero__dia-chi muted">{info.address}</p>}

        <div className="rest-hero__nut">
          {chiDuong && (
            <a
              className="btn btn--primary"
              href={chiDuong}
              target="_blank"
              rel="noopener noreferrer"
              onClick={onChiDuong}
            >
              <IconPin className="icon-inline" /> {t('restPage.directions')}
            </a>
          )}
          <button
            type="button"
            className={daLuu ? 'dish-attr dish-attr--nut rest-hero__luu--on' : 'dish-attr dish-attr--nut'}
            aria-pressed={daLuu}
            onClick={onToggleLuu}
          >
            <IconHeart filled={daLuu} /> {daLuu ? t('restPage.saved') : t('restPage.save')}
          </button>
        </div>
      </div>

      {/* Tranh Hà Nội - thuần trang trí, CSS ẩn ở màn hẹp (giống trang món). */}
      {tranh && (
        <img
          className="dish-detail__art"
          src={tranh.src}
          alt=""
          aria-hidden="true"
          width={tranh.width}
          height={tranh.height}
          loading="lazy"
        />
      )}
    </section>
  );
}

/**
 * Cột NỘI DUNG của trang chi tiết quán: nhận xét tổng hợp (Lớp 4) · ảnh · review gốc.
 *
 * Đây là LỚP LÀM GIÀU - chỉ ~2,5% quán có (1.345/52.871, đo 2026-10-28). Quán không có
 * thì hiện MỘT thẻ nói thẳng là chưa thu thập được, không để một vùng trắng khó hiểu.
 */
import { useState } from 'react';
import type { RestaurantDetailData } from '@moodbite/api-client';
import { ReviewSummary } from '@/widgets/restaurant-list';
import { IconInfo, IconStar } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { reviewCoChu } from '../model/lienKet';

/** Số review hiện lúc đầu - nhiều hơn thì cột này dài gấp mấy lần cột bên cạnh. */
const SO_REVIEW_BAN_DAU = 4;
/** Ảnh hiện trong lưới. Apify trả tối đa ~10 ảnh, phần lớn quán có 1-3. */
const SO_ANH_TOI_DA = 8;

export function RestaurantReviews({ detail }: { detail: RestaurantDetailData }) {
  const t = useT();
  const [xemHet, setXemHet] = useState(false);
  // Ảnh tải hỏng (link Google hết hạn). Ẩn từng ô thì được, nhưng hỏng HẾT mà vẫn còn thẻ
  // "Ảnh quán (8)" rỗng thì người xem tưởng trang lỗi - nên đếm để ẩn cả thẻ.
  const [anhLoi, setAnhLoi] = useState<ReadonlySet<string>>(new Set());

  if (!detail.has_details) {
    return (
      <section className="rest-card rest-card--trong">
        <IconInfo className="rest-card__icon-lon" />
        <h2 className="rest-card__tieu-de">{t('restPage.noEnrichmentTitle')}</h2>
        <p className="muted">{t('restPage.noEnrichmentHint')}</p>
      </section>
    );
  }

  const reviews = reviewCoChu(detail.reviews);
  const hien = xemHet ? reviews : reviews.slice(0, SO_REVIEW_BAN_DAU);
  const anh = detail.images.slice(0, SO_ANH_TOI_DA).filter((src) => !anhLoi.has(src));

  return (
    <>
      {detail.review_summary && (
        <section className="rest-card">
          <ReviewSummary summary={detail.review_summary} />
        </section>
      )}

      {anh.length > 0 && (
        <section className="rest-card">
          <h2 className="rest-card__tieu-de">{t('restPage.photos', { n: anh.length })}</h2>
          <div className="rest-anh">
            {anh.map((src, i) => (
              <img
                key={src}
                src={src}
                alt={t('rest.photoAlt', { name: detail.name ?? '' }) + ` ${i + 1}`}
                loading="lazy"
                // Link ảnh Google có thể hết hạn -> bỏ ô đó (và cả thẻ nếu hỏng hết).
                onError={() => setAnhLoi((cu) => new Set(cu).add(src))}
              />
            ))}
          </div>
        </section>
      )}

      {reviews.length > 0 && (
        <section className="rest-card">
          <h2 className="rest-card__tieu-de">{t('restPage.reviews', { n: reviews.length })}</h2>
          <ul className="rest-review">
            {hien.map((r, i) => (
              <li key={i} className="rest-review__muc">
                <div className="rest-review__dau">
                  {r.name && <strong>{r.name}</strong>}
                  {r.stars != null && (
                    <span className="rest-review__sao" aria-label={`${r.stars}/5`}>
                      {Array.from({ length: r.stars }, (_, k) => (
                        <IconStar key={k} />
                      ))}
                    </span>
                  )}
                  {r.publishedAt && (
                    <span className="muted small">{r.publishedAt.slice(0, 10)}</span>
                  )}
                </div>
                <p>{r.text}</p>
              </li>
            ))}
          </ul>
          {reviews.length > hien.length && (
            <button type="button" className="btn btn--pill-giua" onClick={() => setXemHet(true)}>
              {t('restPage.moreReviews', { n: reviews.length - hien.length })}
            </button>
          )}
        </section>
      )}
    </>
  );
}

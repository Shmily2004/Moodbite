/**
 * Cột BÊN của trang chi tiết quán: bản đồ vị trí · thông tin liên hệ · nguồn dữ liệu.
 *
 * Bản đồ đặt TRÊN CÙNG cột bên, giống vị trí bản đồ ở trang món - người dùng hai trang
 * tìm bản đồ ở cùng một chỗ.
 */
import type { RestaurantDetailData, RestaurantInfo } from '@moodbite/api-client';
import {
  describeCluster,
  describeFreshness,
  describeSurvey,
  describeVerification,
  formatPrice,
  tenNenTang,
} from '@/entities/restaurant';
import { ReportClosureButton } from '@/features/report-closure';
import { IconClock, IconInfo, IconPin, IconSparkle } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { safeHttpUrl } from '@/shared/lib';
import { bangGioMoCua, tagKhongGian } from '../model/lienKet';
import { RestaurantLocationMap } from './RestaurantLocationMap';

interface Props {
  restaurantId: string;
  info: RestaurantInfo;
  detail: RestaurantDetailData;
}

export function RestaurantSidebar({ restaurantId, info, detail }: Props) {
  const t = useT();
  const gio = bangGioMoCua(detail.opening_hours);
  const khongGian = tagKhongGian(detail.atmosphere, info.atmosphere_tags ?? []);
  const gia = formatPrice(detail.price_range ?? info.price_range);
  // Link đến từ dữ liệu CÀO/nhập -> chỉ render khi là http/https (chặn `javascript:`).
  const lienKet = [
    { nhan: t('restDetail.menu'), url: safeHttpUrl(detail.menu_url) },
    { nhan: t('restDetail.website'), url: safeHttpUrl(detail.website ?? info.website) },
    // Nhãn = tên miền ("facebook.com"). Chỉ dựng `URL` SAU khi `safeHttpUrl` đã duyệt, vì
    // `new URL` ném lỗi với chuỗi hỏng - một link rác không được làm sập cả trang.
    ...(info.socials ?? []).map((s) => {
      const url = safeHttpUrl(s);
      return { nhan: url ? new URL(url).hostname.replace(/^www\./, '') : '', url };
    }),
  ].filter((x): x is { nhan: string; url: string } => Boolean(x.url));

  const tuoi = describeFreshness(info.source_updated_at, undefined, t);
  const bangChung = [
    describeVerification(info.source_datasets, t),
    describeSurvey(info.surveyed_at, t),
  ].filter(Boolean);

  return (
    <aside className="rest-side">
      <div className="rest-card rest-card--ban-do">
        <RestaurantLocationMap
          lat={info.latitude}
          lng={info.longitude}
          name={info.name}
        />
      </div>

      <section className="rest-card">
        <h2 className="rest-card__tieu-de">{t('restPage.info')}</h2>
        <dl className="rest-info">
          <dt><IconPin className="icon-inline" /> {t('restPage.address')}</dt>
          <dd>{info.address ?? <span className="muted">{t('restPage.noAddress')}</span>}</dd>

          <dt><IconClock className="icon-inline" /> {t('restPage.hours')}</dt>
          <dd>
            {gio.length > 0 ? (
              <ul className="rest-gio">
                {gio.map((d) => (
                  <li key={d.day}><span>{d.day}</span><span>{d.hours}</span></li>
                ))}
              </ul>
            ) : (
              info.opening_hours ?? <span className="muted">{t('restPage.noHours')}</span>
            )}
          </dd>

          {info.phone && (
            <>
              <dt>{t('restPage.phone')}</dt>
              <dd><a href={`tel:${info.phone.replace(/\s+/g, '')}`}>{info.phone}</a></dd>
            </>
          )}
          {gia && (
            <>
              <dt>{t('restPage.price')}</dt>
              <dd>{gia}</dd>
            </>
          )}
          {khongGian.length > 0 && (
            <>
              <dt>{t('restPage.atmosphere')}</dt>
              <dd>{khongGian.join(', ')}</dd>
            </>
          )}
          {(info.amenities ?? []).length > 0 && (
            <>
              <dt>{t('restPage.amenities')}</dt>
              <dd>{(info.amenities ?? []).join(', ')}</dd>
            </>
          )}
          <dt><IconSparkle className="icon-inline" /> {t('restPage.experience')}</dt>
          {/* `null` = CHƯA phân cụm (Cold Start) -> "Đang cập nhật", không để trống. */}
          <dd>{describeCluster(info.experience_cluster_label, t)}</dd>

          {lienKet.length > 0 && (
            <>
              <dt>{t('restPage.links')}</dt>
              <dd className="rest-info__links">
                {lienKet.map((l) => (
                  <a key={l.url} href={l.url} target="_blank" rel="noopener noreferrer">
                    {l.nhan}
                  </a>
                ))}
              </dd>
            </>
          )}
        </dl>
      </section>

      {/* NGUỒN DỮ LIỆU: mỗi bản ghi phải truy được về nguồn (CLAUDE.md 4b). Đặt cuối, nhạt
          màu - là phần minh bạch cho ai muốn kiểm, không phải nội dung chính. */}
      <section className="rest-card rest-card--nguon">
        <h2 className="rest-card__tieu-de">
          <IconInfo className="icon-inline" /> {t('restPage.source')}
        </h2>
        {info.source && (
          <p className="small">{t('restPage.sourceFrom', { source: tenNenTang(info.source) })}</p>
        )}
        {tuoi && <p className={tuoi.stale ? 'small rest-nguon--cu' : 'small muted'}>{tuoi.text}</p>}
        {bangChung.map((c) => (
          <p key={c} className="small muted">{c}</p>
        ))}
        <ReportClosureButton restaurantId={restaurantId} restaurantName={info.name} />
      </section>
    </aside>
  );
}

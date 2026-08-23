/**
 * Khối MỞ ĐẦU trang chủ. HAI BẢN khác nhau, theo chốt của chủ dự án 2026-08-22:
 *
 *   KHÁCH (chưa đăng nhập)      | ĐÃ ĐĂNG NHẬP
 *   ---------------------------|--------------------------------------
 *   "Chào buổi …" (không tên)   | "Chào buổi …, <tên> 👋"
 *   khẩu hiệu "Ăn gì ở Hà Nội"  | "Hôm nay bạn muốn ăn gì?"
 *   + dải mời đăng nhập         | (không có dải mời)
 *
 * VÌ SAO PHẢI KHÁC: trang chủ của người đã đăng nhập phải cho cảm giác "đây là trang của
 * TÔI". Còn với khách thì mọi câu "dành cho bạn" đều là nói dối — hệ thống chưa biết họ
 * là ai.
 *
 * ⚠️ CÁC THẺ NGỮ CẢNH LÀ DỮ LIỆU THẬT, KHÔNG PHẢI TRANG TRÍ.
 * Chúng lấy nguyên văn từ mảng `context` mà `/dishes/suggest` trả về ("buổi tối",
 * "trời mưa", "28°C" — xem `domain/value_objects/context_signal.py`). Bản thiết kế vẽ sẵn
 * "28°C trời mưa nhẹ"; ta KHÔNG viết cứng chuỗi đó — hôm trời nắng mà vẫn hiện "trời mưa"
 * thì cả trang mất tin cậy. Nhiệt độ/thời tiết chỉ có khi bật `MOODBITE_ENABLE_WEATHER=1`.
 */
import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { ANH_GIAO_DIEN, ROUTES } from '@/shared/config';
import { Slogan } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import type { HamDich } from '@/shared/i18n';

export interface HomeHeroProps {
  /** Tên hiển thị của người đang đăng nhập, hoặc `null` khi là khách. */
  userName: string | null;
  /** Câu ngữ cảnh backend trả về, VD "trời mưa", "buổi tối", "28°C". */
  context: string[];
  onSearch: (query: string) => void;
}

/**
 * Lời chào theo giờ máy người dùng.
 *
 * QUY TẮC HIỂN THỊ thuần tuý nên đặt ở frontend là đúng chỗ — nó không đổi kết quả gợi ý
 * nào. (Giờ ăn dùng để CHẤM ĐIỂM món thì ngược lại, do backend quyết.)
 */
export function loiChao(gio: number, t: HamDich): string {
  if (gio < 11) return t('hero.morning');
  if (gio < 14) return t('hero.noon');
  if (gio < 18) return t('hero.afternoon');
  return t('hero.evening');
}

/**
 * Lời chào TỰ ĐỔI khi qua mốc giờ, không phải chỉ đúng lúc mở trang.
 *
 * VÌ SAO CẦN HẸN GIỜ: React chỉ vẽ lại khi có gì đó thay đổi. Mở trang lúc 17:59 rồi để
 * đó thì tới 18:05 vẫn còn "Chào buổi chiều" — sai mà không ai biết. Đặt hẹn đúng tới
 * MỐC KẾ TIẾP (11h/14h/18h/0h) rồi vẽ lại một lần, thay vì chạy đồng hồ mỗi giây cho một
 * dòng chữ đổi 4 lần/ngày.
 */
function useLoiChao(t: HamDich): string {
  const [gio, setGio] = useState(() => new Date().getHours());

  useEffect(() => {
    const bay_gio = new Date();
    const moc = [11, 14, 18, 24];
    const moc_ke = moc.find((h) => h > bay_gio.getHours()) ?? 24;

    const den_moc = new Date(bay_gio);
    den_moc.setHours(moc_ke, 0, 5, 0); // +5 giây cho chắc đã qua mốc
    const cho = den_moc.getTime() - bay_gio.getTime();

    const hen = setTimeout(() => setGio(new Date().getHours()), cho);
    return () => clearTimeout(hen);
  }, [gio]);

  return loiChao(gio, t);
}

/**
 * Biểu tượng cho một câu ngữ cảnh. QUY TẮC HIỂN THỊ, không đổi dữ liệu gì.
 * Không khớp từ khoá nào thì dùng chiếc đồng hồ chung chung — không bao giờ để trống.
 */
function icon(nguCanh: string): string {
  const chu = nguCanh.toLowerCase();
  if (chu.includes('mưa')) return '🌧️';
  if (chu.includes('quang') || chu.includes('nắng')) return '☀️';
  if (chu.includes('°c')) return '🌡️';
  if (chu.includes('sáng')) return '🌅';
  if (chu.includes('trưa')) return '🍽️';
  if (chu.includes('chiều')) return '🌇';
  if (chu.includes('tối')) return '🌙';
  if (chu.includes('khuya')) return '🌃';
  return '🕒';
}

export function HomeHero({ userName, context, onSearch }: HomeHeroProps) {
  const [query, setQuery] = useState('');
  const t = useT();
  const chao = useLoiChao(t);
  const tranh = ANH_GIAO_DIEN.banner_trang_chu;
  const daDangNhap = userName !== null;

  const guiTim = (event: FormEvent) => {
    event.preventDefault();
    const chu = query.trim();
    if (chu) onSearch(chu);
  };

  return (
    <section className="hero">
      <div className="hero__text">
        <p className="hero__greeting">
          {chao}
          {daDangNhap ? `, ${userName}` : ''} <span aria-hidden="true">👋</span>
        </p>

        {daDangNhap ? (
          <>
            <h1 className="hero__title">{t('hero.titleLoggedIn')}</h1>
            <p className="hero__intro">{t('hero.introLoggedIn')}</p>
          </>
        ) : (
          <>
            <h1 className="hero__slogan">
              <Slogan />
            </h1>
            <p className="hero__intro">{t('hero.introGuest')}</p>
          </>
        )}

        {context.length > 0 && (
          <ul className="hero__signals" aria-label={t('hero.signals')}>
            {context.map((tin) => (
              <li key={tin} className="signal">
                <span className="signal__icon" aria-hidden="true">
                  {icon(tin)}
                </span>
                <span className="signal__text">{tin}</span>
              </li>
            ))}
          </ul>
        )}

        <form className="hero__search" onSubmit={guiTim} role="search">
          <label className="sr-only" htmlFor="hero-search">
            {t('hero.searchLabel')}
          </label>
          <span className="hero__search-icon" aria-hidden="true">
            🔍
          </span>
          <input
            id="hero-search"
            className="hero__search-input"
            value={query}
            placeholder={t('hero.searchPlaceholder')}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button type="submit" className="btn btn--accent" disabled={query.trim() === ''}>
            {t('hero.searchButton')}
          </button>
        </form>

        {/*
          Dải mời đăng nhập NHẸ, chỉ dành cho khách.
          Chủ dự án chốt: không bật popup chặn đường, chỉ một dòng mời. Chỗ "bán" việc đăng
          ký nằm ở cuối trang, sau khi người dùng đã thấy app có ích.
        */}
        {!daDangNhap && (
          <p className="hero__nudge">
            <span aria-hidden="true">✨</span>{' '}
            <Link to={ROUTES.login}>{t('nav.login')}</Link> {t('hero.nudge')}
          </p>
        )}
      </div>

      {tranh && (
        /* Tranh trang trí: `aria-hidden` để trình đọc màn hình bỏ qua. */
        <img
          className="hero__art"
          src={tranh.src}
          alt=""
          width={tranh.width}
          height={tranh.height}
          aria-hidden="true"
        />
      )}
    </section>
  );
}

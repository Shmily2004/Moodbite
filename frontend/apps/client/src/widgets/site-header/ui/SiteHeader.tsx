/**
 * THANH TRÊN của trang chủ: logo · điều hướng · khu vực · nền tối · tài khoản.
 *
 * Là `widget` chứ không phải `app/layout` vì mới chỉ trang chủ dùng — trang bản đồ
 * (`/search`) cố tình không có thanh này để dành trọn màn hình cho bản đồ.
 *
 * ⚠️ CHỈ ĐƯA VÀO ĐÂY THỨ BẤM ĐƯỢC THẬT.
 * Bản thiết kế `design/Home.jpg` có thêm "Theo mood", "Theo thời tiết", "Bộ sưu tập",
 * "Blog" và một chuông thông báo. Bốn trang đó CHƯA TỒN TẠI và không có API nào phía sau
 * chuông. Vẽ ra rồi bấm không đi đâu thì tệ hơn là chưa có: người dùng tưởng app hỏng.
 * Làm trang nào thì thêm một dòng vào `MUC_DIEU_HUONG` là nó tự hiện ra.
 */
import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { BrandLogo, IconPin, LanguageSelect,
  IconClose,
  IconMenu,
} from '@/shared/ui';
import { ThemeToggle } from '@/features/switch-theme';
import { UserAvatar, useUserSessionContext } from '@/entities/user';
import { useAvatar } from '@/features/change-avatar';
import { ROUTES } from '@/shared/config';
import { useT } from '@/shared/i18n';
import type { Khoa } from '@/shared/i18n';

interface MucDieuHuong {
  to: string;
  /** Khoá trong từ điển, KHÔNG phải chữ viết sẵn — nếu không thì thanh trên không dịch được. */
  nhan: Khoa;
}

/** Chỉ những trang ĐÃ CÓ THẬT. Thêm trang mới thì thêm một dòng ở đây. */
const MUC_DIEU_HUONG: MucDieuHuong[] = [
  { to: ROUTES.home, nhan: 'nav.suggest' },
  { to: ROUTES.search, nhan: 'nav.search' },
];

export function SiteHeader() {
  const t = useT();
  const session = useUserSessionContext();
  // Menu ☰ cho màn hình hẹp. Dưới 760px hàng điều hướng + khu công cụ không đủ chỗ và
  // phải cuộn ngang — thao tác không ai nghĩ tới nên coi như các mục đó biến mất.
  const [moMenu, setMoMenu] = useState(false);
  const duong_dan = useLocation().pathname;

  // Chuyển trang thì ĐÓNG menu. Không có dòng này, bấm một mục xong menu vẫn phủ kín
  // màn hình và người dùng tưởng bấm hụt.
  useEffect(() => setMoMenu(false), [duong_dan]);
  const { avatar } = useAvatar();
  const ten = session.user?.display_name || session.user?.username;

  return (
    <header className="site-header">
      <Link to={ROUTES.home} className="site-header__brand" aria-label={t('nav.home')}>
        <BrandLogo height="clamp(34px, 3.4vw, 46px)" />
      </Link>

      {/* Nút ☰ chỉ hiện dưới 760px (xem `home.css`). */}
      <button
        type="button"
        className="site-header__burger"
        aria-label={t('nav.main')}
        aria-expanded={moMenu}
        onClick={() => setMoMenu((cu) => !cu)}
      >
        {moMenu ? <IconClose /> : <IconMenu />}
      </button>

      <nav
        className={moMenu ? 'site-header__nav site-header__nav--mo' : 'site-header__nav'}
        aria-label={t('nav.main')}
      >
        {MUC_DIEU_HUONG.map((muc) => (
          <NavLink
            key={muc.to}
            to={muc.to}
            end={muc.to === ROUTES.home}
            className={({ isActive }) =>
              isActive ? 'site-header__link site-header__link--active' : 'site-header__link'
            }
          >
            {t(muc.nhan)}
          </NavLink>
        ))}
      </nav>

      <div className={moMenu ? 'site-header__tools site-header__tools--mo' : 'site-header__tools'}>
        {/*
          Khu vực CỐ ĐỊNH là Hà Nội — không phải ô chọn.
          Toàn bộ dữ liệu quán chỉ có ở Hà Nội (chốt 2026-08-19, xem CLAUDE.md mục 4b).
          Làm cái dropdown chọn tỉnh khác là hứa một thứ không có dữ liệu.
        */}
        <span className="site-header__place" title={t('nav.cityHint')}>
          <IconPin width={16} height={16} />
          {t('nav.city')}
        </span>

        <LanguageSelect />
        <ThemeToggle />

        {session.isLoggedIn ? (
          <div className="site-header__account">
            <Link className="site-header__me" to={ROUTES.account}>
              <UserAvatar name={ten ?? null} src={avatar} size={32} />
              <span className="site-header__user" title={session.user?.username}>
                {/* Chưa hỏi xong `/auth/me` thì hiện dấu … thay vì nhấp nháy đổi chữ. */}
                {ten ?? '…'}
              </span>
            </Link>
            <button type="button" className="linkish" onClick={session.logout}>
              {t('nav.logout')}
            </button>
          </div>
        ) : (
          <div className="site-header__account">
            <Link className="linkish" to={ROUTES.login}>
              {t('nav.login')}
            </Link>
            <Link className="btn btn--accent btn--sm" to={ROUTES.register}>
              {t('nav.register')}
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}

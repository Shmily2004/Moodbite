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
import { Link, NavLink } from 'react-router-dom';
import { BrandLogo, IconPin } from '@/shared/ui';
import { ThemeToggle } from '@/features/switch-theme';
import { UserAvatar, useUserSessionContext } from '@/entities/user';
import { useAvatar } from '@/features/change-avatar';
import { ROUTES } from '@/shared/config';

interface MucDieuHuong {
  to: string;
  label: string;
}

/** Chỉ những trang ĐÃ CÓ THẬT. Thêm trang mới thì thêm một dòng ở đây. */
const MUC_DIEU_HUONG: MucDieuHuong[] = [
  { to: ROUTES.home, label: 'Gợi ý món ăn' },
  { to: ROUTES.search, label: 'Tìm bằng câu tự nhiên' },
];

export function SiteHeader() {
  const session = useUserSessionContext();
  const { avatar } = useAvatar();
  const ten = session.user?.display_name || session.user?.username;

  return (
    <header className="site-header">
      <Link to={ROUTES.home} className="site-header__brand" aria-label="MoodBite - trang chủ">
        <BrandLogo height="clamp(34px, 3.4vw, 46px)" />
      </Link>

      <nav className="site-header__nav" aria-label="Điều hướng chính">
        {MUC_DIEU_HUONG.map((muc) => (
          <NavLink
            key={muc.to}
            to={muc.to}
            end={muc.to === ROUTES.home}
            className={({ isActive }) =>
              isActive ? 'site-header__link site-header__link--active' : 'site-header__link'
            }
          >
            {muc.label}
          </NavLink>
        ))}
      </nav>

      <div className="site-header__tools">
        {/*
          Khu vực CỐ ĐỊNH là Hà Nội — không phải ô chọn.
          Toàn bộ dữ liệu quán chỉ có ở Hà Nội (chốt 2026-08-19, xem CLAUDE.md mục 4b).
          Làm cái dropdown chọn tỉnh khác là hứa một thứ không có dữ liệu.
        */}
        <span className="site-header__place" title="Dữ liệu MoodBite hiện chỉ có ở Hà Nội">
          <IconPin width={16} height={16} />
          Hà Nội
        </span>

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
              Đăng xuất
            </button>
          </div>
        ) : (
          <div className="site-header__account">
            <Link className="linkish" to={ROUTES.login}>
              Đăng nhập
            </Link>
            <Link className="btn btn--accent btn--sm" to={ROUTES.register}>
              Đăng ký
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}

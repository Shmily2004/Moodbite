/**
 * THANH TAB DƯỚI ĐÁY cho điện thoại — `design/Home.jpg` (bản di động).
 *
 * Chỉ hiện dưới 768px (CSS `home.css`, mục THANH TAB). Ở màn rộng `SiteHeader` đã có đủ
 * điều hướng; hiện cả hai là hai thanh làm cùng một việc.
 *
 * Gắn ở `RootLayout` chứ không ở từng trang, để trang mới tự có; layout quyết định trang
 * nào KHÔNG hiện (nhóm trang đăng nhập — xem `RootLayout`).
 */
import type { ComponentType } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { IconHeart, IconHome, IconSparkle, IconUser } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { MUC_TAB, tabDangMo } from '../model/mucTab';
import type { MaTab } from '../model/mucTab';

const ICON: Record<MaTab, ComponentType<{ className?: string }>> = {
  home: IconHome,
  suggest: IconSparkle,
  favorites: IconHeart,
  me: IconUser,
};

export function BottomTabBar() {
  const t = useT();
  const { pathname, search } = useLocation();
  const dangMo = tabDangMo(pathname, search);

  return (
    <nav className="tabbar" aria-label={t('tabbar.label')}>
      <ul className="tabbar__list">
        {MUC_TAB.map((muc) => {
          const Icon = ICON[muc.ma];
          const sang = muc.ma === dangMo;
          return (
            <li key={muc.ma}>
              <Link
                to={muc.to}
                className={sang ? 'tabbar__item tabbar__item--on' : 'tabbar__item'}
                aria-current={sang ? 'page' : undefined}
              >
                <Icon className="tabbar__icon" />
                <span>{t(muc.nhan)}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

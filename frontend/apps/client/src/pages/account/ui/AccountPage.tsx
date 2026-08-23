/**
 * TRANG TÀI KHOẢN — `/account`. Dựng theo `frontend/design/profile.png`.
 *
 * BỐ CỤC ĐÚNG BẢN THIẾT KẾ: thanh bên trái (danh sách mục) · cột giữa (nội dung) ·
 * cột phải (cấp độ + huy hiệu, chỉ ở tab Tổng quan).
 *
 * TAB LÀ THAM SỐ TRÊN URL (`?tab=saved`), không phải state trong bộ nhớ. Nhờ vậy nút Back
 * hoạt động đúng, và người dùng gửi được đường dẫn tới đúng mục mình đang xem. Đây là
 * điều `useState` không làm được, và cũng là lý do không dùng `useState` ở đây.
 *
 * ⛔ BA MỤC TRONG BẢN THIẾT KẾ CHƯA DỰNG — đã báo cáo riêng cho chủ dự án, và lý do là
 *    THIẾU DỮ LIỆU chứ không phải thiếu thời gian:
 *      · "Địa chỉ của tôi"      -> không có bảng địa chỉ, cũng chưa có endpoint nào.
 *                                  Vị trí hiện lấy từ trình duyệt (`features/pick-location`).
 *      · "Bộ sưu tập của tôi"   -> cần bảng `collections` + endpoint. Khác "đã lưu" ở chỗ
 *                                  người dùng tự đặt tên nhóm — là một tính năng riêng.
 *      · "Thông báo"            -> không có nguồn thông báo nào. Cái chuông đỏ trên bản
 *                                  thiết kế sẽ luôn trống.
 *    Vẽ ba mục đó ra rồi bấm vào không có gì thì tệ hơn là chưa có (CLAUDE.md mục 4).
 */
import { useMemo } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { SiteHeader } from '@/widgets/site-header';
import { LevelCard, BadgeGrid, StatTiles } from '@/widgets/user-progress';
import { AvatarPicker } from '@/features/change-avatar';
import { TastePicker } from '@/features/taste-preferences';
import { useFavorites } from '@/features/save-favorite';
import { useRecentDishes } from '@/features/recent-dishes';
import { ThemeToggle } from '@/features/switch-theme';
import { ChangePasswordForm } from '@/features/change-password';
import { useUserSessionContext, useUserStats } from '@/entities/user';
import { LanguageSelect } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import type { Khoa } from '@/shared/i18n';
import { ROUTES } from '@/shared/config';
import { BadgesTab, ProfileTab, RecentTab, SavedTab, thangNam } from './tabs';

/** Mã tab nằm trên URL. Đổi giá trị ở đây là đổi đường dẫn — cân nhắc trước khi sửa. */
const TABS = [
  { id: 'overview', nhan: 'account.tab.overview', icon: '🏠' },
  { id: 'profile', nhan: 'account.tab.profile', icon: '👤' },
  { id: 'taste', nhan: 'account.tab.taste', icon: '🍽️' },
  { id: 'saved', nhan: 'account.tab.saved', icon: '❤️' },
  { id: 'recent', nhan: 'account.tab.recent', icon: '🕘' },
  { id: 'badges', nhan: 'account.tab.badges', icon: '🏅' },
  { id: 'settings', nhan: 'account.tab.settings', icon: '⚙️' },
] as const satisfies ReadonlyArray<{ id: string; nhan: Khoa; icon: string }>;

type TabId = (typeof TABS)[number]['id'];

export function AccountPage() {
  const session = useUserSessionContext();
  const navigate = useNavigate();
  const t = useT();
  const favorites = useFavorites();
  const recent = useRecentDishes();
  const { stats, loading: dangTaiStats } = useUserStats();
  const [params, setParams] = useSearchParams();

  // Tab lạ trên URL (gõ tay, link cũ) -> quay về Tổng quan thay vì trang trắng.
  const tab = useMemo<TabId>(() => {
    const gia_tri = params.get('tab');
    return (TABS.find((x) => x.id === gia_tri)?.id ?? 'overview') as TabId;
  }, [params]);

  if (!session.isLoggedIn) {
    return <Navigate to={ROUTES.login} replace />;
  }

  const ten = session.user?.display_name || session.user?.username || null;
  const thamGia = thangNam(session.user?.created_at);
  const doiTab = (id: TabId) => setParams(id === 'overview' ? {} : { tab: id });

  return (
    <div className="page">
      <SiteHeader />

      <div className="account-shell">
        {/* --- Thanh bên --- */}
        <nav className="account-side" aria-label={t('account.sectionLabel')}>
          <p className="account-side__label">{t('account.sectionLabel')}</p>
          <ul className="account-side__list">
            {TABS.map((muc) => (
              <li key={muc.id}>
                <button
                  type="button"
                  className={
                    muc.id === tab
                      ? 'account-side__item account-side__item--on'
                      : 'account-side__item'
                  }
                  aria-current={muc.id === tab ? 'page' : undefined}
                  onClick={() => doiTab(muc.id)}
                >
                  <span aria-hidden="true">{muc.icon}</span> {t(muc.nhan)}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <main className="account-main">
          {/* --- Thẻ đầu trang: luôn hiện ở mọi tab, như bản thiết kế --- */}
          <section className="account__head">
            <AvatarPicker name={ten} />

            <div className="account__id">
              <h1 className="account__name">{ten ?? '…'}</h1>
              <p className="account__line">@{session.user?.username}</p>
              {session.user?.email ? (
                <p className="account__line">✉️ {session.user.email}</p>
              ) : (
                /* Không có email thì nói rõ HỆ QUẢ, thay vì để trống cho người dùng đoán. */
                <p className="account__line account__line--warn">{t('account.noEmail')}</p>
              )}
              {thamGia && (
                <p className="account__since">
                  🗓️ {t('account.memberSince', { date: thamGia })}
                </p>
              )}
            </div>

            <StatTiles stats={stats} viewedLocal={recent.recent.length} />
          </section>

          <div className={tab === 'overview' ? 'account-body account-body--two' : 'account-body'}>
            <div className="account-col">
              {tab === 'overview' && (
                <>
                  <TastePicker />
                  <SavedTab favorites={favorites} />
                  <RecentTab recent={recent} />
                </>
              )}
              {tab === 'profile' && <ProfileTab user={session.user ?? null} />}
              {tab === 'taste' && <TastePicker />}
              {tab === 'saved' && <SavedTab favorites={favorites} />}
              {tab === 'recent' && <RecentTab recent={recent} />}
              {tab === 'badges' && <BadgesTab stats={stats} loading={dangTaiStats} />}
              {tab === 'settings' && (
                <section className="panel">
                  <h2 className="panel__title">
                    <span aria-hidden="true">⚙️</span> {t('account.settings.title')}
                  </h2>
                  <div className="account__settings">
                    <div className="account__setting">
                      <span>{t('account.settings.dark')}</span>
                      <ThemeToggle />
                    </div>
                    <div className="account__setting">
                      <span>{t('account.settings.language')}</span>
                      <LanguageSelect />
                    </div>
                    <div className="account__setting account__setting--doc">
                      <span>{t('account.settings.password')}</span>
                      <ChangePasswordForm />
                    </div>
                    <div className="account__setting">
                      <span>{t('account.settings.logout')}</span>
                      <button
                        type="button"
                        className="btn btn--sm"
                        onClick={() => {
                          session.logout();
                          navigate(ROUTES.home);
                        }}
                      >
                        {t('nav.logout')}
                      </button>
                    </div>
                  </div>
                </section>
              )}
            </div>

            {/* Cột phải chỉ ở Tổng quan — đúng bản thiết kế. Tab "Cấp độ & huy hiệu" đã
                có nguyên hai thẻ này ở cột chính rồi, lặp lại là thừa. */}
            {tab === 'overview' && (
              <aside className="account-aside">
                <LevelCard stats={stats} loading={dangTaiStats} />
                <BadgeGrid stats={stats} loading={dangTaiStats} />
              </aside>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

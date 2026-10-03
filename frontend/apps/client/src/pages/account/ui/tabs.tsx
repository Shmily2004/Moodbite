/**
 * NỘI DUNG TỪNG TAB của trang tài khoản (Hồ sơ, Cấp độ). Tab Yêu thích / Đã xem nằm ở
 * `savedTabs.tsx`, tab Tổng quan ở `OverviewTab.tsx`.
 *
 * Tách khỏi `AccountPage.tsx` để mỗi file giữ đúng một trách nhiệm: file kia lo KHUNG
 * (thanh bên, thẻ đầu trang, chọn tab), file này lo NỘI DUNG. Gộp lại thì một file phải
 * dài hơn 400 dòng và mỗi lần sửa một tab là phải cuộn qua sáu tab khác.
 */
import { ThemeToggle } from '@/features/switch-theme';
import { ChangePasswordForm } from '@/features/change-password';
import {
  IconCompass,
  IconHeart,
  IconMap,
  IconSettings,
  IconShield,
  IconThumbUp,
  LanguageSelect,
} from '@/shared/ui';
import { useT } from '@/shared/i18n';
import type { UserSelf, UserStatsData } from '@/shared/api';
import { LevelCard, BadgeGrid } from '@/widgets/user-progress';

/** "05/2024" từ chuỗi ISO. Sai định dạng thì thà không hiện gì còn hơn hiện "Invalid Date". */
export function thangNam(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
}

// ---------------------------------------------------------------------------
// Hồ sơ cá nhân
// ---------------------------------------------------------------------------

export interface ProfileTabProps {
  user: UserSelf | null;
}

export function ProfileTab({ user }: ProfileTabProps) {
  const t = useT();
  const thamGia = thangNam(user?.created_at);

  const dong = [
    { nhan: t('account.profile.username'), gia_tri: user?.username ?? '—' },
    { nhan: t('account.profile.displayName'), gia_tri: user?.display_name ?? '—' },
    { nhan: t('account.profile.email'), gia_tri: user?.email ?? null },
    { nhan: t('account.profile.joined'), gia_tri: thamGia ?? '—' },
    { nhan: t('account.profile.role'), gia_tri: user?.role ?? '—' },
  ];

  return (
    <section className="panel">
      <h2 className="panel__title">{t('account.profile.title')}</h2>

      <dl className="profile-grid">
        {dong.map((d) => (
          <div key={d.nhan} className="profile-grid__row">
            <dt>{d.nhan}</dt>
            <dd>
              {d.gia_tri ?? (
                <span className="account__line--warn">{t('account.noEmail')}</span>
              )}
            </dd>
          </div>
        ))}
      </dl>

      {/* Nói rõ VÌ SAO chưa sửa được, thay vì để một cái nút bấm không ăn thua. */}
      <p className="section-sub">{t('account.profile.readonly')}</p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Cấp độ & huy hiệu (tab riêng, ngoài cột phải của tab Tổng quan)
// ---------------------------------------------------------------------------

export interface BadgesTabProps {
  stats: UserStatsData | null;
  loading: boolean;
}

export function BadgesTab({ stats, loading }: BadgesTabProps) {
  const t = useT();

  return (
    <>
      <LevelCard stats={stats} loading={loading} />
      <BadgeGrid stats={stats} loading={loading} />
      <section className="panel">
        <h2 className="panel__title">{t('account.level.how')}</h2>
        {/* Bảng điểm KHÔNG viết cứng ở đây — mỗi con số dưới đây phải khớp với
            `domain/services/gamification.py`. Hiện chỉ có 5 dòng nên chép tay chấp nhận
            được; thêm loại điểm mới thì backend nên trả cả bảng điểm xuống. */}
        <ul className="rule-list">
          <li><IconCompass /> {t('points.viewPlace')} — <strong>+2</strong></li>
          <li><IconMap /> {t('points.directions')} — <strong>+3</strong></li>
          <li><IconThumbUp /> {t('points.feedback')} — <strong>+3</strong></li>
          <li><IconHeart /> {t('points.save')} — <strong>+5</strong></li>
          <li><IconShield /> {t('points.report')} — <strong>+10</strong></li>
        </ul>
        <p className="section-sub">
          {t('points.note1')}
          <strong>{t('points.note2')}</strong>
          {t('points.note3')}
        </p>
      </section>
    </>
  );
}

// ---------------------------------------------------------------------------
// Cài đặt (tách khỏi `AccountPage.tsx` 2026-09-16 để file trang chỉ còn lo khung)
// ---------------------------------------------------------------------------

export function SettingsPanel({ onLogout }: { onLogout: () => void }) {
  const t = useT();

  return (
    <section className="panel">
      <h2 className="panel__title">
        <IconSettings /> {t('account.settings.title')}
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
          <button type="button" className="btn btn--sm" onClick={onLogout}>
            {t('nav.logout')}
          </button>
        </div>
      </div>
    </section>
  );
}

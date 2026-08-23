/**
 * Thẻ "HUY HIỆU CỦA BẠN".
 *
 * HIỆN CẢ HUY HIỆU CHƯA ĐẠT, ở dạng mờ kèm tiến độ ("12/20"). Chỉ hiện cái đã đạt thì
 * người mới nhìn vào một ô trống và không biết phải làm gì để có — huy hiệu mất luôn tác
 * dụng khuyến khích, thứ duy nhất khiến nó đáng làm.
 *
 * Danh sách huy hiệu và ngưỡng do BACKEND quyết (`domain/services/gamification.py`).
 * Frontend không có bảng huy hiệu thứ hai — thêm huy hiệu mới chỉ sửa một chỗ.
 */
import { useT } from '@/shared/i18n';
import type { UserStatsData } from '@/shared/api';

export interface BadgeGridProps {
  stats: UserStatsData | null;
  loading?: boolean;
}

export function BadgeGrid({ stats, loading }: BadgeGridProps) {
  const t = useT();

  if (loading || !stats) {
    return (
      <section className="panel">
        <h2 className="panel__title">{t('account.badges.title')}</h2>
        <p className="section-sub">{t('common.loading')}</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2 className="panel__title">{t('account.badges.title')}</h2>

      <ul className="badges">
        {stats.badges.map((hh) => (
          <li
            key={hh.badge_id}
            className={hh.earned ? 'badge badge--on' : 'badge'}
            title={hh.description}
          >
            <span className="badge__icon" aria-hidden="true">
              {hh.emoji}
            </span>
            <span className="badge__name">{hh.name}</span>
            <span className="badge__desc">{hh.description}</span>
            <span className="badge__state">
              {hh.earned
                ? t('account.badges.earned')
                : t('account.badges.progress', { current: hh.current, target: hh.target })}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

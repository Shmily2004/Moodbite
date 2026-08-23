/**
 * Thẻ "CẤP ĐỘ CỦA BẠN" — bên phải trang tài khoản, đúng như bản thiết kế.
 *
 * ⚠️ MỌI SỐ ĐỀU DO SERVER ĐẾM (`GET /me/stats`). Bản thiết kế vẽ "Cấp 2 · 320/500 điểm";
 * đó là hình minh hoạ, KHÔNG phải dữ liệu. Tài khoản mới hiện đúng "Cấp 1 · 0 điểm".
 *
 * Thanh tiến độ tính TRONG khoảng giữa hai cấp, không phải trên tổng điểm tối đa — nếu
 * không, người ở cấp 2 sẽ nhìn thấy một thanh gần như trống suốt nhiều tuần. Công thức ở
 * `domain/services/gamification.py`, frontend chỉ vẽ lại con số server gửi xuống.
 */
import { useT } from '@/shared/i18n';
import type { UserStatsData } from '@/shared/api';

export interface LevelCardProps {
  stats: UserStatsData | null;
  loading?: boolean;
}

export function LevelCard({ stats, loading }: LevelCardProps) {
  const t = useT();

  if (loading || !stats) {
    return (
      <section className="panel">
        <h2 className="panel__title">{t('account.level.title')}</h2>
        <p className="section-sub">{t('common.loading')}</p>
      </section>
    );
  }

  const cap = stats.level;
  const phan_tram = Math.round((cap.ratio ?? 0) * 100);

  return (
    <section className="panel">
      <h2 className="panel__title">{t('account.level.title')}</h2>

      <div className="level">
        {/* Ngôi sao là hình trang trí; số cấp mới là thông tin, nên nó nằm ở chữ. */}
        <div className="level__badge" aria-hidden="true">
          ⭐
        </div>
        <div className="level__body">
          <p className="level__name">{cap.current.name}</p>
          <p className="level__rank">{t('account.level.level', { n: cap.current.number })}</p>

          <div
            className="level__bar"
            role="progressbar"
            aria-valuenow={phan_tram}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={t('account.level.title')}
          >
            <span className="level__fill" style={{ width: `${phan_tram}%` }} />
          </div>

          {cap.next ? (
            <>
              <p className="level__points">
                {t('account.level.points', {
                  points: cap.points,
                  next: cap.next.min_points,
                })}
              </p>
              <p className="level__hint">
                {t('account.level.toNext', {
                  n: cap.points_to_next ?? 0,
                  level: cap.next.number,
                })}
              </p>
            </>
          ) : (
            <p className="level__points">{t('account.level.max')}</p>
          )}
        </div>
      </div>
    </section>
  );
}

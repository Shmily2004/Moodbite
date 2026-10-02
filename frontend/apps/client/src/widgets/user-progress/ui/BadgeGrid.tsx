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
  /**
   * Chỉ hiện tối đa N huy hiệu trên MỘT HÀNG (thẻ ở tab Tổng quan, 2026-10-02 theo
   * `design/profile.png`). Bỏ trống = hiện hết dạng lưới (tab "Cấp độ & huy hiệu").
   * Lưới 2×3 ở cột phải từng kéo thẻ cao ~600px, đẩy "Khẩu vị" khỏi màn hình.
   */
  limit?: number;
  /** Có thì hiện "Xem tất cả →" ở đầu thẻ (chuyển sang tab huy hiệu). */
  onSeeAll?: () => void;
}

export function BadgeGrid({ stats, loading, limit, onSeeAll }: BadgeGridProps) {
  const t = useT();

  if (loading || !stats) {
    return (
      <section className="panel">
        <h2 className="panel__title">{t('account.badges.title')}</h2>
        <p className="section-sub">{t('common.loading')}</p>
      </section>
    );
  }

  // Bản rút gọn: huy hiệu ĐÃ ĐẠT lên trước (đó là thứ người dùng muốn khoe), phần còn
  // lại giữ nguyên thứ tự backend. Chỉ đổi THỨ TỰ HIỂN THỊ, không lọc bỏ cái nào — tab
  // đầy đủ vẫn có hết.
  const ds =
    limit != null
      ? [...stats.badges]
          .sort((a, b) => Number(b.earned) - Number(a.earned))
          .slice(0, limit)
      : stats.badges;
  const gon = limit != null;

  return (
    <section className="panel">
      <div className="results__head">
        <h2 className="panel__title">{t('account.badges.title')}</h2>
        {onSeeAll && (
          <button type="button" className="linkish" onClick={onSeeAll}>
            {t('common.viewAll')} →
          </button>
        )}
      </div>

      <ul className={gon ? 'badges badges--hang' : 'badges'}>
        {ds.map((hh) => (
          <li
            key={hh.badge_id}
            className={hh.earned ? 'badge badge--on' : 'badge'}
            title={hh.description}
          >
            <span className="badge__icon" aria-hidden="true">
              {hh.emoji}
            </span>
            <span className="badge__name">{hh.name}</span>
            {/* Bản một hàng: ô chỉ rộng ~70px, mô tả dài sẽ xuống 4 dòng -> để ở `title`. */}
            {!gon && <span className="badge__desc">{hh.description}</span>}
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

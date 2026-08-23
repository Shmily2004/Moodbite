/**
 * Bốn ô số liệu ở đầu trang tài khoản: Món đã lưu · Quán yêu thích · Món đã xem ·
 * Lượt khám phá — đúng bốn ô như bản thiết kế.
 *
 * ⚠️ CẢ BỐN ĐỀU LÀ SỐ ĐẾM THẬT, không có ô nào là số minh hoạ:
 *   Món đã lưu / Quán yêu thích -> bảng `saved_items` ở server
 *   Món đã xem                  -> lịch sử trên MÁY NÀY (localStorage), nên chú thích rõ
 *   Lượt khám phá               -> số QUÁN KHÁC NHAU đã mở xem đủ lâu, server đếm
 *
 * Bản thiết kế ghi ô thứ tư là "Bộ sưu tập"; tính năng đó chưa tồn tại nên ô này đổi
 * thành "Lượt khám phá" — thứ chủ dự án đã chốt làm và ta đếm được thật.
 */
import { useT } from '@/shared/i18n';
import type { UserStatsData } from '@/shared/api';

export interface StatTilesProps {
  stats: UserStatsData | null;
  /** Số món đã xem — đọc từ localStorage nên do trang truyền vào, không lấy từ server. */
  viewedLocal: number;
}

export function StatTiles({ stats, viewedLocal }: StatTilesProps) {
  const t = useT();

  const o = [
    { icon: '🍽️', value: stats?.saved_dishes ?? 0, label: t('account.stat.savedDishes') },
    { icon: '❤️', value: stats?.saved_restaurants ?? 0, label: t('account.stat.savedRestaurants') },
    { icon: '🕘', value: viewedLocal, label: t('account.stat.viewed') },
    { icon: '🧭', value: stats?.explorations ?? 0, label: t('account.stat.explorations') },
  ];

  return (
    <ul className="stat-tiles">
      {o.map((muc) => (
        <li key={muc.label} className="stat">
          <span className="stat__icon" aria-hidden="true">
            {muc.icon}
          </span>
          <span className="stat__value">{muc.value}</span>
          <span className="stat__label">{muc.label}</span>
        </li>
      ))}
    </ul>
  );
}

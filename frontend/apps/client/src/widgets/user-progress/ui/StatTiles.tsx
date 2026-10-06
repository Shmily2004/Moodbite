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
import { IconClock, IconCompass, IconDining, IconHeart } from '@/shared/ui';

export interface StatTilesProps {
  stats: UserStatsData | null;
  /** Số món đã xem — đọc từ localStorage nên do trang truyền vào, không lấy từ server. */
  viewedLocal: number;
  /** `/me/stats` đang tải — ô số liệu server hiện "…", KHÔNG hiện 0. */
  loading?: boolean;
  /** `/me/stats` lỗi — ô số liệu server hiện "—" kèm câu báo + nút thử lại. */
  error?: string | null;
  onRetry?: () => void;
}

/**
 * Giá trị của một ô số liệu SERVER.
 *
 * ⚠️ `None ≠ 0` (CLAUDE.md mục 4): trước 2026-10-06 ô dùng `?? 0`, nên lúc đang tải hay
 * tải lỗi người dùng thấy "0 món đã lưu" — tưởng mình vừa mất hết dữ liệu. Chưa có số thì
 * hiện "…" (đang tải) hoặc "—" (không tải được), kèm nhãn cho trình đọc màn hình.
 */
function giaTriServer(
  value: number | undefined,
  loading: boolean,
): { text: string; trangThai: 'co' | 'dang-tai' | 'chua-co' } {
  if (value !== undefined && value !== null) return { text: String(value), trangThai: 'co' };
  if (loading) return { text: '…', trangThai: 'dang-tai' };
  return { text: '—', trangThai: 'chua-co' };
}

export function StatTiles({
  stats,
  viewedLocal,
  loading = false,
  error = null,
  onRetry,
}: StatTilesProps) {
  const t = useT();

  // Icon SVG thay emoji (2026-09-29, checklist A9) — cùng hình với tab tương ứng ở thanh
  // bên trang tài khoản (dao dĩa · tim · đồng hồ), để một khái niệm chỉ có một hình.
  const o = [
    { icon: <IconDining />, ...giaTriServer(stats?.saved_dishes, loading), label: t('account.stat.savedDishes') },
    { icon: <IconHeart />, ...giaTriServer(stats?.saved_restaurants, loading), label: t('account.stat.savedRestaurants') },
    { icon: <IconClock />, text: String(viewedLocal), trangThai: 'co' as const, label: t('account.stat.viewed') },
    { icon: <IconCompass />, ...giaTriServer(stats?.explorations, loading), label: t('account.stat.explorations') },
  ];

  return (
    <div className="stat-tiles-wrap">
      <ul className="stat-tiles" aria-busy={loading || undefined}>
        {o.map((muc) => (
          <li key={muc.label} className="stat">
            <span className="stat__icon" aria-hidden="true">
              {muc.icon}
            </span>
            <span
              className="stat__value"
              aria-label={
                muc.trangThai === 'dang-tai'
                  ? t('account.stat.loading')
                  : muc.trangThai === 'chua-co'
                    ? t('account.stat.unavailable')
                    : undefined
              }
            >
              {muc.text}
            </span>
            <span className="stat__label">{muc.label}</span>
          </li>
        ))}
      </ul>
      {error && !loading && (
        <p className="notice notice--warn small stat-tiles__loi" role="status">
          {error}{' '}
          {onRetry && (
            <button type="button" className="btn btn--link" onClick={onRetry}>
              {t('account.stat.retry')}
            </button>
          )}
        </p>
      )}
    </div>
  );
}

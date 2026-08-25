/**
 * KHỐI "DÀNH RIÊNG CHO BẠN" — món và quán người dùng đã bấm trái tim.
 *
 * Chủ dự án chốt 2026-08-25: "phần dành riêng cho bạn với quán và món đã lưu là phải có".
 * Trước đó danh sách yêu thích CHỈ nằm trong tab `?tab=saved` của trang tài khoản — tức
 * là người dùng phải chủ động đi tìm mới thấy thứ chính họ đã lưu.
 *
 * ⚠️ CHỈ HIỆN KHI ĐÃ CÓ GÌ ĐÓ. Một khối rỗng với dòng "chưa lưu gì" nằm giữa trang chủ
 * chỉ làm trang dài thêm mà không nói được gì — người chưa lưu bao giờ thì cũng chưa cần
 * tới nó. Trang tài khoản mới là chỗ đúng để hiện trạng thái rỗng, vì ở đó người dùng
 * ĐANG đi tìm nó.
 *
 * KHÔNG gọi API: nhận sẵn `favorites` từ trang. Trang chủ vốn đã dựng `useFavorites` để
 * biết trái tim nào đang bật, dựng thêm một hook nữa là gọi mạng hai lần cho cùng dữ liệu.
 */
import { Link } from 'react-router-dom';
import type { UseFavoritesResult } from '@/features/save-favorite';
import { ROUTES } from '@/shared/config';
import { useT } from '@/shared/i18n';

export interface ForYouProps {
  favorites: UseFavoritesResult;
  /** Số mục hiện tối đa cho mỗi nhóm. Còn lại xem ở trang tài khoản. */
  gioiHan?: number;
}

export function ForYou({ favorites, gioiHan = 6 }: ForYouProps) {
  const t = useT();

  const mon = favorites.dishes.slice(0, gioiHan);
  const quan = favorites.restaurants.slice(0, gioiHan);
  if (mon.length === 0 && quan.length === 0) return null;

  return (
    <section className="for-you">
      <div className="results__head">
        <h2 className="section-title">{t('forYou.title')}</h2>
        <Link className="linkish" to={`${ROUTES.account}?tab=saved`}>
          {t('forYou.seeAll')} →
        </Link>
      </div>
      <p className="section-sub">{t('forYou.sub')}</p>

      {mon.length > 0 && (
        <div className="for-you__nhom">
          <p className="for-you__nhan">{t('forYou.dishes')}</p>
          <ul className="for-you__list">
            {mon.map((muc) => (
              <li key={muc.itemId}>
                <Link className="chip" to={ROUTES.dish.replace(':dishId', muc.itemId)}>
                  {muc.name}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {quan.length > 0 && (
        <div className="for-you__nhom">
          <p className="for-you__nhan">{t('forYou.places')}</p>
          <ul className="for-you__list">
            {quan.map((muc) => (
              <li key={muc.itemId}>
                {/* Quán CHƯA có trang riêng — panel chi tiết nằm trong trang bản đồ.
                    Link chết chỉ để "cho đủ" thì tệ hơn là không có link. */}
                <span className="chip chip--flat">{muc.name}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

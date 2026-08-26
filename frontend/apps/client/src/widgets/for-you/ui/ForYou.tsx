/**
 * KHỐI "DÀNH RIÊNG CHO BẠN" — hai danh sách người dùng tự tạo.
 *
 *   ♥  Món yêu thích  (trái tim)   — món tôi THÍCH
 *   🔖 Đã lưu         (dấu trang)  — món/quán tôi ĐỊNH ĂN, để dành xem sau
 *
 * Chủ dự án chốt 2026-08-25: "phần dành riêng cho bạn với quán và món đã lưu là phải có".
 * Rồi 2026-08-26 chốt tiếp: hai thứ đó là HAI DANH SÁCH TÁCH BẠCH, không phải một.
 * Trước đó danh sách yêu thích CHỈ nằm trong tab `?tab=saved` của trang tài khoản — tức
 * là người dùng phải chủ động đi tìm mới thấy thứ chính họ đã lưu.
 *
 * ⚠️ CHỈ HIỆN NHÓM NÀO CÓ NỘI DUNG. Một khối rỗng với dòng "chưa lưu gì" nằm giữa trang
 * chủ chỉ làm trang dài thêm mà không nói được gì — người chưa lưu bao giờ thì cũng chưa
 * cần tới nó. Trang tài khoản mới là chỗ đúng để hiện trạng thái rỗng, vì ở đó người dùng
 * ĐANG đi tìm nó.
 *
 * KHÔNG gọi API: nhận sẵn `favorites` từ trang. Trang vốn đã dựng `useFavorites` để biết
 * nút nào đang bật, dựng thêm một hook nữa là gọi mạng hai lần cho cùng dữ liệu.
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import type { MucYeuThich, NhomDaLuu, UseFavoritesResult } from '@/features/save-favorite';
import { ROUTES } from '@/shared/config';
import { IconBookmark, IconHeart } from '@/shared/ui';
import { useT } from '@/shared/i18n';

export interface ForYouProps {
  favorites: UseFavoritesResult;
  /** Số mục hiện tối đa cho mỗi nhóm. Còn lại xem ở trang tài khoản. */
  gioiHan?: number;
}

export function ForYou({ favorites, gioiHan = 6 }: ForYouProps) {
  const t = useT();

  const coGi = (nhom: NhomDaLuu) => nhom.items.length > 0;
  if (!coGi(favorites.favorite) && !coGi(favorites.bookmark)) return null;

  return (
    <section className="for-you">
      <div className="results__head">
        <h2 className="section-title">{t('forYou.title')}</h2>
        <Link className="linkish" to={`${ROUTES.account}?tab=saved`}>
          {t('forYou.seeAll')} →
        </Link>
      </div>
      <p className="section-sub">{t('forYou.sub')}</p>

      <DanhSach
        nhan={t('forYou.favorites')}
        icon={<IconHeart filled />}
        nhom={favorites.favorite}
        gioiHan={gioiHan}
      />
      <DanhSach
        nhan={t('forYou.bookmarks')}
        icon={<IconBookmark filled />}
        nhom={favorites.bookmark}
        gioiHan={gioiHan}
      />
    </section>
  );
}

/** Một danh sách (yêu thích HOẶC đã lưu), tách tiếp thành món và quán. */
function DanhSach({
  nhan,
  icon,
  nhom,
  gioiHan,
}: {
  nhan: string;
  icon: ReactNode;
  nhom: NhomDaLuu;
  gioiHan: number;
}) {
  // Gọi `useT()` tại chỗ thay vì nhận `t` qua prop: kiểu `HamDich` chỉ chấp nhận những
  // khoá CÓ THẬT trong từ điển, khai lại chữ ký bằng `string` là vứt mất chốt chặn đó.
  const t = useT();
  const mon = nhom.dishes.slice(0, gioiHan);
  const quan = nhom.restaurants.slice(0, gioiHan);
  if (mon.length === 0 && quan.length === 0) return null;

  return (
    <div className="for-you__danh-sach">
      <p className="for-you__ten-danh-sach">
        {icon} {nhan}
      </p>

      {mon.length > 0 && (
        <div className="for-you__nhom">
          <p className="for-you__nhan">{t('forYou.dishes')}</p>
          <ul className="for-you__list">
            {mon.map((muc: MucYeuThich) => (
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
            {quan.map((muc: MucYeuThich) => (
              <li key={muc.itemId}>
                {/* Quán CHƯA có trang riêng — panel chi tiết nằm trong trang bản đồ.
                    Link chết chỉ để "cho đủ" thì tệ hơn là không có link. */}
                <span className="chip chip--flat">{muc.name}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

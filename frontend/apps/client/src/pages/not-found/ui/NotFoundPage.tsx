/**
 * Trang 404. Nói rõ đường dẫn sai và đưa người dùng về chỗ dùng được.
 *
 * Dựng trong khung `.page` + `SiteHeader` như mọi trang khác (2026-10-28). Bản cũ là một
 * khối chữ trơn trên nền xám, không có thanh trên - người lạc vào đây mất luôn lối đi
 * sang các mục khác, và trang trông như thuộc một ứng dụng khác.
 */
import { Link } from 'react-router-dom';
import { SiteHeader } from '@/widgets/site-header';
import { ROUTES } from '@/shared/config';
import { useT } from '@/shared/i18n';

export function NotFoundPage() {
  const t = useT();
  return (
    <div className="page">
      <SiteHeader />
      <main className="dish-page">
        <div className="state state--404">
          <p className="state__title">{t('notFound.title')}</p>
          <p className="muted">{t('notFound.hint')}</p>
          {/* Về TRANG CHỦ (luồng chính "chọn món trước"), không về `/search` như bản cũ. */}
          <Link className="btn btn--primary" to={ROUTES.home}>
            {t('notFound.back')}
          </Link>
        </div>
      </main>
    </div>
  );
}

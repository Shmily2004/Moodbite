/** Trang 404. Nói rõ đường dẫn sai và đưa người dùng về chỗ dùng được. */
import { Link } from 'react-router-dom';
import { useT } from '@/shared/i18n';

export function NotFoundPage() {
  const t = useT();
  return (
    <div className="plain">
      <h2>{t('notFound.title')}</h2>
      <p className="muted">
        {t('notFound.hint')}
      </p>
      <p>
        <Link to="/">{t('notFound.back')}</Link>
      </p>
    </div>
  );
}

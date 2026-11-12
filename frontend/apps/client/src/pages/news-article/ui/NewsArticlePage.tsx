/**
 * TRANG MỘT BÀI VIẾT — `/tin-tuc/:slug` (UC14, bước "Chọn một bài" -> "Đọc bài").
 *
 * Bài nháp và bài không tồn tại đều hiện cùng một câu (backend trả 404 cho cả hai).
 */
import { Link, useParams } from 'react-router-dom';
import { SiteHeader } from '@/widgets/site-header';
import { NewsArticleView, useNewsArticle } from '@/entities/post';
import { ROUTES } from '@/shared/config';
import { useT } from '@/shared/i18n';

export function NewsArticlePage() {
  const t = useT();
  const { slug = '' } = useParams<{ slug: string }>();
  const { post, loading, notFound, error } = useNewsArticle(slug);

  return (
    <div className="page">
      <SiteHeader />
      <main className="dish-page news-page">
        <Link className="news-back" to={ROUTES.news}>
          {t('news.back')}
        </Link>

        {loading && <p className="muted">{t('news.loading')}</p>}
        {!loading && notFound && (
          <div className="state">
            <p className="state__title">{t('news.notFound')}</p>
          </div>
        )}
        {!loading && !notFound && error && (
          <div className="state">
            <p className="state__title">{t('news.error')}</p>
          </div>
        )}
        {!loading && post && <NewsArticleView post={post} />}
      </main>
    </div>
  );
}

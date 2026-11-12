/**
 * TRANG TIN TỨC — `/tin-tuc` (UC14 trong `docs/bieu_do_uml`).
 *
 * Yêu cầu đăng nhập: route nằm trong nhóm `RequireLogin` ở `app/routes.tsx`, đúng luồng biểu
 * đồ ("chưa đăng nhập -> chuyển tới trang đăng nhập").
 */
import { SiteHeader } from '@/widgets/site-header';
import { NewsList, useNewsList } from '@/entities/post';
import { useT } from '@/shared/i18n';

export function NewsPage() {
  const t = useT();
  const { posts, loading, error } = useNewsList();

  return (
    <div className="page">
      <SiteHeader />
      <main className="dish-page news-page">
        <header className="news-hero">
          <p className="news-hero__eyebrow">{t('nav.news')}</p>
          <h1 className="news-hero__title">{t('news.title')}</h1>
          <p className="news-hero__intro">{t('news.intro')}</p>
        </header>

        {loading && <p className="muted">{t('news.loading')}</p>}
        {!loading && error && (
          <div className="state">
            <p className="state__title">{t('news.error')}</p>
          </div>
        )}
        {!loading && !error && posts.length === 0 && (
          <div className="state">
            <p className="state__title">{t('news.empty')}</p>
          </div>
        )}
        {!loading && !error && posts.length > 0 && <NewsList posts={posts} />}
      </main>
    </div>
  );
}

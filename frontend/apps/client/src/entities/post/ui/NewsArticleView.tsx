/**
 * VIEW một bài viết — chỉ JSX.
 *
 * Nội dung được tách đoạn theo dòng trống và đưa vào `<p>` như CHỮ. Không render HTML từ
 * dữ liệu: thẻ trong nội dung hiện nguyên văn (xem test).
 *
 * Nguồn (`source_name`/`source_url`) hiện CÙNG bài, kể cả bài admin tự viết. Nội dung từ
 * web phải ghi nguồn (CLAUDE.md mục 4b); với bài admin thì trường này có thể trống.
 */
import type { PostPublic } from '@/shared/api';
import { useT } from '@/shared/i18n';
import { dinhDangNgay } from './NewsList';

export interface NewsArticleViewProps {
  post: PostPublic;
}

/** Tách đoạn theo dòng trống. Bỏ đoạn rỗng để không sinh `<p>` trống. */
export function tachDoan(noiDung: string): string[] {
  return noiDung
    .split(/\n\s*\n/)
    .map((d) => d.trim())
    .filter((d) => d.length > 0);
}

export function NewsArticleView({ post }: NewsArticleViewProps) {
  const t = useT();
  const ngay = dinhDangNgay(post.last_updated ?? post.published_at);
  const doan = tachDoan(post.body);

  return (
    <article className="news-article">
      {post.image_url && (
        <figure className="news-article__figure">
          <img className="news-article__img" src={post.image_url} alt="" />
          {post.image_credit && (
            <figcaption className="news-article__credit">
              {t('news.photo')}: {post.image_credit}
            </figcaption>
          )}
        </figure>
      )}

      <header className="news-article__head">
        {ngay && (
          <p className="news-article__date">
            {t('news.updated')}: {ngay}
          </p>
        )}
        <h1 className="news-article__title">{post.title}</h1>
        {post.summary && <p className="news-article__lead">{post.summary}</p>}
      </header>

      <div className="news-article__body">
        {doan.map((d, i) => (
          // pre-line: giữ xuống dòng đơn bên trong một đoạn.
          <p key={i} style={{ whiteSpace: 'pre-line' }}>
            {d}
          </p>
        ))}
      </div>

      {post.source_name && (
        <footer className="news-article__source">
          {t('news.source')}:{' '}
          {post.source_url ? (
            <a href={post.source_url} target="_blank" rel="noopener noreferrer">
              {post.source_name}
            </a>
          ) : (
            post.source_name
          )}
        </footer>
      )}
    </article>
  );
}

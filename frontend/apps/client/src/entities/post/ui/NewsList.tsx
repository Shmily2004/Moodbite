/**
 * VIEW danh sách tin tức — chỉ JSX, không gọi API (xem CLAUDE.md mục 1b).
 *
 * Bài chưa có ảnh (đa số, vì dữ liệu bài là chữ) nên ô bìa là một khối màu có chữ cái đầu
 * của tiêu đề — CHỦ ĐÍCH, giống cách `.thumb--generated` xử lý quán chưa có ảnh.
 */
import { Link } from 'react-router-dom';
import type { PostPublic } from '@/shared/api';
import { newsArticleRoute } from '@/shared/config';
import { useT } from '@/shared/i18n';

export interface NewsListProps {
  posts: PostPublic[];
}

/** Hiển thị ngày theo quy ước giao diện (định dạng là chuyện của frontend, không phải nghiệp vụ). */
export function dinhDangNgay(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('vi-VN');
}

/** Chữ cái đầu của tiêu đề, làm nhãn cho ô bìa. Tiêu đề rỗng thì dùng dấu chấm. */
function chuDau(tieuDe: string): string {
  const ky = tieuDe.trim().charAt(0);
  return ky ? ky.toUpperCase() : '•';
}

export function NewsList({ posts }: NewsListProps) {
  const t = useT();
  return (
    <ul className="news-grid">
      {posts.map((bai) => (
        <li key={bai.post_id} className="news-card">
          <Link to={newsArticleRoute(bai.slug)} className="news-card__link">
            <span className="news-card__cover" aria-hidden="true">
              {bai.image_url ? (
                // Ảnh trang trí: tiêu đề đã nằm ngay bên dưới nên alt để rỗng.
                <img className="news-card__img" src={bai.image_url} alt="" loading="lazy" />
              ) : (
                <span className="news-card__initial">{chuDau(bai.title)}</span>
              )}
            </span>
            <span className="news-card__body">
              <span className="news-card__date">
                {dinhDangNgay(bai.published_at) || t('news.updated')}
              </span>
              <span className="news-card__title">{bai.title}</span>
              {bai.summary && <span className="news-card__summary">{bai.summary}</span>}
              <span className="news-card__more">{t('news.readMore')}</span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

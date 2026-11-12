/**
 * VIEWMODEL một bài viết (UC14, bước "Tải nội dung bài").
 *
 * `notFound` tách riêng khỏi `error`: bài nháp hoặc không tồn tại đều trả 404 từ backend
 * (cố ý không phân biệt, xem `PostNotFoundError`) — giao diện hiện cùng một câu cho cả hai.
 */
import { useEffect, useState } from 'react';
import { api, ApiError } from '@/shared/api';
import type { PostPublic } from '@/shared/api';

export interface UseNewsArticleResult {
  post: PostPublic | null;
  loading: boolean;
  notFound: boolean;
  error: string | null;
}

export function useNewsArticle(slug: string): UseNewsArticleResult {
  const [post, setPost] = useState<PostPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let conSong = true;
    setLoading(true);
    setNotFound(false);
    setError(null);
    api
      .getPost(slug)
      .then((kq) => {
        if (!conSong) return;
        setPost(kq.post);
      })
      .catch((err: unknown) => {
        if (!conSong) return;
        setPost(null);
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true);
        } else {
          setError(err instanceof ApiError ? err.message : (err as Error).message);
        }
      })
      .finally(() => {
        if (conSong) setLoading(false);
      });
    return () => {
      conSong = false;
    };
  }, [slug]);

  return { post, loading, notFound, error };
}

/**
 * VIEWMODEL danh sách tin tức (UC14 "Xem tin tức", bước "Tải bài đã công khai").
 *
 * Chỉ ĐIỀU PHỐI gọi API. Backend đã lọc nháp ở `GET /posts`; frontend KHÔNG lọc lại theo
 * `status` — làm vậy là hai nơi cùng quyết định "bài nào được hiện".
 */
import { useEffect, useState } from 'react';
import { api, ApiError } from '@/shared/api';
import type { PostPublic } from '@/shared/api';

export interface UseNewsListResult {
  posts: PostPublic[];
  loading: boolean;
  /** Chuỗi lỗi kỹ thuật. Trang tự chọn câu hiển thị cho người dùng. */
  error: string | null;
}

export function useNewsList(): UseNewsListResult {
  const [posts, setPosts] = useState<PostPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let conSong = true;
    api
      .listPosts()
      .then((kq) => {
        if (!conSong) return;
        setPosts(kq.posts);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!conSong) return;
        setError(err instanceof ApiError ? err.message : (err as Error).message);
      })
      .finally(() => {
        if (conSong) setLoading(false);
      });
    return () => {
      conSong = false;
    };
  }, []);

  return { posts, loading, error };
}

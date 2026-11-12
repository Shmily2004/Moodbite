/**
 * VIEWMODEL quản lý bài viết (UC23 "Quản lý bài viết" trong `docs/bieu_do_uml`).
 *
 * Chỉ ĐIỀU PHỐI gọi API và giữ trạng thái màn hình. Luật "bài nào được công khai", "tiêu
 * đề bao nhiêu ký tự" do backend quyết (`domain/entities/post.py`); frontend chỉ hiện câu
 * lỗi backend trả về.
 */
import { useCallback, useEffect, useState } from 'react';
import { adminApi, ApiError } from '@admin/shared/api';
import type { PostPublic, PostStatus, PostWriteRequest } from '@admin/shared/api';

export type BoLocBaiViet = 'all' | PostStatus;

export interface UsePostsResult {
  posts: PostPublic[];
  filter: BoLocBaiViet;
  setFilter: (f: BoLocBaiViet) => void;
  loading: boolean;
  /** Lỗi tải danh sách. */
  error: string | null;
  /** Lỗi của thao tác lưu/xoá gần nhất. Tách riêng để không che danh sách. */
  actionError: string | null;
  reload: () => void;
  save: (postId: string | null, body: PostWriteRequest) => Promise<PostPublic | null>;
  remove: (postId: string) => Promise<boolean>;
}

function thongBao(err: unknown): string {
  return err instanceof ApiError ? err.message : (err as Error).message;
}

export function usePosts(): UsePostsResult {
  const [posts, setPosts] = useState<PostPublic[]>([]);
  const [filter, setFilter] = useState<BoLocBaiViet>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [lan, setLan] = useState(0);

  useEffect(() => {
    let conSong = true;
    setLoading(true);
    adminApi
      .listPosts(filter === 'all' ? undefined : filter)
      .then((kq) => {
        if (!conSong) return;
        setPosts(kq.posts);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!conSong) return;
        setError(thongBao(err));
      })
      .finally(() => {
        if (conSong) setLoading(false);
      });
    return () => {
      conSong = false;
    };
  }, [filter, lan]);

  const reload = useCallback(() => setLan((n) => n + 1), []);

  const save = useCallback(
    async (postId: string | null, body: PostWriteRequest) => {
      setActionError(null);
      try {
        const kq = postId
          ? await adminApi.updatePost(postId, body)
          : await adminApi.createPost(body);
        reload();
        return kq.post;
      } catch (err) {
        setActionError(thongBao(err));
        return null;
      }
    },
    [reload],
  );

  const remove = useCallback(
    async (postId: string) => {
      setActionError(null);
      try {
        await adminApi.deletePost(postId);
        reload();
        return true;
      } catch (err) {
        setActionError(thongBao(err));
        return false;
      }
    },
    [reload],
  );

  return { posts, filter, setFilter, loading, error, actionError, reload, save, remove };
}

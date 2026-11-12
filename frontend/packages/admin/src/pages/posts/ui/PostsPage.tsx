/**
 * TRANG QUẢN LÝ BÀI VIẾT — `/quan-tri/bai-viet` (UC23 trong `docs/bieu_do_uml`).
 *
 * Luồng theo biểu đồ: soạn / sửa / xoá bài -> backend ghi bài và ghi nhật ký -> bài công
 * khai hiện trên trang tin tức của khách, bài nháp chỉ quản trị thấy.
 */
import { useState } from 'react';
import { PostEditor, usePosts } from '@admin/features/manage-posts';
import type { BoLocBaiViet } from '@admin/features/manage-posts';
import type { PostPublic, PostWriteRequest } from '@admin/shared/api';

const BO_LOC: { khoa: BoLocBaiViet; nhan: string }[] = [
  { khoa: 'all', nhan: 'Tất cả' },
  { khoa: 'published', nhan: 'Công khai' },
  { khoa: 'draft', nhan: 'Nháp' },
];

/** `null` = không mở editor; `'new'` = đang soạn bài mới; còn lại là đang sửa bài đó. */
type DangSua = null | 'new' | PostPublic;

export function PostsPage() {
  const { posts, filter, setFilter, loading, error, actionError, save, remove } = usePosts();
  const [dang, setDang] = useState<DangSua>(null);
  const [dangLuu, setDangLuu] = useState(false);

  const luu = async (body: PostWriteRequest) => {
    const postId = dang && dang !== 'new' ? dang.post_id : null;
    setDangLuu(true);
    const kq = await save(postId, body);
    setDangLuu(false);
    if (kq) setDang(null);
  };

  const xoa = async () => {
    if (!dang || dang === 'new') return;
    if (!window.confirm(`Xoá bài "${dang.title}"? Việc này không hoàn tác được.`)) return;
    setDangLuu(true);
    const ok = await remove(dang.post_id);
    setDangLuu(false);
    if (ok) setDang(null);
  };

  return (
    <section className="panel">
      <div className="bang__dau">
        <h2 className="panel__tieu-de">Quản lý bài viết</h2>
        <button type="button" onClick={() => setDang('new')}>
          + Bài viết mới
        </button>
      </div>
      <p className="muted">
        Bài <strong>công khai</strong> hiện trên trang tin tức của khách. Bài <strong>nháp</strong>{' '}
        chỉ quản trị thấy. Mọi thao tác đều được ghi vào nhật ký hoạt động.
      </p>

      <div className="chip-hang" role="group" aria-label="Lọc theo trạng thái">
        {BO_LOC.map((l) => (
          <button
            key={l.khoa}
            type="button"
            className={filter === l.khoa ? 'chip chip--dang' : 'chip'}
            aria-pressed={filter === l.khoa}
            onClick={() => setFilter(l.khoa)}
          >
            {l.nhan}
          </button>
        ))}
      </div>

      {error && <p className="notice notice--warn">{error}</p>}

      {dang !== null && (
        <PostEditor
          key={dang === 'new' ? 'new' : dang.post_id}
          post={dang === 'new' ? null : dang}
          onSave={luu}
          onDelete={dang === 'new' ? undefined : xoa}
          onCancel={() => setDang(null)}
          saving={dangLuu}
          actionError={actionError}
        />
      )}

      {loading && <p className="muted">Đang tải…</p>}
      {!loading && !error && posts.length === 0 && (
        <p className="muted">Chưa có bài viết nào.</p>
      )}

      {!loading && posts.length > 0 && (
        <table className="bang">
          <thead>
            <tr>
              <th>Tiêu đề</th>
              <th>Trạng thái</th>
              <th>Cập nhật</th>
            </tr>
          </thead>
          <tbody>
            {posts.map((bai) => (
              <tr key={bai.post_id} onClick={() => setDang(bai)} style={{ cursor: 'pointer' }}>
                <td>{bai.title}</td>
                <td>{bai.status === 'published' ? 'Công khai' : 'Nháp'}</td>
                <td>{bai.updated_at ? bai.updated_at.slice(0, 10) : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

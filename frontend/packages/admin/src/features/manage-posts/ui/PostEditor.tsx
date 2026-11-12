/**
 * VIEW form soạn/sửa bài — chỉ JSX và state của ô nhập. Không gọi API: việc lưu do
 * `usePosts` (viewmodel) làm, nhận qua `onSave`.
 */
import { useState } from 'react';
import type { FormEvent } from 'react';
import type { PostPublic, PostStatus, PostWriteRequest } from '@admin/shared/api';

export interface PostEditorProps {
  /** null = tạo bài mới. */
  post: PostPublic | null;
  onSave: (body: PostWriteRequest) => void;
  onDelete?: () => void;
  onCancel: () => void;
  saving: boolean;
  actionError: string | null;
}

export function PostEditor({
  post,
  onSave,
  onDelete,
  onCancel,
  saving,
  actionError,
}: PostEditorProps) {
  const [title, setTitle] = useState(post?.title ?? '');
  const [summary, setSummary] = useState(post?.summary ?? '');
  const [body, setBody] = useState(post?.body ?? '');
  const [status, setStatus] = useState<PostStatus>(post?.status ?? 'draft');
  const [lastUpdated, setLastUpdated] = useState(post?.last_updated ?? '');
  const [imageUrl, setImageUrl] = useState(post?.image_url ?? '');
  const [imageCredit, setImageCredit] = useState(post?.image_credit ?? '');

  const submit = (e: FormEvent) => {
    e.preventDefault();
    // Nguồn (source_*) giữ nguyên giá trị cũ: form này không sửa nguồn, và bài admin tự
    // viết thì nguồn vốn trống. Gửi lại đúng giá trị để không làm mất dữ liệu khi sửa.
    onSave({
      title,
      summary,
      body,
      status,
      source_name: post?.source_name ?? null,
      source_url: post?.source_url ?? null,
      last_updated: lastUpdated || null,
      // Ảnh từ mạng (https) BẮT BUỘC có nguồn — backend kiểm, form chỉ gửi đúng cái người nhập.
      image_url: imageUrl.trim() || null,
      image_credit: imageCredit.trim() || null,
    });
  };

  return (
    <form className="panel" onSubmit={submit}>
      <h3 className="panel__tieu-de">{post ? 'Sửa bài viết' : 'Bài viết mới'}</h3>

      <label>
        Tiêu đề
        <input value={title} onChange={(e) => setTitle(e.target.value)} required />
      </label>
      <label>
        Tóm tắt
        <input value={summary} onChange={(e) => setSummary(e.target.value)} />
      </label>
      <label>
        Nội dung
        <textarea rows={12} value={body} onChange={(e) => setBody(e.target.value)} />
      </label>
      <label>
        Ngày cập nhật nội dung (tuỳ chọn)
        <input type="date" value={lastUpdated} onChange={(e) => setLastUpdated(e.target.value)} />
      </label>
      <label>
        Ảnh minh hoạ (tuỳ chọn): đường dẫn `/anh/ten-file.png` (ảnh trong dự án) hoặc `https://...`
        <input value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} placeholder="/anh/..." />
      </label>
      <label>
        Nguồn & giấy phép ảnh (bắt buộc nếu ảnh từ mạng)
        <input value={imageCredit} onChange={(e) => setImageCredit(e.target.value)} />
      </label>
      <label>
        Trạng thái
        <select value={status} onChange={(e) => setStatus(e.target.value as PostStatus)}>
          <option value="draft">Nháp — chỉ quản trị thấy</option>
          <option value="published">Công khai — hiện cho khách</option>
        </select>
      </label>

      {actionError && <p className="notice notice--warn">{actionError}</p>}

      <div className="bang__dau">
        <button type="button" className="ghost" onClick={onCancel}>
          Huỷ
        </button>
        {post && onDelete && (
          <button type="button" className="ghost" onClick={onDelete} disabled={saving}>
            Xoá bài
          </button>
        )}
        <button type="submit" disabled={saving}>
          {saving ? 'Đang lưu…' : 'Lưu'}
        </button>
      </div>
    </form>
  );
}

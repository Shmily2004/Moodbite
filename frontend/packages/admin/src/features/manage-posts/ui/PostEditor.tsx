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

  // Ảnh xem trước chỉ là tiện ích hiển thị: đường dẫn sai thì ảnh lỗi và ẩn đi, KHÔNG chặn
  // lưu. Việc chặn đường dẫn sai nằm ở backend (`validate_image`).
  const anhXemTruoc = imageUrl.trim();

  return (
    <form className="panel post-editor" onSubmit={submit}>
      <div className="post-editor__dau">
        <h3 className="panel__tieu-de">{post ? 'Sửa bài viết' : 'Bài viết mới'}</h3>
        <span className={status === 'published' ? 'pill pill--on' : 'pill pill--off'}>
          {status === 'published' ? 'Sẽ công khai' : 'Nháp'}
        </span>
      </div>

      <div className="post-editor__luoi">
        <label className="post-editor__rong">
          Tiêu đề
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label className="post-editor__rong">
          Tóm tắt <span className="post-editor__goi-y">hiện ở danh sách tin tức</span>
          <input value={summary} onChange={(e) => setSummary(e.target.value)} />
        </label>
        <label className="post-editor__rong">
          Nội dung
          <textarea rows={12} value={body} onChange={(e) => setBody(e.target.value)} />
        </label>

        <fieldset className="post-editor__rong post-editor__anh-khung">
          <legend>Ảnh minh hoạ <span className="post-editor__goi-y">(tuỳ chọn)</span></legend>
          <div className="post-editor__anh-hang">
            <div className="post-editor__anh-nhap">
              <label>
                Đường dẫn ảnh
                <input
                  value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                  placeholder="/anh/ten-file.png hoặc https://..."
                />
                <span className="post-editor__goi-y">
                  Ảnh trong dự án bắt đầu bằng <code>/anh/</code>. Ảnh từ mạng phải bắt đầu bằng <code>https://</code> và ghi nguồn bên dưới.
                </span>
              </label>
              <label>
                Nguồn &amp; giấy phép ảnh
                <input value={imageCredit} onChange={(e) => setImageCredit(e.target.value)} />
              </label>
            </div>
            {anhXemTruoc && (
              <img
                className="post-editor__anh-xem"
                src={anhXemTruoc}
                alt="Xem trước ảnh minh hoạ"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
                onLoad={(e) => {
                  e.currentTarget.style.display = '';
                }}
              />
            )}
          </div>
        </fieldset>

        <label>
          Ngày cập nhật nội dung <span className="post-editor__goi-y">(tuỳ chọn)</span>
          <input type="date" value={lastUpdated} onChange={(e) => setLastUpdated(e.target.value)} />
        </label>
        <label>
          Trạng thái
          <select value={status} onChange={(e) => setStatus(e.target.value as PostStatus)}>
            <option value="draft">Nháp — chỉ quản trị thấy</option>
            <option value="published">Công khai — hiện cho khách</option>
          </select>
        </label>
      </div>

      {actionError && <p className="notice notice--warn">{actionError}</p>}

      <div className="post-editor__chan">
        {post && onDelete && (
          <button type="button" className="ghost post-editor__xoa" onClick={onDelete} disabled={saving}>
            Xoá bài
          </button>
        )}
        <button type="button" className="ghost" onClick={onCancel}>
          Huỷ
        </button>
        <button type="submit" disabled={saving}>
          {saving ? 'Đang lưu…' : 'Lưu'}
        </button>
      </div>
    </form>
  );
}
